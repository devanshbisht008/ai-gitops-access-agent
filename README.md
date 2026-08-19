# AI-assisted GitOps Access Provisioning Agent

> A hybrid agentic AI & deterministic Python automation Proof of Concept (POC) for cross-data product access requests via declarative GitOps workflows.

---

## 1. Problem Statement
In modern enterprise data platforms, cross data product access requests (e.g. connecting a governance consumer to a marketing analytics data product across environments) are often processed manually. Engineers must parse ticketing requests, validate naming conventions, inspect GitHub YAML configuration repositories for pre-existing access, manually edit configuration files, create feature branches, and submit Pull Requests. This manual approach is error-prone, introduces security oversight risks, and creates provisioning bottlenecks.

---

## 2. Current Manual Process
1. A cross-data product access request lands on a ticketing board (e.g. Jira or ServiceNow).
2. An engineer manually identifies the data consumer, data provider, source/target environment mapping, and access scope.
3. The engineer validates naming conventions against enterprise rules.
4. The engineer looks up the data product owner in a repository or lookup table.
5. The engineer manually checks GitHub YAML configuration files to confirm whether access already exists.
6. If access does not exist, an approval task is created manually.
7. Approval stays manual.
8. After approval, the engineer updates the provider YAML file manually.
9. The engineer creates a Git feature branch.
10. The engineer raises a Pull Request (PR).
11. PR code review and approval remain manual.
12. After merge, CI/CD pipelines (e.g., Jenkins) execute access grant scripts in Databricks/Snowflake.

---

## 3. Proposed Hybrid Architecture
This POC decouples human decision-making and security policies from deterministic repository mechanics using a **Hybrid Architecture**:

- **Agentic AI Layer (`src/agent/`)**:
  - **Intake Agent**: Accepts structured JSON, inline text, or natural language requests, extracting key request parameters using rule-based/regex logic (with a pluggable interface for LLM backends).
  - **Validation Agent**: Normalizes naming conventions (cleaning suffixes like `_LH`/`-LH`, replacing `_` with `-`, capitalizing `DS-`/`CADP-` prefixes), validates required fields, and provides clear policy violation narratives.
  - **Summary Agent**: Generates executive terminal reports and highlights mandatory human-in-the-loop steps.

- **Deterministic Automation Layer (`src/core/` & `src/gitops/`)**:
  - **Core Logic**: Performs YAML file lookup, permission structure inspection, duplicate prevention, safe YAML mutation with `status: pending_pr`, and syntax validation.
  - **GitOps Layer**: Creates standard feature branches (`feature/{req_id}-{access_type}-access`), prepares conventional commits, and opens Pull Requests with automated approval checklists.

```
+-------------------------------------------------------------------------+
|                              INTAKE LAYER                               |
|   JSON File / CLI Argument / Natural Language Text Input                 |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                             AGENTIC LAYER                               |
|   1. IntakeAgent        --> Parse & extract fields                      |
|   2. ValidationAgent    --> Normalize names & validate rules            |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                         DETERMINISTIC LAYER                             |
|   3. YAMLAccessChecker  --> Scan provider YAML for existing access      |
|   4. YAMLModifier       --> Update YAML (status: pending_pr) & validate |
|   5. GitOps Layer       --> Branch creation, Commit, PR Generation      |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                      HUMAN-IN-THE-LOOP SAFEGUARD                         |
|   - Data Product Owner Approval (Manual)                               |
|   - PR Review & Code Inspection (Manual)                               |
|   - Merge Execution & Pipeline Trigger (Manual)                        |
+-------------------------------------------------------------------------+
```

---

## 4. What is Automated vs. What Remains Manual

### Automated (0-Touch):
- Input parsing (JSON & Natural Language text)
- Data product name normalization (stripping `_LH`/`-LH`, prefix validation, hyphen conversion)
- Enterprise validation rule enforcement
- Automated check for pre-existing active/pending permissions
- Provider YAML configuration modification and syntax validation
- Feature branch creation
- Git commit staging
- Pull Request generation with pre-populated metadata & approval checklist
- Executive report generation

