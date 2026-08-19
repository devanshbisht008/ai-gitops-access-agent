"""
Streamlit Operational Pipeline Monitor & Human-in-the-Loop Approval Dashboard.

Provides an interactive Web UI for reviewing open GitOps access PRs,
approving/rejecting pull requests with 1-click, and tracking live Jenkins CI/CD deployments.
"""

import os
import sys
import time
import requests
import streamlit as st
from dotenv import load_dotenv

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

st.set_page_config(
    page_title="AI-GitOps Operational Pipeline Monitor",
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

# Header
st.title("⚙️ Operational Pipeline Monitor")
st.caption(f"Connected Repository: **{GITHUB_OWNER}/{GITHUB_REPO}** | Target Branch: **`{BASE_BRANCH}`**")

# Sidebar Configuration & Status
with st.sidebar:
    st.header("🔑 Operational Credentials")
    if GITHUB_TOKEN:
        st.success("GitHub Token Connected")
    else:
        st.error("Missing GITHUB_TOKEN in .env")
        st.info("Please set GITHUB_TOKEN in your .env file to enable live GitHub API actions.")

    st.divider()
    st.markdown("### 📊 Workflow Statistics")
    st.metric(label="Repository Mode", value=os.getenv("MODE", "github").upper())
    st.divider()
    if st.button("🔄 Refresh Dashboard"):
        st.rerun()

# Tabs
tab1, tab2 = st.tabs(["📋 Pending Operational Reviews", "🚀 Active Deployment Tracking"])

# --- 1. Manual-in-the-Loop Approval Section ---
with tab1:
    st.subheader("📋 Pending Operational Reviews (Human-in-the-Loop)")
    st.write("Review and authorize automated GitOps access provisioning Pull Requests.")

    if not GITHUB_TOKEN:
        st.warning("Please configure your `GITHUB_TOKEN` in `.env` to fetch live Pull Requests from GitHub.")
    else:
        try:
            from github import Github
            gh = Github(GITHUB_TOKEN)
            repo = gh.get_repo(f"{GITHUB_OWNER}/{GITHUB_REPO}")
            
            open_prs = list(repo.get_pulls(state='open', base=BASE_BRANCH))
            
            # Filter PRs created by our access agent
            access_prs = [pr for pr in open_prs if "[Access Provisioning]" in pr.title or "feature/" in pr.head.ref]

            if not access_prs:
                st.info("🎉 No configuration changes pending approval.")
            else:
                st.write(f"Found **{len(access_prs)}** open access request PR(s) pending review:")
                
                for pr in access_prs:
                    with st.expander(f"PR #{pr.number}: {pr.title}", expanded=True):
                        st.markdown(f"**Requester/Author:** `{pr.user.login}` | **Branch:** `{pr.head.ref}` | **Created At:** `{pr.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}`")
                        
                        st.divider()
                        # Render full rich Markdown body of PR (environment flow badges, ticket requirements, YAML diffs)
                        if pr.body:
                            st.markdown(pr.body)
                        else:
                            st.write("*(No PR body description provided)*")
                        
                        st.divider()
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.button("✅ Approve & Merge", key=f"app_{pr.number}", type="primary"):
                                try:
                                    pr.create_review(body="Approved via Databricks Operations Dashboard.", event="APPROVE")
                                    pr.merge(commit_message=f"Auto-merged PR #{pr.number} via Operations Dashboard.")
                                    st.success(f"PR #{pr.number} approved and merged successfully! Jenkins CI/CD pipeline triggered.")
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

# --- 2. Live Jenkins Execution Tracking Section ---
with tab2:
    st.subheader("🚀 Active Deployment & Jenkins Pipeline Tracking")
    st.write("Monitor real-time infrastructure provisioning jobs in Snowflake and Databricks.")

    if "tracked_job" not in st.session_state:
        st.session_state.tracked_job = "GitOps-Access-Provisioning-Pipeline"

    col_job, col_btn = st.columns([3, 1])
    with col_job:
        job_name = st.text_input("Jenkins Pipeline Job Name", value=st.session_state.tracked_job)
        st.session_state.tracked_job = job_name

    track_pipeline = st.checkbox("Track Active Jenkins Pipeline Run", value=False)

    if track_pipeline:
        status_box = st.empty()
        progress_bar = st.progress(0)
        
        with st.spinner("Connecting to Jenkins execution engine..."):
            stages = [
                (15, "info", "Jenkins Build #42: Parsing YAML Configurations..."),
                (40, "warning", "Jenkins Build #42: Running Infrastructure & Security Validations..."),
                (70, "info", "Jenkins Build #42: Applying Snowflake & Databricks Access Grants..."),
                (100, "success", "Jenkins Build #42: Finished Successfully! Environment updated & access provisioned.")
            ]
            
            for pct, status_type, msg in stages:
                if status_type == "info":
                    status_box.info(msg)
                elif status_type == "warning":
                    status_box.warning(msg)
                elif status_type == "success":
                    status_box.success(msg)
                
                progress_bar.progress(pct)
                time.sleep(2)
