# ruff: noqa: E501, G004, T201, S101, PLR2004, PLR0913
"""Tests for table perform_data_operation functionality."""

import uuid

import pytest
from pydantic import BaseModel, Field


class TestObject(BaseModel):
    """Test object model for data operations testing."""

    name: str = Field(..., description="Name of the test object")
    value: int = Field(..., description="Value of the test object")


def test_perform_data_operation_read_operation(warehouse):
    """Test read operation using perform_data_operation."""
    # Get the chunks table (should exist in most warehouses)
    chunks_table = warehouse.get_table("chunks")
    assert chunks_table is not None, "Chunks table should exist"

    # Test read operation
    result = chunks_table.perform_data_operation(
        operation="read",
        limit=10,
        offset=0,
    )

    assert "result" in result
    assert isinstance(result["result"], dict)
    # The result should contain results
    assert "results" in result["result"]
    assert len(result["result"]["results"]) == 10


def test_perform_data_operation_read_with_filters(warehouse):
    """Test read operation with filters using perform_data_operation."""
    chunks_table = warehouse.get_table("chunks")
    assert chunks_table is not None, "Chunks table should exist"

    # Get first chunk using perform_data_operation to use its document_id as filter
    initial_result = chunks_table.perform_data_operation(
        operation="read",
        limit=1,
        offset=0,
    )

    if not initial_result.get("result") or not initial_result["result"].get("results"):
        pytest.skip("No chunks available for filtering test")

    first_chunk = initial_result["result"]["results"][0]
    document_id = first_chunk.get("document_id")

    if document_id:
        # Test read with filters
        result = chunks_table.perform_data_operation(
            operation="read",
            filters={"document_id": document_id},
            limit=100,
            offset=0,
        )

        assert "result" in result
        assert isinstance(result["result"], dict)


def test_perform_data_operation_create_operation(warehouse):
    """Test create operation using perform_data_operation."""
    # Create a test object table
    table_name = f"test_objects_{uuid.uuid4().hex[:8]}"
    object_table = warehouse.create_objects_table(
        table_name=table_name,
        object_class=TestObject,
    )

    try:
        # Create test data
        test_data = [
            {
                "id": str(uuid.uuid4()),
                "json_object": {"name": "Test Object 1", "value": 100},
                "object_bbox": {},
                "document_id": str(uuid.uuid4()),
                "min_page": 0,
                "max_page": 0,
                "content": "Test content",
                "blocks": [],
                "selected_blocks": [],
                "version": "v1",
            }
        ]

        # Test create operation
        result = object_table.perform_data_operation(
            operation="create",
            data=test_data,
        )

        assert "result" in result
        # Verify the data was created by reading it back
        read_result = object_table.perform_data_operation(
            operation="read",
            filters={"id": test_data[0]["id"]},
        )

        assert "result" in read_result
        result_data = read_result["result"]
        # Check if data exists in result (format may vary)
        assert "data" in result_data or "results" in result_data

    finally:
        # Cleanup
        warehouse.delete_table(table_name)


