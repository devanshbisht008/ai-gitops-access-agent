"""Request normalization engine."""

import re
from typing import Dict, Any
from src.core.models import AccessRequest, NormalizedRequest

def clean_data_product_name(name: str) -> str:
    """
    Cleans and normalizes data product names:
    - Removes trailing '-LH' or '_LH'
    - Replaces underscores with hyphens
    - Capitalizes prefixes (DS-, CADP-, SADP-)
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
    elif cleaned.lower().startswith("sadp-"):
        cleaned = "SADP-" + cleaned[5:]
        
    return cleaned

def get_next_request_id(request_id: str) -> str:
    """
    Extracts trailing numeric counter from request_id and increments it by 1.
    Example: 'REQ-1001' -> 'REQ-1002', 'REQ-SADP-3001' -> 'REQ-SADP-3002'
    """
    if not request_id:
        return "REQ-1001"
    match = re.search(r'^(.*?)(0*(\d+))$', request_id.strip())
    if match:
        prefix = match.group(1)
        num_str = match.group(2)
        val = int(match.group(3)) + 1
        new_num_str = str(val).zfill(len(num_str))
        return f"{prefix}{new_num_str}"
    return "REQ-1001"

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
        
        # Clean tables list (support comma-separated string or list)
        tables = [t.strip() for t in request.tables if t and t.strip()] if request.tables else []

        # Enforce Rule: If table names are specified (1 or more), access_scope is 'table'.
        # If no table access is specified, default to full schema access ('schema').
        if tables:
            access_scope = "table"
        else:
            access_scope = "schema"
        
        # ML use case detection from flag or justification
        justification = request.business_justification.strip() if request.business_justification else ""
        is_ml = request.is_ml_use_case or bool(re.search(r'\b(ml|machine\s*learning|model|llm)\b', justification, re.IGNORECASE))
        
        return NormalizedRequest(
            request_id=request.request_id.strip() if request.request_id else "REQ-1000",
            consumer=cleaned_consumer,
            provider=cleaned_provider,
            source_environment=source_env,
            target_environment=target_env,
            access_type=access_type,
            access_scope=access_scope,
            requested_by=request.requested_by.strip() if request.requested_by else "unknown@example.com",
            business_justification=justification,
            tables=tables,
            is_ml_use_case=is_ml
        )
