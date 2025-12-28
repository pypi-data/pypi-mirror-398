"""
JavaScript/TypeScriptコード解析モジュール
JSDocコメントを抽出してAPI情報を生成
"""

from pathlib import Path
import re
from typing import TYPE_CHECKING

from ...models import APIInfo
from .base_parser import BaseParser

if TYPE_CHECKING:
    from ...models import APIParameter


class JSParser(BaseParser):
    """JavaScript/TypeScriptコード解析クラス"""

    PARSER_TYPE: str = "javascript"  # type: ignore[misc]

    # JSDocコメントのパターン
    JSDOC_PATTERN = re.compile(
        r"/\*\*\s*\n(.*?)\*/\s*\n\s*(?:export\s+)?(?:async\s+)?(?:(?:function|class)\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=|(\w+)\s*\([^)]*\)\s*\{)",
        re.DOTALL | re.MULTILINE,
    )

    # 関数定義のパターン
    FUNCTION_PATTERN = re.compile(
        r"(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>|(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>|(\w+)\s*\([^)]*\)\s*\{)",
        re.MULTILINE,
    )

    # クラス定義のパターン
    CLASS_PATTERN = re.compile(r"(?:export\s+)?class\s+(\w+)", re.MULTILINE)

    def _parse_to_ast(self, content: str, file_path: Path) -> str:
        """ASTにパース（正規表現ベースなのでコンテンツをそのまま返す）"""
        return content

    def _extract_elements(self, content: str, file_path: Path) -> list[APIInfo]:
        """要素を抽出"""
        apis = []
        class_stack = []

        # クラス定義を先に抽出してclass_stackを作成
        for match in self.CLASS_PATTERN.finditer(content):
            name = match.group(1)
            class_start = match.start()
            # 対応する}を見つける
            brace_count = 0
            class_end = class_start
            for i, char in enumerate(content[class_start:], class_start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        class_end = i + 1
                        break
            class_stack.append((name, class_start, class_end))

        # JSDoc付きの関数/クラスを抽出
        for match in self.JSDOC_PATTERN.finditer(content):
            docstring = match.group(1).strip()
            name = match.group(2) or match.group(3) or match.group(4)

            # 行番号を取得
            line_num = content[: match.start()].count("\n") + 1

            # 関数かクラスかを判定
            api_type = "function"
            if "class" in match.group(0):
                api_type = "class"
            elif match.group(4):  # メソッドの場合
                api_type = "method"

            # シグネチャを抽出
            signature = self._extract_signature(content, match.end(), name, api_type)

            # パラメータを抽出
            parameters = self._extract_parameters(docstring)

            apis.append(
                APIInfo(
                    name=name,
                    type=api_type,
                    signature=signature,
                    docstring=self._clean_jsdoc(docstring),
                    parameters=parameters,
                    line_number=line_num,
                    file_path=str(file_path.relative_to(self.project_root)),
                    language="javascript",
                )
            )

        # JSDocなしの関数も抽出（簡易版）
        for match in self.FUNCTION_PATTERN.finditer(content):
            name = match.group(1) or match.group(2) or match.group(3) or match.group(4)
            if name and not any(api.name == name for api in apis):
                line_num = content[: match.start()].count("\n") + 1

                # クラス内にあるかをチェック
                api_type = "function"
                for _class_name, class_start, class_end in class_stack:
                    if class_start < match.start() < class_end:
                        api_type = "method"
                        break

                signature = self._extract_signature(content, match.end(), name, api_type)
                apis.append(
                    APIInfo(
                        name=name,
                        type=api_type,
                        signature=signature,
                        docstring="",
                        line_number=line_num,
                        file_path=str(file_path.relative_to(self.project_root)),
                        language="javascript",
                    )
                )

        for match in self.CLASS_PATTERN.finditer(content):
            name = match.group(1)
            if name and not any(api.name == name for api in apis):
                line_num = content[: match.start()].count("\n") + 1
                signature = f"class {name}"
                apis.append(
                    APIInfo(
                        name=name,
                        type="class",
                        signature=signature,
                        docstring="",
                        line_number=line_num,
                        file_path=str(file_path.relative_to(self.project_root)),
                        language="javascript",
                    )
                )

        return apis

    def _extract_signature(self, content: str, start_pos: int, name: str, api_type: str) -> str:
        """
        シグネチャを抽出

        Args:
            content: ファイル内容
            start_pos: 開始位置
            name: 関数/クラス名
            api_type: 'function' または 'class'

        Returns:
            シグネチャ文字列
        """
        # 簡易的なシグネチャ抽出
        if api_type == "class":
            return f"class {name}"

        # 関数のシグネチャを抽出（簡易版）
        lines = content[start_pos : start_pos + 10].split("\n")
        if lines:
            first_line = lines[0].strip()
            if "(" in first_line:
                end_pos = first_line.find(")") + 1
                if end_pos > 0:
                    # 関数名を含むシグネチャを構築
                    sig = first_line[:end_pos]
                    # 関数名が含まれていない場合は追加
                    if name not in sig:
                        # パラメータ部分を抽出
                        param_start = sig.find("(")
                        if param_start >= 0:
                            return f"function {name}{sig[param_start:]}"
                    return sig

        return f"function {name}(...)"

    def _extract_parameters(self, docstring: str) -> "list[APIParameter] | None":
        """
        JSDocからパラメータを抽出

        Args:
            docstring: JSDocコメントの内容

        Returns:
            APIParameterオブジェクトのリスト、またはNone
        """
        from ...models import APIParameter

        params: "list[APIParameter]" = []
        lines = docstring.split("\n")
        for line in lines:
            # * を削除してから処理
            line = line.strip().lstrip("*").strip()
            if line.startswith("@param"):
                # @param {type} name - description
                # ドット付きのパラメータ名を処理
                parts = line.split()
                if len(parts) >= 3:
                    param_type = parts[1].strip("{}") if len(parts) > 1 else "any"
                    param_name = parts[2].rstrip("-").strip()
                    # ドットを含む場合は最後の部分のみを取得
                    if "." in param_name:
                        param_name = param_name.split(".")[-1]
                    # 説明を抽出（- 以降）
                    description = None
                    if "-" in line:
                        desc_start = line.find("-") + 1
                        description = line[desc_start:].strip()
                    params.append(
                        APIParameter(
                            name=param_name,
                            type=param_type,
                            description=description,
                        )
                    )
        return params if params else None

    def _clean_jsdoc(self, docstring: str) -> str:
        """
        JSDocコメントをクリーンアップ

        Args:
            docstring: 生のJSDoc文字列

        Returns:
            クリーンアップされた文字列
        """
        # * を削除
        lines = [line.strip().lstrip("*").strip() for line in docstring.split("\n")]
        return "\n".join(lines).strip()

    def get_supported_extensions(self) -> list[str]:
        """サポートする拡張子を返す"""
        from ...detectors.detector_patterns import DetectorPatterns

        return DetectorPatterns.get_source_extensions(
            "javascript"
        ) + DetectorPatterns.get_source_extensions("typescript")
