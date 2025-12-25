# ruff: noqa: ANN003, D105, EM102, PLR2004, G004, PLC0415, TC003
from __future__ import annotations

import logging
import time
from pathlib import Path

import requests

from .base import BaseAPIClient
from .exception import CRFAPIError
from .task import Task

logger = logging.getLogger(__name__)


class Table(BaseAPIClient):
    def __init__(
        self,
        base_url: str,
        token: str,
        warehouse_id: str,
        table_id: str,
        name: str = None,
        **kwargs,
    ):
        super().__init__(base_url, token)
        self.warehouse_id = warehouse_id
        self.table_id = table_id
        self.name = name
        # Store any additional table attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _get_deployed_or_latest_version_id(self, use_deployed_version: bool = False) -> str:
        version = self.get_latest_or_deployed_version(use_deployed_version)
        return version.get("id")

    def _write_batch(self, version_id: str, batch: list[dict], override: bool = False) -> dict:
        """Write a single batch of data, returning response or error dict."""
        try:
            return self.perform_data_operation(
                operation="create", data=batch, table_version_id=version_id, override=override
            )
        except Exception as e:
            logger.exception(
                "Error writing data for batch",
                extra={"batch_size": len(batch)},
            )
            return {"error": str(e)}

    def write_data(
        self,
        data: list[dict],
        override: bool = False,
        table_version_id: str | None = None,
        use_deployed_version: bool = False,
        batch_size: int = 1000,
    ) -> dict:
        """Write data to this table using perform_data_operation method"""
        if isinstance(data, dict):
            data = [data]

        if table_version_id:
            version_id = table_version_id
        else:
            try:
                version_id = self._get_deployed_or_latest_version_id(use_deployed_version)
            except Exception:
                logger.exception("Error getting deployed or latest version.")
                version_id = self.create_version()["id"]
                logger.info(f"Created new version: {version_id}")
        if override:
            self.clear_data(version_id)

        # Handle batching
        if batch_size and len(data) > batch_size:
            batches = [data[i : i + batch_size] for i in range(0, len(data), batch_size)]
            responses = [self._write_batch(version_id, batch) for batch in batches]
            return {"status": "success", "batches_responses": responses}

        # Single batch or no batching
        return self.perform_data_operation(
            operation="create", data=data, table_version_id=version_id
        )

    def clear_data(self, version_id: str) -> dict:
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/clear-table/",
            json={"table_name": self.name, "version_id": version_id},
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def get_data(
        self,
        offset: int = 0,
        page_size: int = 10000,
        max_results: int | None = None,
        table_version_id: str | None = None,
        filters: dict | None = None,
        columns: list[str] | None = None,
    ) -> list[dict]:
        """
        Download data from this table with pagination support.

        Parameters
        ----------
        offset : int
            Starting offset for pagination (default: 0)
        page_size : int
            Number of records to fetch per page (default: 10000)
        max_results : int, optional
            Maximum number of results to fetch. If None, fetches page_size records.
        table_version_id : str, optional
            Specific table version ID. If None, uses the latest version.
        filters : dict, optional
            Filters to apply to the query.
        columns : list[str], optional
            Columns to fetch. If None, fetches all columns.

        Returns
        -------
        list[dict]
            List of records from the table.

        """
        data = []
        total_fetched = 0
        # if max_results is not provided, we will fetch page_size once
        if max_results is None:
            max_results = 1000000

        while total_fetched < max_results:
            response = self.perform_data_operation(
                operation="read",
                table_version_id=table_version_id,
                filters=filters,
                limit=min(page_size, max_results - total_fetched),
                offset=total_fetched + offset,
                columns=columns,
            )
            result = response["result"]
            data.extend(result["results"])
            total_fetched += len(result["results"])
            if not result["has_next"]:
                break
        return data

    def update_data(self, table_version_id: str, data: list[dict]):
        """
        Update data in this table.

        Parameters
        ----------
        table_version_id : str
            Table version ID to update data in
        data : list[dict]
            List of dictionaries to update. Each dict must have an 'id' field.

        Note: The 'id' field in each data item is used to identify which rows to update.
        No filters parameter is needed - the handler uses the 'id' from each data item.

        """
        return self.perform_data_operation(
            operation="update", table_version_id=table_version_id, data=data
        )

    def delete_data(self, table_version_id: str, filters: dict):
        return self.perform_data_operation(
            operation="delete",
            table_version_id=table_version_id,
            filters=filters,
        )

    def perform_data_operation(
        self,
        operation: str,
        data: list[dict] | None = None,
        table_version_id: str | None = None,
        filters: dict | None = None,
        limit: int | None = None,
        offset: int | None = None,
        override: bool = False,
        columns: list[str] | None = None,
    ) -> dict:
        """
        Perform data operations (read, create, update, delete) on this table.

        Parameters
        ----------
        operation : str
            Operation to perform: 'read', 'create', 'update', or 'delete'
        data : list[dict] | None
            Data for create/update operations. Required for 'create' and 'update' operations.
            For 'update' operations, each dict in the list must have an 'id' field.
        filters : dict | None
            Filters for delete operations. Required for 'delete' operations.
            Not used for 'update' operations (the handler uses 'id' from each data item).
        table_version_id : str | None
            Optional table version ID. If not provided, uses the latest version.
        limit : int
            Limit for read operations (default: 10000)
        offset : int
            Offset for read operations (default: 0)
        override : bool
            Override for create operations (default: False)
        columns : list[str], optional
            Columns to fetch. If None, fetches all columns.

        Returns
        -------
        dict
            Result of the operation

        Raises
        ------
        CRFAPIError
            If the API request fails

        """
        # Build request payload
        payload = {"operation": operation}
        if data is not None:
            payload["data"] = data
        if filters is not None:
            payload["filters"] = filters
        if table_version_id is not None:
            payload["table_version_id"] = table_version_id
        if operation == "read":
            payload["limit"] = limit
            payload["offset"] = offset
        if override:
            payload["override"] = override
        if columns is not None:
            payload["columns"] = columns
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/tables/{self.table_id}/data-operations/",
            headers=self._get_headers(),
            json=payload,
        )

        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)

        return response.json()

    def push_to_retrieval(self) -> Task | None:
        if self.object_type == "chunk":
            response = requests.post(
                f"{self.base_url}/api/v1/projects/{self.warehouse_id}/tables/{self.table_id}/push-chunks/",
                headers=self._get_headers(),
                json={},
            )
        elif self.object_type == "tag":
            response = requests.post(
                f"{self.base_url}/api/v1/projects/{self.warehouse_id}/tables/{self.table_id}/push-tags/",
                headers=self._get_headers(),
                json={},
            )
        elif self.object_type == "object":
            response = requests.post(
                f"{self.base_url}/api/v1/projects/{self.warehouse_id}/tables/{self.table_id}/push-objects/",
                headers=self._get_headers(),
                json={},
            )
        else:
            raise ValueError(f"Unsupported object type for push to retrieval: {self.object_type}")
        if response.status_code != 200:
            logger.error(f"Error pushing to retrieval: {response.text}")
            return None
        task_id = response.json().get("pipeline_run_id")
        return Task(self.base_url, self.token, self.warehouse_id, task_id, "pending")

    def list_versions(self) -> list[dict]:
        return self._get_paginated_data(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/tables/{self.table_id}/versions/",
        )

    def get_latest_or_deployed_version(self, use_deployed_version: bool = False) -> dict:
        response = requests.get(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/tables/{self.table_id}/latest-or-deployed-version/",
            headers=self._get_headers(),
            params={"use_deployed_version": use_deployed_version},
        )
        response.raise_for_status()
        return response.json()

    def create_version(self) -> dict:
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/tables/{self.table_id}/versions/",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def delete(self) -> dict:
        return requests.delete(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/tables/{self.table_id}/",
            headers=self._get_headers(),
        )

    def set_deployed_version(self, version_id: str) -> dict:
        return requests.post(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/tables/{self.table_id}/set-default-version/",
            headers=self._get_headers(),
            json={"version_id": version_id},
        )

    def update_table_version_dependencies(self, dependencies: dict, version_id: str) -> dict:
        response = requests.patch(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/tables-versions/{version_id}/",
            headers=self._get_headers(),
            json={"table_version_dependencies": dependencies},
        )
        response.raise_for_status()
        return response.json()

    def __repr__(self):
        return (
            f"Table(id='{self.table_id}', name='{self.name}', warehouse_id='{self.warehouse_id}')"
        )

    def raw(self):
        response = requests.get(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/tables/{self.table_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            raise ValueError(f"Error getting table: {response.text}")
        return response.json()

    def __str__(self):
        return f"Table: {self.name} ({self.table_id})"

    def _get_warehouse(self):
        """Get a Warehouse instance for this table's project."""
        from .warehouse import Warehouse

        return Warehouse(self.base_url, self.token, self.warehouse_id)

    def export_to_dataset(
        self,
        table_version_id: str | None = None,
        output_dataset_id: str | None = None,
        wait_for_completion: bool = True,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> dict:
        """
        Export table version to output dataset.

        Args:
            table_version_id: Table version to export. If None, uses deployed or latest.
            output_dataset_id: Optional output dataset to export to. If None, creates new one.
            wait_for_completion: If True, polls until operation completes or fails.
            poll_interval: Seconds between status checks (default: 2.0).
            timeout: Maximum seconds to wait for completion (default: 300.0).

        Returns:
            Operation dict with status and result.

        """
        if not table_version_id:
            table_version_id = self._get_deployed_or_latest_version_id()

        payload = {
            "job_type": "export",
            "scope": "table_version",
            "table_version": table_version_id,
        }
        if output_dataset_id:
            payload["output_dataset"] = output_dataset_id

        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/import-export-operations/",
            headers=self._get_headers(),
            json=payload,
        )
        response.raise_for_status()
        operation = response.json()

        if wait_for_completion:
            warehouse = self._get_warehouse()
            return warehouse.poll_import_export_operation(operation["id"], poll_interval, timeout)
        return operation

    def import_from_dataset(
        self,
        input_dataset_id: str | None = None,
        data: dict | list | str | bytes | Path | None = None,
        table_version_id: str | None = None,
        override: bool = False,
        wait_for_completion: bool = True,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> dict:
        """
        Import data to table version from input dataset or raw data.

        You must provide either input_dataset_id OR data, not both.

        Args:
            input_dataset_id: Existing input dataset ID to import from.
            data: Data to upload and import. Can be:
                - list: List of row dicts to import
                - str: Raw JSON string (must be a JSON array)
                - bytes: Raw JSON bytes (must be a JSON array)
                - Path: Path to a JSON file containing an array of rows
            table_version_id: Target table version. If None, uses deployed or latest.
            override: If True, clears existing data before import.
            wait_for_completion: If True, polls until operation completes or fails.
            poll_interval: Seconds between status checks (default: 2.0).
            timeout: Maximum seconds to wait for completion (default: 300.0).

        Returns:
            Operation dict with status and result.

        Example:
            >>> # Import from existing input dataset
            >>> result = table.import_from_dataset(input_dataset_id="uuid-here")

            >>> # Import by uploading data directly
            >>> result = table.import_from_dataset(
            ...     data=[{"id": 1, "name": "test"}, {"id": 2, "name": "other"}], override=True
            ... )

        """
        if input_dataset_id is None and data is None:
            raise ValueError("Either input_dataset_id or data must be provided")
        if input_dataset_id is not None and data is not None:
            raise ValueError("Cannot provide both input_dataset_id and data")

        warehouse = self._get_warehouse()

        if data is not None:
            temp_dataset = warehouse.upload_temp_dataset(
                data=data,
                filename=f"import_{self.name}_{int(time.time())}.json",
            )
            input_dataset_id = temp_dataset["id"]

        if not table_version_id:
            table_version_id = self._get_deployed_or_latest_version_id()

        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/import-export-operations/",
            headers=self._get_headers(),
            json={
                "job_type": "import",
                "scope": "table_version",
                "table_version": table_version_id,
                "input_dataset": input_dataset_id,
                "options": {"override": override},
            },
        )
        response.raise_for_status()
        operation = response.json()

        if wait_for_completion:
            return warehouse.poll_import_export_operation(operation["id"], poll_interval, timeout)
        return operation
