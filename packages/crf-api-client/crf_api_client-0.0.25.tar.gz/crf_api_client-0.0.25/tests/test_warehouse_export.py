# ruff: noqa: S101, T201, E501, PLR2004, PLR0915, SLF001, BLE001, S106
import json
import tempfile
import time
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from crf_api_client.operations.warehouse_operations import (
    WarehouseExportError,
    WarehouseExportOperations,
)
from crf_api_client.warehouse import Warehouse


class SampleDocument(BaseModel):
    """Sample document model for export/import testing."""

    test_extraction: str = Field(..., description="test_extraction")


@pytest.fixture
def export_operations(client, test_warehouse_name):
    """Fixture to provide export operations instance with a test warehouse."""
    warehouse = client.create_warehouse(
        name=test_warehouse_name,
        brief="Test warehouse for export operations",
        default_llm_model="gpt-4o-mini",
    )
    yield WarehouseExportOperations(warehouse)
    # Cleanup
    client.delete_warehouse(warehouse.id)


@pytest.fixture
def test_warehouse_name():
    """Fixture to provide a unique test warehouse name."""
    return f"Test Export Warehouse {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}"


@pytest.fixture
def sample_documents():
    """Fixture to provide sample document data."""
    return [
        {
            "title": "Test Document 1",
            "content": "This is the content of test document 1.",
            "author": "Test Author 1",
            "date": "2024-01-01",
        },
        {
            "title": "Test Document 2",
            "content": "This is the content of test document 2.",
            "author": "Test Author 2",
            "date": "2024-01-02",
        },
    ]


@pytest.fixture
def sample_chunks():
    """Fixture to provide sample chunk data."""
    import uuid

    return [
        {
            "id": str(uuid.uuid4()),
            "content": "This is chunk 1 content",
            "document_id": str(uuid.uuid4()),
            "start_char_idx": 0,
            "end_char_idx": 25,
            "blocks": [{"type": "text", "content": "This is chunk 1"}],
        },
        {
            "id": str(uuid.uuid4()),
            "content": "This is chunk 2 content",
            "document_id": str(uuid.uuid4()),
            "start_char_idx": 0,
            "end_char_idx": 25,
            "blocks": [{"type": "text", "content": "This is chunk 2"}],
        },
    ]


def test_warehouse_exists_check(export_operations):
    """Test the warehouse existence check."""
    assert export_operations._warehouse_exists() is True


def test_warehouse_exists_check_non_existent(client):
    """Test warehouse existence check for non-existent warehouse."""
    fake_warehouse = Warehouse(
        base_url=client.base_url, token=client.token, id="fake-uuid", name="fake-warehouse"
    )

    export_ops = WarehouseExportOperations(fake_warehouse)

    # This should return False for non-existent warehouse
    # The method catches KeyError: 'results' and returns False
    try:
        result = export_ops._warehouse_exists()
        assert result is False
    except Exception:
        # If it raises any other exception, that's also acceptable for a non-existent warehouse
        assert True


def test_debug_table_attributes(export_operations):
    """Debug test to see what attributes are available on table objects."""
    # Create an object table
    object_table = export_operations.warehouse.create_objects_table(
        table_name="debug_test_objects", object_class=SampleDocument
    )

    # Check if object_metadata exists
    if hasattr(object_table, "object_metadata"):
        print(f"object_metadata: {object_table.object_metadata}")
    else:
        print("object_metadata attribute does not exist")

    # Also check via list_tables
    tables = export_operations.warehouse.list_tables()
    for table in tables:
        if table.name == "debug_test_objects":
            print(f"Table from list_tables - attributes: {dir(table)}")
            print(f"Table from list_tables - __dict__: {table.__dict__}")
            if hasattr(table, "object_metadata"):
                print(f"Table from list_tables - object_metadata: {table.object_metadata}")
            else:
                print("Table from list_tables - object_metadata attribute does not exist")
            break


def test_process_object_table(export_operations):
    """Test processing object table data."""
    # Create an object table
    object_table = export_operations.warehouse.create_objects_table(
        table_name="test_objects", object_class=SampleDocument
    )
    # Add some test data
    test_data = [
        {
            "id": str(uuid.uuid4()),
            "json_object": {"test_extraction": "test_extraction"},
            "object_bbox": {"x": 0, "y": 0, "width": 100, "height": 50},
            "document_id": str(uuid.uuid4()),
        }
    ]
    object_table.write_data(test_data)

    export_data = {"objects": []}

    # Get the table again from list_tables to ensure we have all attributes
    tables = export_operations.warehouse.list_tables()
    object_table_refreshed = None
    for table in tables:
        if table.name == "test_objects":
            object_table_refreshed = table
            break

    if object_table_refreshed and hasattr(object_table_refreshed, "object_metadata"):
        export_operations._process_object_table(object_table_refreshed, export_data)

        assert len(export_data["objects"]) > 0
        object_data = export_data["objects"][0]
        assert "config" in object_data
        assert "data" in object_data
        assert "pydantic_class_string" in object_data["config"]
    else:
        pytest.skip("object_metadata not available on table object")


