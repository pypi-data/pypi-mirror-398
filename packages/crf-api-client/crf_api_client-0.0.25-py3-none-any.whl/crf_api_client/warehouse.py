# ruff: noqa: ANN003, D105, PLW2901, RET504, PLR2004, EM102, G004, A002, ARG002

from __future__ import annotations

import inspect
import json
import logging
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from pathlib import Path
from typing import List, Set, Type

import requests
from datamodel_code_generator import DataModelType, InputFileType, generate
from pydantic import BaseModel

from .base import BaseAPIClient
from .exception import CRFAPIError
from .models import (
    Feedback,
    FeedbackClassification,
    FeedbackClassificationResponse,
    GroundTruth,
    GroundTruthsFromFeedbacks,
)
from .operations.warehouse_operations import WarehouseExportOperations
from .playground_agent import PlaygroundAgent
from .table import Table
from .task import Task

logger = logging.getLogger(__name__)


def inject_docstring(code: str, class_name: str, docstring: str) -> str:
    """Insert a docstring into a generated class definition."""
    docstring_block = '    """' + docstring.strip().replace("\n", "\n    ") + '"""\n'

    # Use regex to find the class definition
    pattern = rf"(class {re.escape(class_name)}\(.*?\):\n)"

    # Inject the docstring after the class declaration
    return re.sub(pattern, r"\1" + docstring_block, code)


def _collect_str_enums(model_cls: Type[BaseModel]) -> Set[str]:
    """
    Collect names of Enum classes that inherit from str by inspecting the model's module.

    This simpler approach finds all enum classes in the same module as the model
    that inherit from str, rather than recursively traversing field types.

    Args:
        model_cls: The Pydantic model class to inspect

    Returns:
        Set of enum class names that inherit from str

    """
    str_enum_names: Set[str] = set()

    # Get the module where the model is defined
    module = inspect.getmodule(model_cls)
    if module is None:
        return str_enum_names

    # Inspect all classes in the module
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Check if it's an Enum that inherits from str
        if issubclass(obj, Enum) and str in obj.__mro__:
            str_enum_names.add(name)

    return str_enum_names


def _fix_str_enum_inheritance(code: str, str_enum_names: Set[str]) -> str:
    """
    Fix enum class definitions to include str inheritance.

    Replaces `class EnumName(Enum):` with `class EnumName(str, Enum):`
    for enums that should inherit from str.

    Args:
        code: Generated Python code
        str_enum_names: Set of enum class names that should inherit from str

    Returns:
        Fixed code with str inheritance added to enum definitions

    """
    if not str_enum_names:
        return code

    # Single regex pattern that matches both cases: (Enum): and (Enum, ...)
    for enum_name in str_enum_names:
        # Match: class EnumName(Enum): or class EnumName(Enum, ...)
        pattern = rf"class {re.escape(enum_name)}\(Enum([,\)])"
        replacement = rf"class {enum_name}(str, Enum\1"
        code = re.sub(pattern, replacement, code)

    return code


def model_to_code(model_cls: Type[BaseModel], *, class_name: str | None = None) -> str:
    """
    Convert a Pydantic model class into nicely-formatted source code.

    using `datamodel-code-generator` entirely in memory.

    Parameters
    ----------
    model_cls : Type[BaseModel]
        The Pydantic model you want to export.
    class_name : str | None
        Optional new name for the top-level class in the generated file.

    Returns
    -------
    str
        A Python module (including imports) as plain text.

    """
    # 1) Collect enum classes that inherit from str before schema generation
    str_enum_names = _collect_str_enums(model_cls)

    # 2) Serialize the model`s *schema* (not an instance) to JSON text
    schema_text = json.dumps(model_cls.model_json_schema())
    docstring = model_cls.__doc__ or ""

    # 3) Create a temporary *.py* file, have `generate()` write into it, read it back
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "model.py"
        generate(
            schema_text,
            input_file_type=InputFileType.JsonSchema,
            input_filename=f"{model_cls.__name__}.json",
            output=out_path,
            output_model_type=DataModelType.PydanticV2BaseModel,
            class_name=class_name or model_cls.__name__,
        )
        lines = out_path.read_text().splitlines()
        new_text = "\n".join(lines[6:])

        # 4) Fix enum definitions to preserve str inheritance
        new_text = _fix_str_enum_inheritance(new_text, str_enum_names)

        # 5) Inject docstrings for all referenced models
        for _, model in model_cls.model_fields.items():  # noqa: PERF102
            if hasattr(model.annotation, "__origin__") and model.annotation.__origin__ is list:
                # Handle List[Model] case
                inner_type = model.annotation.__args__[0]
                if issubclass(inner_type, BaseModel) and inner_type.__doc__:
                    new_text = inject_docstring(new_text, inner_type.__name__, inner_type.__doc__)
            elif (
                isinstance(model.annotation, type)
                and issubclass(model.annotation, BaseModel)
                and model.annotation.__doc__
            ):
                # Handle direct Model reference case
                new_text = inject_docstring(
                    new_text, model.annotation.__name__, model.annotation.__doc__
                )

        # 6) Finally inject the main model's docstring
        return inject_docstring(new_text, class_name or model_cls.__name__, docstring)


