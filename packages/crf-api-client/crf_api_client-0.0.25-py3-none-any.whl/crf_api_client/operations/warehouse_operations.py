# ruff: noqa: G004, PERF203, BLE001, PLR0915

from __future__ import annotations

import json
import logging
import zipfile
from collections import defaultdict
from contextlib import contextmanager

import requests
from tqdm import tqdm

from ..exception import CRFAPIError

logger = logging.getLogger(__name__)


class WarehouseExportError(Exception):
    """Custom exception for warehouse export errors"""


@contextmanager
def api_operation(error_type: Exception, operation_name: str):
    try:
        yield
    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        AttributeError,
        WarehouseExportError,
    ) as e:
        error_message = f"Failed to {operation_name}: {e!s}"
        raise error_type(error_message) from e


class WarehouseExportOperations:
    """Contains all warehouse export-related operations."""

    def __init__(self, warehouse):
        """
        Initialize with a warehouse instance.

        Args:
            warehouse: The Warehouse instance to operate on

        """
        self.warehouse = warehouse

    def _warehouse_exists(self) -> bool:
        """
        Return True if the warehouse still exists on the server.

        Uses list_tables() and detects deletion via KeyError: 'results'.
        """
        try:
            # If the project exists, this should return without error
            self.warehouse.list_tables()
        except KeyError as e:
            # Backend returns a payload without 'results' when project is gone
            if "'results'" in str(e):
                return False
            raise
        else:
            return True

    def _collect_project_and_documents(self, export_data: dict) -> None:
        """Collect project details and documents."""
        error_type = WarehouseExportError

        with api_operation(error_type, "get project details"):
            export_data["project"] = {
                "name": self.warehouse.name,
                "business_brief": self.warehouse.business_brief,
                "default_llm_model": self.warehouse.default_llm_model,
                "reducto_parsing_options": self.warehouse.reducto_parsing_options,
                "push_to_graph_options": getattr(self.warehouse, "push_to_graph_options", {}),
                "default_chunking_maximum_chunk_size": (
                    self.warehouse.default_chunking_maximum_chunk_size
                ),
                "default_chunking_minimum_chunk_size": (
                    self.warehouse.default_chunking_minimum_chunk_size
                ),
                "default_chunking_page_as_separator": (
                    self.warehouse.default_chunking_page_as_separator
                ),
                "default_chunking_title_section_separator_mode": (
                    self.warehouse.default_chunking_title_section_separator_mode
                ),
                "default_chunking_excluded_block_types": (
                    self.warehouse.default_chunking_excluded_block_types
                ),
                "max_fetchable_objects": self.warehouse.max_fetchable_objects,
                "all_queries": getattr(self.warehouse, "all_queries", []),
                "reasoning_workflows": getattr(self.warehouse, "reasoning_workflows", []),
                "ontology": getattr(self.warehouse, "ontology", {}),
            }

        with api_operation(error_type, "get documents"):
            export_data["documents"] = self.warehouse.list_documents()

    def _collect_tools(self, export_data: dict) -> None:
        """Collect tools."""
        error_type = WarehouseExportError
        with api_operation(error_type, "get tools"):
            export_data["tools"] = self.warehouse.list_tools()

    def _collect_agent_settings(self, export_data: dict) -> None:
        """Collect agent settings."""
        try:
            export_data["agent_settings"] = self.warehouse.list_agent_settings()
        except (CRFAPIError, requests.RequestException) as e:
            # If agent settings endpoint fails (e.g., 500 error),
            # log warning and continue with empty list
            status_code = "unknown"
            if (
                isinstance(e, CRFAPIError) and hasattr(e, "response") and e.response is not None
            ) or (
                isinstance(e, requests.RequestException)
                and hasattr(e, "response")
                and e.response is not None
            ):
                status_code = e.response.status_code

            logger.warning(
                f"Failed to collect agent settings (status: {status_code}): {e!s}. "
                "Continuing export with empty agent settings."
            )
            export_data["agent_settings"] = []

    def _collect_object_extractors(self, export_data: dict) -> None:
        """Collect object extractors."""
        error_type = WarehouseExportError
        with api_operation(error_type, "get object extractors"):
            export_data["object_extractors"] = self.warehouse.list_object_extractors()

    def _collect_tag_extractors(self, export_data: dict) -> None:
        """Collect tag extractors."""
        error_type = WarehouseExportError
        with api_operation(error_type, "get tag extractors"):
            export_data["tag_extractors"] = self.warehouse.list_tag_extractors()

    def _collect_chunk_extractors(self, export_data: dict) -> None:
        """Collect chunk extractors."""
        error_type = WarehouseExportError
        with api_operation(error_type, "get chunk extractors"):
            export_data["chunk_extractors"] = self.warehouse.list_chunk_extractors()

    def _collect_local_documents(self, export_data: dict) -> None:
        """Collect local documents at project level."""
        error_type = WarehouseExportError
        with api_operation(error_type, "get local documents"):
            export_data["local_documents"] = [
                doc
                for doc in self.warehouse.list_local_documents()
                if doc.get("type") == "agent_settings"
            ]

    def _collect_ground_truths(self, export_data: dict) -> None:
        """Collect ground truths."""
        error_type = WarehouseExportError
        with api_operation(error_type, "get ground truths"):
            export_data["ground_truths"] = self.warehouse.list_ground_truths()

    def _process_default_table(self, table, table_type, export_data: dict) -> None:
        """Process default table data."""
        error_type = WarehouseExportError
        with api_operation(error_type, f"get {table_type}"):
            if table_type not in export_data:
                export_data[table_type] = []
            export_data[table_type].append(
                {
                    "name": table.name,
                    "data": table.get_data(),
                    "columns": table.columns,
                }
            )

    def _process_object_table(self, table, export_data: dict) -> None:
        """Process object table data with model file handling."""
        error_type = WarehouseExportError
        with api_operation(error_type, "get objects"):
            # Store the pydantic class code separately for import
            object_metadata = table.object_metadata.copy()
            if "object_pydantic_class" in object_metadata:
                object_metadata["pydantic_class_string"] = object_metadata["object_pydantic_class"]
                del object_metadata["object_pydantic_class"]
            if "objects" not in export_data:
                export_data["objects"] = []
            export_data["objects"].append(
                {
                    "name": table.name,
                    "config": object_metadata,
                    "data": table.get_data(),
                }
            )

    def _process_tag_table(self, table, export_data: dict) -> None:
        """Process tag table data."""
        error_type = WarehouseExportError
        with api_operation(error_type, "get tags"):
            if "tags" not in export_data:
                export_data["tags"] = []
            export_data["tags"].append(
                {
                    "name": table.name,
                    "config": table.object_metadata,
                    "data": table.get_data(),
                }
            )

    def _process_alert_tables(self, table, export_data: dict) -> None:
        """Process alert table data."""
        error_type = WarehouseExportError

        if table.object_type == "tag_alert":
            with api_operation(error_type, "get tag alerts"):
                export_data["tag_alerts"].append(
                    {
                        "config": {
                            "name": table.name,
                        },
                        "data": table.get_data(),
                    }
                )
        elif table.object_type == "object_alert":
            with api_operation(error_type, "get object alerts"):
                alerts = table.get_data()
                export_data["object_alerts"].append(
                    {
                        "config": {
                            "name": table.name,
                        },
                        "data": alerts,
                    }
                )

    def _process_table_by_type(self, table, export_data: dict) -> None:
        """Process table data based on its object type."""
        if table.object_type == "chunk":
            self._process_default_table(table, "chunks", export_data)
        elif table.object_type == "block":
            self._process_default_table(table, "blocks", export_data)
        elif table.object_type == "parsed_document":
            self._process_default_table(table, "parsed_documents", export_data)
        elif table.object_type == "object":
            self._process_object_table(table, export_data)
        elif table.object_type == "tag":
            self._process_tag_table(table, export_data)
        elif table.object_type in ["tag_alert", "object_alert"]:
            self._process_alert_tables(table, export_data)
        elif table.object_type == "status":
            pass  # Skip status tables
        else:
            error_message = f"Unknown table type: {table.object_type}"
            raise WarehouseExportError(error_message)

    def _process_table_new(self, table, export_data: dict) -> None:
        """Process table with versions"""
        error_type = WarehouseExportError
        with api_operation(error_type, f"get {table.name}"):
            table_raw = table.raw()
            if table_raw.get("object_type") == "status":
                return
            export_data["tables"][table.name] = table.raw()
            versions = table.list_versions()
            versions.sort(key=lambda x: x["version"])
            export_data["tables"][table.name]["versions"] = versions

    def _download_documents(
        self, zip_file: zipfile.ZipFile, documents: list[dict], error_type: Exception
    ) -> None:
        """
        Download documents and add them to the zip file.

        Args:
            zip_file: The zip file to add documents to
            documents: List of document dictionaries containing 'id', 'name', and 'file' keys
            error_type: Exception type to use for error handling

        """
        if documents:
            with tqdm(
                total=len(documents), desc="Downloading documents", unit="doc", leave=False
            ) as doc_pbar:
                for document in documents:
                    try:
                        doc_pbar.set_description(f"Downloading {document['name']}")
                        with api_operation(error_type, f"download document {document['name']}"):
                            doc_response = requests.get(
                                document["file"],
                                stream=True,
                            )
                            doc_response.raise_for_status()
                            doc_path = f"documents/{document['id']}/{document['name']}"
                            zip_file.writestr(doc_path, doc_response.content)
                            message = f"Downloaded and added document: {document['name']}"
                            logger.info(message)

                    except (
                        OSError,
                        ValueError,
                        RuntimeError,
                        KeyError,
                        AttributeError,
                        WarehouseExportError,
                    ) as e:
                        message = f"Failed to download document {document['name']}: {e}"
                        logger.warning(message)
                    doc_pbar.update(1)

    def _download_tables_data(
        self, zip_file: zipfile.ZipFile, tables: list[dict], error_type: Exception
    ) -> None:
        """
        Download tables data and add them to the zip file.

        Args:
            zip_file: The zip file to add documents to
            tables: List of table dictionaries containing 'id', 'name', and 'file' keys
            error_type: Exception type to use for error handling

        """
        if tables:
            with tqdm(
                total=len(tables), desc="Downloading tables", unit="table", leave=False
            ) as table_pbar:
                for table in tables.values():
                    table_obj = self.warehouse.get_table(table["id"])
                    for version in table["versions"]:
                        try:
                            table_pbar.set_description(
                                f"Downloading {table['name']} version {version['id']}"
                            )
                            with api_operation(
                                error_type,
                                f"download table {table['name']} version {version['id']}",
                            ):
                                try:
                                    table_data = table_obj.get_data(
                                        table_version_id=version["id"],
                                        page_size=1000,
                                    )
                                except Exception:
                                    table_data = table_obj.get_data(
                                        table_version_id=version["id"],
                                        page_size=10,
                                    )
                                table_path = f"tables_data/{table['id']}/{version['id']}"
                                zip_file.writestr(
                                    table_path, json.dumps(table_data, indent=2, default=str)
                                )
                                message = (
                                    f"Downloaded and added table {table['name']}"
                                    f"version {version['id']}"
                                )
                                logger.info(message)
                        except Exception as e:
                            message = (
                                f"Failed to download table {table['name']}"
                                f"version {version['id']}: {e}"
                            )
                            logger.warning(message)
                    table_pbar.update(1)
                    table_pbar.refresh()

    def _download_local_documents(
        self, zip_file: zipfile.ZipFile, local_documents: list[dict], error_type: Exception
    ) -> None:
        """Download local documents for agent settings and add them to the zip file."""
        if local_documents:
            with tqdm(
                total=len(local_documents),
                desc="Downloading local documents",
                unit="doc",
                leave=False,
            ) as doc_pbar:
                for local_doc in local_documents:
                    try:
                        doc_pbar.set_description(f"Downloading {local_doc['name']}")
                        with api_operation(
                            error_type, f"download local document {local_doc['name']}"
                        ):
                            doc_response = requests.get(
                                local_doc["file"],
                                stream=True,
                            )
                            doc_response.raise_for_status()
                            doc_path = f"local_documents/{local_doc['id']}/{local_doc['name']}"
                            zip_file.writestr(doc_path, doc_response.content)
                            message = f"Downloaded and added local document: {local_doc['name']}"
                            logger.info(message)

                    except (
                        OSError,
                        ValueError,
                        RuntimeError,
                        KeyError,
                        AttributeError,
                        WarehouseExportError,
                    ) as e:
                        message = f"Failed to download local document {local_doc.get('name', 'unknown')}: {e}"  # noqa: E501
                        logger.warning(message)
                    doc_pbar.update(1)

    def export_warehouse(self, output_path: str | None = None) -> str:
        """Export all relevant data for this warehouse and create a zip file."""
        error_type = WarehouseExportError

        with tqdm(total=10, desc="Exporting Warehouse", unit="step") as pbar:
            try:
                pbar.set_description("Validating warehouse exists")
                with api_operation(error_type, "validate warehouse exists"):
                    if not self._warehouse_exists():
                        self._raise_warehouse_not_found_error()
                pbar.update(1)
                pbar.refresh()

                pbar.set_description("Collecting project details and documents")
                export_data = defaultdict(list)
                self._collect_project_and_documents(export_data)
                pbar.update(1)
                pbar.refresh()

                pbar.set_description("Collecting Tools")
                self._collect_tools(export_data)
                pbar.update(1)
                pbar.refresh()

                pbar.set_description("Collecting Agent Settings")
                self._collect_agent_settings(export_data)
                pbar.update(1)
                pbar.refresh()

                pbar.set_description("Collecting Local Documents")
                self._collect_local_documents(export_data)
                pbar.update(1)
                pbar.refresh()

                pbar.set_description("Collecting Ground Truths")
                self._collect_ground_truths(export_data)
                pbar.update(1)
                pbar.refresh()

                pbar.set_description("Collecting extractors")
                self._collect_object_extractors(export_data)
                self._collect_tag_extractors(export_data)
                self._collect_chunk_extractors(export_data)
                pbar.update(1)
                pbar.refresh()

                pbar.set_description("Processing tables")
                export_data["tables"] = {}
                tables = self.warehouse.list_tables()
                with tqdm(
                    total=len(tables), desc="Processing tables", unit="table", leave=False
                ) as table_pbar:
                    for table in tables:
                        table_pbar.set_description(f"Processing {table.name}")
                        self._process_table_new(table, export_data)
                        table_pbar.update(1)
                export_data = dict(export_data)
                pbar.update(1)
                pbar.refresh()

                pbar.set_description("Creating zip file")
                if output_path is None:
                    output_path = f"warehouse_{self.warehouse.id}.zip"

                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.writestr(
                        "export_data.json", json.dumps(export_data, indent=2, default=str)
                    )
                pbar.update(1)
                pbar.refresh()

                pbar.set_description("Downloading tables data")
                if export_data["tables"]:
                    with zipfile.ZipFile(output_path, "a") as zip_file:
                        self._download_tables_data(zip_file, export_data["tables"], error_type)
                pbar.update(1)

                pbar.set_description("Downloading documents")
                if export_data["documents"]:
                    with zipfile.ZipFile(output_path, "a") as zip_file:
                        self._download_documents(zip_file, export_data["documents"], error_type)
                pbar.update(1)
                pbar.refresh()

                pbar.set_description("Downloading local documents")
                if export_data.get("local_documents"):
                    with zipfile.ZipFile(output_path, "a") as zip_file:
                        self._download_local_documents(
                            zip_file, export_data["local_documents"], error_type
                        )
                pbar.update(1)
                pbar.set_description("Export completed")
                pbar.refresh()

            except Exception as e:
                error_message = f"Failed to export warehouse: {e!s}"
                raise error_type(error_message) from e

        message = f"Warehouse export completed: {output_path}"
        logger.info(message)
        return output_path

    def _raise_warehouse_not_found_error(self):
        """Raise error when warehouse is not found."""
        error_message = f"Warehouse with ID {self.warehouse.id} does not exist"
        raise WarehouseExportError(error_message)
