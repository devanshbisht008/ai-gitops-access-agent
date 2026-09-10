"""Unit tests for SQLite TicketStoreRepository."""

import os
import tempfile
import pytest
from src.core.models import AccessRequest, NormalizedRequest, ValidationResult, AccessCheckResult, ProvisioningReport
from src.core.ticket_store import TicketStoreRepository

@pytest.fixture
def temp_repo():
    """Provides a TicketStoreRepository pointing to a temporary database file."""
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = f.name
    f.close()
    repo = TicketStoreRepository(db_path=db_path)
    yield repo
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except OSError:
        pass

def test_save_ticket_provisioned(temp_repo):
    norm_req = NormalizedRequest(
        request_id="REQ-1001",
        consumer="DS-TDA-Governance",
        provider="DS-Digital-AB-Testing-Evaluation",
        source_environment="dev",
        target_environment="prod",
        access_type="dev_to_prod",
        access_scope="schema",
        requested_by="user@example.com",
        business_justification="Unit test justification"
    )
    val_res = ValidationResult(is_valid=True, errors=[])
    report = ProvisioningReport(
        request_id="REQ-1001",
        normalized_request=norm_req,
        validation_result=val_res,
        existing_access_result=None,
        action_taken={"Feature branch created": "feature/req-1001", "Pull request": "https://github.com/org/repo/pull/1001"}
    )

    saved = temp_repo.save_ticket(report)
    assert saved["ticket_id"] == "REQ-1001"
    assert saved["status"] == "PROVISIONED"
    assert saved["consumer"] == "DS-TDA-Governance"

    fetched = temp_repo.get_ticket("REQ-1001")
    assert fetched is not None
    assert fetched["ticket_id"] == "REQ-1001"
    assert fetched["status"] == "PROVISIONED"

def test_save_ticket_rejected(temp_repo):
    norm_req = NormalizedRequest(
        request_id="REQ-1002",
        consumer="SADP-Sales-Analytics",
        provider="CADP-Customer-Insights",
        source_environment="dev",
        target_environment="dev",
        access_type="dev_to_dev",
        access_scope="schema",
        requested_by="sadp.user@example.com",
        business_justification="Invalid cross DP SADP to CADP"
    )
    val_res = ValidationResult(is_valid=False, errors=["SADP data products cannot request access to CADP data products."])
    report = ProvisioningReport(
        request_id="REQ-1002",
        normalized_request=norm_req,
        validation_result=val_res,
        existing_access_result=None,
        action_taken={"Status": "Aborted"}
    )

    saved = temp_repo.save_ticket(report)
    assert saved["ticket_id"] == "REQ-1002"
    assert saved["status"] == "REJECTED"

    all_tickets = temp_repo.get_all_tickets()
    assert len(all_tickets) == 1
    assert all_tickets[0]["status"] == "REJECTED"

def test_get_latest_ticket_id(temp_repo):
    assert temp_repo.get_latest_ticket_id() is None

    norm_req1 = NormalizedRequest("REQ-1001", "DS-A", "DS-B", "dev", "prod", "dev_to_prod", "schema", "u@e.com", "j")
    rep1 = ProvisioningReport("REQ-1001", norm_req1, ValidationResult(True), None)
    temp_repo.save_ticket(rep1)

    assert temp_repo.get_latest_ticket_id() == "REQ-1001"

    norm_req2 = NormalizedRequest("REQ-1002", "DS-A", "DS-B", "dev", "prod", "dev_to_prod", "schema", "u@e.com", "j")
    rep2 = ProvisioningReport("REQ-1002", norm_req2, ValidationResult(True), None)
    temp_repo.save_ticket(rep2)

    assert temp_repo.get_latest_ticket_id() == "REQ-1002"

def test_on_conflict_update_ticket(temp_repo):
    norm_req = NormalizedRequest("REQ-1001", "DS-A", "DS-B", "dev", "prod", "dev_to_prod", "schema", "u@e.com", "j")
    rep1 = ProvisioningReport("REQ-1001", norm_req, ValidationResult(False, errors=["Initial error"]), None)
    temp_repo.save_ticket(rep1)

    assert temp_repo.get_ticket("REQ-1001")["status"] == "REJECTED"

    rep2 = ProvisioningReport("REQ-1001", norm_req, ValidationResult(True), None, action_taken={"Pull request": "https://pr.url"})
    temp_repo.save_ticket(rep2)

    assert temp_repo.get_ticket("REQ-1001")["status"] == "PROVISIONED"
    assert len(temp_repo.get_all_tickets()) == 1
