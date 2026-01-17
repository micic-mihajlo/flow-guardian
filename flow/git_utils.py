"""Git operations for context capture."""
from git import Repo
from git.exc import InvalidGitRepositoryError
from pathlib import Path
from typing import Optional


def get_repo() -> Optional[Repo]:
    """Get git repo for current directory."""
    try:
        return Repo(Path.cwd(), search_parent_directories=True)
    except InvalidGitRepositoryError:
        return None


def get_git_state(repo: Repo) -> dict:
    """Extract current git state."""
    try:
        branch = repo.active_branch.name
    except TypeError:
        branch = "detached HEAD"

    modified = [item.a_path for item in repo.index.diff(None)]
    staged = [item.a_path for item in repo.index.diff("HEAD")]

    recent_commits = []
    for commit in list(repo.iter_commits(max_count=5)):
        recent_commits.append(f"{commit.hexsha[:7]} - {commit.message.strip()[:50]}")

    try:
        diff = repo.git.diff("--stat")
    except:
        diff = ""

    return {
        "branch": branch,
        "head": repo.head.commit.hexsha,
        "modified_files": modified + staged,
        "recent_commits": recent_commits,
        "diff_summary": diff[:1000]
    }


def get_changes_since(repo: Repo, since_sha: str) -> str:
    """Get summary of changes since a commit."""
    try:
        commits = list(repo.iter_commits(f"{since_sha}..HEAD"))
        if not commits:
            return "No new commits"

        changes = []
        for commit in commits[:10]:
            author = commit.author.name
            msg = commit.message.strip().split("\n")[0][:60]
            changes.append(f"* {author}: {msg}")

        return "\n".join(changes)
    except:
        return "Unable to determine changes"