class Warehouse(BaseAPIClient):
    def __init__(self, base_url: str, token: str, id: str, name: str = None, **kwargs):
        super().__init__(base_url, token)
        self.name = name
        self.id = id
        # Store any additional warehouse attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _get_headers(self):
        return {"Authorization": f"Token {self.token}", "Content-Type": "application/json"}

    def _get_headers_without_content_type(self):
        return {"Authorization": f"Token {self.token}"}

    def _get_paginated_data(self, url: str, params: dict = {}) -> list[dict]:
        next_url = url
        data = []
        use_https = url.startswith("https://")
        is_first_call = True

        while next_url:
            # Ensure HTTPS consistency if base URL uses HTTPS
            if use_https and next_url.startswith("http://"):
                next_url = next_url.replace("http://", "https://")
            if is_first_call:
                response = requests.get(next_url, headers=self._get_headers(), params=params)
                is_first_call = False
            else:
                response = requests.get(next_url, headers=self._get_headers())

            # Check response status before parsing JSON
            if response.status_code != 200:
                # Try to parse error response, but handle cases where it's not JSON
                try:
                    error_data = response.json()
                except (ValueError, requests.JSONDecodeError):
                    error_data = {"detail": response.text or f"HTTP {response.status_code}"}
                raise CRFAPIError(error_data, response)

            # Check if response has content before parsing
            if not response.text or not response.text.strip():
                # Empty response, return empty list
                break

            try:
                response_data = response.json()
            except (ValueError, requests.JSONDecodeError) as e:
                raise CRFAPIError(
                    {
                        "detail": f"Invalid JSON response: {e!s}",
                        "response_text": response.text[:500],
                    },
                    response,
                ) from e

            data.extend(response_data.get("results", []))
            next_url = response_data.get("next")

        return data

    # Table-related methods that return Table objects
    def get_table(self, table_identifier: str | int) -> Table:
        """Get a specific table by name or ID and return as Table object"""
        # First try to find by name, then by ID
        tables = self.list_tables()

        for table in tables:
            if table_identifier in (table.name, table.table_id):
                return table

        msg = f"Table '{table_identifier}' not found in warehouse {self.id}"
        raise ValueError(msg)

    def get_deployed_or_latest_chunks_table_version_id(self) -> str | None:
        """Get the deployed or latest chunks table version"""
        try:
            chunks_table = self.get_table("chunks")
        except ValueError:
            return None
        versions = chunks_table.list_versions()
        if len(versions) == 0:
            return None
        for version in versions:
            if version.get("deployed"):
                return version.get("id")
        return versions[-1].get("id")

    def create_table(
        self,
        table_name: str,
        columns: list[dict],
        object_type: str = "custom",
        object_metadata: dict = {},
        table_version_dependencies: dict = {},
    ) -> Table:
        """Create a table in this warehouse and return as Table object"""
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/tables/",
            headers=self._get_headers(),
            json={
                "name": table_name,
                "columns": columns,
                "object_type": object_type,
                "object_metadata": object_metadata,
                "table_version_dependencies": table_version_dependencies,
            },
        )
        data = response.json()

        return Table(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            table_id=data.get("id"),
            name=data.get("name"),
            **{k: v for k, v in data.items() if k not in ["id", "name"]},
        )

    def list_tables(self) -> List[Table]:
        """List all tables in this warehouse as Table objects"""
        tables_data = self._get_paginated_data(f"{self.base_url}/api/v1/projects/{self.id}/tables/")
        tables = []
        for table_data in tables_data:
            table = Table(
                base_url=self.base_url,
                token=self.token,
                warehouse_id=self.id,
                table_id=table_data.get("id"),
                name=table_data.get("name"),
                **{k: v for k, v in table_data.items() if k not in ["id", "name"]},
            )
            tables.append(table)
        return tables

    def delete_table(self, table_identifier: str | Table) -> None:
        """Delete a table by ID, name, or Table object"""
        if isinstance(table_identifier, Table):
            table_id = table_identifier.table_id
        else:
            # Find table by name or ID
            tables = self.list_tables()
            table_id = None
            for table in tables:
                if table_identifier in (table.name, table.table_id):
                    table_id = table.table_id
                    break

            if not table_id:
                msg = f"Table '{table_identifier}' not found in warehouse {self.id}"
                raise ValueError(msg)

        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/tables/{table_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 204:
            raise CRFAPIError(response.json(), response)

    # Tools management
    def list_tools(self) -> List[dict]:
        """List all tools in this warehouse"""
        return self._get_paginated_data(f"{self.base_url}/api/v1/projects/{self.id}/tools/")

    def create_tool(self, tool: dict) -> dict:
        """Create a tool in this warehouse"""
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/tools/",
            headers=self._get_headers(),
            json=tool,
        )
        if response.status_code != 201:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def update_tool(self, tool_id: str, tool: dict) -> dict:
        """Update a tool by ID"""
        response = requests.put(
            f"{self.base_url}/api/v1/projects/{self.id}/tools/{tool_id}/",
            headers=self._get_headers(),
            json=tool,
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def delete_tool(self, tool_id: str) -> None:
        """Delete a tool by ID"""
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/tools/{tool_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 204:
            raise CRFAPIError(response.json(), response)

    def run_tool(self, tool_id: str, input: dict) -> dict:
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/tools/{tool_id}/run/",
            headers=self._get_headers(),
            json=input,
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        return response.json()

    # Agent Settings management
    def list_agent_settings(self) -> List[dict]:
        """List all agent settings in this warehouse."""
        url = f"{self.base_url}/api/v1/projects/{self.id}/agent-settings/"
        return self._get_paginated_data(url)

    def get_agent_settings(self, settings_id: str) -> dict:
        """Get agent settings by ID."""
        response = requests.get(
            f"{self.base_url}/api/v1/projects/{self.id}/agent-settings/{settings_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def get_playground_agent(self, agent_settings_id: str) -> PlaygroundAgent:
        """Get a playground agent by agent settings ID and return as PlaygroundAgent object"""
        # Verify the agent settings exists
        agent_settings = self.get_agent_settings(agent_settings_id)

        return PlaygroundAgent(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            agent_settings_id=agent_settings_id,
            **{k: v for k, v in agent_settings.items() if k not in ["id"]},
        )

    def create_agent_settings(self, settings: dict) -> dict:
        """Create agent settings in this warehouse."""
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/agent-settings/",
            headers=self._get_headers(),
            json=settings,
        )
        if response.status_code != 201:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def update_agent_settings(self, settings_id: str, settings: dict) -> dict:
        """Update agent settings by ID."""
        response = requests.put(
            f"{self.base_url}/api/v1/projects/{self.id}/agent-settings/{settings_id}/",
            headers=self._get_headers(),
            json=settings,
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def delete_agent_settings(self, settings_id: str) -> None:
        """Delete agent settings by ID."""
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/agent-settings/{settings_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 204:
            raise CRFAPIError(response.json(), response)

    # Ground Truth management
    def list_ground_truths(self) -> List[dict]:
        """List all ground truths in this warehouse."""
        url = f"{self.base_url}/api/v1/projects/{self.id}/ground-truths/"
        return self._get_paginated_data(url)

    def get_ground_truth(self, ground_truth_id: str) -> dict:
        """Get a ground truth by ID."""
        response = requests.get(
            f"{self.base_url}/api/v1/projects/{self.id}/ground-truths/{ground_truth_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def create_ground_truth(
        self,
        query: str,
        answer: str,
        additional_notes: str | None = None,
        source_feedback_id: str | None = None,
    ) -> dict:
        """Create a ground truth in this warehouse."""
        payload = {
            "query": query,
            "answer": answer,
        }
        if additional_notes is not None:
            payload["additional_notes"] = additional_notes
        if source_feedback_id is not None:
            payload["source_feedback_id"] = source_feedback_id

        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/ground-truths/",
            headers=self._get_headers(),
            json=payload,
        )
        if response.status_code != 201:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def update_ground_truth(
        self,
        ground_truth_id: str,
        query: str | None = None,
        answer: str | None = None,
        additional_notes: str | None = None,
        source_feedback_id: str | None = None,
    ) -> dict:
        """Update a ground truth by ID."""
        payload = {}
        if query is not None:
            payload["query"] = query
        if answer is not None:
            payload["answer"] = answer
        if additional_notes is not None:
            payload["additional_notes"] = additional_notes
        if source_feedback_id is not None:
            payload["source_feedback_id"] = source_feedback_id
        response = requests.patch(
            f"{self.base_url}/api/v1/projects/{self.id}/ground-truths/{ground_truth_id}/",
            headers=self._get_headers(),
            json=payload,
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def delete_ground_truth(self, ground_truth_id: str) -> None:
        """Delete a ground truth by ID."""
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/ground-truths/{ground_truth_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 204:
            raise CRFAPIError(response.json(), response)

    # Settings management
    def update_settings(self, **settings) -> dict:
        """Update warehouse settings"""
        response = requests.patch(
            f"{self.base_url}/api/v1/projects/{self.id}/",
            headers=self._get_headers(),
            json=settings,
        )
        return response.json()

    def list_conversations(self) -> list[dict]:
        """List all playground conversations for this warehouse"""
        url = f"{self.base_url}/api/v1/projects/{self.id}/playground-conversations/"
        conversations = self._get_paginated_data(url)
        return conversations

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a playground conversation by ID"""
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/playground-conversations/{conversation_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 204:
            raise CRFAPIError(response.text, response)

    # LocalDocument management methods
    def upload_local_documents_to_agent_settings(
        self, agent_settings_id: str, file_paths: List[str], batch_size: int = 10
    ) -> List[dict]:
        """Upload local documents to an agent settings"""
        responses = []
        all_local_documents = []

        # Process files in batches
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i : i + batch_size]
            files_to_upload = []

            try:
                # Open files for current batch
                for file_path in batch:
                    files_to_upload.append(("files", (Path(file_path).name, open(file_path, "rb"))))

                # Upload current batch
                response = requests.post(
                    f"{self.base_url}/api/v1/projects/{self.id}/agent-settings/"
                    f"{agent_settings_id}/local-documents/bulk-upload/",
                    headers=self._get_headers_without_content_type(),
                    files=files_to_upload,
                )
                if response.status_code != 201:
                    raise CRFAPIError(response.json(), response)
                batch_response = response.json()
                if isinstance(batch_response, list):
                    all_local_documents.extend(batch_response)
                else:
                    all_local_documents.append(batch_response)
                responses.append(batch_response)

            finally:
                # Ensure files are closed even if an error occurs
                for _, (_, file_obj) in files_to_upload:
                    file_obj.close()

        return all_local_documents

    def upload_local_documents_bulk(
        self,
        file_paths: List[str],
        doc_type: str,
        agent_settings_id: str = None,
        conversation_id: str = None,
        skip_processing: bool = False,
        batch_size: int = 10,
    ) -> List[dict]:
        """Upload local documents at project level with bulk upload"""
        if doc_type == "agent_settings" and not agent_settings_id:
            raise ValueError("agent_settings_id is required when type is 'agent_settings'")
        if doc_type == "conversation" and not conversation_id:
            raise ValueError("conversation_id is required when type is 'conversation'")

        responses = []
        all_local_documents = []

        # Process files in batches
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i : i + batch_size]
            files_to_upload = []

            try:
                # Open files for current batch
                for file_path in batch:
                    files_to_upload.append(
                        ("files", (file_path.split("/")[-1], open(file_path, "rb")))
                    )

                # Prepare form data
                data = {
                    "type": doc_type,
                    "skip_processing": "true" if skip_processing else "false",
                }
                if agent_settings_id:
                    data["agent_settings"] = agent_settings_id
                if conversation_id:
                    data["conversation"] = conversation_id

                # Upload current batch
                response = requests.post(
                    f"{self.base_url}/api/v1/projects/{self.id}/local-documents/bulk-upload/",
                    headers=self._get_headers_without_content_type(),
                    files=files_to_upload,
                    data=data,
                )
                if response.status_code != 201:
                    raise CRFAPIError(response.json(), response)
                batch_response = response.json()
                if isinstance(batch_response, list):
                    all_local_documents.extend(batch_response)
                else:
                    all_local_documents.append(batch_response)
                responses.append(batch_response)

            finally:
                # Ensure files are closed even if an error occurs
                for _, (_, file_obj) in files_to_upload:
                    file_obj.close()

        return all_local_documents

    def delete_local_document_from_agent_settings(
        self, agent_settings_id: str, local_document_id: str
    ) -> None:
        """Delete a local document from an agent settings"""
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/agent-settings/"
            f"{agent_settings_id}/local-documents/{local_document_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 204:
            raise CRFAPIError(response.json(), response)

    def list_local_documents_for_agent_settings(self, agent_settings_id: str) -> List[dict]:
        """List all local documents for an agent settings"""
        url = (
            f"{self.base_url}/api/v1/projects/{self.id}/agent-settings/"
            f"{agent_settings_id}/local-documents/"
        )
        return self._get_paginated_data(url)

    def list_local_documents(self) -> List[dict]:
        """List all local documents for this warehouse (project-level)"""
        url = f"{self.base_url}/api/v1/projects/{self.id}/local-documents/"
        return self._get_paginated_data(url)

    # Document management methods
    def upload_documents(
        self, file_paths: List[str], skip_parsing: bool = False, batch_size: int = 10
    ) -> List[dict]:
        """Upload documents to this warehouse"""
        responses = []
        data = {"skip_parsing": "true"} if skip_parsing else {}

        # Process files in batches
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i : i + batch_size]
            files_to_upload = []

            try:
                # Open files for current batch
                for file_path in batch:
                    files_to_upload.append(
                        ("files", (file_path.split("/")[-1], open(file_path, "rb")))
                    )

                # Upload current batch
                response = requests.post(
                    f"{self.base_url}/api/v1/projects/{self.id}/documents/bulk-upload/",
                    headers=self._get_headers_without_content_type(),
                    files=files_to_upload,
                    data=data,
                )
                responses.append(response.json())

            finally:
                # Ensure files are closed even if an error occurs
                for _, (_, file_obj) in files_to_upload:
                    file_obj.close()

        return responses

    def list_documents(self) -> List[dict]:
        """List all documents in this warehouse"""
        return self._get_paginated_data(f"{self.base_url}/api/v1/projects/{self.id}/documents/")

    def list_documents_without_file(self) -> List[dict]:
        """List all documents in this warehouse"""
        return self._get_paginated_data(
            f"{self.base_url}/api/v1/projects/{self.id}/documents/get-without-file/?limit=1000"
        )

    def delete_documents(self, document_ids: List[str]) -> dict:
        """Remove documents from this warehouse"""
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/documents/bulk-delete/",
            headers=self._get_headers(),
            json={"document_ids": document_ids},
        )
        return response.json()

    def create_objects_table(
        self, table_name, object_class, object_name=None, table_version_dependencies: dict = {}
    ):
        data = {
            "name": table_name,
            "columns": [
                {"name": "id", "type": "uuid"},
                {"name": "json_object", "type": "json"},
                {"name": "object_bbox", "type": "json"},
                {"name": "document_id", "type": "uuid"},
                {"name": "min_page", "type": "int"},
                {"name": "max_page", "type": "int"},
                {"name": "content", "type": "text"},
                {"name": "blocks", "type": "json"},
                {"name": "selected_blocks", "type": "json"},
                {"name": "version", "type": "text"},
            ],
            "object_type": "object",
            "object_metadata": {
                "object_name": object_class.__name__ if object_name is None else object_name,
                "object_pydantic_class": model_to_code(object_class)
                if isinstance(object_class, type)
                else object_class,
            },
        }
        # Only set table_version_dependencies if explicitly provided
        if table_version_dependencies:
            data["table_version_dependencies"] = table_version_dependencies

        r = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/tables/",
            headers=self._get_headers(),
            json=data,
        )
        if r.status_code == 400:
            raise CRFAPIError(f"Bad request: {r.text}", r)
        r.raise_for_status()
        data = r.json()

        return Table(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            table_id=data.get("id"),
            name=data.get("name"),
            object_type=data.get("object_type"),
        )

    def create_tag_table(self, table_name, tagging_tree, table_version_dependencies: dict = {}):
        data = {
            "name": table_name,
            "columns": [
                {"name": "chunk_id", "type": "uuid"},
                {"name": "metadata", "type": "json"},
                {"name": "id", "type": "text"},
            ],
            "object_type": "tag",
            "object_metadata": {
                "tag_name": tagging_tree.get("name", "Manually Created Tag"),
                "tagging_tree": tagging_tree,
            },
        }
        if table_version_dependencies.get("chunks"):
            data["table_version_dependencies"] = table_version_dependencies
        else:
            data["table_version_dependencies"] = {
                "chunks": self.get_deployed_or_latest_chunks_table_version_id()
            }

        r = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/tables/",
            headers=self._get_headers(),
            json=data,
        )
        if r.status_code == 400:
            raise CRFAPIError(f"Bad request: {r.text}", r)
        r.raise_for_status()
        data = r.json()

        return Table(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            table_id=data.get("id"),
            name=data.get("name"),
            object_type=data.get("object_type"),
        )

    def create_document_tags_table(self, table_name, document_tags):
        data = {
            "name": table_name,
            "columns": [
                {"name": "id", "type": "uuid"},
                {"name": "document_id", "type": "uuid"},
                {"name": "tag_name", "type": "text"},
                {"name": "tag_value", "type": "text"},
                {"name": "justification", "type": "text"},
                {"name": "verbatim", "type": "text"},
            ],
            "object_type": "document_tags",
            "object_metadata": {"tags": document_tags},
        }

        r = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/tables/",
            headers=self._get_headers(),
            json=data,
        )
        if r.status_code == 400:
            raise CRFAPIError(f"Bad request: {r.text}", r)
        r.raise_for_status()
        data = r.json()

        return Table(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            table_id=data.get("id"),
            name=data.get("name"),
            object_type=data.get("object_type"),
        )

    def run_document_tags_extraction(
        self,
        table_id: str | None = None,
        mode: str | None = None,
        llm_model: str | None = None,
        document_ids: list[str] | None = None,
        should_push_to_graph: bool = False,
        metadata_structure: dict | None = None,
    ):
        fields = {
            "table_id": table_id,
            "mode": mode,
            "llm_model": llm_model,
            "document_ids": document_ids,
            "should_push_to_graph": should_push_to_graph,
            "metadata_structure": metadata_structure,
        }
        payload = {k: v for k, v in fields.items() if v is not None}
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/run-document-tag-extraction/",
            headers=self._get_headers(),
            json=payload,
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        data = response.json()
        return Task(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            task_id=data.get("pipeline_run_id"),
            status="pending",
            **{k: v for k, v in data.items() if k not in ["pipeline_run_id"]},
        )

    def __repr__(self):
        return f"Warehouse(id='{self.id}', name='{self.name}')"

    def __str__(self):
        return f"Warehouse: {self.name} ({self.id})"

    def retrieve_with_semantic_search(
        self,
        query: str,
        n_objects: int = 10,
        indexes: list[str] = [],
        included_tags: dict | list[dict] | None = None,
        excluded_tags: dict | list[dict] | None = None,
        reformulate_query: bool = False,
        rerank: bool = False,
        included_objects: list[dict] | None = None,
        excluded_objects: list[dict] | None = None,
        included_attributes: list[dict] | None = None,
        excluded_attributes: list[dict] | None = None,
        selected_documents: list[dict] | None = None,
        **kwargs,
    ) -> list:
        if "enrich_with_chunks" in kwargs:
            logger.warning("enrich_with_chunks is deprecated and has no effect.")
        if not indexes:
            indexes = ["chunks"]
        if included_tags is None:
            included_tags = {}
        if excluded_tags is None:
            excluded_tags = {}
        if included_attributes is None:
            included_attributes = []
        if excluded_attributes is None:
            excluded_attributes = []
        """Retrieve objects from this warehouse with semantic search"""
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/retrieve-with-naive/",
            headers=self._get_headers(),
            json={
                "query": query,
                "n_objects": n_objects,
                "indexes": indexes,
                "included_tags": included_tags,
                "excluded_tags": excluded_tags,
                "reformulate_query": reformulate_query,
                "rerank": rerank,
                "included_objects": included_objects,
                "excluded_objects": excluded_objects,
                "included_attributes": included_attributes,
                "excluded_attributes": excluded_attributes,
                "selected_documents": selected_documents,
            },
        )

        if response.status_code == 200:
            return response.json()["retrieval_results"]
        logger.exception(f"Failed to retrieve with semantic search: {response.text}")
        return []

    def generate_answer_with_semantic_search(
        self,
        question: str,
        query: str | None,
        n_objects: int = 10,
        indexes: list[str] = [],
        included_tags: dict | list[dict] | None = None,
        excluded_tags: dict | list[dict] | None = None,
        reformulate_query: bool = False,
        rerank: bool = False,
        **kwargs,
    ) -> str | None:
        if "enrich_with_chunks" in kwargs:
            logger.warning("enrich_with_chunks is deprecated and has no effect.")
        if not indexes:
            indexes = ["chunks"]
        if included_tags is None:
            included_tags = {}
        if excluded_tags is None:
            excluded_tags = {}
        if query is None:
            query = question
        """Retrieve objects from this warehouse with semantic search"""
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/retrieve-with-naive/",
            headers=self._get_headers(),
            json={
                "query": query,
                "question": question,
                "n_objects": n_objects,
                "indexes": indexes,
                "included_tags": included_tags,
                "excluded_tags": excluded_tags,
                "reformulate_query": reformulate_query,
                "rerank": rerank,
            },
        )

        if response.status_code == 200:
            return response.json()["answer"]
        logger.error(f"Failed to generate answer with semantic search: {response.text}")
        return None

    def retrieve_with_full_text_search(
        self,
        query: str,
        indexes: list[str] = [],
        n_objects: int = 10,
        question: str = "",
        included_tags: dict | list[dict] | None = None,
        excluded_tags: dict | list[dict] | None = None,
        reformulate_query: bool = False,
        rerank: bool = False,
        included_objects: list[dict] | None = None,
        excluded_objects: list[dict] | None = None,
        included_attributes: list[dict] | None = None,
        excluded_attributes: list[dict] | None = None,
        selected_documents: list[dict] | None = None,
        **kwargs,
    ) -> list:
        """Retrieve objects from this warehouse with full-text search"""
        if "enrich_with_chunks" in kwargs:
            logger.warning("enrich_with_chunks is deprecated and has no effect.")
        if not indexes:
            indexes = ["chunks"]
        if included_tags is None:
            included_tags = {}
        if excluded_tags is None:
            excluded_tags = {}
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/retrieve-with-full-text-search/",
            headers=self._get_headers(),
            json={
                "query": query,
                "indexes": indexes,
                "n_objects": n_objects,
                "question": question,
                "included_tags": included_tags,
                "excluded_tags": excluded_tags,
                "reformulate_query": reformulate_query,
                "rerank": rerank,
                "included_objects": included_objects,
                "excluded_objects": excluded_objects,
                "included_attributes": included_attributes,
                "excluded_attributes": excluded_attributes,
                "selected_documents": selected_documents,
            },
        )

        if response.status_code == 200:
            return response.json()["retrieval_results"]
        logger.error(f"Failed to retrieve with full-text search: {response.text}")
        return []

    def generate_answer_with_full_text_search(
        self,
        question: str,
        query: str | None,
        indexes: list[str] = [],
        n_objects: int = 10,
        included_tags: dict | list[dict] | None = None,
        excluded_tags: dict | list[dict] | None = None,
        reformulate_query: bool = False,
        rerank: bool = False,
        **kwargs,
    ) -> str | None:
        """Retrieve objects from this warehouse with full-text search"""
        if "enrich_with_chunks" in kwargs:
            logger.warning("enrich_with_chunks is deprecated and has no effect.")
        if not indexes:
            indexes = ["chunks"]
        if included_tags is None:
            included_tags = {}
        if excluded_tags is None:
            excluded_tags = {}
        if query is None:
            query = question
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/retrieve-with-full-text-search/",
            headers=self._get_headers(),
            json={
                "query": query,
                "indexes": indexes,
                "n_objects": n_objects,
                "question": question,
                "included_tags": included_tags,
                "excluded_tags": excluded_tags,
                "reformulate_query": reformulate_query,
                "rerank": rerank,
            },
        )

        if response.status_code == 200:
            return response.json()["answer"]
        logger.error(f"Failed to generate answer with full-text search: {response.text}")
        return None

    def retrieve_with_hybrid_search(
        self,
        query: str,
        indexes: list[str] = [],
        n_objects: int = 10,
        question: str = "",
        rrf_k: int = 60,
        included_tags: dict | list[dict] | None = None,
        excluded_tags: dict | list[dict] | None = None,
        reformulate_query: bool = False,
        rerank: bool = False,
        included_objects: list[dict] | None = None,
        excluded_objects: list[dict] | None = None,
        included_attributes: list[dict] | None = None,
        excluded_attributes: list[dict] | None = None,
        selected_documents: list[dict] | None = None,
        **kwargs,
    ) -> list:
        """Retrieve objects from this warehouse with hybrid search using RRF algorithm."""
        if "enrich_with_chunks" in kwargs:
            logger.warning("enrich_with_chunks is deprecated and has no effect.")
        if not indexes:
            indexes = ["chunks"]
        if included_tags is None:
            included_tags = {}
        if excluded_tags is None:
            excluded_tags = {}
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/retrieve-with-hybrid-search/",
            headers=self._get_headers(),
            json={
                "query": query,
                "indexes": indexes,
                "n_objects": n_objects,
                "question": question,
                "rrf_k": rrf_k,
                "included_tags": included_tags,
                "excluded_tags": excluded_tags,
                "reformulate_query": reformulate_query,
                "rerank": rerank,
                "included_objects": included_objects,
                "excluded_objects": excluded_objects,
                "included_attributes": included_attributes,
                "excluded_attributes": excluded_attributes,
                "selected_documents": selected_documents,
            },
        )

        if response.status_code == 200:
            return response.json()["retrieval_results"]
        logger.error(f"Failed to retrieve with hybrid search: {response.text}")
        return []

    def generate_answer_with_hybrid_search(
        self,
        question: str,
        query: str | None,
        indexes: list[str] = [],
        n_objects: int = 10,
        rrf_k: int = 60,
        included_tags: dict | list[dict] | None = None,
        excluded_tags: dict | list[dict] | None = None,
        reformulate_query: bool = False,
        rerank: bool = False,
        **kwargs,
    ) -> str | None:
        """Retrieve objects from this warehouse with hybrid search using RRF algorithm."""
        if "enrich_with_chunks" in kwargs:
            logger.warning("enrich_with_chunks is deprecated and has no effect.")
        if not indexes:
            indexes = ["chunks"]
        if included_tags is None:
            included_tags = {}
        if excluded_tags is None:
            excluded_tags = {}
        if query is None:
            query = question
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/retrieve-with-hybrid-search/",
            headers=self._get_headers(),
            json={
                "query": query,
                "indexes": indexes,
                "n_objects": n_objects,
                "question": question,
                "rrf_k": rrf_k,
                "included_tags": included_tags,
                "excluded_tags": excluded_tags,
                "reformulate_query": reformulate_query,
                "rerank": rerank,
            },
        )

        if response.status_code == 200:
            return response.json()["answer"]
        logger.error(f"Failed to generate answer with hybrid search: {response.text}")
        return None

    def retrieve_with_cypher(self, cypher_query: str) -> list[dict]:
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/run-neo4j-query/",
            headers=self._get_headers(),
            json={"cypher_query": cypher_query},
        )
        return response.json()

    def retrieve_with_templated_query(
        self, query_template: str, template_variables: dict, **kwargs
    ) -> list[dict]:
        if "enrich_with_chunks" in kwargs:
            logger.warning("enrich_with_chunks is deprecated and has no effect.")
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/run-templated-neo4j-query/",
            headers=self._get_headers(),
            json={
                "query_template": query_template,
                "template_variables": template_variables,
            },
        )
        return response.json()

    def generate_cypher_query(self, instruction: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/generate-cypher-query/",
            headers=self._get_headers(),
            json={"user_instruction": instruction},
        )
        return response.json()

    # Task-related methods that return Task objects
    def list_tasks(self) -> List[Task]:
        """List all tasks in this warehouse as Task objects"""
        tasks_data = self._get_paginated_data(
            f"{self.base_url}/api/v1/projects/{self.id}/pipeline-runs/"
        )
        tasks = []
        for task_data in tasks_data:
            task = Task(
                base_url=self.base_url,
                token=self.token,
                warehouse_id=self.id,
                task_id=task_data.get("id"),
                name=task_data.get("name"),
                **{k: v for k, v in task_data.items() if k not in ["id", "name"]},
            )
            tasks.append(task)
        return tasks

    def get_task(self, task_id: str | int) -> Task:
        """Get a specific task by ID and return as Task object"""
        response = requests.get(
            f"{self.base_url}/api/v1/projects/{self.id}/pipeline-runs/{task_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        return Task(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            task_id=response.json().get("id"),
            name=response.json().get("name"),
            **{k: v for k, v in response.json().items() if k not in ["id", "name"]},
        )

    def run_object_extraction_task(
        self,
        object_extractor_id: str,
        mode: str = "recreate-all",
        compute_alerts: bool = False,
        llm_model: str | None = None,
        document_ids: List[str] | None = None,
        chunk_ids: List[str] | None = None,
        filtering_tag_extractor_id: str | None = None,
        filtering_key: str | None = None,
        filtering_value: str | None = None,
        version_id: str | None = None,
        chunks_table_version_id: str | None = None,
        **kwargs,
    ) -> Task:
        """Run an object extraction task and return as Task object"""
        if chunk_ids is None:
            chunk_ids = []
        if document_ids is None:
            document_ids = []
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/object-extractors/{object_extractor_id}/run-push/",
            headers=self._get_headers(),
            json={
                "mode": mode,
                "compute_alerts": compute_alerts,
                "llm_model": llm_model,
                "document_ids": document_ids,
                "chunk_ids": chunk_ids,
                "filtering_tag_extractor": filtering_tag_extractor_id,
                "filtering_key": filtering_key,
                "filtering_value": filtering_value,
                "version_id": version_id,
                "chunks_table_version_id": chunks_table_version_id,
                **kwargs,
            },
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        data = response.json()

        return Task(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            task_id=data.get("pipeline_run_id"),
            status="pending",
            **{k: v for k, v in data.items() if k not in ["pipeline_run_id"]},
        )

    def run_tag_extraction_task(
        self,
        tag_extractor_id: str,
        mode: str = "recreate-all",
        compute_alerts: bool = False,
        llm_model: str | None = None,
        document_ids: List[str] | None = None,
        chunk_ids: List[str] | None = None,
        version_id: str | None = None,
        chunks_table_version_id: str | None = None,
        **kwargs,
    ) -> Task:
        """Run a tag extraction task and return as Task object"""
        if chunk_ids is None:
            chunk_ids = []
        if document_ids is None:
            document_ids = []
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/tag-extractors/{tag_extractor_id}/run-push/",
            headers=self._get_headers(),
            json={
                "mode": mode,
                "compute_alerts": compute_alerts,
                "llm_model": llm_model,
                "document_ids": document_ids,
                "chunk_ids": chunk_ids,
                "version_id": version_id,
                "chunks_table_version_id": chunks_table_version_id,
                **kwargs,
            },
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        data = response.json()

        return Task(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            task_id=data.get("pipeline_run_id"),
            status="pending",
            **{k: v for k, v in data.items() if k not in ["pipeline_run_id"]},
        )

    def run_parsing_task(
        self,
        mode: str = "recreate-all",
        document_ids: List[str] | None = None,
        **kwargs,
    ) -> Task:
        """Run a parsing task and return as Task object"""
        if document_ids is None:
            document_ids = []
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/run-parsing/",
            headers=self._get_headers(),
            json={
                "mode": mode,
                "document_ids": document_ids,
                **kwargs,
            },
        )
        response.raise_for_status()
        data = response.json()

        return Task(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            task_id=data.get("pipeline_run_id"),
            status="pending",
            **{k: v for k, v in data.items() if k not in ["pipeline_run_id"]},
        )

    def list_object_extractors(self) -> list[dict]:
        return self._get_paginated_data(
            f"{self.base_url}/api/v1/projects/{self.id}/object-extractors/"
        )

    def create_object_extractor(
        self,
        brief: str,
        document_ids: list[str] | None = None,
        extractable_pydantic_class: str | None = None,
        extractable_object: BaseModel | None = None,
        extraction_prompt: str = None,
        llm_model: str = None,
        block_grouping_config: dict | None = None,
        filtered_on_block_types: bool = False,
        block_types: list[str] = [],
        name: str = None,
        compute_alerts: bool = True,
        blocks_table_version: str | None = None,
        add_anchoring_object: bool = True,
        **kwargs,
    ) -> dict:
        if document_ids is None:
            document_ids = []

        if extractable_object is not None:
            extractable_pydantic_class = model_to_code(extractable_object)

        # For backward compatibility with old API
        if kwargs.get("window_size_pages") is not None:
            block_grouping_config = {
                "type": "page_window",
                "window_size_pages": kwargs.get("window_size_pages"),
            }

        if block_grouping_config is None:
            block_grouping_config = {"type": "page_window", "window_size_pages": 5}

        # Create base payload
        payload = {
            "brief": brief,
            "document_ids": document_ids,
            "extractable_pydantic_class": extractable_pydantic_class,
            "extraction_prompt": extraction_prompt,
            "llm_model": llm_model,
            "name": name,
            "prompt_generation_status": "completed",
            "compute_alerts": compute_alerts,
            "block_grouping_config": block_grouping_config,
            "filtered_on_block_types": filtered_on_block_types,
            "block_types": block_types,
            "blocks_table_version": blocks_table_version,
            "add_anchoring_object": add_anchoring_object,
        }

        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/object-extractors/",
            headers=self._get_headers(),
            json=payload,
        )
        if response.status_code != 201:
            raise CRFAPIError(response.json(), response)
        self.create_object_extractor_tables_and_versions(response.json())
        return response.json()

    def create_object_extractor_without_tables_and_versions(
        self,
        brief: str,
        document_ids: list[str] | None = None,
        extractable_pydantic_class: str | None = None,
        extractable_object: BaseModel | None = None,
        extraction_prompt: str = None,
        llm_model: str = None,
        name: str = None,
        compute_alerts: bool = True,
        blocks_table_version: str | None = None,
        block_grouping_config: dict | None = None,
        filtered_on_block_types: bool = False,
        block_types: list[str] = [],
        **kwargs,
    ) -> dict:
        if document_ids is None:
            document_ids = []

        if extractable_object is not None:
            extractable_pydantic_class = model_to_code(extractable_object)

        # Default block_grouping_config if not provided
        if block_grouping_config is None:
            block_grouping_config = {"type": "page_window", "window_size_pages": 5}

        # Create payload with only non-None values
        payload = {
            "brief": brief,
            "document_ids": document_ids,
            "extractable_pydantic_class": extractable_pydantic_class,
            "extraction_prompt": extraction_prompt,
            "llm_model": llm_model,
            "name": name,
            "prompt_generation_status": "completed",
            "compute_alerts": compute_alerts,
            "block_grouping_config": block_grouping_config,
            "filtered_on_block_types": filtered_on_block_types,
            "block_types": block_types,
            "blocks_table_version": blocks_table_version,
        }

        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/object-extractors/",
            headers=self._get_headers(),
            json=payload,
        )
        if response.status_code != 201:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def update_object_extractor(
        self,
        object_extractor_id: str,
        brief: str = None,
        document_ids: list[str] = None,
        extractable_pydantic_class: str | None = None,
        extractable_object: BaseModel | None = None,
        extraction_prompt: str = None,
        llm_model: str = None,
        name: str = None,
        compute_alerts: bool = True,
        block_grouping_config: dict | None = None,
        filtered_on_block_types: bool | None = None,
        block_types: list[str] | None = None,
        set_latest_version_as_default: bool = True,
        blocks_table_version: str | None = None,
    ) -> dict:
        if extractable_object is not None:
            extractable_pydantic_class = model_to_code(extractable_object)

        fields = {
            "brief": brief,
            "document_ids": document_ids,
            "extractable_pydantic_class": extractable_pydantic_class,
            "extraction_prompt": extraction_prompt,
            "llm_model": llm_model,
            "name": name,
            "compute_alerts": compute_alerts,
            "block_grouping_config": block_grouping_config,
            "filtered_on_block_types": filtered_on_block_types,
            "block_types": block_types,
            "set_latest_as_default": set_latest_version_as_default,
            "blocks_table_version": blocks_table_version,
        }

        payload = {k: v for k, v in fields.items() if v is not None}

        response = requests.patch(
            f"{self.base_url}/api/v1/projects/{self.id}/object-extractors/{object_extractor_id}/",
            headers=self._get_headers(),
            json=payload,
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def delete_object_extractor(self, object_extractor_id: str) -> dict:
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/object-extractors/{object_extractor_id}/",
            headers=self._get_headers(),
        )
        return response.text

    def create_object_extractor_tables_and_versions(self, object_extractor_data: dict) -> dict:
        object_extractor_id = object_extractor_data.get("id")
        pydantic_class = object_extractor_data.get("extractable_pydantic_class")
        responses = []
        tables_and_schemas = [
            {
                "name": f"extracted_objects_extractor_{object_extractor_id}",
                "columns": [
                    {"name": "id", "type": "uuid"},
                    {"name": "json_object", "type": "json"},
                    {"name": "object_bbox", "type": "json"},
                    {"name": "document_id", "type": "uuid"},
                    {"name": "min_page", "type": "int"},
                    {"name": "max_page", "type": "int"},
                    {"name": "content", "type": "text"},
                    {"name": "blocks", "type": "json"},
                    {"name": "selected_blocks", "type": "json"},
                    {"name": "version", "type": "text"},
                ],
                "object_type": "object",
                "object_metadata": {
                    "object_pydantic_class": pydantic_class,
                    "object_name": object_extractor_data.get("name"),
                },
            },
            {
                "name": f"alerts_extractor_{object_extractor_id}",
                "columns": [
                    {"name": "id", "type": "uuid"},
                    {"name": "json_alert", "type": "json"},
                    {"name": "extracted_object_id", "type": "uuid"},
                    {"name": "document_id", "type": "uuid"},
                    {"name": "min_page", "type": "int"},
                    {"name": "max_page", "type": "int"},
                ],
                "object_type": "object_alert",
                "object_metadata": {},
            },
            {
                "name": f"pushed_objects_extractor_{object_extractor_id}",
                "columns": [
                    {"name": "status", "type": "text"},
                ],
                "object_type": "status",
                "object_metadata": {},
            },
        ]
        responses = []
        for table in tables_and_schemas:
            table = self.create_table(
                table["name"], table["columns"], table["object_type"], table["object_metadata"]
            )
            version = table.create_version()
            responses.append(version)
        return responses

    def run_object_extractor(
        self,
        object_extractor_id: str,
        document_ids: list[str] | None = None,
        version_id: str | None = None,
        blocks_table_version: str | None = None,
    ) -> Task:
        if document_ids is None:
            document_ids = []
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/object-extractors/{object_extractor_id}/run/",
            headers=self._get_headers(),
            json={
                "document_ids": document_ids,
                "version_id": version_id,
                "blocks_table_version": blocks_table_version,
            },
        )
        task = Task(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            task_id=response.json().get("pipeline_run_id"),
            status="pending",
            **{k: v for k, v in response.json().items() if k not in ["pipeline_run_id"]},
        )
        return task

    def list_tag_extractors(self) -> list[dict]:
        return self._get_paginated_data(
            f"{self.base_url}/api/v1/projects/{self.id}/tag-extractors/"
        )

    def create_tag_extractor(
        self,
        brief: str,
        chunk_ids: list[str] | None = None,
        document_ids: list[str] | None = None,
        tagging_tree: list[dict] | None = None,
        extraction_prompt: str = None,
        llm_model: str = None,
        name: str = None,
        compute_alerts: bool = True,
        enforce_single_tag: bool = False,
        chunks_table_version: str | None = None,
    ) -> dict:
        if chunk_ids is None:
            chunk_ids = []
        if document_ids is None:
            document_ids = []
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/tag-extractors/",
            headers=self._get_headers(),
            json={
                "brief": brief,
                "chunk_ids": chunk_ids,
                "document_ids": document_ids,
                "tagging_tree": tagging_tree,
                "extraction_prompt": extraction_prompt,
                "llm_model": llm_model,
                "name": name,
                "prompt_generation_status": "completed",
                "compute_alerts": compute_alerts,
                "enforce_single_tag": enforce_single_tag,
                "chunks_table_version": chunks_table_version,
            },
        )
        if response.status_code != 201:
            raise CRFAPIError(response.json(), response)
        self.create_tag_extractor_tables_and_versions(response.json())
        return response.json()

    def create_tag_extractor_without_tables_and_versions(
        self,
        brief: str,
        chunk_ids: list[str] | None = None,
        document_ids: list[str] | None = None,
        tagging_tree: list[dict] | None = None,
        extraction_prompt: str = None,
        llm_model: str = None,
        name: str = None,
        compute_alerts: bool = True,
        enforce_single_tag: bool = False,
        chunks_table_version: str | None = None,
    ) -> dict:
        if chunk_ids is None:
            chunk_ids = []
        if document_ids is None:
            document_ids = []
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/tag-extractors/",
            headers=self._get_headers(),
            json={
                "brief": brief,
                "chunk_ids": chunk_ids,
                "document_ids": document_ids,
                "tagging_tree": tagging_tree,
                "extraction_prompt": extraction_prompt,
                "llm_model": llm_model,
                "name": name,
                "prompt_generation_status": "completed",
                "compute_alerts": compute_alerts,
                "enforce_single_tag": enforce_single_tag,
                "chunks_table_version": chunks_table_version,
            },
        )
        if response.status_code != 201:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def update_tag_extractor(
        self,
        tag_extractor_id: str,
        brief: str = None,
        chunk_ids: list[str] = None,
        document_ids: list[str] = None,
        tagging_tree: list[dict] = None,
        extraction_prompt: str = None,
        llm_model: str = None,
        name: str = None,
        compute_alerts: bool = True,
        deployed_tagging_tree: list[dict] = None,
        deployed_extraction_prompt: str = None,
        deployed_llm_model: str = None,
        enforce_single_tag: bool = None,
        set_latest_version_as_default: bool = True,
        chunks_table_version: str | None = None,
    ) -> dict:
        fields = {
            "brief": brief,
            "chunk_ids": chunk_ids,
            "document_ids": document_ids,
            "tagging_tree": tagging_tree,
            "extraction_prompt": extraction_prompt,
            "llm_model": llm_model,
            "name": name,
            "compute_alerts": compute_alerts,
            "deployed_tagging_tree": deployed_tagging_tree,
            "deployed_extraction_prompt": deployed_extraction_prompt,
            "deployed_llm_model": deployed_llm_model,
            "enforce_single_tag": enforce_single_tag,
            "set_latest_as_default": set_latest_version_as_default,
            "chunks_table_version": chunks_table_version,
        }
        payload = {k: v for k, v in fields.items() if v is not None}
        if compute_alerts is not None:
            payload["compute_alerts"] = compute_alerts

        response = requests.patch(
            f"{self.base_url}/api/v1/projects/{self.id}/tag-extractors/{tag_extractor_id}/",
            headers=self._get_headers(),
            json=payload,
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def delete_tag_extractor(self, tag_extractor_id: str) -> str:
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/tag-extractors/{tag_extractor_id}/",
            headers=self._get_headers(),
        )
        return response.text

    def run_tag_extractor(
        self,
        tag_extractor_id: str,
        document_ids: list[str] | None = None,
        chunk_ids: list[str] | None = None,
        version_id: str | None = None,
        chunks_table_version_id: str | None = None,
    ) -> Task:
        if chunk_ids is None:
            chunk_ids = []
        if document_ids is None:
            document_ids = []
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/tag-extractors/{tag_extractor_id}/run/",
            headers=self._get_headers(),
            json={
                "document_ids": document_ids,
                "chunk_ids": chunk_ids,
                "version_id": version_id,
                "chunks_table_version_id": chunks_table_version_id,
            },
        )
        task = Task(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            task_id=response.json().get("pipeline_run_id"),
            status="pending",
            **{k: v for k, v in response.json().items() if k not in ["pipeline_run_id"]},
        )
        return task

    def create_tag_extractor_tables_and_versions(self, tag_extractor_data: dict) -> dict:
        tag_extractor_id = tag_extractor_data.get("id")
        tag_extractor_name = tag_extractor_data.get("name")
        tagging_tree = tag_extractor_data.get("tagging_tree")
        responses = []
        tables_and_schemas = [
            {
                "name": f"extracted_tags_extractor_{tag_extractor_id}",
                "columns": [
                    {"name": "chunk_id", "type": "uuid"},
                    {"name": "metadata", "type": "json"},
                    {"name": "id", "type": "text"},
                ],
                "object_type": "tag",
                "object_metadata": {
                    "tag_name": tag_extractor_name,
                    "tagging_tree": tagging_tree,
                },
            },
            {
                "name": f"alerts_tags_extractor_{tag_extractor_id}",
                "columns": [
                    {"name": "id", "type": "uuid"},
                    {"name": "chunk_id", "type": "uuid"},
                    {"name": "json_alert", "type": "json"},
                ],
                "object_type": "tag_alert",
                "object_metadata": {},
            },
        ]
        for table in tables_and_schemas:
            table = self.create_table(
                table["name"], table["columns"], table["object_type"], table["object_metadata"]
            )
            version = table.create_version()
            responses.append(version)
        return responses

    def list_chunk_extractors(self) -> list[dict]:
        return self._get_paginated_data(
            f"{self.base_url}/api/v1/projects/{self.id}/chunks-extractors/"
        )

    def create_chunk_extractor(
        self,
        name: str,
        document_ids: list[str],
        maximum_chunk_size: int = 10000,
        minimum_chunk_size: int = 200,
        page_as_separator: bool = False,
        title_section_separator_mode: str = "both",
        excluded_block_types: list[str] = [],
    ) -> dict:
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/chunks-extractors/",
            headers=self._get_headers(),
            json={
                "name": name,
                "document_ids": document_ids,
                "maximum_chunk_size": maximum_chunk_size,
                "minimum_chunk_size": minimum_chunk_size,
                "page_as_separator": page_as_separator,
                "title_section_separator_mode": title_section_separator_mode,
                "excluded_block_types": excluded_block_types,
            },
        )
        if response.status_code != 201:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def update_chunk_extractor(
        self,
        chunk_extractor_id: str,
        name: str = None,
        document_ids: list[str] = None,
        maximum_chunk_size: int = None,
        minimum_chunk_size: int = None,
        page_as_separator: bool = None,
        title_section_separator_mode: str = None,
        excluded_block_types: list[str] = None,
        set_latest_version_as_default: bool = True,
    ) -> dict:
        fields = {
            "name": name,
            "document_ids": document_ids,
            "maximum_chunk_size": maximum_chunk_size,
            "minimum_chunk_size": minimum_chunk_size,
            "page_as_separator": page_as_separator,
            "title_section_separator_mode": title_section_separator_mode,
            "excluded_block_types": excluded_block_types,
            "set_latest_as_default": set_latest_version_as_default,
        }
        payload = {k: v for k, v in fields.items() if v is not None}
        response = requests.patch(
            f"{self.base_url}/api/v1/projects/{self.id}/chunks-extractors/{chunk_extractor_id}/",
            headers=self._get_headers(),
            json=payload,
        )
        return response.json()

    def delete_chunk_extractor(self, chunk_extractor_id: str) -> str:
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/chunks-extractors/{chunk_extractor_id}/",
            headers=self._get_headers(),
        )
        return response.text

    def run_chunk_extractor(
        self,
        chunk_extractor_id: str,
        document_ids: list[str] | None = None,
        version_id: str | None = None,
    ) -> Task:
        if document_ids is None:
            document_ids = []
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/chunks-extractors/{chunk_extractor_id}/run/",
            headers=self._get_headers(),
            json={
                "document_ids": document_ids,
                "version_id": version_id,
            },
        )
        task = Task(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            task_id=response.json().get("pipeline_run_id"),
            status="pending",
            **{k: v for k, v in response.json().items() if k not in ["pipeline_run_id"]},
        )
        return task

    def run_sync_to_retrieval(self, push_to_retrieval_json: dict | None = None) -> Task:
        if not push_to_retrieval_json:
            push_to_retrieval_response = requests.post(
                f"{self.base_url}/api/v1/projects/{self.id}/generate-sync-to-graph-steps/",
                headers=self._get_headers(),
                json={},
            )
            push_to_retrieval_json = push_to_retrieval_response.json()

        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/run-sync-to-graph-steps/",
            headers=self._get_headers(),
            json=push_to_retrieval_json,
        )
        task = Task(
            base_url=self.base_url,
            token=self.token,
            warehouse_id=self.id,
            task_id=response.json().get("pipeline_run_id"),
            status="pending",
            **{k: v for k, v in response.json().items() if k not in ["pipeline_run_id"]},
        )
        return task

    def export_warehouse(self, output_path: str | None = None) -> str:
        """
        Export all relevant data for this warehouse and create a zip file.

        Args:
            output_path: Optional path for the output zip file. If None, creates a file
                        named "warehouse_export_{warehouse_id}.zip" in the current directory.

        Returns:
            str: Path to the created zip file

        Raises:
            WarehouseExportError: If any export operation fails

        """
        export_ops = WarehouseExportOperations(self)
        return export_ops.export_warehouse(output_path)

    def sync_to_retrieval(self) -> None:
        # First we sync the chunks table
        chunks_table = self.get_table("chunks")
        logger.info(f"Pushing {chunks_table.name} to retrieval")
        sync_task = chunks_table.push_to_retrieval()
        task_result = sync_task.wait_for_completion()
        if task_result.get("status") != "completed":
            logger.error(f"Failed to push {chunks_table.name} to retrieval")
            return

        warehouse_tables = self.list_tables()
        for table in warehouse_tables:
            versions = table.list_versions()
            has_deployed_version = False
            for version in versions:
                if version.get("deployed"):
                    has_deployed_version = True
                    break
            if not has_deployed_version:
                logger.warning(f"No deployed version found for table {table.name}, skipping")
                continue
            if table.object_type in ["object", "tag"]:
                logger.info(f"Pushing {table.name} to retrieval")
                sync_task = table.push_to_retrieval()
                task_result = sync_task.wait_for_completion()
                if task_result.get("status") != "completed":
                    logger.error(f"Failed to push {table.name} to retrieval")
        return

    def classify_feedbacks(
        self,
        feedback_list: List[Feedback],
        llm_client,
        system_prompt: str,
        model: str = "gpt-4o-mini",
    ) -> List[FeedbackClassificationResponse]:
        def classify_single_feedback(feedback: Feedback) -> FeedbackClassificationResponse | None:
            user_prompt = f"Feedback: {feedback.feedback}"
            try:
                response = llm_client.responses.parse(
                    model=model,
                    input=[
                        {"role": "system", "content": system_prompt.strip()},
                        {"role": "user", "content": user_prompt.strip()},
                    ],
                    text_format=FeedbackClassification,
                )
                parsed_response = response.output_parsed
                return FeedbackClassificationResponse(
                    feedback=feedback, feedback_classification=parsed_response
                )
            except Exception:
                logger.exception(f"Failed to classify feedback: {feedback.feedback}.")
                return None

        feedback_classifications: List[FeedbackClassificationResponse] = []

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {
                executor.submit(classify_single_feedback, feedback): feedback
                for feedback in feedback_list
            }
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    feedback_classifications.append(result)

        return feedback_classifications

    def get_conversation(self, conversation_id: str) -> dict:
        """Gets a conversation by ID."""
        url = (
            f"{self.base_url}/api/v1/projects/{self.id}/playground-conversations/{conversation_id}/"
        )
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def create_ground_truths_from_feedbacks(
        self,
        feedbacks: List[Feedback],
        llm_client,
        system_prompt: str,
        model: str = "gpt-4o-mini",
    ) -> List[GroundTruth]:
        def process_single_feedback(feedback_item: Feedback) -> GroundTruth | None:
            feedback = feedback_item.feedback

            feedback_content = feedback.feedback

            feedback_context = feedback.context
            feedback_user_message = feedback_context.get("user_message", "")

            feedback_conversation_id = feedback_context.get("conversation_id", "")
            try:
                conversation = self.get_conversation(feedback_conversation_id)
            except Exception:
                logger.exception(f"Failed to get conversation for feedback (ID: {feedback.id}).")
                return None
            chat_history = conversation["chat_history"]

            # sending prompt instructions and feedback content to LLM
            user_prompt = (
                f"Feedback content: {feedback_content} \n\n "
                f"User's message related to its feedback: {feedback_user_message} \n\n "
                f"Chat history: {chat_history}"
            )
            try:
                response = llm_client.responses.parse(
                    model=model,
                    input=[
                        {"role": "system", "content": system_prompt.strip()},
                        {"role": "user", "content": user_prompt.strip()},
                    ],
                    text_format=GroundTruthsFromFeedbacks,
                )
                parsed_response = response.output_parsed

                return GroundTruth(
                    source_feedback_id=feedback.id,
                    query=parsed_response.question,
                    answer=parsed_response.groundtruth,
                    additional_notes=parsed_response.additional_notes,
                )
            except Exception:
                logger.exception(
                    f"Failed to create ground truth from feedback (ID: {feedback.id})."
                )
                return None

        ground_truths: List[GroundTruth] = []

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {
                executor.submit(process_single_feedback, feedback): feedback
                for feedback in feedbacks
            }
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    ground_truths.append(result)

        return ground_truths

    def list_feedbacks(self, status: str = "to_review") -> List[Feedback]:
        """Lists all feedbacks for the warehouse."""
        url = f"{self.base_url}/api/v1/projects/{self.id}/feedbacks/"
        if status:
            url += f"?status={status}"
        feedbacks = self._get_paginated_data(url)
        return [Feedback(**feedback) for feedback in feedbacks]

    def update_feedback(self, feedback_id: str, status: str) -> dict:
        """Updates a feedback by ID."""
        payload = {"status": status}
        response = requests.patch(
            f"{self.base_url}/api/v1/projects/{self.id}/feedbacks/{feedback_id}/",
            headers=self._get_headers(),
            json=payload,
        )
        if response.status_code != 200:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def upload_temp_dataset(
        self,
        data: dict | list | str | bytes | Path,
        filename: str = "data.json",
        content_type: str = "application/json",
    ) -> dict:
        """
        Upload data to a new temp dataset.

        Args:
            data: Data to upload. Can be:
                - dict/list: Will be JSON serialized
                - str: Raw string content
                - bytes: Raw bytes content
                - Path: Path to a file to upload
            filename: Name for the uploaded file (default: "data.json").
            content_type: MIME type of the content (default: "application/json").

        Returns:
            Dict with temp_dataset info including 'id'.

        Example:
            >>> temp_dataset = warehouse.upload_temp_dataset(
            ...     data={"rows": [{"id": 1, "name": "test"}]}, filename="export.json"
            ... )
            >>> print(temp_dataset["id"])

        """
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/temp-datasets/generate-presigned-upload-url/",
            headers=self._get_headers(),
            json={"filename": filename, "content_type": content_type},
        )
        response.raise_for_status()
        presigned_data = response.json()

        temp_dataset_id = presigned_data["temp_dataset_id"]
        upload_url = presigned_data["upload_url"]
        file_key = presigned_data["file_key"]
        additional_fields = presigned_data.get("additional_fields", {})

        if isinstance(data, Path):
            content = data.read_bytes()
        elif isinstance(data, (dict, list)):
            content = json.dumps(data, default=str).encode("utf-8")
        elif isinstance(data, str):
            content = data.encode("utf-8")
        else:
            content = data

        method = additional_fields.get("method", "PUT")
        if method == "POST":
            form_fields = additional_fields.get("form_fields", {})
            files = {"file": (filename, content, content_type)}
            upload_response = requests.post(upload_url, data=form_fields, files=files)
        else:
            headers = additional_fields.get("headers", {"Content-Type": content_type})
            upload_response = requests.put(upload_url, data=content, headers=headers)

        upload_response.raise_for_status()

        confirm_response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/temp-datasets/confirm-upload/",
            headers=self._get_headers(),
            json={"temp_dataset_id": temp_dataset_id, "file_key": file_key},
        )
        confirm_response.raise_for_status()

        return confirm_response.json()["temp_dataset"]

    def get_temp_dataset(self, temp_dataset_id: str) -> dict:
        """Get temp dataset details."""
        response = requests.get(
            f"{self.base_url}/api/v1/projects/{self.id}/temp-datasets/{temp_dataset_id}/",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def list_temp_datasets(self) -> list[dict]:
        """List all temp datasets in the project."""
        return self._get_paginated_data(f"{self.base_url}/api/v1/projects/{self.id}/temp-datasets/")

    def delete_temp_dataset(self, temp_dataset_id: str) -> None:
        """Delete a temp dataset."""
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/temp-datasets/{temp_dataset_id}/",
            headers=self._get_headers(),
        )
        response.raise_for_status()

    def poll_import_export_operation(
        self,
        operation_id: str,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> dict:
        """
        Poll import/export operation status until completion or timeout.

        Args:
            operation_id: ID of the operation to poll.
            poll_interval: Seconds between status checks (default: 2.0).
            timeout: Maximum seconds to wait (default: 300.0).

        Returns:
            Final operation dict.

        Raises:
            TimeoutError: If operation doesn't complete within timeout.
            CRFAPIError: If operation fails.

        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Operation {operation_id} did not complete within {timeout}s")

            response = requests.get(
                f"{self.base_url}/api/v1/projects/{self.id}/import-export-operations/{operation_id}/",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            operation = response.json()

            if operation["status"] == "completed":
                return operation
            if operation["status"] == "failed":
                raise CRFAPIError(
                    {"error": operation.get("error_message", "Operation failed")},
                    response,
                )

            time.sleep(poll_interval)

    def list_users(self) -> list[dict]:
        """List all users in the project."""
        return self._get_paginated_data(f"{self.base_url}/api/v1/projects/{self.id}/users/")

    def remove_user(self, user_id: str) -> None:
        """Remove a user from the project."""
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/users/{user_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 204:
            raise CRFAPIError(response.json(), response)

    def invite_user(self, email: str, permissions: list[str] = ["CAN_VIEW_DATA"]) -> dict:
        """
        Add a user to the warehouse

        possibles permissions: ["CAN_VIEW_DATA", "CAN_RUN_TASKS", "CAN_PERFORM_ADMIN_ACTIONS"]
        """
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.id}/invites/invite/",
            headers=self._get_headers(),
            json={"email": email, "permissions": permissions},
        )
        if response.status_code != 201:
            raise CRFAPIError(response.json(), response)
        return response.json()

    def list_invites(self, status: str = "pending") -> list[dict]:
        """List all invites in the project."""
        return self._get_paginated_data(
            f"{self.base_url}/api/v1/projects/{self.id}/invites/?status={status}"
        )

    def delete_invite(self, invite_id: str) -> None:
        """Delete an invite from the project."""
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.id}/invites/{invite_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 204:
            raise CRFAPIError(response.json(), response)
