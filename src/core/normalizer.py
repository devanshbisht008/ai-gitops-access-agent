"""Request normalization engine."""

import re
from typing import Dict, Any
from src.core.models import AccessRequest, NormalizedRequest

def clean_data_product_name(name: str) -> str:
    """
    Cleans and normalizes data product names:
    - Removes trailing '-LH' or '_LH'
    - Replaces underscores with hyphens
    - Capitalizes prefixes (DS-, CADP-)
    """
    if not name:
        return ""
    
    cleaned = name.strip()
    # Strip trailing _LH or -LH (case-insensitive)
    cleaned = re.sub(r'([_-][lL][hH])+$', '', cleaned)
    # Replace all underscores with hyphens
    cleaned = cleaned.replace('_', '-')
    
    # Capitalize standard enterprise prefixes if lowercased
    if cleaned.lower().startswith("ds-"):
        cleaned = "DS-" + cleaned[3:]
    elif cleaned.lower().startswith("cadp-"):
        cleaned = "CADP-" + cleaned[5:]
        
    return cleaned

class RequestNormalizer:
    """Normalizes raw input access requests according to enterprise conventions."""
    
    @staticmethod
    def normalize(request: AccessRequest) -> NormalizedRequest:
        """Transforms a raw AccessRequest into a NormalizedRequest."""
        cleaned_consumer = clean_data_product_name(request.consumer)
        cleaned_provider = clean_data_product_name(request.provider)
        
        source_env = request.source_environment.strip().lower()
        target_env = request.target_environment.strip().lower()
        access_scope = request.access_scope.strip().lower()
        
        access_type = f"{source_env}_to_{target_env}"
        
        return NormalizedRequest(
            request_id=request.request_id.strip() if request.request_id else "REQ-1000",
            consumer=cleaned_consumer,
            provider=cleaned_provider,
            source_environment=source_env,
            target_environment=target_env,
            access_type=access_type,
            access_scope=access_scope,
            requested_by=request.requested_by.strip() if request.requested_by else "unknown@example.com",
            business_justification=request.business_justification.strip() if request.business_justification else ""
        )
