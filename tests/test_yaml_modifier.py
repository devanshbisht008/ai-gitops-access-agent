"""Unit tests for YAML file modification and validation."""

import os
import yaml
import pytest
from src.core.models import NormalizedRequest
from src.core.yaml_modifier import YAMLModifier
from src.utils.file_utils import load_yaml_file

def test_add_new_permission_and_duplicate_prevention(tmp_path):
    repo_dir = tmp_path / "sample_repo"
    dp_dir = repo_dir / "data_products"
    dp_dir.mkdir(parents=True)

    yaml_file = dp_dir / "DS-Digital-AB-Testing-Evaluation.yaml"
    yaml_file.write_text("""
data_product: DS-Digital-AB-Testing-Evaluation
owner: sample.owner@example.com
permissions:
  - consumer: DS-TDA-Governance
    source_environment: dev
    target_environment: dev
    access_type: dev_to_dev
    access_scope: schema
    status: active
""", encoding="utf-8")

    modifier = YAMLModifier(repo_dir=str(repo_dir))

    req = NormalizedRequest(
        request_id="REQ-1001",
        consumer="DS-TDA-Governance",
        provider="DS-Digital-AB-Testing-Evaluation",
        source_environment="dev",
        target_environment="prod",
        access_type="dev_to_prod",
        access_scope="schema",
        requested_by="sample@example.com",
        business_justification="Test justification"
    )

    # 1. Add permission first time
    success, file_path, msg = modifier.add_permission(req, owner_email="sample.owner@example.com")
    assert success is True
    assert os.path.exists(file_path)

    # Check content
    updated_data = load_yaml_file(file_path)
    permissions = updated_data.get("permissions", [])
    assert len(permissions) == 2
    added_perm = permissions[1]
    assert added_perm["consumer"] == "DS-TDA-Governance"
    assert added_perm["source_environment"] == "dev"
    assert added_perm["target_environment"] == "prod"
    assert added_perm["access_type"] == "dev_to_prod"
    assert added_perm["access_scope"] == "schema"
    assert added_perm["status"] == "pending_pr"

    # 2. Try adding duplicate permission
    success_dup, file_path_dup, msg_dup = modifier.add_permission(req, owner_email="sample.owner@example.com")
    assert success_dup is True
    updated_data_dup = load_yaml_file(file_path)
    assert len(updated_data_dup.get("permissions", [])) == 2  # Length must remain 2 (no duplicate added)

def test_yaml_full_schema_access_and_tables(tmp_path):
    repo_dir = tmp_path / "sample_repo"
    dp_dir = repo_dir / "data_products"
    dp_dir.mkdir(parents=True)

    yaml_file = dp_dir / "CADP-Customer-Insights.yaml"
    yaml_file.write_text("""
data_product: CADP-Customer-Insights
owner: sample.owner@example.com
available_tables:
  - customer_profiles
  - transaction_features
permissions: []
""", encoding="utf-8")

    modifier = YAMLModifier(repo_dir=str(repo_dir))

    # Test 1: Schema access adds full_schema_access: true
    req_schema = NormalizedRequest(
        request_id="REQ-SCH-01",
        consumer="DS-TDA-Governance",
        provider="CADP-Customer-Insights",
        source_environment="dev",
        target_environment="prod",
        access_type="dev_to_prod",
        access_scope="schema",
        requested_by="user@example.com",
        business_justification="Schema access"
    )

    success_s, file_path_s, _ = modifier.add_permission(req_schema)
    assert success_s is True
    data_s = load_yaml_file(file_path_s)
    perm_s = data_s["permissions"][0]
    assert perm_s["full_schema_access"] is True

    # Test 2: Table access adds full_schema_access: false and tables array
    req_table = NormalizedRequest(
        request_id="REQ-TBL-01",
        consumer="DS-Digital-AB-Testing-Evaluation",
        provider="CADP-Customer-Insights",
        source_environment="dev",
        target_environment="dev",
        access_type="dev_to_dev",
        access_scope="table",
        tables=["customer_profiles"],
        requested_by="user@example.com",
        business_justification="Table access"
    )

    success_t, file_path_t, _ = modifier.add_permission(req_table)
    assert success_t is True
    data_t = load_yaml_file(file_path_t)
    perm_t = data_t["permissions"][1]
    assert perm_t["full_schema_access"] is False
    assert perm_t["tables"] == ["customer_profiles"]

    # Test 3: Table access with missing catalog table fails modification
    req_missing_table = NormalizedRequest(
        request_id="REQ-TBL-02",
        consumer="DS-Digital-AB-Testing-Evaluation",
        provider="CADP-Customer-Insights",
        source_environment="dev",
        target_environment="dev",
        access_type="dev_to_dev",
        access_scope="table",
        tables=["non_existent_table"],
        requested_by="user@example.com",
        business_justification="Table access"
    )

    success_m, _, msg_m = modifier.add_permission(req_missing_table)
    assert success_m is False
    assert "Table verification failed" in msg_m
