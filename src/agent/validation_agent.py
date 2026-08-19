"""Validation agent for coordinate normalization, validation, and explanation."""

from typing import Tuple
from src.core.models import AccessRequest, NormalizedRequest, ValidationResult
from src.core.normalizer import RequestNormalizer
from src.core.validator import RequestValidator

class ValidationAgent:
    """
    Validation Agent orchestrates request normalization, rule validation,
    and explanation generation.
    """

    def __init__(self):
        self.normalizer = RequestNormalizer()
        self.validator = RequestValidator()

    def process_and_validate(self, request: AccessRequest) -> Tuple[NormalizedRequest, ValidationResult]:
        """Normalizes and validates an incoming access request."""
        normalized = self.normalizer.normalize(request)
        validation_result = self.validator.validate(normalized)
        return normalized, validation_result

    def explain_failures(self, validation_result: ValidationResult) -> str:
        """Generates a human-friendly narrative explanation of validation errors."""
        if validation_result.is_valid:
            return "All request validation rules passed successfully."
        
        explanation = ["Request validation failed due to the following policy violations:"]
        for err in validation_result.errors:
            explanation.append(f" - {err}")
        
        return "\n".join(explanation)
