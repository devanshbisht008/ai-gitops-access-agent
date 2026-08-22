"""Unit tests for request validation logic."""

import pytest
from src.core.models import NormalizedRequest
from src.core.validator import RequestValidator

def test_valid_request_passes_validation():
    valid_req = NormalizedRequest(
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
    result = RequestValidator.validate(valid_req)
    assert result.is_valid is True
    assert len(result.errors) == 0

def test_invalid_prefix_fails_validation():
    invalid_prefix_req = NormalizedRequest(
        request_id="REQ-1002",
        consumer="INVALID-Prefix-Product",
        provider="DS-Digital-AB-Testing-Evaluation",
        source_environment="dev",
        target_environment="prod",
        access_type="dev_to_prod",
        access_scope="schema",
        requested_by="sample@example.com",
        business_justification="Test"
    )
    result = RequestValidator.validate(invalid_prefix_req)
    assert result.is_valid is False
    assert any("must start with one of" in err for err in result.errors)

def test_invalid_environment_fails_validation():
    invalid_env_req = NormalizedRequest(
        request_id="REQ-1003",
        consumer="DS-TDA-Governance",
        provider="DS-Digital-AB-Testing-Evaluation",
        source_environment="invalid_env",
        target_environment="prod",
        access_type="invalid_env_to_prod",
        access_scope="schema",
        requested_by="sample@example.com",
        business_justification="Test"
    )
    result = RequestValidator.validate(invalid_env_req)
    assert result.is_valid is False
    assert any("Invalid source_environment" in err for err in result.errors)

def test_sadp_to_primary_allowed():
    req = NormalizedRequest(
        request_id="REQ-SADP-001",
        consumer="SADP-Sales-Analytics",
        provider="sadp-gops-addit-primary",
        source_environment="dev",
        target_environment="dev",
        access_type="dev_to_dev",
        access_scope="schema",
        requested_by="user@example.com",
        business_justification="Access primary SADP"
    )
    res = RequestValidator.validate(req)
    assert res.is_valid is True

def test_sadp_to_non_primary_sadp_rejected():
    req = NormalizedRequest(
        request_id="REQ-SADP-002",
        consumer="SADP-Sales-Analytics",
        provider="SADP-Marketing-Metrics",
        source_environment="dev",
        target_environment="dev",
        access_type="dev_to_dev",
        access_scope="schema",
        requested_by="user@example.com",
        business_justification="Access non-primary SADP"
    )
    res = RequestValidator.validate(req)
    assert res.is_valid is False
    assert any("except primary data products" in err for err in res.errors)

def test_sadp_to_cadp_rejected():
    req = NormalizedRequest(
        request_id="REQ-SADP-003",
        consumer="SADP-Sales-Analytics",
        provider="CADP-Customer-Insights",
        source_environment="dev",
        target_environment="dev",
        access_type="dev_to_dev",
        access_scope="schema",
        requested_by="user@example.com",
        business_justification="Access CADP from SADP"
    )
    res = RequestValidator.validate(req)
    assert res.is_valid is False
    assert any("SADP" in err and "CADP" in err and "access is not allowed" in err for err in res.errors)

def test_prod_to_dev_cross_dp_rejected():
    req = NormalizedRequest(
        request_id="REQ-XENV-001",
        consumer="DS-TDA-Governance",
        provider="CADP-Customer-Insights",
        source_environment="prod",
        target_environment="dev",
        access_type="prod_to_dev",
        access_scope="schema",
        requested_by="user@example.com",
        business_justification="Prod to Dev cross DP"
    )
    res = RequestValidator.validate(req)
    assert res.is_valid is False
    assert any("Prod to Dev access between 2 different data products is against guidelines" in err for err in res.errors)

def test_prod_to_dev_self_non_ml_rejected():
    req = NormalizedRequest(
        request_id="REQ-XENV-002",
        consumer="CADP-Customer-Insights",
        provider="CADP-Customer-Insights",
        source_environment="prod",
        target_environment="dev",
        access_type="prod_to_dev",
        access_scope="schema",
        requested_by="user@example.com",
        business_justification="Standard access",
        is_ml_use_case=False
    )
    res = RequestValidator.validate(req)
    assert res.is_valid is False
    assert any("only allowed for ML Use Cases" in err for err in res.errors)

def test_prod_to_dev_self_ml_allowed():
    req = NormalizedRequest(
        request_id="REQ-XENV-003",
        consumer="CADP-Customer-Insights",
        provider="CADP-Customer-Insights",
        source_environment="prod",
        target_environment="dev",
        access_type="prod_to_dev",
        access_scope="schema",
        requested_by="user@example.com",
        business_justification="ML model training use case",
        is_ml_use_case=True
    )
    res = RequestValidator.validate(req)
    assert res.is_valid is True
    assert any("provisioned for ML Use Case" in w for w in res.warnings)
