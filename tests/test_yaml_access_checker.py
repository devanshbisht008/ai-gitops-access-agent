"""Unit tests for YAML access checking."""

import os
import pytest
from src.core.models import NormalizedRequest
from src.core.yaml_access_checker import YAMLAccessChecker

def test_existing_access_detected(tmp_path):
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

    checker = YAMLAccessChecker(repo_dir=str(repo_dir))

    # Test existing dev -> dev request
    existing_req = NormalizedRequest(
        request_id="REQ-1002",
        consumer="DS-TDA-Governance",
        provider="DS-Digital-AB-Testing-Evaluation",
        source_environment="dev",
        target_environment="dev",
        access_type="dev_to_dev",
        access_scope="schema",
        requested_by="user@example.com",
        business_justification="Test"
    )

    res_existing = checker.check_access_exists(existing_req)
    assert res_existing.access_exists is True

    # Test non-existing dev -> prod request
    new_req = NormalizedRequest(
        request_id="REQ-1001",
        consumer="DS-TDA-Governance",
        provider="DS-Digital-AB-Testing-Evaluation",
        source_environment="dev",
        target_environment="prod",
        access_type="dev_to_prod",
        access_scope="schema",
        requested_by="user@example.com",
        business_justification="Test"
    )

    res_new = checker.check_access_exists(new_req)
    assert res_new.access_exists is False
