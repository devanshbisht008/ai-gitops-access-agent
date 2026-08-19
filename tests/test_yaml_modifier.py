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

def test_yaml_syntax_validity_after_modification(tmp_path):
    repo_dir = tmp_path / "sample_repo"
    modifier = YAMLModifier(repo_dir=str(repo_dir))

    req = NormalizedRequest(
        request_id="REQ-1004",
        consumer="CADP-Customer-Insights",
        provider="DS-TDA-Governance",
        source_environment="stage",
        target_environment="prod",
        access_type="stage_to_prod",
        access_scope="table",
        requested_by="user@example.com",
        business_justification="Test syntax"
    )

    success, file_path, msg = modifier.add_permission(req)
    assert success is True

    # Verify YAML is valid by parsing with PyYAML
    with open(file_path, "r", encoding="utf-8") as f:
        parsed = yaml.safe_load(f)

    assert parsed["data_product"] == "DS-TDA-Governance"
    assert parsed["permissions"][0]["consumer"] == "CADP-Customer-Insights"
