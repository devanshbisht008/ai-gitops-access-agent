"""Main CLI entrypoint for AI-assisted GitOps Access Provisioning Agent."""

import argparse
import os
import sys

# Ensure src module is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent.intake_agent import IntakeAgent
from src.agent.validation_agent import ValidationAgent
from src.agent.summary_agent import SummaryAgent
from src.core.owner_lookup import OwnerLookup
from src.core.yaml_access_checker import YAMLAccessChecker
from src.core.yaml_modifier import YAMLModifier
from src.core.models import ProvisioningReport
from src.gitops.github_client import GitHubClient
from src.gitops.branch_manager import BranchManager
from src.gitops.commit_manager import CommitManager
from src.gitops.pr_manager import PullRequestManager
from src.utils.logger import setup_logger

logger = setup_logger("main")

def run_pipeline(request_input: str, mode: str = "local", repo_dir: str = "sample_repo") -> ProvisioningReport:
    """Executes full access provisioning pipeline."""
    
    # 1. Intake Agent
    logger.info("Initializing Intake Agent...")
    intake_agent = IntakeAgent()
    raw_request = intake_agent.parse_input(request_input)

    # 2. Validation Agent
    logger.info("Running Validation Agent...")
    val_agent = ValidationAgent()
    norm_req, val_result = val_agent.process_and_validate(raw_request)

    summary_agent = SummaryAgent()

    if not val_result.is_valid:
        logger.warning("Request validation failed.")
        return ProvisioningReport(
            request_id=norm_req.request_id,
            normalized_request=norm_req,
            validation_result=val_result,
            existing_access_result=None,
            action_taken={"Status": "Aborted due to validation errors"},
            manual_steps=[]
        )

    # 3. Owner Lookup
    owner_lookup = OwnerLookup(mapping_csv_path=os.path.join(os.path.dirname(__file__), "..", "config", "owner_mapping.csv"))
    owner_email = owner_lookup.get_owner(norm_req.provider)

    # 4. Check Existing Access in YAML
    logger.info("Checking YAML configuration files for existing access...")
    yaml_checker = YAMLAccessChecker(repo_dir=repo_dir)
    access_check = yaml_checker.check_access_exists(norm_req)

    if access_check.access_exists:
        logger.info("Access already exists in YAML configuration. Skipping modification.")
        return ProvisioningReport(
            request_id=norm_req.request_id,
            normalized_request=norm_req,
            validation_result=val_result,
            existing_access_result=access_check,
            action_taken={
                "Action": "None (Access already active or pending)",
                "Provider File": yaml_checker.get_provider_yaml_path(norm_req.provider)
            },
            manual_steps=["No further action needed. Access already provisioned."]
        )

    # 5. Execute GitOps Automation (Feature Branch, YAML Modify, Commit, PR)
    logger.info("Access not found. Executing GitOps automation layer...")
    gh_client = GitHubClient(mode=mode)
    branch_mgr = BranchManager(gh_client)
    commit_mgr = CommitManager(gh_client)
    pr_mgr = PullRequestManager(gh_client)
    yaml_modifier = YAMLModifier(repo_dir=repo_dir)

    # Step A: Branch Creation
    branch_name = branch_mgr.create_branch(norm_req)

    # Step B: YAML Modification & Syntax Validation
    success, file_path, mod_msg = yaml_modifier.add_permission(norm_req, owner_email)
    if not success:
        logger.error(f"YAML modification failed: {mod_msg}")
        return ProvisioningReport(
            request_id=norm_req.request_id,
            normalized_request=norm_req,
            validation_result=val_result,
            existing_access_result=access_check,
            action_taken={"Status": "Failed during YAML modification", "Error": mod_msg},
            manual_steps=[]
        )

    # Step C: Commit Changes
    commit_status = commit_mgr.commit_changes(norm_req, file_path, branch_name)

    temp_report = ProvisioningReport(
        request_id=norm_req.request_id,
        normalized_request=norm_req,
        validation_result=val_result,
        existing_access_result=access_check,
        action_taken={"Feature branch created": branch_name, "YAML updated": file_path},
        manual_steps=[]
    )

    # Step D: Create Pull Request with Rich Markdown Summary
    pr_url = pr_mgr.create_pull_request(norm_req, branch_name, owner_email, file_path, report=temp_report)

    # Step E: Assemble Final Report

    actions = {
        "Feature branch created": branch_name,
        "YAML updated": os.path.basename(file_path),
        "YAML validation": "Passed",
        "Commit status": commit_status,
        "Pull request": pr_url,
    }

    manual_checklist = summary_agent.get_default_manual_steps()

    return ProvisioningReport(
        request_id=norm_req.request_id,
        normalized_request=norm_req,
        validation_result=val_result,
        existing_access_result=access_check,
        action_taken=actions,
        manual_steps=manual_checklist
    )

def main():
    parser = argparse.ArgumentParser(
        description="AI-assisted GitOps Access Provisioning Agent CLI"
    )
    parser.add_argument(
        "--request",
        required=True,
        help="Path to JSON file, text file, or inline JSON string of the access request"
    )
    parser.add_argument(
        "--mode",
        choices=["local", "github"],
        default="local",
        help="Execution mode: 'local' (simulation) or 'github' (live Git/GitHub API)"
    )
    parser.add_argument(
        "--repo-dir",
        default="sample_repo",
        help="Path to sample repository directory (default: 'sample_repo')"
    )

    args = parser.parse_args()

    report = run_pipeline(request_input=args.request, mode=args.mode, repo_dir=args.repo_dir)

    summary_agent = SummaryAgent()
    output = summary_agent.create_summary(report)
    print(output)

if __name__ == "__main__":
    main()
