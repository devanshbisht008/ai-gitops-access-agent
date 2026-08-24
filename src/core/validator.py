"""Request validation rules engine."""

from typing import List
from src.core.models import NormalizedRequest, ValidationResult

ALLOWED_ENVIRONMENTS = {"dev", "qa", "stage", "prod"}
ALLOWED_SCOPES = {"schema", "table", "volume"}
ALLOWED_PREFIXES = ("DS-", "CADP-", "SADP-")

def get_dp_type(name: str) -> str:
    """Extracts DP type prefix (SADP, CADP, or DS)."""
    if not name:
        return ""
    upper = name.upper()
    if upper.startswith("SADP-"):
        return "SADP"
    if upper.startswith("CADP-"):
        return "CADP"
    if upper.startswith("DS-"):
        return "DS"
    return ""

def is_primary_sadp(name: str) -> bool:
    """Checks if SADP data product is a primary data product (sadp-*-primary*)."""
    if not name:
        return False
    lower = name.lower()
    return lower.startswith("sadp-") and "-primary" in lower

class RequestValidator:
    """Validates normalized requests against enterprise business and governance rules."""
    
    @staticmethod
    def validate(request: NormalizedRequest) -> ValidationResult:
        """Enforces enterprise validation rules on a normalized request."""
        errors: List[str] = []
        warnings: List[str] = []

        # Rule 1: consumer required
        if not request.consumer:
            errors.append("Field 'consumer' is required.")

        # Rule 2: provider required
        if not request.provider:
            errors.append("Field 'provider' is required.")

        # Rule 3: source_environment required
        if not request.source_environment:
            errors.append("Field 'source_environment' is required.")
        elif request.source_environment not in ALLOWED_ENVIRONMENTS:
            errors.append(
                f"Invalid source_environment '{request.source_environment}'. "
                f"Must be one of: {sorted(list(ALLOWED_ENVIRONMENTS))}"
            )

        # Rule 4: target_environment required
        if not request.target_environment:
            errors.append("Field 'target_environment' is required.")
        elif request.target_environment not in ALLOWED_ENVIRONMENTS:
            errors.append(
                f"Invalid target_environment '{request.target_environment}'. "
                f"Must be one of: {sorted(list(ALLOWED_ENVIRONMENTS))}"
            )

        # Rule 5: access_scope required
        if not request.access_scope:
            errors.append("Field 'access_scope' is required.")
        elif request.access_scope not in ALLOWED_SCOPES:
            errors.append(
                f"Invalid access_scope '{request.access_scope}'. "
                f"Must be one of: {sorted(list(ALLOWED_SCOPES))}"
            )

        # Rule 6: Prefix validation (DS-, CADP-, SADP-)
        if request.consumer and not any(request.consumer.upper().startswith(prefix) for prefix in ALLOWED_PREFIXES):
            errors.append(
                f"Consumer name '{request.consumer}' must start with one of: {ALLOWED_PREFIXES}"
            )
        
        if request.provider and not any(request.provider.upper().startswith(prefix) for prefix in ALLOWED_PREFIXES):
            errors.append(
                f"Provider name '{request.provider}' must start with one of: {ALLOWED_PREFIXES}"
            )

        # Rule 7: No underscores after normalization
        if "_" in request.consumer:
            errors.append(f"Consumer name '{request.consumer}' contains invalid underscores.")
        if "_" in request.provider:
            errors.append(f"Provider name '{request.provider}' contains invalid underscores.")

        # Rule 8: Cross Data Product (XDP) Entitlement Matrix
        consumer_type = get_dp_type(request.consumer)
        provider_type = get_dp_type(request.provider)

        if consumer_type == "SADP":
            if provider_type == "SADP":
                if not is_primary_sadp(request.provider):
                    errors.append(
                        f"Access violation: SADP ({request.consumer}) to SADP ({request.provider}) "
                        f"access (except primary data products) is not allowed."
                    )
            elif provider_type in ("CADP", "DS"):
                errors.append(
                    f"Access violation: SADP ({request.consumer}) to {provider_type} ({request.provider}) "
                    f"access is not allowed."
                )
        elif consumer_type == "CADP":
            if provider_type == "SADP":
                errors.append(
                    f"Access violation: CADP ({request.consumer}) to SADP ({request.provider}) "
                    f"access is not allowed."
                )

        # Rule 9: Environment Flow Isolation Rules (Dev-Dev, Dev-Prod, Prod-Prod, Prod-Dev)
        if request.source_environment == "prod" and request.target_environment == "dev":
            if request.consumer != request.provider:
                errors.append(
                    "Access violation: Prod to Dev access between 2 different data products is "
                    "against guidelines and cannot be provisioned."
                )
            else:
                if not request.is_ml_use_case:
                    errors.append(
                        "Access violation: Prod to Dev access within a single data product is "
                        "only allowed for ML Use Cases with ML Journey Owner approval."
                    )
                else:
                    warnings.append(
                        "Prod to Dev access is provisioned for ML Use Case with ML Journey Owner "
                        "approval on a temporary basis."
                    )

        # Rule 10: Table Scope Validation
        if request.access_scope == "table" and not request.tables:
            warnings.append(
                "Access scope is set to 'table', but no specific table names were provided in the request."
            )

        # Check self-access warning
        if request.consumer == request.provider:
            warnings.append("Consumer and provider are identical (Self-Data-Product-Access).")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