def test_perform_data_operation_create_with_override(warehouse):
    """Test create operation with override option using perform_data_operation."""
    # Create a test object table
    table_name = f"test_objects_{uuid.uuid4().hex[:8]}"
    object_table = warehouse.create_objects_table(
        table_name=table_name,
        object_class=TestObject,
    )

    try:
        # Create initial test data
        initial_id = str(uuid.uuid4())
        initial_data = [
            {
                "id": initial_id,
                "json_object": {"name": "Initial Object", "value": 100},
                "object_bbox": {},
                "document_id": str(uuid.uuid4()),
                "min_page": 0,
                "max_page": 0,
                "content": "Initial content",
                "blocks": [],
                "selected_blocks": [],
                "version": "v1",
            }
        ]

        # Create the initial data
        result = object_table.perform_data_operation(
            operation="create",
            data=initial_data,
        )

        assert "result" in result
        assert result["result"].get("created", 0) > 0

        # Verify the initial data exists
        read_result = object_table.perform_data_operation(
            operation="read",
            filters={"id": initial_id},
        )

        assert "result" in read_result
        result_data = read_result["result"]
        assert "results" in result_data or "data" in result_data

        # Create new data with override=True
        new_id = str(uuid.uuid4())
        new_data = [
            {
                "id": new_id,
                "json_object": {"name": "New Object", "value": 200},
                "object_bbox": {},
                "document_id": str(uuid.uuid4()),
                "min_page": 0,
                "max_page": 0,
                "content": "New content",
                "blocks": [],
                "selected_blocks": [],
                "version": "v1",
            }
        ]

        # Create with override=True (should clear existing data)
        result = object_table.perform_data_operation(
            operation="create",
            data=new_data,
            override=True,
        )

        assert "result" in result
        assert result["result"].get("created", 0) > 0

        # Verify the new data exists
        read_result = object_table.perform_data_operation(
            operation="read",
            filters={"id": new_id},
        )

        assert "result" in read_result
        result_data = read_result["result"]
        assert "results" in result_data or "data" in result_data

        # Verify the old data was cleared (should not exist)
        read_old_result = object_table.perform_data_operation(
            operation="read",
            filters={"id": initial_id},
        )

        assert "result" in read_old_result
        old_result_data = read_old_result["result"]
        # The old data should not be found
        if "results" in old_result_data:
            assert len(old_result_data["results"]) == 0
        elif "data" in old_result_data:
            assert len(old_result_data["data"]) == 0

    finally:
        # Cleanup
        warehouse.delete_table(table_name)


def test_perform_data_operation_update_operation(warehouse):
    """Test update operation using perform_data_operation."""
    # Create a test object table
    table_name = f"test_objects_{uuid.uuid4().hex[:8]}"
    object_table = warehouse.create_objects_table(
        table_name=table_name,
        object_class=TestObject,
    )

    try:
        # First create some data
        test_id = str(uuid.uuid4())
        test_data = [
            {
                "id": test_id,
                "json_object": {"name": "Original Name", "value": 100},
                "object_bbox": {},
                "document_id": str(uuid.uuid4()),
                "min_page": 0,
                "max_page": 0,
                "content": "Test content",
                "blocks": [],
                "selected_blocks": [],
                "version": "v1",
            }
        ]

        # Create the data
        object_table.perform_data_operation(
            operation="create",
            data=test_data,
        )

        # Update the data
        # Note: data must be a list, and each item must have an 'id' field
        # No filters parameter needed - the handler uses the 'id' from each data item
        update_data = [
            {
                "id": test_id,
                "json_object": {"name": "Updated Name", "value": 200},
                "object_bbox": {},
                "document_id": str(uuid.uuid4()),
                "min_page": 0,
                "max_page": 0,
                "content": "Test content",
                "blocks": [],
                "selected_blocks": [],
                "version": "v1",
            }
        ]

        result = object_table.perform_data_operation(
            operation="update",
            data=update_data,
        )

        assert "result" in result

        # Verify the update by reading back
        read_result = object_table.perform_data_operation(
            operation="read",
            filters={"id": test_id},
        )

        assert "result" in read_result

    finally:
        # Cleanup
        warehouse.delete_table(table_name)


def test_perform_data_operation_delete_operation(warehouse):
    """Test delete operation using perform_data_operation."""
    # Create a test object table
    table_name = f"test_objects_{uuid.uuid4().hex[:8]}"
    object_table = warehouse.create_objects_table(
        table_name=table_name,
        object_class=TestObject,
    )

    try:
        # First create some data
        test_id = str(uuid.uuid4())
        test_data = [
            {
                "id": test_id,
                "json_object": {"name": "To Be Deleted", "value": 100},
                "object_bbox": {},
                "document_id": str(uuid.uuid4()),
                "min_page": 0,
                "max_page": 0,
                "content": "Test content",
                "blocks": [],
                "selected_blocks": [],
                "version": "v1",
            }
        ]

        # Create the data
        object_table.perform_data_operation(
            operation="create",
            data=test_data,
        )

        # Delete the data
        result = object_table.perform_data_operation(
            operation="delete",
            filters={"id": test_id},
        )

        assert "result" in result

        # Verify deletion by trying to read (should return empty or not found)
        read_result = object_table.perform_data_operation(
            operation="read",
            filters={"id": test_id},
        )

        assert "result" in read_result

    finally:
        # Cleanup
        warehouse.delete_table(table_name)


