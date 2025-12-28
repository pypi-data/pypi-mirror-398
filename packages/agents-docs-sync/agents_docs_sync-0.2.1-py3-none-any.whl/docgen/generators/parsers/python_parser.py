"""
Pythonコード解析モジュール
docstringを抽出してAPI情報を生成
"""

import ast
from pathlib import Path
import sys

from ...models import APIInfo
from .base_parser import BaseParser

# Python 3.9+ では ast.unparse が利用可能
if sys.version_info >= (3, 9):
    _ast_unparse = ast.unparse
else:
    # Python 3.8以下では簡易的な実装を使用
    def _ast_unparse(node):
        """簡易的なASTノードの文字列化"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Str):  # Python 3.7以前
            return repr(node.s)
        else:
            return str(node)


class PythonParser(BaseParser):
    """Pythonコード解析クラス"""

    PARSER_TYPE: str = "python"  # type: ignore[misc]

    def _parse_to_ast(self, content: str, file_path: Path) -> ast.AST | None:
        """ASTにパース"""
        try:
            return ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return None

    def _extract_elements(self, tree: ast.AST | None, file_path: Path) -> list[APIInfo]:
        """要素を抽出"""
        if tree is None:
            return []

        visitor = PythonASTVisitor(file_path, self.project_root)
        visitor.visit(tree)
        return visitor.apis

    def get_supported_extensions(self) -> list[str]:
        """サポートする拡張子を返す"""
        from ...detectors.detector_patterns import DetectorPatterns

        return DetectorPatterns.get_source_extensions("python")


class PythonASTVisitor(ast.NodeVisitor):
    """Python AST訪問クラス"""

    def __init__(self, file_path: Path, project_root: Path):
        self.file_path = file_path
        self.project_root = project_root
        self.apis: list[APIInfo] = []
        self.class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        # プライベートクラス（_で始まる）はスキップ（オプション）
        if node.name.startswith("_") and not node.name.startswith("__"):
            return

        signature = self._get_class_signature(node)
        docstring = ast.get_docstring(node) or ""

        self.apis.append(
            APIInfo(
                name=node.name,
                type="class",
                signature=signature,
                docstring=docstring or None,
                line_number=node.lineno,
                file_path=str(self.file_path.relative_to(self.project_root)),
                language="python",
            )
        )

        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node):
        self._visit_function(node, "function")

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node, "function")

    def _visit_function(self, node, base_type: str):
        # プライベート関数（_で始まる）はスキップ（オプション）
        if node.name.startswith("_") and not node.name.startswith("__"):
            return

        api_type = "method" if self.class_stack else base_type
        signature = self._get_function_signature(node)
        docstring = ast.get_docstring(node) or ""

        # パラメータと戻り値の型を取得
        from ...models import APIParameter

        api_parameters: list[APIParameter] = []
        for arg in node.args.args:
            param_name = arg.arg
            param_type = _ast_unparse(arg.annotation) if arg.annotation else "Any"
            api_parameters.append(
                APIParameter(
                    name=param_name,
                    type=param_type,
                    description=None,
                )
            )

        return_type = None
        if node.returns:
            return_type = _ast_unparse(node.returns)

        self.apis.append(
            APIInfo(
                name=node.name,
                type=api_type,
                signature=signature,
                docstring=docstring or None,
                parameters=api_parameters if api_parameters else None,
                return_type=return_type or None,
                line_number=node.lineno,
                file_path=str(self.file_path.relative_to(self.project_root)),
                language="python",
            )
        )

    def _get_function_signature(self, node) -> str:
        """
        関数のシグネチャを文字列として取得

        Args:
            node: AST関数ノード (FunctionDef or AsyncFunctionDef)

        Returns:
            シグネチャ文字列
        """
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {_ast_unparse(arg.annotation)}"
            args.append(arg_str)

        def_type = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        signature = f"{def_type} {node.name}({', '.join(args)})"
        if node.returns:
            signature += f" -> {_ast_unparse(node.returns)}"
        signature += ":"

        return signature

    def _get_class_signature(self, node: ast.ClassDef) -> str:
        """
        クラスのシグネチャを文字列として取得

        Args:
            node: ASTクラスノード

        Returns:
            シグネチャ文字列
        """
        return f"class {node.name}:"
