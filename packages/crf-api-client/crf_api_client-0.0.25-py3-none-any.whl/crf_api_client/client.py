# ruff: noqa: PLR2004, TRY002, ARG002, D200, E501
import logging
from typing import Optional

import requests

from .base import BaseAPIClient
from .exception import CRFAPIError
from .operations.client_operations import ClientImportOperations
from .warehouse import Warehouse

logger = logging.getLogger(__name__)


class CRFAPIClient(BaseAPIClient):
    def __init__(self, base_url: str, token: str):
        super().__init__(base_url, token)

    # Warehouse methods
    def list_warehouses(self) -> list[Warehouse]:
        """List all warehouses and return them as Warehouse objects"""
        warehouse_data = self._get_paginated_data(f"{self.base_url}/api/v1/projects/")
        warehouses = []
        for data in warehouse_data:
            warehouse = Warehouse(
                base_url=self.base_url,
                token=self.token,
                id=data.get("id"),
                name=data.get("name"),
                **{k: v for k, v in data.items() if k not in ["id", "name"]},
            )
            warehouses.append(warehouse)
        return warehouses

    def create_warehouse(
        self, name: str, brief: Optional[str] = None, default_llm_model: Optional[str] = None
    ) -> Warehouse:
        """Create a new warehouse and return it as a Warehouse object"""
        if brief is None:
            brief = "Warehouse about " + name
        create_warehouse_payload = {
            "name": name,
            "business_brief": brief,
        }
        if default_llm_model:
            create_warehouse_payload["default_llm_model"] = default_llm_model

        response = requests.post(
            f"{self.base_url}/api/v1/projects/",
            headers=self._get_headers(),
            json=create_warehouse_payload,
        )
        if response.status_code != 201:
            raise CRFAPIError(response.json(), response)
        data = response.json()

        return Warehouse(
            base_url=self.base_url,
            token=self.token,
            name=data.get("name"),
            id=data.get("id"),
            **{k: v for k, v in data.items() if k not in ["id", "name"]},
        )

    def delete_warehouse(
        self,
        warehouse_id: str,
    ) -> dict:
        """Delete a warehouse and its associated Neo4j data."""
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{warehouse_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 204:
            raise CRFAPIError(response.json(), response)

        return {
            "warehouse_deleted": True,
        }

    def get_warehouse(self, warehouse_id: str) -> Warehouse:
        """Get a warehouse"""
        response = requests.get(
            f"{self.base_url}/api/v1/projects/{warehouse_id}/",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        data = response.json()
        return Warehouse(
            base_url=self.base_url,
            token=self.token,
            id=data.get("id"),
            name=data.get("name"),
            **{k: v for k, v in data.items() if k not in ["id", "name"]},
        )

    def import_warehouse(self, zip_path: str) -> Warehouse:
        """
        Import warehouse data into a new warehouse.

        Args:
            zip_path: Path to the zip file containing warehouse export data

        Returns:
            Warehouse: The newly created warehouse object

        Raises:
            WarehouseImportError: If any critical import step fails

        """
        import_ops = ClientImportOperations(self)
        return import_ops.import_warehouse(zip_path)
