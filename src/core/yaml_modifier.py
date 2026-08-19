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

        # Check for duplicates before appending
        new_perm = {
            "consumer": request.consumer,
            "source_environment": request.source_environment,
            "target_environment": request.target_environment,
            "access_type": request.access_type,
            "access_scope": request.access_scope,
            "status": "pending_pr"
        }

        for perm in yaml_data["permissions"]:
            if (
                perm.get("consumer") == new_perm["consumer"]
                and perm.get("source_environment") == new_perm["source_environment"]
                and perm.get("target_environment") == new_perm["target_environment"]
                and perm.get("access_scope") == new_perm["access_scope"]
            ):
                return True, yaml_path, "Permission already present in YAML structure."

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
