"""Unit tests for request normalization."""

import pytest
from src.core.models import AccessRequest
from src.core.normalizer import RequestNormalizer, clean_data_product_name

def test_clean_data_product_name_lh_suffix():
    assert clean_data_product_name("DS_Digital_AB_Testing_Evaluation_LH") == "DS-Digital-AB-Testing-Evaluation"
    assert clean_data_product_name("DS_TDA_Governance_LH") == "DS-TDA-Governance"
    assert clean_data_product_name("CADP_Customer_Insights-LH") == "CADP-Customer-Insights"

def test_clean_data_product_name_underscores():
    assert clean_data_product_name("DS_My_Data_Product") == "DS-My-Data-Product"
    assert clean_data_product_name("ds_lowercase_test") == "DS-lowercase-test"
    assert clean_data_product_name("cadp_analytics_hub") == "CADP-analytics-hub"

def test_request_normalizer_full_request():
    raw_req = AccessRequest(
        request_id="REQ-1001",
        consumer="DS_TDA_Governance_LH",
        provider="DS_Digital_AB_Testing_Evaluation_LH",
        source_environment="DEV",
        target_environment="PROD",
        access_scope="SCHEMA",
        requested_by="user@example.com",
        business_justification="Test normalization"
    )
    
    norm = RequestNormalizer.normalize(raw_req)
    
    assert norm.request_id == "REQ-1001"
    assert norm.consumer == "DS-TDA-Governance"
    assert norm.provider == "DS-Digital-AB-Testing-Evaluation"
    assert norm.source_environment == "dev"
    assert norm.target_environment == "prod"
    assert norm.access_type == "dev_to_prod"
    assert norm.access_scope == "schema"

def test_get_next_request_id_auto_increment():
    from src.core.normalizer import get_next_request_id
    assert get_next_request_id("REQ-1001") == "REQ-1002"
    assert get_next_request_id("REQ-1009") == "REQ-1010"
    assert get_next_request_id("REQ-SADP-3001") == "REQ-SADP-3002"
    assert get_next_request_id("REQ-999") == "REQ-1000"
    assert get_next_request_id("") == "REQ-1001"
