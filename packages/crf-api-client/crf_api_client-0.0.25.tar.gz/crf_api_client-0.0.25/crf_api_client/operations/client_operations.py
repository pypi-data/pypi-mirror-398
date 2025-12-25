# ruff: noqa: C901, TID252, PLR0912, PLR0915, G004, E501

import json
import logging
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path

from tqdm import tqdm

from ..table import Table
from ..warehouse import Warehouse

logger = logging.getLogger(__name__)


class WarehouseImportError(Exception):
    """Custom exception for critical warehouse import errors that should stop the import"""


class TableImportError(Exception):
    """Custom exception for non-critical table import errors that allow import to continue"""


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
        WarehouseImportError,
    ) as e:
        error_message = f"Failed to {operation_name}: {e!s}"
        raise error_type(error_message) from e


class ClientImportOperations:
    """Contains all client import-related operations."""

    def __init__(self, client):
        """
        Initialize with a client instance.

        Args:
            client: The CRFAPIClient instance to operate on

        """
        self.client = client

    def _validate_warehouse_data(self, warehouse_data: dict) -> None:
        """Validate that warehouse_data contains required keys."""
        required_keys = ["project", "documents"]
        missing_keys = [key for key in required_keys if key not in warehouse_data]
        if missing_keys:
            error_message = f"Missing required data keys: {', '.join(missing_keys)}"
            raise WarehouseImportError(error_message)

    def _create_warehouse_from_data(self, warehouse_data: dict) -> tuple[Warehouse, str]:
        """Create a new warehouse from the project data."""
        project_data = warehouse_data["project"]
        warehouse = self.client.create_warehouse(
            name=project_data["name"],
            brief=project_data["business_brief"],
            default_llm_model=project_data.get("default_llm_model", "gpt-4o"),
        )
        additional_setting_keys = [
            "reducto_parsing_options",
            "push_to_graph_options",
            "default_chunking_maximum_chunk_size",
            "default_chunking_minimum_chunk_size",
            "default_chunking_page_as_separator",
            "default_chunking_title_section_separator_mode",
            "default_chunking_excluded_block_types",
            "max_fetchable_objects",
            "all_queries",
            "reasoning_workflows",
            "ontology",
        ]
        additional_settings = {
            key: project_data[key] for key in additional_setting_keys if key in project_data
        }
        if additional_settings:
            with api_operation(WarehouseImportError, "update warehouse settings"):
                warehouse.update_settings(**additional_settings)
        return warehouse, warehouse.id

    def _upload_documents_and_map_ids(
        self,
        warehouse: Warehouse,
        warehouse_data: dict,
        document_paths: list[str],
        progress_bar: tqdm = None,
    ) -> dict:
        """Upload documents and create mapping from old to new document IDs."""
        if progress_bar:
            progress_bar.set_description("Uploading documents to warehouse")
        warehouse.upload_documents(document_paths, skip_parsing=True)

        if progress_bar:
            progress_bar.set_description("Mapping document IDs")

        uploaded_documents = warehouse.list_documents()

        document_ids_old_to_new = {}
        for document in warehouse_data["documents"]:
            matching_docs = [d for d in uploaded_documents if d["name"] == document["name"]]
            if matching_docs:
                document_ids_old_to_new[document["id"]] = matching_docs[0]["id"]
            else:
                message = f"Could not find uploaded document with name: {document['name']}"
                logger.warning(message)
                continue
        if progress_bar:
            progress_bar.set_description("Document upload completed")

        return document_ids_old_to_new

    def _process_tools_data(
        self, warehouse: Warehouse, tools_data: list, document_ids_old_to_new: dict
    ) -> dict:
        """Process and import tools."""
        default_tools = warehouse.list_tools()
        tools_id_maps = {}
        for tool_data in tools_data:
            message = f"Creating tool: {tool_data.get('name')}"
            logger.info(message)
            # Handle the default tools (readonly tools)
            # If the tool is readonly, then it's already been created with the project
            existing_tool = None
            if tool_data.get("readonly"):
                existing_tool = [
                    t
                    for t in default_tools
                    if t.get("name") == tool_data.get("name") and t.get("readonly") is True
                ]
                existing_tool = existing_tool[0] if existing_tool else None
            if existing_tool:
                message = f"Process default tool with name {tool_data.get('name')}"
                logger.info(message)
                tools_id_maps[tool_data.get("id")] = existing_tool.get("id")
                continue
            old_id = tool_data.get("id")
            tool_data["project"] = warehouse.id
            del tool_data["id"]
            if tool_data.get("document_mode") == "select_documents":
                tool_data["document_parameters"] = [
                    {"id": document_ids_old_to_new[doc["id"]], "name": doc["name"]}
                    for doc in tool_data.get("document_parameters", [])
                    if doc["id"] in document_ids_old_to_new
                ]
            res = warehouse.create_tool(tool_data)
            message = f"Successfully created tool: {tool_data.get('name')}. ID: {res.get('id')}"
            logger.info(message)
            new_id = res.get("id")
            tools_id_maps[old_id] = new_id
        return tools_id_maps

    def _process_agent_settings_data_with_mapping(
        self, warehouse: Warehouse, agent_settings_data: list, tools_id_maps: dict
    ) -> dict:
        """Process and import agent settings, returning ID mapping."""
        agent_settings_id_maps = {}
        default_agent_settings = warehouse.list_agent_settings()
        for agent_setting_data in agent_settings_data:
            message = f"Creating agent setting: {agent_setting_data.get('name')}"
            logger.info(message)
            old_id = agent_setting_data.get("id")
            # Handle the default agent settings (readonly agent settings)
            # If the agent setting is readonly, then it's already been created with the project
            existing_agent_settings = None
            if agent_setting_data.get("readonly"):
                existing_agent_settings = [
                    a
                    for a in default_agent_settings
                    if a.get("name") == agent_setting_data.get("name")
                ]
                existing_agent_settings = (
                    existing_agent_settings[0] if existing_agent_settings else None
                )
            if existing_agent_settings:
                message = (
                    f"Process default agent setting with name {agent_setting_data.get('name')}"
                )
                logger.info(message)
                agent_settings_id_maps[old_id] = existing_agent_settings.get("id")
                continue
            agent_setting_data_copy = agent_setting_data.copy()
            agent_setting_data_copy["project"] = warehouse.id
            del agent_setting_data_copy["id"]
            # There is a "id" key in the knowledge_graph_parameters, we need to remove it. It is not
            # used in the backend
            agent_setting_data_copy["knowledge_graph_parameters"] = [
                {"name": param["name"]}
                for param in agent_setting_data_copy.get("knowledge_graph_parameters", [])
            ]
            agent_setting_data_copy["tools"] = [
                tools_id_maps[tool_id]
                for tool_id in agent_setting_data_copy.get("tools", [])
                if tool_id in tools_id_maps
            ]
            res = warehouse.create_agent_settings(agent_setting_data_copy)
            message = (
                f"Successfully created agent setting: {agent_setting_data.get('name')}."
                f"ID: {res.get('id')}"
            )
            logger.info(message)
            agent_settings_id_maps[old_id] = res.get("id")
        return agent_settings_id_maps

    def _process_local_documents_data(
        self,
        warehouse: Warehouse,
        warehouse_data: dict,
        agent_settings_id_maps: dict,
        temp_path: Path,
        progress_bar: tqdm = None,
    ) -> None:
        """Process and import local documents."""
        if "local_documents" not in warehouse_data or not warehouse_data["local_documents"]:
            return

        local_documents_data = warehouse_data["local_documents"]

        # Group local documents by type
        agent_settings_docs = [
            doc for doc in local_documents_data if doc.get("type") == "agent_settings"
        ]
        conversation_docs = [
            doc for doc in local_documents_data if doc.get("type") == "conversation"
        ]

        # Process agent_settings local documents
        if agent_settings_docs:
            if progress_bar:
                progress_bar.set_description("Uploading local documents for agent settings")
            # Group by agent_settings_id for batch upload
            docs_by_agent_settings = {}
            for doc in agent_settings_docs:
                old_agent_settings_id = doc.get("agent_settings")
                if not old_agent_settings_id:
                    logger.warning(
                        f"Local document {doc.get('id')} has no agent_settings, skipping"
                    )
                    continue
                new_agent_settings_id = agent_settings_id_maps.get(old_agent_settings_id)
                if not new_agent_settings_id:
                    logger.warning(
                        f"Could not map agent_settings_id {old_agent_settings_id} for local document {doc.get('id')}, skipping"
                    )
                    continue
                if new_agent_settings_id not in docs_by_agent_settings:
                    docs_by_agent_settings[new_agent_settings_id] = []
                docs_by_agent_settings[new_agent_settings_id].append(doc)

            # Upload files for each agent_settings
            for new_agent_settings_id, docs in docs_by_agent_settings.items():
                file_paths = []
                for doc in docs:
                    doc_id = doc.get("id")
                    doc_name = doc.get("name")
                    local_doc_path = temp_path / "local_documents" / doc_id / doc_name
                    if not local_doc_path.exists():
                        logger.warning(f"Local document file not found: {local_doc_path}, skipping")
                        continue
                    file_paths.append(str(local_doc_path))

                if file_paths:
                    try:
                        warehouse.upload_local_documents_bulk(
                            file_paths=file_paths,
                            doc_type="agent_settings",
                            agent_settings_id=new_agent_settings_id,
                            skip_processing=True,
                        )
                        message = (
                            f"Successfully uploaded {len(file_paths)} local documents "
                            f"for agent settings {new_agent_settings_id}"
                        )
                        logger.info(message)
                    except Exception:
                        logger.exception(
                            f"Failed to upload local documents for agent settings {new_agent_settings_id}"
                        )

        # Process conversation local documents
        # Note: Conversations are not currently imported, so we skip these
        if conversation_docs:
            logger.warning(
                f"Found {len(conversation_docs)} local documents for conversations, "
                "but conversations are not imported. Skipping."
            )

    def _process_ground_truths_data(self, warehouse: Warehouse, ground_truths_data: list) -> None:
        """Process and import ground truths."""
        for ground_truth_data in ground_truths_data:
            message = f"Creating ground truth: {ground_truth_data.get('query')[:50]}..."
            logger.info(message)
            # Create ground truth with only the fields that can be set during creation
            # Note: source_feedback_id is not included since feedbacks are not imported
            res = warehouse.create_ground_truth(
                query=ground_truth_data.get("query"),
                answer=ground_truth_data.get("answer"),
                additional_notes=ground_truth_data.get("additional_notes"),
            )
            message = f"Successfully created ground truth. ID: {res.get('id')}"
            logger.info(message)

    def _process_object_extractors_data(
        self, warehouse: Warehouse, object_extractors_data: list
    ) -> None:
        """Process and import object extractors."""
        obj_extractor_id_maps = {}
        for extractor_data in object_extractors_data:
            message = f"Creating object extractor: {extractor_data.get('name')}"
            logger.info(message)
            old_id = extractor_data.get("id")
            res = warehouse.create_object_extractor_without_tables_and_versions(
                brief=extractor_data.get("brief"),
                document_ids=extractor_data.get("document_ids", []),
                extractable_pydantic_class=extractor_data.get("extractable_pydantic_class"),
                extraction_prompt=extractor_data.get("extraction_prompt"),
                llm_model=extractor_data.get("llm_model"),
                name=extractor_data.get("name"),
                compute_alerts=extractor_data.get("compute_alerts", True),
                block_grouping_config=extractor_data.get("block_grouping_config", {}),
                filtered_on_block_types=extractor_data.get("filtered_on_block_types", False),
                block_types=extractor_data.get("block_types", []),
            )
            message = (
                f"Successfully created object extractor: {extractor_data.get('name')}.",
                f"ID: {res.get('id')}",
            )
            logger.info(message)
            new_id = res.get("id")
            obj_extractor_id_maps[old_id] = new_id
        return obj_extractor_id_maps

    def _process_tag_extractors_data(self, warehouse: Warehouse, tag_extractors_data: list) -> None:
        """Process and import tag extractors."""
        tag_extractor_id_maps = {}
        for extractor_data in tag_extractors_data:
            message = f"Creating tag extractor: {extractor_data.get('name')}"
            logger.info(message)
            old_id = extractor_data.get("id")
            res = warehouse.create_tag_extractor_without_tables_and_versions(
                brief=extractor_data.get("brief"),
                chunk_ids=extractor_data.get("chunk_ids", []),
                document_ids=extractor_data.get("document_ids", []),
                tagging_tree=extractor_data.get("tagging_tree"),
                extraction_prompt=extractor_data.get("extraction_prompt"),
                llm_model=extractor_data.get("llm_model"),
                name=extractor_data.get("name"),
                compute_alerts=extractor_data.get("compute_alerts"),
                enforce_single_tag=extractor_data.get("enforce_single_tag", False),
            )
            message = (
                f"Successfully created tag extractor: {extractor_data.get('name')}.",
                f"ID: {res.get('id')}",
            )
            logger.info(message)
            new_id = res.get("id")
            tag_extractor_id_maps[old_id] = new_id
        return tag_extractor_id_maps

    def _process_chunks_extractors_data(
        self, warehouse: Warehouse, chunks_extractors_data: list
    ) -> None:
        """Process and import chunks extractors."""
        chunk_extractor_id_maps = {}
        # First we remove the default chunk extractor
        try:
            existing_chunks_extractors = warehouse.list_chunk_extractors()
            warehouse.delete_chunk_extractor(existing_chunks_extractors[0]["id"])
        except Exception:
            logger.exception("Failed to delete default chunk extractor")
        for extractor_data in chunks_extractors_data:
            message = f"Creating chunk extractor: {extractor_data.get('name')}"
            logger.info(message)
            old_id = extractor_data.get("id")
            res = warehouse.create_chunk_extractor(
                name=extractor_data.get("name"),
                document_ids=extractor_data.get("document_ids", []),
                maximum_chunk_size=extractor_data.get("maximum_chunk_size"),
                minimum_chunk_size=extractor_data.get("minimum_chunk_size"),
                page_as_separator=extractor_data.get("page_as_separator"),
                title_section_separator_mode=extractor_data.get("title_section_separator_mode"),
                excluded_block_types=extractor_data.get("excluded_block_types", []),
            )
            message = (
                f"Successfully created chunk extractor: {extractor_data.get('name')}.",
                f"ID: {res.get('id')}",
            )
            logger.info(message)
            new_id = res.get("id")
            chunk_extractor_id_maps[old_id] = new_id
        return chunk_extractor_id_maps

    def _import_tables(
        self,
        warehouse: Warehouse,
        warehouse_data: dict,
        document_ids_old_to_new: dict,
        obj_extractor_id_maps: dict,
        tag_extractor_id_maps: dict,
        chunk_extractor_id_maps: dict,
        temp_path: Path,
        progress_bar: tqdm,
    ) -> None:
        """Import all tables from warehouse data."""
        all_extractor_id_maps = {
            **obj_extractor_id_maps,
            **tag_extractor_id_maps,
            **chunk_extractor_id_maps,
        }
        versions_mapping = {}
        for table_data in warehouse_data["tables"].values():
            table_name = table_data["name"]
            if progress_bar:
                progress_bar.set_description(f"Processing table: {table_name}")

            try:
                table_name = self.get_new_table_name(table_name, all_extractor_id_maps)
            except TableImportError:
                logger.exception(
                    f"Failed to get new table name for {table_name}. Continuing with original table name."
                )
            try:
                created_table = warehouse.get_table(table_name)
            except ValueError:
                created_table = warehouse.create_table(
                    table_name=table_name,
                    columns=table_data["columns"],
                    object_type=table_data["object_type"],
                    object_metadata=table_data["object_metadata"],
                )
            versions = table_data["versions"]
            versions.sort(key=lambda x: x["version"])
            for i, version in enumerate(versions):
                if progress_bar:
                    progress_bar.set_description(
                        f"Processing {table_name} version {i + 1}/{len(versions)}"
                    )
                created_version = created_table.create_version()
                if version.get("deployed") is True:
                    created_table.set_deployed_version(created_version["id"])
                versions_mapping[version["id"]] = created_version["id"]
                self.write_table_data_with_version_mapping(
                    created_table,
                    table_data["id"],
                    created_version["id"],
                    version["id"],
                    document_ids_old_to_new,
                    temp_path,
                )
            if progress_bar:
                progress_bar.update(1)

        # Finally we update the dependencies
        for table_data in warehouse_data["tables"].values():
            table_name = table_data["name"]
            try:
                table_name = self.get_new_table_name(table_name, all_extractor_id_maps)
            except TableImportError:
                logger.exception(
                    f"Failed to get new table name for {table_name}, skipping dependency update"
                )
                continue
            try:
                table = warehouse.get_table(table_name)
            except ValueError:
                logger.warning(f"Table {table_name} not found, skipping dependency update")
                continue
            for version in table_data["versions"]:
                old_version_id = version["id"]
                if old_version_id not in versions_mapping:
                    logger.warning(
                        f"Version {old_version_id} not found in versions_mapping, skipping dependency update"
                    )
                    continue
                old_dependencies = version.get("table_version_dependencies", {})
                new_dependencies = {
                    k: versions_mapping[v]
                    for k, v in old_dependencies.items()
                    if v in versions_mapping
                }
                table.update_table_version_dependencies(
                    new_dependencies, versions_mapping[old_version_id]
                )
        return versions_mapping

    def get_new_table_name(self, table_name: str, all_extractor_id_maps: dict) -> str:
        extractor_table_prefixes = [
            "extracted_objects_extractor_",
            "extracted_chunks_extractor_",
            "extracted_tags_extractor_",
        ]
        if not any(table_name.startswith(prefix) for prefix in extractor_table_prefixes):
            return table_name
        try:
            old_extractor_id = table_name.split("_")[-1]
            new_extractor_id = all_extractor_id_maps[old_extractor_id]
            return table_name.rsplit(old_extractor_id, 1)[0] + new_extractor_id
        except KeyError as e:
            error_message = f"Failed to get new table name for {table_name}"
            logger.exception(error_message)
            raise TableImportError(error_message) from e

    def write_table_data_with_version_mapping(
        self,
        table: Table,
        original_table_id: str,
        new_version_id: str,
        old_version_id: str,
        document_ids_old_to_new: dict,
        temp_path: Path,
    ) -> None:
        """Write table data with version mapping."""
        try:
            data = json.load(open(temp_path / "tables_data" / original_table_id / old_version_id))
        except FileNotFoundError:
            logger.warning(f"Table data not found for {original_table_id} version {old_version_id}")
            return
        for row in data:
            if "document_id" in row and row["document_id"] in document_ids_old_to_new:
                row["document_id"] = document_ids_old_to_new[row["document_id"]]
        table.write_data(data, table_version_id=new_version_id, override=True)
        message = f"Successfully wrote data to {table.name} version {new_version_id}"
        logger.info(message)

    def _update_objects_extractors_dependencies(
        self,
        warehouse: Warehouse,
        object_extractors_data: list,
        tables_versions_mapping: dict,
        obj_extractor_id_maps: dict,
        document_ids_old_to_new,
    ) -> None:
        no_doc_id_uuid = "00000000-0000-0000-0000-000000000000"
        reversed_obj_extractor_id_maps = {v: k for k, v in obj_extractor_id_maps.items()}
        for object_extractor in warehouse.list_object_extractors():
            document_ids = object_extractor.get("document_ids", [])
            new_document_ids = [
                document_ids_old_to_new.get(doc_id, no_doc_id_uuid) for doc_id in document_ids
            ]
            old_id = reversed_obj_extractor_id_maps[object_extractor["id"]]
            extractor_data = next(filter(lambda x: x["id"] == old_id, object_extractors_data))
            old_blocks_table_version = extractor_data.get("blocks_table_version")
            if old_blocks_table_version is None:
                continue
            new_blocks_table_version = tables_versions_mapping[old_blocks_table_version]
            warehouse.update_object_extractor(
                object_extractor["id"],
                blocks_table_version=new_blocks_table_version,
                document_ids=new_document_ids,
            )

    def _update_tag_extractors_dependencies(
        self,
        warehouse: Warehouse,
        tag_extractors_data: list,
        tables_versions_mapping: dict,
        tag_extractor_id_maps: dict,
        document_ids_old_to_new: dict,
    ) -> None:
        reversed_tag_extractor_id_maps = {v: k for k, v in tag_extractor_id_maps.items()}
        for tag_extractor in warehouse.list_tag_extractors():
            document_ids = tag_extractor.get("document_ids", [])
            new_document_ids = [document_ids_old_to_new[doc_id] for doc_id in document_ids]
            old_id = reversed_tag_extractor_id_maps[tag_extractor["id"]]
            extractor_data = next(filter(lambda x: x["id"] == old_id, tag_extractors_data))
            old_chunks_table_version = extractor_data.get("chunks_table_version")
            if old_chunks_table_version is None:
                continue
            new_chunks_table_version = tables_versions_mapping[old_chunks_table_version]
            warehouse.update_tag_extractor(
                tag_extractor["id"],
                chunks_table_version=new_chunks_table_version,
                document_ids=new_document_ids,
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
        error_type = WarehouseImportError
        warehouse_id = None

        with tqdm(total=10, desc="Importing Warehouse", unit="step") as pbar:
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    pbar.set_description("Extracting data from zip file")
                    temp_path = Path(temp_dir)

                    with zipfile.ZipFile(zip_path, "r") as zip_file:
                        zip_file.extractall(temp_path)

                    export_data_path = temp_path / "export_data.json"
                    if not export_data_path.exists():
                        self._raise_export_data_not_found_error()

                    with open(export_data_path) as f:
                        warehouse_data = json.load(f)

                    document_paths = []
                    documents_dir = temp_path / "documents"
                    if documents_dir.exists():
                        for doc_folder in documents_dir.iterdir():
                            if doc_folder.is_dir():
                                for doc_file in doc_folder.iterdir():
                                    if doc_file.is_file():
                                        document_paths.append(str(doc_file))
                                        break
                    pbar.update(1)
                    pbar.refresh()

                    pbar.set_description("Creating new warehouse")
                    self._validate_warehouse_data(warehouse_data)
                    with api_operation(error_type, "create warehouse"):
                        warehouse, warehouse_id = self._create_warehouse_from_data(warehouse_data)
                    pbar.update(1)
                    pbar.refresh()

                    pbar.set_description("Uploading documents")
                    with api_operation(error_type, "upload documents and map IDs"):
                        if document_paths:
                            with tqdm(
                                total=len(document_paths),
                                desc="Uploading documents",
                                unit="doc",
                                leave=False,
                            ) as doc_pbar:
                                document_ids_old_to_new = self._upload_documents_and_map_ids(
                                    warehouse, warehouse_data, document_paths, doc_pbar
                                )
                        else:
                            document_ids_old_to_new = {}
                    pbar.update(1)
                    pbar.refresh()

                    pbar.set_description("Creating tools")
                    tools_id_maps = {}
                    if "tools" in warehouse_data:
                        tools_id_maps = self._process_tools_data(
                            warehouse, warehouse_data["tools"], document_ids_old_to_new
                        )
                    pbar.update(1)
                    pbar.refresh()

                    pbar.set_description("Creating agent settings")
                    agent_settings_id_maps = {}
                    if "agent_settings" in warehouse_data:
                        agent_settings_id_maps = self._process_agent_settings_data_with_mapping(
                            warehouse, warehouse_data["agent_settings"], tools_id_maps
                        )
                    pbar.update(1)
                    pbar.refresh()

                    pbar.set_description("Importing local documents")
                    if "local_documents" in warehouse_data:
                        self._process_local_documents_data(
                            warehouse,
                            warehouse_data,
                            agent_settings_id_maps,
                            temp_path,
                        )
                    pbar.update(1)
                    pbar.refresh()

                    pbar.set_description("Importing ground truths")
                    if "ground_truths" in warehouse_data:
                        self._process_ground_truths_data(warehouse, warehouse_data["ground_truths"])
                    pbar.update(1)
                    pbar.refresh()

                    pbar.set_description("Creating extractors")
                    obj_extractor_id_maps = self._process_object_extractors_data(
                        warehouse, warehouse_data["object_extractors"]
                    )
                    tag_extractor_id_maps = self._process_tag_extractors_data(
                        warehouse, warehouse_data["tag_extractors"]
                    )
                    chunk_extractor_id_maps = self._process_chunks_extractors_data(
                        warehouse, warehouse_data["chunk_extractors"]
                    )
                    pbar.update(1)
                    pbar.refresh()

                    pbar.set_description("Importing tables")
                    with api_operation(error_type, "import tables"):
                        # Count total table operations
                        table_count = 0
                        for table_type, table_data in warehouse_data.items():
                            if table_type not in ["project", "documents"]:
                                if table_type in ["chunks", "blocks", "parsed_documents"]:
                                    table_count += 1
                                elif (
                                    table_type
                                    in ["objects", "object_extractors", "tags", "tag_extractors"]
                                    or "alert" in table_type
                                ):
                                    table_count += len(table_data)

                        with tqdm(
                            total=table_count,
                            desc="Importing tables",
                            unit="table",
                            leave=False,
                        ) as table_pbar:
                            tables_versions_mapping = self._import_tables(
                                warehouse,
                                warehouse_data,
                                document_ids_old_to_new,
                                obj_extractor_id_maps,
                                tag_extractor_id_maps,
                                chunk_extractor_id_maps,
                                temp_path,
                                table_pbar,
                            )
                        self._update_objects_extractors_dependencies(
                            warehouse,
                            warehouse_data["object_extractors"],
                            tables_versions_mapping,
                            obj_extractor_id_maps,
                            document_ids_old_to_new,
                        )
                        self._update_tag_extractors_dependencies(
                            warehouse,
                            warehouse_data["tag_extractors"],
                            tables_versions_mapping,
                            tag_extractor_id_maps,
                            document_ids_old_to_new,
                        )
                    pbar.update(1)
                    pbar.refresh()

                    pbar.set_description("Import completed")
                    pbar.update(1)
                    pbar.refresh()

                except Exception as e:
                    if warehouse_id:
                        with api_operation(error_type, "clean up a failed warehouse"):
                            self.client.delete_warehouse(warehouse_id)
                            message = f"Cleaned up a failed warehouse {warehouse_id}"
                            logger.info(message)
                    error_message = f"Failed to import warehouse: {e!s}"
                    raise error_type(error_message) from e

            return self.client.get_warehouse(warehouse_id)

    def _raise_export_data_not_found_error(self):
        """Raise error when export_data.json is not found."""
        raise WarehouseImportError("export_data.json not found in zip file")