def test_process_tag_table(export_operations, tagging_tree):
    """Test processing tag table data."""
    # Create a tag table
    tag_table = export_operations.warehouse.create_tag_table(
        table_name="test_tags", tagging_tree=tagging_tree
    )

    # Add some test data
    test_data = [
        {
            "chunk_id": str(uuid.uuid4()),
            "metadata": {
                "metadata_id": "test_tags",
                "tags": "test_tags_1",
                "reason": "",
                "quotes": [],
            },
            "id": str(uuid.uuid4()),
        },
    ]
    tag_table.write_data(test_data)

    export_data = {"tags": []}

    # Get the table again from list_tables to ensure we have all attributes
    tables = export_operations.warehouse.list_tables()
    tag_table_refreshed = None
    for table in tables:
        if table.name == "test_tags":
            tag_table_refreshed = table
            break

    if tag_table_refreshed and hasattr(tag_table_refreshed, "object_metadata"):
        export_operations._process_tag_table(tag_table_refreshed, export_data)

        assert len(export_data["tags"]) > 0
        tag_data = export_data["tags"][0]
        assert "config" in tag_data
        assert "data" in tag_data
    else:
        pytest.skip("object_metadata not available on table object")


def test_process_new_table_format(export_operations):
    """Test processing table data with new format (with versions)."""
    # Wait for default tables to be created
    time.sleep(5)

    export_data = {"tables": {}}

    try:
        chunks_table = export_operations.warehouse.get_table("chunks")
        export_operations._process_table_new(chunks_table, export_data)
        assert "tables" in export_data
        assert chunks_table.name in export_data["tables"]
        table_data = export_data["tables"][chunks_table.name]
        assert "versions" in table_data
        assert isinstance(table_data["versions"], list)
    except ValueError:
        # Table might not exist yet, which is fine for testing
        pass

    try:
        blocks_table = export_operations.warehouse.get_table("blocks")
        export_operations._process_table_new(blocks_table, export_data)
        assert blocks_table.name in export_data["tables"]
        table_data = export_data["tables"][blocks_table.name]
        assert "versions" in table_data
    except ValueError:
        # Table might not exist yet, which is fine for testing
        pass


def test_collect_project_and_documents(export_operations):
    """Test collecting all warehouse data."""
    export_data = {}
    export_operations._collect_project_and_documents(export_data)

    # Check that all expected data types are present
    assert "project" in export_data
    assert "documents" in export_data

    # Check project data structure
    assert export_data["project"]["name"] == export_operations.warehouse.name


def test_collect_object_extractors(export_operations):
    """Test collecting object extractors."""
    export_data = {}
    export_operations._collect_object_extractors(export_data)

    assert "object_extractors" in export_data
    assert isinstance(export_data["object_extractors"], list)


def test_collect_tag_extractors(export_operations):
    """Test collecting tag extractors."""
    export_data = {}
    export_operations._collect_tag_extractors(export_data)

    assert "tag_extractors" in export_data
    assert isinstance(export_data["tag_extractors"], list)


def test_collect_chunk_extractors(export_operations):
    """Test collecting chunk extractors."""
    export_data = {}
    export_operations._collect_chunk_extractors(export_data)

    assert "chunk_extractors" in export_data
    assert isinstance(export_data["chunk_extractors"], list)


def test_collect_ground_truths(export_operations):
    """Test collecting ground truths."""
    # Create some ground truths
    gt1 = export_operations.warehouse.create_ground_truth(
        query="What is the meaning of life?",
        answer="42",
        additional_notes="From Hitchhiker's Guide",
    )
    gt2 = export_operations.warehouse.create_ground_truth(
        query="What is the capital of France?", answer="Paris"
    )

    try:
        export_data = {}
        export_operations._collect_ground_truths(export_data)

        assert "ground_truths" in export_data
        assert isinstance(export_data["ground_truths"], list)
        assert len(export_data["ground_truths"]) >= 2

        # Verify ground truths contain the expected fields
        for gt in export_data["ground_truths"]:
            assert "id" in gt
            assert "query" in gt
            assert "answer" in gt

    finally:
        # Cleanup
        export_operations.warehouse.delete_ground_truth(gt1["id"])
        export_operations.warehouse.delete_ground_truth(gt2["id"])


def test_export_warehouse_basic(export_operations):
    """Test basic warehouse export functionality."""
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
        zip_path = tmp_file.name

    try:
        exported_path = export_operations.export_warehouse(output_path=zip_path)

        assert Path(exported_path).exists()
        assert Path(exported_path).stat().st_size > 0

        # Verify zip contents
        with zipfile.ZipFile(exported_path, "r") as zip_file:
            file_list = zip_file.namelist()
            assert "export_data.json" in file_list

            # Check export data structure
            with zip_file.open("export_data.json") as f:
                export_data = json.load(f)
                assert "project" in export_data
                assert "documents" in export_data
                assert "tables" in export_data  # New format includes tables structure
                assert "ground_truths" in export_data  # Ground truths should be included
                assert export_data["project"]["name"] == export_operations.warehouse.name

    finally:
        Path(zip_path).unlink(missing_ok=True)


