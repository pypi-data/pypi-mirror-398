from __future__ import annotations

import subprocess


def run_git_command(args: list[str]) -> subprocess.CompletedProcess:
    """
    Run a git command with the given args.

    Returns:
        a CompletedProcess object
    """
    # ignoring S603 because args is controlled internally so no injection risk
    cmd = ["git", *args]
    return subprocess.run(  # noqa: S603
        cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )


def is_inside_working_tree() -> bool:
    """
    Check if we're inside a working directory (can execute commit and diff
    commands)
    """
    out = run_git_command(["rev-parse", "--is-inside-work-tree"])
    return out.returncode == 0 and out.stdout.strip() == "true"


def is_changed() -> bool:
    """
    Check if we have changed files
    """
    out = run_git_command(["diff", "--name-only"])
    return (out.returncode == 0) and (out.stdout.strip() != "")


def get_diff() -> str | None:
    """
    Get the diff from the current working directory.

    Returns:
        the diff as a string (raw Git output), or None if an error occurred
    """
    if not is_changed():
        return ""

    out = run_git_command(["--no-pager", "diff", "--no-color"])

    if out.returncode == 0:
        return out.stdout.strip()
    return None


def commit(msg: str) -> tuple[int, str]:
    """
    commit with msg as the commit text.
    Returns:
        the return value from running the commit command, stdout, and stderr
    """
    out = run_git_command(["commit", "-a", "-m", msg])
    ret = out.stdout.strip() if out.stdout.strip() != "" else out.stderr.strip()
    return out.returncode, ret


def clean_diff(diff: str | None) -> str:
    """
    Remove unnecessary information from the diff.
    """
    if diff is None:
        return ""

    lines = diff.splitlines()
    for line in lines[:]:
        if line.startswith(("diff --git", "index ", "warning:")):
            lines.remove(line)
    return "\n".join(lines)


def get_clean_diff() -> str:
    """
    Get the current git diff, sanitized for LLM consumption.
    """
    diff = get_diff()
    return clean_diff(diff)
