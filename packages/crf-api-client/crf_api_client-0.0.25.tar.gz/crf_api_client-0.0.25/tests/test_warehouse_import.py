# ruff: noqa: S101, T201, E501, PLR2004, PLR0915, SLF001
import json
import tempfile
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import BaseModel

from crf_api_client.operations.client_operations import ClientImportOperations, WarehouseImportError


class SampleDocument(BaseModel):
    """Sample document model for import/export testing."""

    title: str
    content: str
    author: str
    date: str


@pytest.fixture
def import_operations(client):
    """Fixture to provide ClientImportOperations instance."""
    return ClientImportOperations(client)


@pytest.fixture
def test_warehouse_name():
    """Fixture to provide a unique test warehouse name."""
    return f"Test Import Warehouse {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}"


@pytest.fixture
def sample_warehouse_data():
    """Fixture to provide sample warehouse data for import testing."""
    # Generate consistent UUIDs for test data
    doc_id_1 = str(uuid.uuid4())
    doc_id_2 = str(uuid.uuid4())

    # Table and version IDs
    chunks_table_id = str(uuid.uuid4())
    chunks_version_id = str(uuid.uuid4())

    return {
        "project": {
            "name": "Test Import Project",
            "business_brief": "Test project for import functionality",
            "default_llm_model": "gpt-4o-mini",
        },
        "documents": [
            {
                "id": doc_id_1,
                "name": "wanderlog_full_stack_software_engineer__new_graduates__canada_.pdf",
                "file": "https://example.com/wanderlog_full_stack_software_engineer__new_graduates__canada_.pdf",
            },
            {
                "id": doc_id_2,
                "name": "luthor_lead_senior_engineer__ruby_on_rails_.pdf",
                "file": "https://example.com/luthor_lead_senior_engineer__ruby_on_rails_.pdf",
            },
        ],
        "tables": {
            "chunks": {
                "id": chunks_table_id,
                "name": "chunks",
                "columns": [
                    "id",
                    "content",
                    "document_id",
                    "previous_chunk_id",
                    "next_chunk_id",
                    "start_char_idx",
                    "end_char_idx",
                    "blocks",
                ],
                "object_type": "chunk",
                "object_metadata": {},
                "versions": [
                    {
                        "id": chunks_version_id,
                        "version": 1,
                        "deployed": True,
                        "table_version_dependencies": {},
                    }
                ],
            },
        },
        "object_extractors": [],
        "tag_extractors": [],
        "chunk_extractors": [],
        "ground_truths": [],
    }


@pytest.fixture
def simple_warehouse_data():
    """Fixture to provide simple warehouse data for basic import testing (no objects/tags/alerts)."""
    # Generate consistent UUIDs for simple test data
    doc_id_1 = str(uuid.uuid4())
    chunks_table_id = str(uuid.uuid4())
    chunks_version_id = str(uuid.uuid4())

    return {
        "project": {
            "name": "Simple Import Project",
            "business_brief": "Simple test project for basic import functionality",
            "default_llm_model": "gpt-4o-mini",
        },
        "documents": [
            {
                "id": doc_id_1,
                "name": "wanderlog_full_stack_software_engineer__new_graduates__canada_.pdf",
                "file": "https://example.com/wanderlog_full_stack_software_engineer__new_graduates__canada_.pdf",
            }
        ],
        "tables": {
            "chunks": {
                "id": chunks_table_id,
                "name": "chunks",
                "columns": [
                    "id",
                    "content",
                    "document_id",
                    "previous_chunk_id",
                    "next_chunk_id",
                    "start_char_idx",
                    "end_char_idx",
                    "blocks",
                ],
                "object_type": "chunk",
                "object_metadata": {},
                "versions": [
                    {
                        "id": chunks_version_id,
                        "version": 1,
                        "deployed": True,
                        "table_version_dependencies": {},
                    }
                ],
            },
        },
        "object_extractors": [],
        "tag_extractors": [],
        "chunk_extractors": [],
        "ground_truths": [],
    }


@pytest.fixture
def sample_document_paths(input_pdfs_dir):
    """Fixture to provide sample document paths for import testing."""
    pdf_files = list(input_pdfs_dir.glob("*.pdf"))[:2]
    return [str(pdf) for pdf in pdf_files] if pdf_files else []


def test_create_warehouse_from_data(import_operations, simple_warehouse_data):
    """Test warehouse creation from data."""
    try:
        warehouse, warehouse_id = import_operations._create_warehouse_from_data(
            simple_warehouse_data
        )

        assert warehouse is not None
        assert warehouse.name == simple_warehouse_data["project"]["name"]
        assert warehouse.business_brief == simple_warehouse_data["project"]["business_brief"]
        assert warehouse_id is not None

    finally:
        if "warehouse" in locals():
            import_operations.client.delete_warehouse(warehouse_id)