### Manual (Human-in-the-Loop):
- Data product owner approval decision
- Pull Request code review and security verification
- Pull Request merge execution
- Production access provisioning pipeline execution

---

## 5. Folder Structure
```
ai-gitops-access-agent/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── config/
│   ├── settings.yaml
│   └── owner_mapping.csv
├── sample_requests/
│   ├── request_valid.json
│   ├── request_existing_access.json
│   ├── request_invalid_name.json
│   └── request_natural_language.txt
├── sample_repo/
│   └── data_products/
│       ├── DS-Digital-AB-Testing-Evaluation.yaml
│       ├── DS-TDA-Governance.yaml
│       └── CADP-Customer-Insights.yaml
├── src/
│   ├── main.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── intake_agent.py
│   │   ├── validation_agent.py
│   │   └── summary_agent.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── normalizer.py
│   │   ├── validator.py
│   │   ├── owner_lookup.py
│   │   ├── yaml_access_checker.py
│   │   ├── yaml_modifier.py
│   │   └── report_generator.py
│   ├── gitops/
│   │   ├── __init__.py
│   │   ├── github_client.py
│   │   ├── branch_manager.py
│   │   ├── commit_manager.py
│   │   └── pr_manager.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── file_utils.py
└── tests/
    ├── test_normalizer.py
    ├── test_validator.py
    ├── test_yaml_access_checker.py
    └── test_yaml_modifier.py
```

---

## 6. Setup Instructions (Windows)

1. Open PowerShell or Command Prompt in the `ai-gitops-access-agent` project root folder:
   ```cmd
   cd ai-gitops-access-agent
   ```

2. Create a virtual environment:
   ```cmd
   python -m venv .venv
   ```

3. Activate the virtual environment:
   ```cmd
   .venv\Scripts\activate
   ```

4. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

5. (Optional) Copy `.env.example` to `.env` if configuring GitHub mode:
   ```cmd
   copy .env.example .env
   ```

---

## 7. How to Run

### Local Simulation Mode (Offline / Demo-Safe)
In local mode, the tool runs offline against `sample_repo/`, creates simulated branch/PR output, and makes 0 external network calls:
```cmd
python src/main.py --request sample_requests/request_valid.json --mode local
```

### GitHub API Mode (Live Integration)
Set your GitHub token in `.env` and run:
```cmd
python src/main.py --request sample_requests/request_valid.json --mode github
```

### Natural Language Input
Run against a freeform text file:
```cmd
python src/main.py --request sample_requests/request_natural_language.txt --mode local
```

### Running Unit Tests
Execute unit tests using pytest:
```cmd
pytest
```

---

## 8. Sample Input and Output

### Sample Input (`sample_requests/request_valid.json`)
```json
{
  "request_id": "REQ-1001",
  "consumer": "DS_TDA_Governance_LH",
  "provider": "DS_Digital_AB_Testing_Evaluation_LH",
  "source_environment": "dev",
  "target_environment": "prod",
  "access_scope": "schema",
  "requested_by": "sample.user@example.com",
  "business_justification": "Need dev to prod access for governance validation"
}
```

### Sample Output (Terminal Report)
```text
==================================================
AI-assisted GitOps Access Provisioning
==================================================
Request ID: REQ-1001
Normalized Request:
  Consumer: DS-TDA-Governance
  Provider: DS-Digital-AB-Testing-Evaluation
  Access: dev_to_prod
  Scope: schema
Validation: Passed
Existing Access: Not Found
  Details: No matching permission found for DS-TDA-Governance in DS-Digital-AB-Testing-Evaluation.yaml
Action Taken:
  - Feature branch created: feature/req-1001-dev-to-prod-access
  - YAML updated: DS-Digital-AB-Testing-Evaluation.yaml
  - YAML validation: Passed
  - Commit status: Simulated Commit: 'feat(gitops): provision dev_to_prod access for DS-TDA-Governance on DS-Digital-AB-Testing-Evaluation [REQ-1001]' on branch 'feature/req-1001-dev-to-prod-access'
  - Pull request: https://github.com/example-org/data-product-access-config/pull/1001 (Local Simulation)
Manual Step Required:
  - Product owner approval must be confirmed manually
  - PR must be reviewed and approved manually
  - Merge must be performed by authorized reviewer
==================================================
```

