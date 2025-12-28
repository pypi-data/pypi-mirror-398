import subprocess


def get_python_command() -> str:
    """利用可能なPythonコマンドを取得する（uv優先）"""
    # uvが利用可能か確認
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return "uv run python3"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # python3が利用可能か確認
    try:
        subprocess.run(["python3", "--version"], capture_output=True, check=True)
        return "python3"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return "python"


def run_command(
    command: list[str], cwd: str | None = None, capture_output: bool = False
) -> tuple[int, str, str]:
    """コマンドを実行する"""
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=capture_output, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_changed_files(staged: bool = False) -> list[str]:
    """変更されたファイルを取得する"""
    cmd = ["git", "diff", "--name-only"]
    if staged:
        cmd.append("--cached")

    code, stdout, _ = run_command(cmd)
    if code != 0:
        return []

    return [f for f in stdout.splitlines() if f.strip()]


def is_git_repo(path: str) -> bool:
    """Gitリポジトリか確認する"""
    code, _, _ = run_command(["git", "rev-parse", "--is-inside-work-tree"], cwd=path)
    return code == 0
