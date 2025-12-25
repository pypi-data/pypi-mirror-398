# ruff: noqa: E501, G004, T201, S101, PLR2004
"""Tests for table limit functionality."""


def test_table_get_data_limit_functionality(warehouse):
    """Test comprehensive table get_data limit functionality."""
    # Get the chunks table
    chunks_table = warehouse.get_table("chunks")
    assert chunks_table is not None, "Chunks table should exist"

    print("\n=== Testing Table get_data Limit Functionality ===")

    # Step 1: Get all data without arguments and log count
    print("\n1. Getting all data without arguments...")
    all_data = chunks_table.get_data()
    all_count = len(all_data)
    print(f"Total chunks count: {all_count}")
    assert all_count > 0, "Should have some chunks in the table"

    # Step 2: Get data with max_results=10 and ensure we only have first 10
    print("\n2. Getting data with max_results=10...")
    limited_data = chunks_table.get_data(max_results=10)
    limited_count = len(limited_data)
    print(f"Limited chunks count: {limited_count}")

    expected_limit_count = min(10, all_count)
    assert limited_count == expected_limit_count, (
        f"Expected {expected_limit_count} chunks, got {limited_count}"
    )

    # Verify we got the first 10 chunks (same order)
    for i in range(limited_count):
        assert limited_data[i]["id"] == all_data[i]["id"], (
            f"Chunk {i} should match between all_data and limited_data"
        )

    # Step 3: Get data with offset=10 and ensure we have everything but first 10
    print("\n3. Getting data with offset=10...")
    offset_data = chunks_table.get_data(offset=10)
    offset_count = len(offset_data)
    print(f"Offset chunks count: {offset_count}")

    expected_offset_count = max(0, all_count - 10)
    assert offset_count == expected_offset_count, (
        f"Expected {expected_offset_count} chunks with offset, got {offset_count}"
    )

    # Verify we got chunks starting from index 10
    if all_count > 10:
        for i in range(min(5, offset_count)):  # Check first 5 of offset data
            assert offset_data[i]["id"] == all_data[i + 10]["id"], (
                f"Offset chunk {i} should match all_data[{i + 10}]"
            )

    # Step 4: Use first chunk ID to filter and ensure we only have one result
    if all_count > 0:
        print("\n4. Getting data filtered by first chunk ID...")
        first_chunk_id = all_data[0]["id"]
        chunk_filtered_data = chunks_table.get_data(filters={"id": first_chunk_id})
        chunk_filtered_count = len(chunk_filtered_data)
        print(f"Chunk ID filtered count: {chunk_filtered_count}")

        assert chunk_filtered_count == 1, (
            f"Expected 1 chunk when filtering by ID, got {chunk_filtered_count}"
        )
        assert chunk_filtered_data[0]["id"] == first_chunk_id, (
            "Filtered chunk should have the correct ID"
        )

    # Step 5: Use first document ID to filter and verify count matches
    if all_count > 0:
        print("\n5. Getting data filtered by first document ID...")
        first_document_id = all_data[0]["document_id"]

        # Count how many chunks have this document_id in all_data
        expected_doc_count = sum(
            1 for chunk in all_data if chunk.get("document_id") == first_document_id
        )

        # Get filtered data
        doc_filtered_data = chunks_table.get_data(filters={"document_id": first_document_id})
        doc_filtered_count = len(doc_filtered_data)
        print(f"Document ID filtered count: {doc_filtered_count} (expected: {expected_doc_count})")

        assert doc_filtered_count == expected_doc_count, (
            f"Expected {expected_doc_count} chunks for document ID, got {doc_filtered_count}"
        )

        # Verify all returned chunks have the correct document_id
        for chunk in doc_filtered_data:
            assert chunk.get("document_id") == first_document_id, (
                "All chunks should have the correct document_id"
            )

    # Step 6: Test combining max_results with filters
    if all_count > 5:
        print("\n6. Testing max_results with offset combination...")
        limited_offset_data = chunks_table.get_data(max_results=5, offset=2)
        limited_offset_count = len(limited_offset_data)
        expected_limited_offset = min(5, max(0, all_count - 2))
        print(
            f"Limited + offset count: {limited_offset_count} (expected: {expected_limited_offset})"
        )

        assert limited_offset_count == expected_limited_offset, (
            f"Expected {expected_limited_offset} chunks with limit+offset"
        )

        # Verify we got the correct chunks (starting from index 2, max 5 items)
        for i in range(limited_offset_count):
            assert limited_offset_data[i]["id"] == all_data[i + 2]["id"], (
                f"Limited+offset chunk {i} should match all_data[{i + 2}]"
            )

    print("\n=== All table limit tests passed! ===")
