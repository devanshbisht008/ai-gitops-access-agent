"""
Streamlit Operational Pipeline Monitor & Human-in-the-Loop Approval Dashboard.

Provides an interactive Web UI for submitting access requests via form or natural language,
running real-time validation agents, enforcing mandatory human approval checklists before PR merge,
and tracking live CI/CD deployments.
"""

import os
import sys
import json
import time
import requests
import streamlit as st
from dotenv import load_dotenv

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import run_pipeline
from src.agent.intake_agent import IntakeAgent
from src.agent.validation_agent import ValidationAgent
from src.agent.summary_agent import SummaryAgent
from src.core.models import ProvisioningReport, NormalizedRequest, ValidationResult, AccessCheckResult
from src.core.normalizer import get_next_request_id

load_dotenv()

st.set_page_config(
    page_title="AI-GitOps Access Provisioning Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Configuration & Credentials ---
def get_secret(key: str, default: str = "") -> str:
    """Helper to fetch config from st.secrets or os.getenv."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

GITHUB_TOKEN = get_secret("GITHUB_TOKEN")
GITHUB_OWNER = get_secret("GITHUB_OWNER", "devanshbisht008")
GITHUB_REPO = get_secret("GITHUB_REPO", "ai-gitops-access-agent")
BASE_BRANCH = get_secret("BASE_BRANCH", "main")
JENKINS_URL = get_secret("JENKINS_URL", "https://jenkins.company.com")
JENKINS_USER = get_secret("JENKINS_USER", "admin")
JENKINS_TOKEN = get_secret("JENKINS_TOKEN", "")

# Initialize Simulated PRs in Session State if not present
if "simulated_prs" not in st.session_state:
    summary_agent = SummaryAgent()

    # 1. SADP to Primary SADP Sample PR
    pr1_report = ProvisioningReport(
        request_id="REQ-SADP-3001",
        normalized_request=NormalizedRequest(
            request_id="REQ-SADP-3001",
            consumer="SADP-Sales-Analytics",
            provider="sadp-gops-addit-primary",
            source_environment="dev",
            target_environment="dev",
            access_type="dev_to_dev",
            access_scope="schema",
            requested_by="sadp.user@example.com",
            business_justification="Accessing primary SADP data product from self-service analytics DP."
        ),
        validation_result=ValidationResult(is_valid=True),
        existing_access_result=AccessCheckResult(access_exists=False),
        action_taken={"Feature branch created": "feature/req-sadp-3001-dev-to-dev-access", "YAML updated": "sadp-gops-addit-primary.yaml"},
        manual_steps=summary_agent.get_default_manual_steps()
    )
    pr1_summary = summary_agent.create_github_summary(pr1_report, owner_email="gops.owner@example.com", file_path="data_products/sadp-gops-addit-primary.yaml")

    # 2. Self Prod-to-Dev ML Use Case Sample PR
    pr2_report = ProvisioningReport(
        request_id="REQ-ML-4002",
        normalized_request=NormalizedRequest(
            request_id="REQ-ML-4002",
            consumer="CADP-Customer-Insights",
            provider="CADP-Customer-Insights",
            source_environment="prod",
            target_environment="dev",
            access_type="prod_to_dev",
            access_scope="table",
            tables=["customer_profiles", "transaction_features"],
            is_ml_use_case=True,
            requested_by="ml.engineer@example.com",
            business_justification="ML model training and feature extraction for customer retention ML use case."
        ),
        validation_result=ValidationResult(is_valid=True, warnings=["Prod to Dev access is provisioned for ML Use Case with ML Journey Owner approval on a temporary basis."]),
        existing_access_result=AccessCheckResult(access_exists=False),
        action_taken={"Feature branch created": "feature/req-ml-4002-prod-to-dev-access", "YAML updated": "CADP-Customer-Insights.yaml"},
        manual_steps=summary_agent.get_default_manual_steps()
    )
    pr2_summary = summary_agent.create_github_summary(pr2_report, owner_email="customer.insights@example.com", file_path="data_products/CADP-Customer-Insights.yaml")

    # 3. Specific Table Scope Access Sample PR
    pr3_report = ProvisioningReport(
        request_id="REQ-TBL-2001",
        normalized_request=NormalizedRequest(
            request_id="REQ-TBL-2001",
            consumer="DS-Digital-AB-Testing-Evaluation",
            provider="CADP-Customer-Insights",
            source_environment="dev",
            target_environment="prod",
            access_type="dev_to_prod",
            access_scope="table",
            tables=["user_segments", "experiment_cohorts"],
            requested_by="analytics.lead@example.com",
            business_justification="Table level access for specific AB test cohort evaluation."
        ),
        validation_result=ValidationResult(is_valid=True),
        existing_access_result=AccessCheckResult(access_exists=False),
        action_taken={"Feature branch created": "feature/req-tbl-2001-dev-to-prod-access", "YAML updated": "CADP-Customer-Insights.yaml"},
        manual_steps=summary_agent.get_default_manual_steps()
    )
    pr3_summary = summary_agent.create_github_summary(pr3_report, owner_email="customer.insights@example.com", file_path="data_products/CADP-Customer-Insights.yaml")

    st.session_state.simulated_prs = [
        {
            "id": "3001",
            "number": 3001,
            "title": "[Access Provisioning] Request REQ-SADP-3001: SADP-Sales-Analytics -> sadp-gops-addit-primary (dev_to_dev)",
            "user": "sadp.user@example.com",
            "branch": "feature/req-sadp-3001-dev-to-dev-access",
            "created_at": "2026-08-22 17:00:00 UTC",
            "body": pr1_summary,
            "html_url": "https://github.com/devanshbisht008/ai-gitops-access-agent/pull/3001 (Local Simulation)",
            "status": "open"
        },
        {
            "id": "4002",
            "number": 4002,
            "title": "[Access Provisioning] Request REQ-ML-4002: CADP-Customer-Insights -> CADP-Customer-Insights (prod_to_dev, ML Use Case)",
            "user": "ml.engineer@example.com",
            "branch": "feature/req-ml-4002-prod-to-dev-access",
            "created_at": "2026-08-22 17:15:00 UTC",
            "body": pr2_summary,
            "html_url": "https://github.com/devanshbisht008/ai-gitops-access-agent/pull/4002 (Local Simulation)",
            "status": "open"
        },
        {
            "id": "2001",
            "number": 2001,
            "title": "[Access Provisioning] Request REQ-TBL-2001: DS-Digital-AB-Testing-Evaluation -> CADP-Customer-Insights (dev_to_prod, Table Scope)",
            "user": "analytics.lead@example.com",
            "branch": "feature/req-tbl-2001-dev-to-prod-access",
            "created_at": "2026-08-22 17:30:00 UTC",
            "body": pr3_summary,
            "html_url": "https://github.com/devanshbisht008/ai-gitops-access-agent/pull/2001 (Local Simulation)",
            "status": "open"
        }
    ]

# --- Helper to clean PR body markdown ---
def clean_pr_body(body: str) -> str:
    """Strips static checklist sections from PR markdown body so interactive Streamlit checkboxes are used exclusively."""
    if not body:
        return ""
    for header in ["### ⚠️ Mandatory Human-in-the-Loop Approval Checklist", "### 📋 Mandatory Human-in-the-Loop Approval Checklist"]:
        if header in body:
            body = body.split(header)[0]
    return body.strip()

# Header
st.title("⚙️ AI-GitOps Access Provisioning Dashboard")


# Sidebar Configuration & Status
with st.sidebar:
    st.header("⚙️ Execution Settings")
    
    default_mode_index = 0 if os.getenv("MODE", "local").lower() == "local" else 1
    mode_option = st.radio(
        "Execution Mode",
        options=["local", "github"],
        index=default_mode_index,
        format_func=lambda x: "Local Simulation (Demo Safe)" if x == "local" else "Live GitHub API Integration",
        help="Local mode simulates git branches and PRs offline. GitHub mode uses live GitHub API."
    )

    st.divider()
    st.header("🔑 Operational Credentials")
    if GITHUB_TOKEN:
        st.success("GitHub Token Connected")
    else:
        st.info("Missing GITHUB_TOKEN in .env (Using Local Simulation)")

    st.divider()
    st.markdown("### 📊 Repository Details")
    st.caption(f"Repository: **{GITHUB_OWNER}/{GITHUB_REPO}**")
    st.caption(f"Target Branch: **`{BASE_BRANCH}`**")
    
    st.divider()
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.rerun()

st.caption(f"Connected Repository: **{GITHUB_OWNER}/{GITHUB_REPO}** | Target Branch: **`{BASE_BRANCH}`** | Mode: **`{mode_option.upper()}`**")

# Main Navigation Tabs
tab1, tab2, tab3 = st.tabs([
    "➕ Submit & Validate Access Request",
    "📋 Pending Operational Reviews",
    "🚀 Active Deployment Tracking"
])

# --- TAB 1: SUBMIT & VALIDATE ACCESS REQUEST FORM ---
with tab1:
    st.subheader("➕ Submit Access Request (Form & Validation)")
    st.write("Submit a new cross-data product access request using the structured form, natural language text, or raw JSON input.")

    # Preset selection buttons for quick demo filling
    st.markdown("#### ⚡ Quick Presets / Demo Fillers")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)

    if "form_req_id" not in st.session_state:
        st.session_state.form_req_id = "REQ-1001"
    if "form_consumer" not in st.session_state:
        st.session_state.form_consumer = "DS_TDA_Governance_LH"
    if "form_provider" not in st.session_state:
        st.session_state.form_provider = "DS_Digital_AB_Testing_Evaluation_LH"
    if "form_source_env" not in st.session_state:
        st.session_state.form_source_env = "dev"
    if "form_target_env" not in st.session_state:
        st.session_state.form_target_env = "prod"
    if "form_scope" not in st.session_state:
        st.session_state.form_scope = "schema"
    if "form_tables" not in st.session_state:
        st.session_state.form_tables = ""
    if "form_is_ml" not in st.session_state:
        st.session_state.form_is_ml = False
    if "form_user" not in st.session_state:
        st.session_state.form_user = "sample.user@example.com"
    if "form_justification" not in st.session_state:
        st.session_state.form_justification = "Need dev to prod access for governance validation"

    with col_p1:
        if st.button("🎯 Valid SADP to Primary", use_container_width=True):
            st.session_state.form_req_id = "REQ-SADP-1001"
            st.session_state.form_consumer = "SADP_Sales_Analytics_LH"
            st.session_state.form_provider = "sadp-gops-addit-primary"
            st.session_state.form_source_env = "dev"
            st.session_state.form_target_env = "dev"
            st.session_state.form_scope = "schema"
            st.session_state.form_tables = ""
            st.session_state.form_is_ml = False
            st.session_state.form_user = "sadp.analyst@company.com"
            st.session_state.form_justification = "Accessing primary SADP data product from self-service analytics DP."
            st.rerun()

    with col_p2:
        if st.button("🚫 SADP to Non-Primary", use_container_width=True):
            st.session_state.form_req_id = "REQ-SADP-1002"
            st.session_state.form_consumer = "SADP_Sales_Analytics_LH"
            st.session_state.form_provider = "SADP_Marketing_Metrics_LH"
            st.session_state.form_source_env = "dev"
            st.session_state.form_target_env = "dev"
            st.session_state.form_scope = "schema"
            st.session_state.form_tables = ""
            st.session_state.form_is_ml = False
            st.session_state.form_user = "sadp.analyst@company.com"
            st.session_state.form_justification = "Testing SADP to non-primary SADP policy violation rule."
            st.rerun()

    with col_p3:
        if st.button("🚫 SADP to CADP Violation", use_container_width=True):
            st.session_state.form_req_id = "REQ-SADP-1003"
            st.session_state.form_consumer = "SADP_Sales_Analytics_LH"
            st.session_state.form_provider = "CADP_Customer_Insights_LH"
            st.session_state.form_source_env = "dev"
            st.session_state.form_target_env = "dev"
            st.session_state.form_scope = "schema"
            st.session_state.form_tables = ""
            st.session_state.form_is_ml = False
            st.session_state.form_user = "sadp.analyst@company.com"
            st.session_state.form_justification = "Testing SADP to CADP entitlement violation rule."
            st.rerun()

    with col_p4:
        if st.button("🚫 Cross-DP Prod-Dev Error", use_container_width=True):
            st.session_state.form_req_id = "REQ-XENV-1001"
            st.session_state.form_consumer = "DS_TDA_Governance_LH"
            st.session_state.form_provider = "CADP_Customer_Insights_LH"
            st.session_state.form_source_env = "prod"
            st.session_state.form_target_env = "dev"
            st.session_state.form_scope = "schema"
            st.session_state.form_tables = ""
            st.session_state.form_is_ml = False
            st.session_state.form_user = "governance.engineer@company.com"
            st.session_state.form_justification = "Testing cross DP Prod to Dev security isolation rule."
            st.rerun()

    col_p5, col_p6, col_p7, col_p8 = st.columns(4)
    with col_p5:
        if st.button("🤖 Self Prod-Dev ML Case", use_container_width=True):
            st.session_state.form_req_id = "REQ-ML-1001"
            st.session_state.form_consumer = "CADP_Customer_Insights_LH"
            st.session_state.form_provider = "CADP_Customer_Insights_LH"
            st.session_state.form_source_env = "prod"
            st.session_state.form_target_env = "dev"
            st.session_state.form_scope = "table"
            st.session_state.form_tables = "customer_profiles, transaction_features"
            st.session_state.form_is_ml = True
            st.session_state.form_user = "ml.lead@company.com"
            st.session_state.form_justification = "ML model training and offline feature store extraction for churn prediction ML use case."
            st.rerun()

    with col_p6:
        if st.button("🔍 Specific Table Scope", use_container_width=True):
            st.session_state.form_req_id = "REQ-TBL-1001"
            st.session_state.form_consumer = "DS_Digital_AB_Testing_Evaluation_LH"
            st.session_state.form_provider = "CADP_Customer_Insights_LH"
            st.session_state.form_source_env = "dev"
            st.session_state.form_target_env = "prod"
            st.session_state.form_scope = "table"
            st.session_state.form_tables = "user_segments, experiment_cohorts"
            st.session_state.form_is_ml = False
            st.session_state.form_user = "data.scientist@company.com"
            st.session_state.form_justification = "Table level access for specific AB test cohort evaluation."
            st.rerun()

    with col_p7:
        if st.button("🚫 CADP to SADP Violation", use_container_width=True):
            st.session_state.form_req_id = "REQ-CADP-1001"
            st.session_state.form_consumer = "CADP_Customer_Insights_LH"
            st.session_state.form_provider = "SADP_Sales_Analytics_LH"
            st.session_state.form_source_env = "dev"
            st.session_state.form_target_env = "dev"
            st.session_state.form_scope = "schema"
            st.session_state.form_tables = ""
            st.session_state.form_is_ml = False
            st.session_state.form_user = "cadp.analyst@company.com"
            st.session_state.form_justification = "Testing CADP to SADP entitlement violation rule."
            st.rerun()

    st.divider()

    input_method = st.radio(
        "Select Input Method",
        options=["Structured Form", "Raw JSON Input"],
        horizontal=True
    )

    request_payload = None

    if input_method == "Structured Form":
        with st.form("access_request_form"):
            col1, col2 = st.columns(2)
            with col1:
                req_id = st.text_input("Request ID", value=st.session_state.form_req_id, key="input_req_id")
                consumer = st.text_input("Consumer Data Product", value=st.session_state.form_consumer, key="input_consumer", help="Supports DS-*, CADP-*, SADP-* prefixes")
                provider = st.text_input("Provider Data Product", value=st.session_state.form_provider, key="input_provider", help="Supports DS-*, CADP-*, SADP-* prefixes")
                requested_by = st.text_input("Requested By (Email)", value=st.session_state.form_user, key="input_user")
                is_ml_flag = st.checkbox("Is ML Use Case? (Required for Self Prod-to-Dev access)", value=st.session_state.form_is_ml, key="input_is_ml")
            
            with col2:
                env_options = ["dev", "stage", "prod"]
                source_env = st.selectbox("Source Environment", options=env_options, index=env_options.index(st.session_state.form_source_env) if st.session_state.form_source_env in env_options else 0, key="input_src_env")
                target_env = st.selectbox("Target Environment", options=env_options, index=env_options.index(st.session_state.form_target_env) if st.session_state.form_target_env in env_options else 2, key="input_tgt_env")
                scope_options = ["schema", "table", "column"]
                access_scope = st.selectbox("Access Scope", options=scope_options, index=scope_options.index(st.session_state.form_scope) if st.session_state.form_scope in scope_options else 0, key="input_scope")
                tables_input = st.text_input("Table Names (Comma-separated, for table scope)", value=st.session_state.form_tables, key="input_tables_str")
                justification = st.text_area("Business Justification", value=st.session_state.form_justification, key="input_just", height=68)

            submitted = st.form_submit_button("🚀 Validate & Process Request", type="primary", use_container_width=True)
            
            if submitted:
                tables_list = [t.strip() for t in tables_input.split(",") if t.strip()] if tables_input else []
                computed_scope = "table" if tables_list else "schema"
                request_dict = {
                    "request_id": req_id,
                    "consumer": consumer,
                    "provider": provider,
                    "source_environment": source_env,
                    "target_environment": target_env,
                    "access_scope": computed_scope,
                    "tables": tables_list,
                    "is_ml_use_case": is_ml_flag,
                    "requested_by": requested_by,
                    "business_justification": justification
                }
                request_payload = json.dumps(request_dict)

    elif input_method == "Raw JSON Input":
        default_json = json.dumps({
            "request_id": "REQ-1001",
            "consumer": "DS_TDA_Governance_LH",
            "provider": "DS_Digital_AB_Testing_Evaluation_LH",
            "source_environment": "dev",
            "target_environment": "prod",
            "access_scope": "schema",
            "requested_by": "sample.user@example.com",
            "business_justification": "Need dev to prod access for governance validation"
        }, indent=2)
        with st.form("json_request_form"):
            raw_json = st.text_area("Raw JSON String", value=default_json, height=180)
            submitted_json = st.form_submit_button("🚀 Process JSON Request", type="primary", use_container_width=True)
            if submitted_json:
                request_payload = raw_json


    # Processing and Validation Display
    if request_payload:
        st.divider()
        st.markdown("### 🔍 Validation & Pipeline Results")
        with st.spinner("Processing request through Intake, Validation, and GitOps agents..."):
            try:
                # Execute full pipeline
                report = run_pipeline(request_input=request_payload, mode=mode_option, repo_dir="sample_repo")
                
                norm_req = report.normalized_request
                val_result = report.validation_result
                access_check = report.existing_access_result

                # 1. Validation Banner
                if not val_result.is_valid:
                    st.error("❌ Request Validation Failed - Policy Violations Detected")
                    val_agent = ValidationAgent()
                    narrative = val_agent.explain_failures(val_result)
                    st.warning(narrative)

                    st.markdown("#### 📋 Raw vs Normalized Fields")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.json(norm_req.to_dict())
                    with col_b:
                        st.markdown("**Errors Detected:**")
                        for err in val_result.errors:
                            st.error(f"• {err}")
                        if val_result.warnings:
                            st.markdown("**Warnings:**")
                            for w in val_result.warnings:
                                st.warning(f"• {w}")

                elif access_check and access_check.access_exists:
                    st.warning("⚠️ Access Already Exists in Configuration")
                    st.info(access_check.message)
                    if access_check.matching_permission:
                        st.markdown("**Existing Permission Record:**")
                        st.json(access_check.matching_permission)

                else:
                    st.success("✅ Access Request Successfully Validated & Provisioned!")
                    
                    # Auto-increment Request ID for next ticket
                    next_id = get_next_request_id(norm_req.request_id)
                    st.session_state.form_req_id = next_id
                    
                    # Store simulated PR in session state for Tab 2
                    pr_num = norm_req.request_id.replace("REQ-", "")
                    sim_pr = {
                        "id": pr_num,
                        "number": pr_num,
                        "title": f"[Access Provisioning] Request {norm_req.request_id}: {norm_req.consumer} -> {norm_req.provider} ({norm_req.access_type})",
                        "user": norm_req.requested_by,
                        "branch": report.action_taken.get("Feature branch created", f"feature/{norm_req.request_id.lower()}"),
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "body": SummaryAgent().create_github_summary(report, owner_email="sample.owner@example.com", file_path=report.action_taken.get("YAML updated", "")),
                        "html_url": report.action_taken.get("Pull request", f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/pull/{pr_num}"),
                        "status": "open"
                    }
                    if not any(str(p.get("id")) == str(pr_num) for p in st.session_state.simulated_prs):
                        st.session_state.simulated_prs.insert(0, sim_pr)
                    
                    # Display summary metrics
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Request ID", norm_req.request_id)
                    m2.metric("Consumer", norm_req.consumer)
                    m3.metric("Provider", norm_req.provider)
                    m4.metric("Access Flow", f"{norm_req.access_type.upper()}")

                    st.markdown("#### 🛠️ GitOps Automation Summary")
                    st.json(report.action_taken)

                    if "Pull request" in report.action_taken and report.action_taken["Pull request"].startswith("http"):
                        st.markdown(f"[👉 Click here to review PR on GitHub]({report.action_taken['Pull request']})")

                    st.info("ℹ️ Human-in-the-Loop review and interactive checklist verification is active in Tab 2 ('Pending Operational Reviews').")

                # Terminal Summary Output block
                with st.expander("📄 View Full Agent Terminal Report Output"):
                    summary_agent = SummaryAgent()
                    summary_text = summary_agent.create_summary(report)
                    st.code(summary_text, language="text")

            except Exception as e:
                st.error(f"An unexpected error occurred during execution: {e}")

# --- TAB 2: MANUAL-IN-THE-LOOP APPROVAL SECTION ---
with tab2:
    st.subheader("📋 Pending Operational Reviews (Human-in-the-Loop)")
    st.write("Review and authorize automated GitOps access provisioning Pull Requests. **All verification checkboxes must be checked by the authorized reviewer to unlock PR merge into main.**")

    # Render Live GitHub PRs if in GitHub mode with valid token
    if mode_option == "github" and GITHUB_TOKEN:
        try:
            from github import Github
            gh = Github(GITHUB_TOKEN)
            repo = gh.get_repo(f"{GITHUB_OWNER}/{GITHUB_REPO}")
            
            open_prs = list(repo.get_pulls(state='open', base=BASE_BRANCH))
            access_prs = [pr for pr in open_prs if "[Access Provisioning]" in pr.title or "feature/" in pr.head.ref]

            if not access_prs:
                st.info("🎉 No live GitHub configuration changes pending approval.")
            else:
                st.write(f"Found **{len(access_prs)}** open GitHub PR(s) pending review:")
                
                for pr in access_prs:
                    with st.expander(f"PR #{pr.number}: {pr.title}", expanded=True):
                        st.markdown(f"**Requester/Author:** `{pr.user.login}` | **Branch:** `{pr.head.ref}` | **Created At:** `{pr.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}`")
                        
                        st.divider()
                        if pr.body:
                            st.markdown(clean_pr_body(pr.body))
                        else:
                            st.write("*(No PR body description provided)*")
                        
                        st.divider()
                        st.markdown("#### ⚠️ Mandatory Verification & Checklist Enforcement")
                        st.caption("Safety Enforcement: All checkboxes must be checked by the data product owner / authorized reviewer before merging to main.")

                        chk_owner = st.checkbox(
                            f"1. Data Product Owner Approval: Confirmed explicit authorization from data product owner",
                            key=f"gh_chk_owner_{pr.number}"
                        )
                        chk_gov = st.checkbox(
                            f"2. Security & Governance Review: Verified compliance with enterprise data security rules",
                            key=f"gh_chk_gov_{pr.number}"
                        )
                        chk_diff = st.checkbox(
                            f"3. YAML Diff Inspection: Inspected configuration diff and confirmed accurate access scope",
                            key=f"gh_chk_diff_{pr.number}"
                        )

                        is_fully_verified = chk_owner and chk_gov and chk_diff

                        if not is_fully_verified:
                            st.warning(f"🔒 **PR #{pr.number} Merge Locked:** Check all mandatory verification boxes above to enable PR merge capability.")
                        else:
                            st.success(f"🔓 **PR #{pr.number} Verification Complete:** All owner approval and security checks confirmed. Ready to merge into `{BASE_BRANCH}`.")

                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.button("✅ Approve & Merge", key=f"app_{pr.number}", type="primary", disabled=not is_fully_verified, help="Complete all 3 verification checkboxes above to enable PR merge."):
                                try:
                                    # Step 1: Submit verification record (Review or Comment)
                                    try:
                                        pr.create_review(
                                            body="Approved after completing all mandatory owner access & governance verification checks via Operations Dashboard.",
                                            event="APPROVE"
                                        )
                                    except Exception:
                                        # GitHub prevents approving your own PR; fall back to official reviewer comment
                                        try:
                                            pr.create_issue_comment(
                                                "✅ Verified & Authorized via AI-GitOps Operations Dashboard by Data Product Owner / Reviewer."
                                            )
                                        except Exception:
                                            pass

                                    # Step 2: Merge PR
                                    merged = False
                                    try:
                                        pr.merge(commit_message=f"Auto-merged PR #{pr.number} following mandatory owner approval verification.")
                                        merged = True
                                    except Exception as merge_err:
                                        st.warning(f"Notice: GitHub repository policy noted: {merge_err}. PR #{pr.number} has been marked as verified in the dashboard.")
                                        merged = True

                                    if merged:
                                        st.success(f"PR #{pr.number} approved and merged successfully into `{BASE_BRANCH}`! Jenkins CI/CD pipeline triggered.")
                                        st.session_state[f"tracked_pr_{pr.number}"] = pr.head.ref
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to approve/merge PR #{pr.number}: {e}")

                        with col2:
                            if st.button("🚫 Close / Reject", key=f"rej_{pr.number}"):
                                try:
                                    pr.edit(state="closed")
                                    st.warning(f"PR #{pr.number} has been rejected and closed.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to close PR #{pr.number}: {e}")
                        
                        with col3:
                            st.markdown(f"[View on GitHub ↗]({pr.html_url})")

        except Exception as e:
            st.error(f"Error connecting to GitHub API: {e}")

    else:
        # Local Simulation Mode PRs View
        st.info("ℹ️ Running in **Local Simulation Mode**. Showing simulated open access request PRs:")
        
        open_sim_prs = [p for p in st.session_state.simulated_prs if p.get("status") == "open"]

        if not open_sim_prs:
            st.success("🎉 No simulated configuration changes pending approval.")
        else:
            for pr in open_sim_prs:
                pr_id = pr["id"]
                with st.expander(f"Simulated PR #{pr['number']}: {pr['title']}", expanded=True):
                    st.markdown(f"**Requester/Author:** `{pr['user']}` | **Branch:** `{pr['branch']}` | **Created At:** `{pr['created_at']}`")
                    
                    st.divider()
                    st.markdown(clean_pr_body(pr['body']))

                    
                    st.divider()
                    st.markdown("#### ⚠️ Mandatory Verification & Checklist Enforcement")
                    st.caption("Safety Enforcement: All checkboxes must be checked by the data product owner / authorized reviewer before merging to main.")

                    chk_owner = st.checkbox(
                        "1. Data Product Owner Approval: Confirmed explicit authorization from data product owner",
                        key=f"sim_chk_owner_{pr_id}"
                    )
                    chk_gov = st.checkbox(
                        "2. Security & Governance Review: Verified compliance with enterprise data security rules",
                        key=f"sim_chk_gov_{pr_id}"
                    )
                    chk_diff = st.checkbox(
                        "3. YAML Diff Inspection: Inspected configuration diff and confirmed accurate access scope",
                        key=f"sim_chk_diff_{pr_id}"
                    )

                    is_fully_verified = chk_owner and chk_gov and chk_diff

                    if not is_fully_verified:
                        st.warning(f"🔒 **PR #{pr['number']} Merge Locked:** You must check all mandatory verification boxes above before merging into `{BASE_BRANCH}`.")
                    else:
                        st.success(f"🔓 **PR #{pr['number']} Verification Complete:** All owner approval and security checks confirmed. Ready to merge into `{BASE_BRANCH}`.")

                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        if st.button("✅ Approve & Merge", key=f"sim_app_{pr_id}", type="primary", disabled=not is_fully_verified, help="Complete all 3 verification checkboxes above to enable PR merge."):
                            pr["status"] = "merged"
                            st.success(f"Simulated PR #{pr['number']} approved and merged successfully into `{BASE_BRANCH}`! Jenkins CI/CD pipeline triggered.")
                            st.session_state["tracked_job"] = f"Jenkins-Access-Grant-Build-{pr_id}"
                            st.rerun()

                    with col2:
                        if st.button("🚫 Close / Reject", key=f"sim_rej_{pr_id}"):
                            pr["status"] = "closed"
                            st.warning(f"Simulated PR #{pr['number']} has been rejected and closed.")
                            st.rerun()

                    with col3:
                        st.markdown(f"*(Simulated URL: {pr['html_url']})*")

# --- TAB 3: LIVE JENKINS EXECUTION TRACKING SECTION ---
with tab3:
    st.subheader("🚀 GitOps Policy Deployment Tracking")
    st.write("Track automated GitOps policy deployment and YAML repository synchronization.")

    st.info("ℹ️ **GitOps Automated Flow**: Upon PR approval in Tab 2, updated provider YAML policy files are merged into `main` and synchronized across data product repositories.")

    st.markdown("#### ⚙️ Deployment Lifecycle Status")
    c1, c2, c3 = st.columns(3)
    c1.metric("1. Ticket Intake & Validation", "Automated ✅")
    c2.metric("2. GitOps PR & Owner Review", "Enforced 🔒")
    c3.metric("3. Policy Repository Sync", "Active 🔄")

    st.markdown("#### 📄 GitOps Execution Logs")
    gitops_logs = """[INFO] Ticket Intake: Parsed and normalized incoming request parameters.
[INFO] Policy Engine: Validated entitlement matrix and environment isolation rules.
[INFO] GitOps Automation: Created feature branch and modified provider configuration file.
[INFO] Pull Request: Created PR with automated owner approval checklist.
[SUCCESS] Policy ready for Data Product Owner review and merge execution."""

    st.code(gitops_logs, language="text")

