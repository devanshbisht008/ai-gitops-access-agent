"""Report generation utility for terminal formatting and audit logging."""

import json
from typing import Dict, Any
from src.core.models import ProvisioningReport

class ReportGenerator:
    """Formats executive terminal output and structured JSON logs."""

    @staticmethod
    def generate_terminal_report(report: ProvisioningReport) -> str:
        """Generates clear, human-readable terminal output."""
        norm = report.normalized_request
        val = report.validation_result
        exist = report.existing_access_result
        actions = report.action_taken

        lines = [
            "=" * 50,
            "AI-assisted GitOps Access Provisioning",
            "=" * 50,
            f"Request ID: {report.request_id}",
            "Normalized Request:",
            f"  Consumer: {norm.consumer}",
            f"  Provider: {norm.provider}",
            f"  Access: {norm.access_type}",
            f"  Scope: {norm.access_scope}",
            f"Validation: {'Passed' if val.is_valid else 'Failed'}",
        ]

        if not val.is_valid:
            lines.append("Errors:")
            for err in val.errors:
                lines.append(f"  - {err}")

        if exist:
            lines.append(f"Existing Access: {'Found' if exist.access_exists else 'Not Found'}")
            if exist.message:
                lines.append(f"  Details: {exist.message}")
        else:
            lines.append("Existing Access: Skipped (Validation Failed)")

        if actions:
            lines.append("Action Taken:")
            for key, val_str in actions.items():
                lines.append(f"  - {key}: {val_str}")

        if report.manual_steps:
            lines.append("Manual Step Required:")
            for step in report.manual_steps:
                lines.append(f"  - {step}")

        lines.append("=" * 50)
        return "\n".join(lines)

    @staticmethod
    def generate_json_audit(report: ProvisioningReport) -> str:
        """Generates a structured JSON string for logging/auditing."""
        payload = {
            "request_id": report.request_id,
            "normalized_request": report.normalized_request.to_dict(),
            "validation": {
                "is_valid": report.validation_result.is_valid,
                "errors": report.validation_result.errors,
                "warnings": report.validation_result.warnings,
            },
            "existing_access": {
                "exists": report.existing_access_result.access_exists if report.existing_access_result else False,
                "message": report.existing_access_result.message if report.existing_access_result else "",
            },
            "action_taken": report.action_taken,
            "manual_steps": report.manual_steps,
        }
        return json.dumps(payload, indent=2)

    @staticmethod
    def generate_github_markdown_summary(report: ProvisioningReport, owner_email: str = "Unassigned", file_path: str = "") -> str:
        """Generates a rich, structured GitHub Markdown summary report of the ticket request and fulfillment."""
        norm = report.normalized_request
        val = report.validation_result
        exist = report.existing_access_result

        # Determine Environment Flow
        src_env = norm.source_environment.upper() if norm.source_environment else "UNKNOWN"
        tgt_env = norm.target_environment.upper() if norm.target_environment else "UNKNOWN"
        env_flow_str = f"{src_env} ➔ {tgt_env}"
        if src_env != tgt_env:
            env_flow_badge = f"🔄 `{env_flow_str}` (Cross-Environment Mapping)"
        else:
            env_flow_badge = f"🟢 `{env_flow_str}` (Same-Environment Mapping)"

        # Determine Fulfillment Status
        if not val.is_valid:
            fulfillment_status = "❌ **Aborted (Policy Validation Violations)**"
        elif exist and exist.access_exists:
            fulfillment_status = "ℹ️ **Skipped (Access Already Active / Pending)**"
        elif report.action_taken and "Feature branch created" in report.action_taken:
            fulfillment_status = "✅ **100% Fulfilled (GitOps PR Open - Pending Merge)**"
        else:
            fulfillment_status = "⚠️ **Pending Execution / Action Required**"

        lines = [
            "## 🔒 AI-Assisted GitOps Access Provisioning Summary",
            "",
            "### 🎯 Ticket Requirement & Fulfillment",
            f"- **Request ID:** `{report.request_id}`",
            f"- **Requester (`requested_by`):** `{norm.requested_by}`",
            f"- **Data Product Owner:** `{owner_email}`",
            f"- **Requirement Fulfillment Status:** {fulfillment_status}",
            "",
            "### 🔄 Environment Flow & Access Specifications",
            "| Specification | Details |",
            "| :--- | :--- |",
            f"| **Environment Flow** | {env_flow_badge} |",
            f"| **Data Consumer** | `{norm.consumer}` |",
            f"| **Data Provider** | `{norm.provider}` |",
            f"| **Access Type** | `{norm.access_type}` |",
            f"| **Access Scope** | `{norm.access_scope}` |",
            f"| **Target Config File** | `{file_path or 'N/A'}` |",
            "",
            "### 📄 Business Justification",
            f"> {norm.business_justification}",
            "",
        ]

        # Validation errors if present
        if not val.is_valid and val.errors:
            lines.append("### ❌ Policy Validation Errors")
            for err in val.errors:
                lines.append(f"- {err}")
            lines.append("")

        # Diff / Changes made section
        if report.action_taken and "Feature branch created" in report.action_taken:
            rel_file = file_path if file_path else f"data_products/{norm.provider}.yaml"
            lines.extend([
                "### 📝 Changes Applied (YAML Diff)",
                f"**Updated File:** `{rel_file}`",
                "```yaml",
                f"+   - consumer: {norm.consumer}",
                f"+     environment: {norm.target_environment}",
                f"+     access_type: {norm.access_type}",
                f"+     access_scope: {norm.access_scope}",
                "+     status: pending_pr",
                f"+     requested_by: {norm.requested_by}",
                "```",
                "",
            ])

        # Manual Steps / Approval Checklist
        lines.extend([
            "---",
            "### ⚠️ Mandatory Human-in-the-Loop Approval Checklist",
            f"- [ ] **Data Product Owner Approval:** Confirmed approval from `{owner_email}`",
            "- [ ] **Governance Review:** Verified compliance with enterprise data sharing rules",
            "- [ ] **Pull Request Review:** Code changes inspected and approved by authorized reviewer",
            "- [ ] **Merge Execution:** Manual merge triggered to trigger provisioning pipelines",
            "",
            "*Automated by AI-assisted GitOps Access Provisioning Agent*",
        ])

        return "\n".join(lines)

