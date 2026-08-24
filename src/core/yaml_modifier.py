"""YAML permission modification engine."""

import os
from typing import Dict, Any, Tuple
import yaml
from src.core.models import NormalizedRequest
from src.utils.file_utils import load_yaml_file, save_yaml_file

class YAMLModifier:
    """Modifies data product YAML configuration files to inject new permissions."""

    def __init__(self, repo_dir: str = "sample_repo"):
        self.repo_dir = repo_dir

    def get_provider_yaml_path(self, provider_name: str) -> str:
        """Returns provider YAML file path."""
        return os.path.join(self.repo_dir, "data_products", f"{provider_name}.yaml")

    def add_permission(self, request: NormalizedRequest, owner_email: str = "sample.owner@example.com") -> Tuple[bool, str, str]:
        """
        Adds a new access definition to the provider's YAML file.
        Returns: (success: bool, file_path: str, message: str)
        """
        yaml_path = self.get_provider_yaml_path(request.provider)
        data_product_dir = os.path.dirname(yaml_path)

        os.makedirs(data_product_dir, exist_ok=True)

        if os.path.exists(yaml_path):
            yaml_data = load_yaml_file(yaml_path)
        else:
            yaml_data = {
                "data_product": request.provider,
                "owner": owner_email,
                "permissions": []
            }

        if "permissions" not in yaml_data or not isinstance(yaml_data["permissions"], list):
            yaml_data["permissions"] = []

        # Table availability verification if catalog defined in provider YAML
        if request.access_scope == "table" and request.tables:
            available_tables = yaml_data.get("available_tables", [])
            if available_tables and isinstance(available_tables, list):
                missing = [t for t in request.tables if t not in available_tables]
                if missing:
                    return False, yaml_path, (
                        f"Table verification failed: Mentioned table(s) {missing} are not present "
                        f"in the lakehouse catalog for '{request.provider}'. Changes cannot be started "
                        "until the tables are created."
                    )

        # Build new permission object with enterprise keywords
        is_full_schema = (not request.tables) or (request.access_scope == "schema")
        new_perm = {
            "consumer": request.consumer,
            "source_environment": request.source_environment,
            "target_environment": request.target_environment,
            "access_type": request.access_type,
            "access_scope": "schema" if is_full_schema else "table",
            "full_schema_access": is_full_schema,
            "status": "pending_pr"
        }
        if not is_full_schema and request.tables:
            new_perm["tables"] = request.tables

        for perm in yaml_data["permissions"]:
            if not isinstance(perm, dict):
                continue
            if (
                perm.get("consumer") == new_perm["consumer"]
                and perm.get("source_environment") == new_perm["source_environment"]
                and perm.get("target_environment") == new_perm["target_environment"]
            ):
                if perm.get("full_schema_access") or perm.get("access_scope") == "schema":
                    return True, yaml_path, "Full schema access already present in YAML structure."

                if new_perm["access_scope"] == "table" and request.tables:
                    existing_tables = perm.get("tables", [])
                    missing_tables = [t for t in request.tables if t not in existing_tables]

                    if missing_tables:
                        existing_tables.extend(missing_tables)
                        perm["tables"] = existing_tables
                        save_yaml_file(yaml_path, yaml_data)
                        return True, yaml_path, f"Updated existing permission: Added missing table(s) {missing_tables} to permissions."
                    else:
                        return True, yaml_path, "Permission for all requested tables already present in YAML structure."

        yaml_data["permissions"].append(new_perm)

        # Write out modified YAML file
        save_yaml_file(yaml_path, yaml_data)

        # Validate syntax by reloading
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
        except Exception as syntax_error:
            return False, yaml_path, f"YAML syntax validation failed after write: {str(syntax_error)}"

        return True, yaml_path, "Permission added successfully and YAML syntax validated."
