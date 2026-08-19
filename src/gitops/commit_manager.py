"""Commit manager for staging and committing GitOps changes."""

from src.core.models import NormalizedRequest
from src.gitops.github_client import GitHubClient

class CommitManager:
    """Manages Git commits for YAML configuration updates."""

    def __init__(self, client: GitHubClient):
        self.client = client

    def generate_commit_message(self, request: NormalizedRequest) -> str:
        """Generates conventional commit message."""
        return f"feat(gitops): provision {request.access_type} access for {request.consumer} on {request.provider} [{request.request_id}]"

    def commit_changes(self, request: NormalizedRequest, file_path: str, branch_name: str) -> str:
        """
        Commits modified YAML file to branch.
        In local mode: returns simulated commit hash / message.
        In github mode: commits file via PyGithub or local git CLI.
        """
        commit_msg = self.generate_commit_message(request)

        if self.client.is_local_mode():
            return f"Simulated Commit: '{commit_msg}' on branch '{branch_name}'"

        if self.client._gh_instance:
            try:
                repo = self.client._gh_instance.get_repo(f"{self.client.owner}/{self.client.repo}")
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Get existing file SHA if updating
                try:
                    contents = repo.get_contents(file_path, ref=branch_name)
                    repo.update_file(contents.path, commit_msg, content, contents.sha, branch=branch_name)
                except Exception:
                    repo.create_file(file_path, commit_msg, content, branch=branch_name)

                return f"Committed to GitHub branch '{branch_name}': '{commit_msg}'"
            except Exception as e:
                # Fallback git CLI
                self.client.run_git_command(["add", file_path])
                self.client.run_git_command(["commit", "-m", commit_msg])
                return f"Git CLI Commit: '{commit_msg}'"

        # Fallback git CLI
        self.client.run_git_command(["add", file_path])
        self.client.run_git_command(["commit", "-m", commit_msg])
        return f"Git CLI Commit: '{commit_msg}'"
