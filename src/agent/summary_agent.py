"""Summary agent for formatting executive reports and manual approval reminders."""

from src.core.models import ProvisioningReport
from src.core.report_generator import ReportGenerator

class SummaryAgent:
    """
    Summary Agent creates human-oriented summaries detailing automated actions
    and explicit manual approval requirements.
    """

    def __init__(self):
        self.report_generator = ReportGenerator()

    def create_summary(self, report: ProvisioningReport) -> str:
        """Renders executive terminal report."""
        return self.report_generator.generate_terminal_report(report)

    def create_github_summary(self, report: ProvisioningReport, owner_email: str = "Unassigned", file_path: str = "") -> str:
        """Renders rich Markdown summary for GitHub Pull Requests and issue comments."""
        return self.report_generator.generate_github_markdown_summary(report, owner_email, file_path)

    def get_default_manual_steps(self) -> list:
        """Returns standard enterprise human-in-the-loop checklist."""
        return [
            "Product owner approval must be confirmed manually",
            "PR must be reviewed and approved manually",
            "Merge must be performed by authorized reviewer"
        ]