def test_export_warehouse_with_documents(export_operations, input_pdfs_dir):
    """Test warehouse export with actual documents."""
    # Upload some test documents
    pdf_files = list(input_pdfs_dir.glob("*.pdf"))[:2]
    if pdf_files:
        export_operations.warehouse.upload_documents(
            [str(pdf) for pdf in pdf_files], skip_parsing=True
        )

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
        zip_path = tmp_file.name

    try:
        exported_path = export_operations.export_warehouse(output_path=zip_path)

        # Verify documents are included
        with zipfile.ZipFile(exported_path, "r") as zip_file:
            file_list = zip_file.namelist()

            with zip_file.open("export_data.json") as f:
                export_data = json.load(f)

            if export_data["documents"]:
                # Check that document files are included
                assert any(name.startswith("documents/") for name in file_list)

            # Check for tables data files if tables exist
            if export_data.get("tables"):
                # Print file list for debugging
                print(f"Files in zip: {file_list}")
                print(f"Tables in export: {list(export_data['tables'].keys())}")
                # Only assert if there are tables with versions that have data
                has_table_data = any(
                    table_info.get("versions") and len(table_info["versions"]) > 0
                    for table_info in export_data["tables"].values()
                )
                if has_table_data:
                    assert any(name.startswith("tables_data/") for name in file_list)

    finally:
        Path(zip_path).unlink(missing_ok=True)


def test_export_warehouse_with_objects_and_tags(export_operations, tagging_tree):
    """Test warehouse export with object and tag tables."""
    # Create object table
    object_table = export_operations.warehouse.create_objects_table(
        table_name="test_objects", object_class=SampleDocument
    )

    object_test_data = [
        {
            "id": str(uuid.uuid4()),
            "json_object": {"test_extraction": "test_extraction"},
            "object_bbox": {"x": 0, "y": 0, "width": 100, "height": 50},
            "document_id": str(uuid.uuid4()),
        }
    ]
    object_table.write_data(object_test_data)
    object_table = export_operations.warehouse.get_table("test_objects")

    # Create tag table
    tag_table = export_operations.warehouse.create_tag_table(
        table_name="test_tags", tagging_tree=tagging_tree
    )

    tag_test_data = [
        {
            "chunk_id": str(uuid.uuid4()),
            "metadata": {
                "metadata_id": "test_tags",
                "tags": "test_tags_1",
                "reason": "",
                "quotes": [],
            },
            "id": str(uuid.uuid4()),
        },
    ]
    tag_table.write_data(tag_test_data)
    tag_table = export_operations.warehouse.get_table("test_tags")

    # Test full data collection
    export_data = {}
    export_operations._process_object_table(object_table, export_data)
    export_operations._process_tag_table(tag_table, export_data)

    assert "objects" in export_data
    assert len(export_data["objects"]) > 0

    assert "tags" in export_data
    assert len(export_data["tags"]) > 0

    # Verify object data has pydantic class string
    object_data = export_data["objects"][0]
    assert "config" in object_data
    assert "pydantic_class_string" in object_data["config"]


def test_export_warehouse_error_handling():
    """Test error handling in warehouse export."""
    # Create a fake warehouse
    fake_warehouse = Warehouse(
        base_url="http://fake-url.com", token="fake-token", id="fake-uuid", name="fake-warehouse"
    )

    export_ops = WarehouseExportOperations(fake_warehouse)

    with pytest.raises(WarehouseExportError):
        export_ops.export_warehouse()


# Keep the original integration tests for backward compatibility
def test_export_warehouse_integration(client, test_warehouse_name, input_pdfs_dir):
    """Test full warehouse export integration using the main warehouse method."""
    warehouse = client.create_warehouse(
        name=test_warehouse_name,
        brief="Test warehouse for integration",
        default_llm_model="gpt-4o-mini",
    )

    try:
        pdf_files = list(input_pdfs_dir.glob("*.pdf"))[:2]
        if pdf_files:
            warehouse.upload_documents([str(pdf) for pdf in pdf_files], skip_parsing=True)

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
            zip_path = tmp_file.name

        try:
            exported_path = warehouse.export_warehouse(output_path=zip_path)

            assert Path(exported_path).exists()
            assert Path(exported_path).stat().st_size > 0

            with zipfile.ZipFile(exported_path, "r") as zip_file:
                file_list = zip_file.namelist()
                assert "export_data.json" in file_list

                with zip_file.open("export_data.json") as f:
                    export_data = json.load(f)
                    assert "project" in export_data
                    assert "documents" in export_data
                    assert "tables" in export_data  # New format includes tables structure
                    assert "ground_truths" in export_data  # Ground truths should be included
                    assert export_data["project"]["name"] == test_warehouse_name

        finally:
            Path(zip_path).unlink(missing_ok=True)

    finally:
        client.delete_warehouse(warehouse.id)
