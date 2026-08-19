"""Intake agent for parsing access requests from JSON or Natural Language text."""

import json
import re
from typing import Dict, Any, Union
from src.core.models import AccessRequest
from src.utils.file_utils import read_json_file, read_text_file

class IntakeAgent:
    """
    Intake Agent understands, parses, and structures incoming requests.
    Supports structured JSON files, dictionaries, and natural language text.
    Designed with a pluggable interface to allow integration of LLM backends.
    """

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm  # Flag for future LLM integration

    def parse_input(self, input_source: Union[str, Dict[str, Any]]) -> AccessRequest:
        """Determines input type and extracts structured AccessRequest."""
        if isinstance(input_source, dict):
            return self._parse_dict(input_source)
        
        if isinstance(input_source, str):
            if input_source.strip().endswith(".json"):
                data = read_json_file(input_source)
                return self._parse_dict(data)
            
            if input_source.strip().endswith(".txt"):
                content = read_text_file(input_source)
                return self._parse_natural_language(content)

            # Check if inline raw JSON string
            if input_source.strip().startswith("{") and input_source.strip().endswith("}"):
                data = json.loads(input_source)
                return self._parse_dict(data)

            # Treat as inline natural language text
            return self._parse_natural_language(input_source)

        raise ValueError(f"Unsupported input source format: {type(input_source)}")

    def _parse_dict(self, data: Dict[str, Any]) -> AccessRequest:
        """Constructs AccessRequest from dictionary data."""
        return AccessRequest(
            request_id=data.get("request_id", "REQ-1000"),
            consumer=data.get("consumer", ""),
            provider=data.get("provider", ""),
            source_environment=data.get("source_environment", ""),
            target_environment=data.get("target_environment", ""),
            access_scope=data.get("access_scope", ""),
            requested_by=data.get("requested_by", "sample.user@example.com"),
            business_justification=data.get("business_justification", "Access Request"),
        )

    def _parse_natural_language(self, text: str) -> AccessRequest:
        """
        Pattern-matching based extraction for natural language text requests.
        Enables rule-based extraction without requiring external LLM API calls.
        """
        request_id_match = re.search(r'(?:Request ID|REQ ID):\s*([A-Za-z0-9_-]+)', text, re.IGNORECASE)
        consumer_match = re.search(r'(?:Consumer|consumer DS_[A-Za-z0-9_]+|consumer CADP_[A-Za-z0-9_]+):\s*([A-Za-z0-9_-]+)|consumer\s+([A-Za-z0-9_-]+)', text, re.IGNORECASE)
        provider_match = re.search(r'(?:Provider|provider DS_[A-Za-z0-9_]+|provider CADP_[A-Za-z0-9_]+):\s*([A-Za-z0-9_-]+)|provider\s+([A-Za-z0-9_-]+)', text, re.IGNORECASE)
        source_env_match = re.search(r'(?:Source Environment|source_env|source):\s*([A-Za-z0-9_-]+)', text, re.IGNORECASE)
        target_env_match = re.search(r'(?:Target Environment|target_env|target):\s*([A-Za-z0-9_-]+)', text, re.IGNORECASE)
        scope_match = re.search(r'(?:Access Scope|scope):\s*([A-Za-z0-9_-]+)', text, re.IGNORECASE)
        requested_by_match = re.search(r'(?:Requested By|user|email):\s*(\S+@\S+)', text, re.IGNORECASE)
        justification_match = re.search(r'(?:Business Justification|justification):\s*(.*)', text, re.IGNORECASE)

        # Helper to pick matched group
        def extract_group(match):
            if not match:
                return ""
            groups = [g for g in match.groups() if g is not None]
            return groups[0].strip() if groups else ""

        request_id = extract_group(request_id_match) or "REQ-NL-1001"
        consumer = extract_group(consumer_match)
        provider = extract_group(provider_match)
        source_env = extract_group(source_env_match)
        target_env = extract_group(target_env_match)
        scope = extract_group(scope_match)
        requested_by = extract_group(requested_by_match) or "sample.user@example.com"
        justification = extract_group(justification_match) or "Natural language access request"

        return AccessRequest(
            request_id=request_id,
            consumer=consumer,
            provider=provider,
            source_environment=source_env,
            target_environment=target_env,
            access_scope=scope,
            requested_by=requested_by,
            business_justification=justification,
        )