def test_validate_warehouse_data(import_operations):
    """Test warehouse data validation."""
    # Test valid data
    valid_data = {"project": {"name": "Test"}, "documents": []}
    import_operations._validate_warehouse_data(valid_data)  # Should not raise

    # Test invalid data
    invalid_data = {
        "project": {"name": "Test"}
        # missing "documents" key
    }

    with pytest.raises(WarehouseImportError):
        import_operations._validate_warehouse_data(invalid_data)


def test_upload_documents_and_map_ids(
    import_operations, simple_warehouse_data, sample_document_paths
):
    """Test document upload and ID mapping."""
    if not sample_document_paths:
        pytest.skip("No document paths available for testing")

    try:
        warehouse, warehouse_id = import_operations._create_warehouse_from_data(
            simple_warehouse_data
        )

        document_ids_old_to_new = import_operations._upload_documents_and_map_ids(
            warehouse, simple_warehouse_data, sample_document_paths
        )

        assert isinstance(document_ids_old_to_new, dict)

        # Check that documents were uploaded
        uploaded_documents = warehouse.list_documents()
        assert len(uploaded_documents) == len(sample_document_paths)

    finally:
        if "warehouse" in locals():
            import_operations.client.delete_warehouse(warehouse_id)


def test_import_tables_new_format(import_operations, sample_warehouse_data, sample_document_paths):
    """Test processing tables with new format (tables with versions)."""
    if not sample_document_paths:
        pytest.skip("No document paths available for testing")

    try:
        warehouse, warehouse_id = import_operations._create_warehouse_from_data(
            sample_warehouse_data
        )

        document_ids_old_to_new = import_operations._upload_documents_and_map_ids(
            warehouse, sample_warehouse_data, sample_document_paths
        )

        chunk_extractor_id_maps = import_operations._process_chunks_extractors_data(
            warehouse, sample_warehouse_data["chunk_extractors"]
        )
        obj_extractor_id_maps = import_operations._process_object_extractors_data(
            warehouse, sample_warehouse_data["object_extractors"]
        )
        tag_extractor_id_maps = import_operations._process_tag_extractors_data(
            warehouse, sample_warehouse_data["tag_extractors"]
        )

        # Create a temporary directory with sample table data
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create tables_data directory structure
            tables_data_dir = temp_path / "tables_data"
            tables_data_dir.mkdir()

            # Create sample data files for each table version
            for table_name, table_info in sample_warehouse_data["tables"].items():
                table_dir = tables_data_dir / table_info["id"]
                table_dir.mkdir()

                for version in table_info["versions"]:
                    # Create minimal sample data using consistent IDs from the fixture
                    if table_name == "chunks":
                        # Extract the first document ID from the sample data for consistency
                        first_doc_id = (
                            sample_warehouse_data["documents"][0]["id"]
                            if sample_warehouse_data["documents"]
                            else str(uuid.uuid4())
                        )
                        # Use document ID for chunk ID to maintain consistency
                        chunk_data = [
                            {
                                "id": first_doc_id,  # Use consistent ID
                                "content": "Sample chunk content",
                                "document_id": next(iter(document_ids_old_to_new.values()))
                                if document_ids_old_to_new
                                else first_doc_id,
                                "previous_chunk_id": None,
                                "next_chunk_id": None,
                                "start_char_idx": 0,
                                "end_char_idx": 20,
                                "blocks": [{"type": "text", "content": "Sample chunk"}],
                            }
                        ]
                    else:
                        chunk_data = []

                    version_file = table_dir / version["id"]
                    with open(version_file, "w") as f:
                        json.dump(chunk_data, f)

            # Test the new _import_tables method
            tables_versions_mapping = import_operations._import_tables(
                warehouse,
                sample_warehouse_data,
                document_ids_old_to_new,
                obj_extractor_id_maps,
                tag_extractor_id_maps,
                chunk_extractor_id_maps,
                temp_path,
                None,  # progress_bar
            )

            # Verify tables were created with versions
            tables = warehouse.list_tables()
            assert len(tables) > 0

            # Check that versions mapping was created
            assert isinstance(tables_versions_mapping, dict)

    finally:
        if "warehouse" in locals():
            import_operations.client.delete_warehouse(warehouse_id)


def test_process_object_extractors_basic(
    import_operations, sample_warehouse_data, sample_document_paths
):
    """Test basic processing of object extractors data."""
    if not sample_document_paths:
        pytest.skip("No document paths available for testing")

    try:
        warehouse, warehouse_id = import_operations._create_warehouse_from_data(
            sample_warehouse_data
        )
        obj_extractor_id_maps = import_operations._process_object_extractors_data(
            warehouse, sample_warehouse_data["object_extractors"]
        )

        # Should succeed with empty object extractors list
        assert isinstance(obj_extractor_id_maps, dict)

    finally:
        if "warehouse" in locals():
            import_operations.client.delete_warehouse(warehouse_id)


