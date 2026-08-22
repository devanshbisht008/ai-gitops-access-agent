"""Unit tests for GitHub Markdown Ticket Summary feature."""

import pytest
from src.core.models import NormalizedRequest, ValidationResult, AccessCheckResult, ProvisioningReport
from src.core.report_generator import ReportGenerator
from src.agent.summary_agent import SummaryAgent
from src.gitops.pr_manager import PullRequestManager
from src.gitops.github_client import GitHubClient

@pytest.fixture
def sample_normalized_request():
    return NormalizedRequest(
        request_id="REQ-1001",
        consumer="DS-Digital-AB-Testing-Evaluation",
        provider="DS-TDA-Governance",
        source_environment="prod",
        target_environment="dev",
        access_type="read",
        access_scope="schema_only",
        requested_by="jane.doe@company.com",
        business_justification="Need governance data for model evaluation."
    )

@pytest.fixture
def sample_valid_report(sample_normalized_request):
    return ProvisioningReport(
        request_id=sample_normalized_request.request_id,
        normalized_request=sample_normalized_request,
        validation_result=ValidationResult(is_valid=True),
        existing_access_result=AccessCheckResult(access_exists=False),
        action_taken={"Feature branch created": "feature/REQ-1001-read-access"},
        manual_steps=["Owner approval required"]
    )

def test_environment_flow_cross_env(sample_valid_report):
    summary = ReportGenerator.generate_github_markdown_summary(
        sample_valid_report,
        owner_email="owner@company.com",
        file_path="data_products/DS-TDA-Governance.yaml"
    )
    assert "PROD ➔ DEV" in summary
    assert "Cross-Environment Mapping" in summary

def test_environment_flow_same_env(sample_normalized_request):
    sample_normalized_request.source_environment = "dev"
    sample_normalized_request.target_environment = "dev"
    report = ProvisioningReport(
        request_id=sample_normalized_request.request_id,
        normalized_request=sample_normalized_request,
        validation_result=ValidationResult(is_valid=True),
        existing_access_result=AccessCheckResult(access_exists=False),
        action_taken={"Feature branch created": "feature/REQ-1001-read-access"},
        manual_steps=[]
    )
    summary = ReportGenerator.generate_github_markdown_summary(report, "owner@company.com")
    assert "DEV ➔ DEV" in summary
    assert "Same-Environment Mapping" in summary

def test_fulfillment_status_fulfilled(sample_valid_report):
    summary = ReportGenerator.generate_github_markdown_summary(sample_valid_report, "owner@company.com")
    assert "100% Fulfilled" in summary

def test_fulfillment_status_aborted(sample_normalized_request):
    report = ProvisioningReport(
        request_id=sample_normalized_request.request_id,
        normalized_request=sample_normalized_request,
        validation_result=ValidationResult(is_valid=False, errors=["Naming rule error"]),
        existing_access_result=AccessCheckResult(access_exists=False),
        action_taken={},
        manual_steps=[]
    )
    summary = ReportGenerator.generate_github_markdown_summary(report, "owner@company.com")
    assert "Aborted" in summary
    assert "Naming rule error" in summary

def test_yaml_diff_snippet_inclusion(sample_valid_report):
    summary = ReportGenerator.generate_github_markdown_summary(
        sample_valid_report,
        owner_email="owner@company.com",
        file_path="data_products/DS-TDA-Governance.yaml"
    )
    assert "```yaml" in summary
    assert "+   - consumer: DS-Digital-AB-Testing-Evaluation" in summary
    assert "+     target_environment: dev" in summary
    assert "+     status: pending_pr" in summary

def test_summary_agent_integration(sample_valid_report):
    agent = SummaryAgent()
    markdown = agent.create_github_summary(sample_valid_report, "owner@company.com")
    assert "## 🔒 AI-Assisted GitOps Access Provisioning Summary" in markdown
    assert "jane.doe@company.com" in markdown

def test_pr_manager_body_generation(sample_normalized_request, sample_valid_report):
    gh_client = GitHubClient(mode="local")
    pr_mgr = PullRequestManager(gh_client)
    body = pr_mgr.generate_pr_body(sample_normalized_request, "owner@company.com", "data_products/DS-TDA-Governance.yaml", sample_valid_report)
    assert "PROD ➔ DEV" in body
    assert "DS-Digital-AB-Testing-Evaluation" in body
