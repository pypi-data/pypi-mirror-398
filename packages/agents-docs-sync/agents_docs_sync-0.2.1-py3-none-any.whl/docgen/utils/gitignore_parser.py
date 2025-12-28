""".gitignoreパーサーユーティリティ

.gitignoreファイルを読み込んで、パターンマッチングを行うためのユーティリティ。
"""

from pathlib import Path
import re

from .logger import get_logger

logger = get_logger(__name__)


class GitIgnoreMatcher:
    """`.gitignore`パターンを解析してマッチングを行うクラス"""

    def __init__(self, project_root: Path, gitignore_path: Path | None = None):
        """
        初期化

        Args:
            project_root: プロジェクトルートディレクトリ
            gitignore_path: .gitignoreファイルのパス（Noneの場合はproject_root/.gitignore）
        """
        self.project_root = Path(project_root).resolve()
        self.gitignore_path = gitignore_path or (self.project_root / ".gitignore")
        self.patterns: list[
            tuple[bool, str, re.Pattern[str]]
        ] = []  # (negated, pattern, compiled_regex)
        self._load_patterns()

    def _load_patterns(self) -> None:
        """`.gitignore`ファイルからパターンを読み込む"""
        if not self.gitignore_path.exists():
            logger.debug(f".gitignore not found: {self.gitignore_path}")
            return

        try:
            with open(self.gitignore_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    pattern = self._parse_line(line)
                    if pattern:
                        negated, pattern_str = pattern
                        compiled = self._compile_pattern(pattern_str)
                        if compiled:
                            self.patterns.append((negated, pattern_str, compiled))
                            logger.debug(
                                f"Loaded pattern (line {line_num}): {'!' if negated else ''}{pattern_str}"
                            )
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to read .gitignore: {e}")

    def _parse_line(self, line: str) -> tuple[bool, str] | None:
        """
        .gitignoreの行をパース

        Args:
            line: .gitignoreの行

        Returns:
            (negated, pattern) のタプル、またはNone（無効な行の場合）
        """
        # コメントと空行をスキップ
        line = line.strip()
        if not line or line.startswith("#"):
            return None

        # 否定パターン（!で始まる）
        negated = False
        if line.startswith("!"):
            negated = True
            line = line[1:].strip()
            if not line:
                return None

        # 末尾の空白を削除（.gitignoreの仕様）
        line = line.rstrip()

        return (negated, line)

    def _compile_pattern(self, pattern: str) -> re.Pattern[str] | None:
        """
        .gitignoreパターンを正規表現にコンパイル

        Args:
            pattern: .gitignoreパターン

        Returns:
            コンパイルされた正規表現、またはNone
        """
        if not pattern:
            return None

        original_pattern = pattern

        # ディレクトリパターン（末尾が/）を検出
        is_dir_pattern = pattern.endswith("/")
        if is_dir_pattern:
            pattern = pattern[:-1]

        # ルートからの相対パス（先頭が/）を検出
        is_anchor = pattern.startswith("/")
        if is_anchor:
            pattern = pattern[1:]

        # パターンを正規表現に変換
        regex_parts = []

        # 先頭のアンカー
        if is_anchor:
            regex_parts.append(r"^")
        else:
            # 任意の位置からマッチ（パスの任意の部分、ディレクトリ名、またはファイル名）
            regex_parts.append(r"(^|/)")

        # パターンを正規表現に変換
        # 特殊文字をエスケープしてから、ワイルドカードを処理
        escaped_pattern = ""
        i = 0
        pattern_len = len(pattern)

        while i < pattern_len:
            char = pattern[i]

            if char == "*":
                # ** の場合は任意のディレクトリ階層
                if i + 1 < pattern_len and pattern[i + 1] == "*":
                    # **/ または /** の処理
                    if i + 2 < pattern_len and pattern[i + 2] == "/":
                        escaped_pattern += r".*"
                        i += 3
                    elif i > 0 and pattern[i - 1] == "/":
                        escaped_pattern += r".*"
                        i += 2
                    else:
                        # ** は任意の文字列（/を含む）
                        escaped_pattern += r".*"
                        i += 2
                else:
                    # * は / 以外の任意の文字
                    escaped_pattern += r"[^/]*"
                    i += 1
            elif char == "?":
                # ? は / 以外の任意の1文字
                escaped_pattern += r"[^/]"
                i += 1
            elif char == "[":
                # 文字クラス [abc] または [a-z] を処理
                j = i + 1
                char_class = "["
                if j < pattern_len and pattern[j] == "!":
                    char_class += "!"
                    j += 1
                # 文字クラス内の文字を収集
                while j < pattern_len:
                    if pattern[j] == "]":
                        char_class += "]"
                        escaped_pattern += char_class
                        i = j + 1
                        break
                    elif pattern[j] == "/":
                        # / を除外（文字クラスから除外）
                        j += 1
                    else:
                        char_class += pattern[j]
                        j += 1
                else:
                    # 閉じ括弧が見つからない場合は [ をリテラルとして扱う
                    escaped_pattern += re.escape("[")
                    i += 1
            elif char in r".^$+{}|()":
                # 正規表現の特殊文字をエスケープ
                escaped_pattern += re.escape(char)
                i += 1
            elif char == "/":
                # パス区切り文字
                escaped_pattern += "/"
                i += 1
            else:
                # 通常の文字もエスケープ（安全のため）
                escaped_pattern += re.escape(char)
                i += 1

        regex_parts.append(escaped_pattern)

        # パターンの終端
        if is_dir_pattern:
            # ディレクトリパターンの場合、/ で終わるか、パスの終端
            regex_parts.append(r"(/|$)")
        else:
            # ファイルパターンの場合、パスの終端または / の前
            regex_parts.append(r"(/|$)")

        regex_str = "".join(regex_parts)

        try:
            return re.compile(regex_str)
        except re.error as e:
            logger.debug(f"Failed to compile pattern '{original_pattern}': {e}, regex: {regex_str}")
            return None

    def is_ignored(self, file_path: Path) -> bool:
        """
        ファイルパスが.gitignoreで無視されるかどうかを判定

        Args:
            file_path: チェックするファイルパス（絶対パスまたは相対パス）

        Returns:
            無視される場合True
        """
        # プロジェクトルートからの相対パスを取得
        try:
            if file_path.is_absolute():
                rel_path = file_path.relative_to(self.project_root)
            else:
                rel_path = file_path
        except ValueError:
            # プロジェクトルート外のパスは無視しない
            return False

        # パスを文字列に変換（スラッシュ区切りに統一）
        path_str = str(rel_path).replace("\\", "/")

        # パターンを順にチェック（後のパターンが優先）
        result = False
        for negated, pattern_str, compiled_regex in self.patterns:
            if compiled_regex.search(path_str):
                result = not negated
                logger.debug(
                    f"Pattern matched: {'!' if negated else ''}{pattern_str} -> {path_str}"
                )

        return result

    def should_exclude_dir(self, dir_path: Path) -> bool:
        """
        ディレクトリを除外すべきかどうかを判定

        Args:
            dir_path: チェックするディレクトリパス

        Returns:
            除外すべき場合True
        """
        # ディレクトリ名だけでチェック（パス全体もチェック）
        try:
            if dir_path.is_absolute():
                rel_path = dir_path.relative_to(self.project_root)
            else:
                rel_path = dir_path
        except ValueError:
            return False

        path_str = str(rel_path).replace("\\", "/")

        # ディレクトリパターンまたはパス全体がマッチするかチェック
        for negated, _pattern_str, compiled_regex in self.patterns:
            if compiled_regex.search(path_str) or compiled_regex.search(path_str + "/"):
                return not negated

        return False


def load_gitignore_patterns(project_root: Path) -> GitIgnoreMatcher | None:
    """
    .gitignoreファイルを読み込んでマッチャーを作成

    Args:
        project_root: プロジェクトルートディレクトリ

    Returns:
        GitIgnoreMatcherインスタンス、またはNone（.gitignoreが存在しない場合）
    """
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        return None

    return GitIgnoreMatcher(project_root, gitignore_path)
