"""Request validation rules engine."""

from typing import List
from src.core.models import NormalizedRequest, ValidationResult

ALLOWED_ENVIRONMENTS = {"dev", "qa", "stage", "prod"}
ALLOWED_SCOPES = {"schema", "table", "volume"}
ALLOWED_PREFIXES = ("DS-", "CADP-")

class RequestValidator:
    """Validates normalized requests against business and governance rules."""
    
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

        # Rule 9: Prefix validation (DS- or CADP-)
        if request.consumer and not any(request.consumer.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            errors.append(
                f"Consumer name '{request.consumer}' must start with one of: {ALLOWED_PREFIXES}"
            )
        
        if request.provider and not any(request.provider.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            errors.append(
                f"Provider name '{request.provider}' must start with one of: {ALLOWED_PREFIXES}"
            )

        # Rule 10: No underscores after normalization
        if "_" in request.consumer:
            errors.append(f"Consumer name '{request.consumer}' contains invalid underscores.")
        if "_" in request.provider:
            errors.append(f"Provider name '{request.provider}' contains invalid underscores.")

        # Check self-access warning
        if request.consumer == request.provider:
            warnings.append("Consumer and provider are identical.")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
