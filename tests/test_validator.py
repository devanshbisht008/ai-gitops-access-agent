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