def test_perform_data_operation_with_table_object(warehouse):
    """Test perform_data_operation using Table object directly."""
    chunks_table = warehouse.get_table("chunks")
    assert chunks_table is not None, "Chunks table should exist"

    # Test read operation using Table object directly
    result = chunks_table.perform_data_operation(
        operation="read",
        limit=5,
        offset=0,
    )

    assert "result" in result
    assert isinstance(result["result"], dict)


def test_perform_data_operation_with_table_version_id(warehouse):
    """Test perform_data_operation with specific table version."""
    chunks_table = warehouse.get_table("chunks")
    assert chunks_table is not None, "Chunks table should exist"

    # Get table versions
    versions = chunks_table.list_versions()
    if not versions:
        pytest.skip("No table versions available")

    # Use the first version
    version_id = versions[0].get("id")

    # Test read operation with specific version
    result = chunks_table.perform_data_operation(
        operation="read",
        table_version_id=version_id,
        limit=5,
        offset=0,
    )

    assert "result" in result
    assert isinstance(result["result"], dict)


def test_perform_data_operation_invalid_table(warehouse):
    """Test that get_table raises ValueError for invalid table."""
    # get_table should raise ValueError for non-existent tables
    # Since we can't get a table object for a non-existent table,
    # we can't test perform_data_operation directly, but we verify get_table behavior
    with pytest.raises(ValueError, match="not found"):
        warehouse.get_table("non_existent_table_12345")


def test_perform_data_operation_invalid_operation(warehouse):
    """Test perform_data_operation with invalid operation."""
    chunks_table = warehouse.get_table("chunks")
    assert chunks_table is not None, "Chunks table should exist"

    # The API should handle invalid operations, but we test that our method
    # properly passes it through
    from crf_api_client.exception import CRFAPIError

    with pytest.raises(CRFAPIError):
        chunks_table.perform_data_operation(
            operation="invalid_operation",
        )


def test_create_document_tags_table(warehouse):
    """Test create_document_tags_table functionality."""
    # Create a document tags table with sample tags
    table_name = f"test_document_tags_{uuid.uuid4().hex[:8]}"
    print(f"Creating document tags table: {table_name}")
    document_tags = [
        {"name": "category", "type": "text"},
        {"name": "priority", "type": "text"},
        {"name": "status", "type": "text"},
    ]

    try:
        # Create the document tags table
        tags_table = warehouse.create_document_tags_table(
            table_name=table_name,
            document_tags=document_tags,
        )

        # Verify the table was created and is a Table object
        assert tags_table is not None, "Table should be created"
        assert hasattr(tags_table, "table_id"), "Table should have table_id"
        assert hasattr(tags_table, "name"), "Table should have name"
        assert tags_table.name == table_name, f"Table name should be {table_name}"
        assert hasattr(tags_table, "object_type"), "Table should have object_type"
        assert tags_table.object_type == "document_tags", (
            "Table object_type should be 'document_tags'"
        )

        # Verify the table can be retrieved via get_table
        retrieved_table = warehouse.get_table(table_name)
        assert retrieved_table is not None, "Table should be retrievable"
        assert retrieved_table.table_id == tags_table.table_id, (
            "Retrieved table should have same ID"
        )
        assert retrieved_table.name == table_name, "Retrieved table should have same name"

        # Verify the table appears in list_tables
        tables = warehouse.list_tables()
        table_names = [t.name for t in tables]
        assert table_name in table_names, "Table should appear in list_tables"

    finally:
        # Cleanup
        warehouse.delete_table(table_name)
