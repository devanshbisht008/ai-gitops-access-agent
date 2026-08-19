"""Data models for access requests, validation, and provisioning reports."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class AccessRequest:
    """Raw incoming access request."""
    consumer: str
    provider: str
    source_environment: str
    target_environment: str
    access_scope: str
    request_id: str = "REQ-1000"
    requested_by: str = "system.user@example.com"
    business_justification: str = "Access request"

@dataclass
class NormalizedRequest:
    """Normalized access request data model."""
    request_id: str
    consumer: str
    provider: str
    source_environment: str
    target_environment: str
    access_type: str
    access_scope: str
    requested_by: str
    business_justification: str

    def to_dict(self) -> Dict[str, Any]:
        """Converts normalized request to a dictionary."""
        return {
            "request_id": self.request_id,
            "consumer": self.consumer,
            "provider": self.provider,
            "source_environment": self.source_environment,
            "target_environment": self.target_environment,
            "access_type": self.access_type,
            "access_scope": self.access_scope,
            "requested_by": self.requested_by,
            "business_justification": self.business_justification,
        }

@dataclass
class ValidationResult:
    """Result of request validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class AccessCheckResult:
    """Result of existing access check in YAML file."""
    access_exists: bool
    matching_permission: Optional[Dict[str, Any]] = None
    message: str = ""

@dataclass
class ProvisioningReport:
    """Complete summary report of the access provisioning workflow."""
    request_id: str
    normalized_request: NormalizedRequest
    validation_result: ValidationResult
    existing_access_result: AccessCheckResult
    action_taken: Dict[str, Any] = field(default_factory=dict)
    manual_steps: List[str] = field(default_factory=list)
