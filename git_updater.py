import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent


def git_pull() -> str:
    """
    Pull latest code từ remote.
    Trả về output string. Raise nếu lỗi.
    """
    result = subprocess.run(
        ["git", "pull"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout.strip() or result.stderr.strip()
    if result.returncode != 0:
        raise RuntimeError(f"git pull thất bại: {output}")
    return output
