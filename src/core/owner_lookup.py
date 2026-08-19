"""Data product owner lookup utility."""

import csv
import os
from typing import Dict, Optional

class OwnerLookup:
    """Resolves data product owners from mapping file or product YAML."""
    
    def __init__(self, mapping_csv_path: str = "config/owner_mapping.csv"):
        self.mapping_csv_path = mapping_csv_path
        self._cache: Dict[str, str] = {}
        self._load_mapping()

    def _load_mapping(self) -> None:
        """Loads owner mapping from CSV if available."""
        if os.path.exists(self.mapping_csv_path):
            with open(self.mapping_csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    product = row.get("data_product", "").strip()
                    owner = row.get("owner", "").strip()
                    if product and owner:
                        self._cache[product] = owner

    def get_owner(self, data_product: str, yaml_owner: Optional[str] = None) -> str:
        """
        Returns the data product owner email address.
        First checks CSV mapping, then falls back to YAML owner field, or default fallback.
        """
        if data_product in self._cache:
            return self._cache[data_product]
        if yaml_owner:
            return yaml_owner
        return f"owner.{data_product.lower().replace('-', '.')}@example.com"