def test_process_tag_extractors_data(
    import_operations, sample_warehouse_data, sample_document_paths
):
    """Test processing of tag extractors data."""
    if not sample_document_paths:
        pytest.skip("No document paths available for testing")

    try:
        warehouse, warehouse_id = import_operations._create_warehouse_from_data(
            sample_warehouse_data
        )

        tag_extractor_id_maps = import_operations._process_tag_extractors_data(
            warehouse, sample_warehouse_data["tag_extractors"]
        )

        # Should succeed with empty tag extractors list
        assert isinstance(tag_extractor_id_maps, dict)

    finally:
        if "warehouse" in locals():
            import_operations.client.delete_warehouse(warehouse_id)


def test_process_ground_truths_data(
    import_operations, sample_warehouse_data
):
    """Test processing of ground truths data."""
    try:
        warehouse, warehouse_id = import_operations._create_warehouse_from_data(
            sample_warehouse_data
        )

        # Test with empty ground truths list
        ground_truths_data = []
        import_operations._process_ground_truths_data(warehouse, ground_truths_data)

        # Test with actual ground truths
        ground_truths_data = [
            {
                "id": str(uuid.uuid4()),
                "query": "What is the meaning of life?",
                "answer": "42",
                "additional_notes": "From Hitchhiker's Guide"
            },
            {
                "id": str(uuid.uuid4()),
                "query": "What is the capital of France?",
                "answer": "Paris",
                "additional_notes": None
            }
        ]
        import_operations._process_ground_truths_data(warehouse, ground_truths_data)

        # Verify ground truths were created
        created_ground_truths = warehouse.list_ground_truths()
        assert len(created_ground_truths) >= 2

        # Verify the content
        queries = [gt["query"] for gt in created_ground_truths]
        assert "What is the meaning of life?" in queries
        assert "What is the capital of France?" in queries

    finally:
        if "warehouse" in locals():
            import_operations.client.delete_warehouse(warehouse_id)


def test_import_warehouse_from_zip_file(
    client, sample_warehouse_data, sample_document_paths, input_pdfs_dir
):
    """Test the main import_warehouse method with a zip file."""
    if not sample_document_paths:
        pytest.skip("No document paths available for testing")

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
        zip_path = tmp_file.name

    try:
        # Create a zip file with the warehouse data
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("export_data.json", json.dumps(sample_warehouse_data, indent=2))

            # Add documents to zip
            if sample_document_paths:
                for i, doc_path in enumerate(sample_document_paths):
                    if Path(doc_path).exists():
                        doc_name = Path(doc_path).name
                        doc_id = sample_warehouse_data["documents"][i]["id"]
                        zip_doc_path = f"documents/{doc_id}/{doc_name}"

                        with open(doc_path, "rb") as f:
                            zip_file.writestr(zip_doc_path, f.read())

            # Add table data files for the new format
            if "tables" in sample_warehouse_data:
                for table_name, table_info in sample_warehouse_data["tables"].items():
                    for version in table_info["versions"]:
                        # Create sample data for each version
                        table_data = []
                        if table_name == "chunks":
                            # Add minimal chunk data using consistent IDs from the fixture
                            doc_id = (
                                sample_warehouse_data["documents"][0]["id"]
                                if sample_warehouse_data["documents"]
                                else str(uuid.uuid4())
                            )
                            chunk_id = doc_id  # Use doc_id for chunk_id to maintain consistency
                            table_data = [
                                {
                                    "id": chunk_id,
                                    "content": "Sample chunk content",
                                    "document_id": doc_id,
                                    "previous_chunk_id": None,
                                    "next_chunk_id": None,
                                    "start_char_idx": 0,
                                    "end_char_idx": 20,
                                    "blocks": [{"type": "text", "content": "Sample chunk"}],
                                }
                            ]

                        table_data_path = f"tables_data/{table_info['id']}/{version['id']}"
                        zip_file.writestr(table_data_path, json.dumps(table_data, indent=2))

        # Test the main import method
        warehouse = client.import_warehouse(zip_path)

        assert warehouse is not None
        assert warehouse.name == sample_warehouse_data["project"]["name"]

    finally:
        Path(zip_path).unlink(missing_ok=True)
        if "warehouse" in locals():
            client.delete_warehouse(warehouse.id)


def test_sample_document_model():
    """Test the SampleDocument model to ensure it works correctly."""
    doc = SampleDocument(
        title="Test Title", content="Test Content", author="Test Author", date="2024-01-01"
    )
    assert doc.title == "Test Title"
    assert doc.content == "Test Content"
    assert doc.author == "Test Author"
    assert doc.date == "2024-01-01"
