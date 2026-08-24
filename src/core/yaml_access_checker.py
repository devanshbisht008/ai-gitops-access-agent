"""YAML access permission checker module."""

import os
from typing import Optional, Dict, Any
from src.core.models import NormalizedRequest, AccessCheckResult
from src.utils.file_utils import load_yaml_file

class YAMLAccessChecker:
    """Checks whether requested access already exists in provider YAML configuration files."""

    def __init__(self, repo_dir: str = "sample_repo"):
        self.repo_dir = repo_dir

    def get_provider_yaml_path(self, provider_name: str) -> str:
        """Returns the expected absolute/relative file path for the provider YAML."""
        return os.path.join(self.repo_dir, "data_products", f"{provider_name}.yaml")

    def check_access_exists(self, request: NormalizedRequest) -> AccessCheckResult:
        """
        Scans the provider's YAML file permissions list to see if equivalent access
        already exists.
        """
        yaml_path = self.get_provider_yaml_path(request.provider)
        
        if not os.path.exists(yaml_path):
            return AccessCheckResult(
                access_exists=False,
                message=f"Provider file does not exist yet: {yaml_path}"
            )

        try:
            yaml_data = load_yaml_file(yaml_path)
        except Exception as e:
            return AccessCheckResult(
                access_exists=False,
                message=f"Failed to read provider YAML file ({yaml_path}): {str(e)}"
            )

        permissions = yaml_data.get("permissions", [])
        if not isinstance(permissions, list):
            permissions = []

        for perm in permissions:
            if not isinstance(perm, dict):
                continue
            
            # Match consumer, source_env, target_env
            match_consumer = (perm.get("consumer") == request.consumer)
            match_source = (perm.get("source_environment") == request.source_environment)
            match_target = (perm.get("target_environment") == request.target_environment)

            if not (match_consumer and match_source and match_target):
                continue

            # Case A: If permission has full_schema_access or scope 'schema', it satisfies any scope
            perm_scope = perm.get("access_scope", "")
            perm_full = perm.get("full_schema_access", perm_scope == "schema")

            if perm_full or perm_scope == "schema":
                return AccessCheckResult(
                    access_exists=True,
                    matching_permission=perm,
                    message=f"Access already exists for {request.consumer} in {request.provider}.yaml (Full Schema Access, status: {perm.get('status', 'active')})"
                )

            # Case B: Table level matching
            if request.access_scope == "table":
                existing_tables = perm.get("tables", [])
                if request.tables and set(request.tables).issubset(set(existing_tables)):
                    return AccessCheckResult(
                        access_exists=True,
                        matching_permission=perm,
                        message=f"Table access already exists for {request.consumer} in {request.provider}.yaml (status: {perm.get('status', 'active')})"
                    )

        return AccessCheckResult(
            access_exists=False,
            message=f"No matching permission found for {request.consumer} in {request.provider}.yaml"
        )
