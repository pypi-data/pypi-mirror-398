import os.path
import subprocess
import warnings
from typing import Optional

from pydantic import BaseModel


class GitInfo(BaseModel):
    repo_name: str
    branch_name: str
    sha: str


def find_git_root(path: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_git_repo_has_changed(path: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", path, "diff", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def get_current_commit(path: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as err:
        warnings.warn(f"Сouldn't get the meta information about git. Error: {str(err)}.")
        return None


def get_current_branch(path: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        branch = result.stdout.strip()
        if branch != "HEAD":
            return branch

        result = subprocess.run(
            ["git", "-C", path, "name-rev", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        name_rev = result.stdout.strip()
        if name_rev:
            return f"{name_rev} (detached)"
        return "detached HEAD"
    except subprocess.CalledProcessError as err:
        warnings.warn(f"Сouldn't get the meta information about git. Error: {str(err)}.")
        return None


def get_git_info(local_path: str) -> Optional[GitInfo]:
    root = find_git_root(local_path)
    if not root:
        return None
    repo_name = os.path.basename(root)
    branch_name = get_current_branch(local_path)
    sha = get_current_commit(local_path)
    if not (branch_name or sha):
        return None

    if get_git_repo_has_changed(local_path):
        warnings.warn(f"Repo {repo_name} have changes.")
        branch_name += " (uncommitted changes)"

    return GitInfo(repo_name=repo_name, branch_name=branch_name, sha=sha)
