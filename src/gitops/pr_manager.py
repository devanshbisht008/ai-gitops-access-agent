"""Pull Request manager for GitOps workflow."""

from typing import Optional
from src.core.models import NormalizedRequest, ProvisioningReport, ValidationResult, AccessCheckResult
from src.core.report_generator import ReportGenerator
from src.gitops.github_client import GitHubClient

class PullRequestManager:
    """Manages creation and formatting of Pull Requests."""

    def __init__(self, client: GitHubClient):
        self.client = client

    def generate_pr_title(self, request: NormalizedRequest) -> str:
        """Generates Pull Request title."""
        return f"[Access Provisioning] Request {request.request_id}: {request.consumer} -> {request.provider} ({request.access_type})"

    def generate_pr_body(
        self,
        request: NormalizedRequest,
        owner_email: str,
        file_path: str,
        report: Optional[ProvisioningReport] = None
    ) -> str:
        """Generates structured Markdown PR body with environment flow, fulfillment status, and approval checklist."""
        if report is None:
            report = ProvisioningReport(
                request_id=request.request_id,
                normalized_request=request,
                validation_result=ValidationResult(is_valid=True),
                existing_access_result=AccessCheckResult(access_exists=False),
                action_taken={"Feature branch created": "active", "YAML updated": file_path},
                manual_steps=[]
            )
        return ReportGenerator.generate_github_markdown_summary(report, owner_email, file_path)

    def create_pull_request(
        self,
        request: NormalizedRequest,
        branch_name: str,
        owner_email: str,
        file_path: str,
        report: Optional[ProvisioningReport] = None
    ) -> str:
        """
        Creates or simulates Pull Request.
        In local mode: returns simulated PR URL.
        In github mode: calls GitHub API to open Pull Request.
        """
        title = self.generate_pr_title(request)
        body = self.generate_pr_body(request, owner_email, file_path, report)

        if self.client.is_local_mode():
            pr_id = request.request_id.replace("REQ-", "")
            return f"https://github.com/{self.client.owner}/{self.client.repo}/pull/{pr_id} (Local Simulation)"

        if self.client._gh_instance:
            try:
                repo = self.client._gh_instance.get_repo(f"{self.client.owner}/{self.client.repo}")
                pr = repo.create_pull(
                    title=title,
                    body=body,
                    head=branch_name,
                    base=self.client.base_branch
                )
                return pr.html_url
            except Exception as e:
                return f"GitHub PR creation failed (API Error: {str(e)}). Simulated PR created for branch '{branch_name}'."

        return f"https://github.com/{self.client.owner}/{self.client.repo}/pull/new/{branch_name} (Simulated)"

    def post_summary_comment(self, pr_number: int, report: ProvisioningReport, owner_email: str, file_path: str) -> bool:
        """Posts a completion summary comment to an open GitHub PR."""
        comment_body = ReportGenerator.generate_github_markdown_summary(report, owner_email, file_path)
        return self.client.post_pr_comment(pr_number, comment_body)

