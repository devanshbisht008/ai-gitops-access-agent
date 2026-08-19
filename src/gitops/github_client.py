"""GitHub API and local Git operation client abstraction."""

import os
import subprocess
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

class GitHubClient:
    """
    Client abstraction for Git and GitHub operations.
    Supports 'local' simulation mode and 'github' API mode.
    """

    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or os.getenv("MODE", "local")).lower()
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.owner = os.getenv("GITHUB_OWNER", "example-org")
        self.repo = os.getenv("GITHUB_REPO", "data-product-access-config")
        self.base_branch = os.getenv("BASE_BRANCH", "main")
        self._gh_instance = None

        if self.mode == "github":
            self._init_pygithub()

    def _init_pygithub(self) -> None:
        """Initializes PyGithub instance if token is available."""
        if not self.token:
            return
        try:
            from github import Github
            self._gh_instance = Github(self.token)
        except ImportError:
            self._gh_instance = None

    def is_local_mode(self) -> bool:
        """Returns True if running in local simulation mode."""
        return self.mode == "local"

    def run_git_command(self, cmd: list, cwd: str = ".") -> Tuple[int, str, str]:
        """Runs local git CLI subprocess command."""
        try:
            res = subprocess.run(
                ["git"] + cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as e:
            return 1, "", str(e)

    def post_pr_comment(self, pr_number: int, comment_body: str) -> bool:
        """Posts a Markdown comment to an open GitHub Pull Request or Issue."""
        if self.is_local_mode():
            return True
        if self._gh_instance:
            try:
                repo = self._gh_instance.get_repo(f"{self.owner}/{self.repo}")
                pr = repo.get_pull(pr_number)
                pr.create_issue_comment(comment_body)
                return True
            except Exception:
                return False
        return False