---

## 9. Limitations
- **Local Branch Isolation**: In local simulation mode, changes are saved directly into the local `sample_repo/` filesystem.
- **Rule-based NLP Engine**: The default `IntakeAgent` uses pattern-matching for text files; complex conversational nuances require plugging in an LLM backend (e.g. Gemini / OpenAI API).
- **Single Provider Scope**: Each request operates on a single provider YAML file.

---

## 10. Future Enhancements & Integration Roadmap
1. **Jira Integration**: Webhook listener to ingest access requests automatically from Jira Service Desk tickets.
2. **Aspen Form Integration**: API connection to consume access request forms directly from Aspen portals.
3. **SharePoint Owner Lookup Integration**: Dynamic resolution of data product owners via SharePoint lists.
4. **Approval Task Creation**: Automated creation of ServiceNow/Jira approval sub-tasks assigned to the data product owner.
5. **Approval Status Polling**: Asynchronous agent task polling approval systems before triggering branch creation.
6. **Teams / Slack Notification**: Real-time channel alerts notifying product owners of pending PRs.
7. **Jenkins Pipeline Trigger**: Automated post-merge webhooks triggering Jenkins deployment jobs.
8. **Databricks Unity Catalog Integration**: Direct query of Databricks system tables for live owner mappings and schema catalog verification.
9. **LLM-Based Natural Language Parser**: Upgrading `IntakeAgent` with structured LLM outputs (`langchain` / `instructor` / Google Gemini API).
10. **Audit Logging & Compliance Vault**: Storing signed JSON audit payloads in Cloud Storage / S3 for compliance.
11. **Role-Based Access Control (RBAC)**: Validating requester entitlement roles prior to request normalization.
12. **Human Approval Dashboard**: Web-based UI (e.g. Streamlit or Next.js) allowing reviewers to inspect diffs and approve PRs.

---

## 11. Stakeholder Demo Script

1. **Introduction**:
   *"Welcome. Today we are demonstrating the AI-assisted GitOps Access Provisioning Agent—a hybrid solution combining intelligent request understanding with deterministic GitOps automation."*

2. **Demonstrate Valid Request Flow**:
   Run: `python src/main.py --request sample_requests/request_valid.json --mode local`
   - Point out how raw input `DS_TDA_Governance_LH` was normalized to `DS-TDA-Governance`.
   - Show that `dev` -> `prod` access type was generated as `dev_to_prod`.
   - Explain how `DS-Digital-AB-Testing-Evaluation.yaml` was modified with `status: pending_pr`.
   - Highlight the **Manual Step Required** section emphasizing zero-trust governance.

3. **Demonstrate Duplicate Access Detection**:
   Run: `python src/main.py --request sample_requests/request_existing_access.json --mode local`
   - Show how the agent detects that `dev` -> `dev` access already exists in `DS-Digital-AB-Testing-Evaluation.yaml`.
   - Highlight that 0 files were modified and no redundant PRs were created.

4. **Demonstrate Validation Error Handling**:
   Run: `python src/main.py --request sample_requests/request_invalid_name.json --mode local`
   - Show how the agent halts execution due to prefix violation (`INVALID_Product_LH`) and outputs actionable error details.

5. **Demonstrate Natural Language Parsing**:
   Run: `python src/main.py --request sample_requests/request_natural_language.txt --mode local`
   - Show how the intake agent parses unformatted text into a structured request.

---

## 12. Enterprise Systems Integration Architecture

To move from this POC to a production enterprise deployment:

- **Jira & Aspen Integration**: Replace the CLI file reader in `IntakeAgent` with a FastAPI webhook handler listening for `jira:issue_created` events.
- **SharePoint Lookup**: Extend `OwnerLookup` to query the Microsoft Graph API (`GET /v1.0/sites/{site-id}/lists/{list-id}/items`) when owner mapping is not found locally.
- **Jenkins Pipeline Trigger**: Configure GitHub repository webhooks to send a payload to `https://jenkins.company.com/generic-webhook-trigger/invoke` upon PR merge to `main`, triggering automated Databricks SQL grant execution.
