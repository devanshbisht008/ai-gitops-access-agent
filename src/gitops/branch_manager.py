"""Branch manager for creating Git feature branches."""

from src.core.models import NormalizedRequest
from src.gitops.github_client import GitHubClient

class BranchManager:
    """Manages Git feature branch creation."""

    def __init__(self, client: GitHubClient):
        self.client = client

    def generate_branch_name(self, request: NormalizedRequest) -> str:
        """Generates standard feature branch name."""
        clean_req_id = request.request_id.lower().replace("_", "-")
        clean_access = request.access_type.lower().replace("_", "-")
        return f"feature/{clean_req_id}-{clean_access}-access"

    def create_branch(self, request: NormalizedRequest) -> str:
        """
        Creates a new Git feature branch.
        In local mode: simulates branch creation.
        In github mode: calls GitHub API or git CLI.
        """
        branch_name = self.generate_branch_name(request)

        if self.client.is_local_mode():
            # Local simulation mode
            return branch_name

        # GitHub mode execution
        if self.client._gh_instance:
            try:
                repo = self.client._gh_instance.get_repo(f"{self.client.owner}/{self.client.repo}")
                base_ref = repo.get_git_ref(f"heads/{self.client.base_branch}")
                repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_ref.object.sha)
                return branch_name
            except Exception as e:
                # Fallback to local git CLI if API fails
                self.client.run_git_command(["checkout", "-b", branch_name])
                return branch_name

        # Fallback git CLI
        self.client.run_git_command(["checkout", "-b", branch_name])
        return branch_name
