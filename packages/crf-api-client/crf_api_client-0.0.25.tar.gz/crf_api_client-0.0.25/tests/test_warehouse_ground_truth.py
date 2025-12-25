# ruff: noqa: S101, T201, E501, PLR2004, PLR0915
"""Tests for ground truth CRUD operations in warehouse."""

import pytest

from crf_api_client.exception import CRFAPIError


def test_list_ground_truths(warehouse):
    """Test listing all ground truths in a warehouse."""
    ground_truths = warehouse.list_ground_truths()
    assert isinstance(ground_truths, list)


def test_create_ground_truth(warehouse):
    """Test creating a new ground truth."""
    query = "What is the capital of France?"
    answer = "The capital of France is Paris."
    additional_notes = "This is a test ground truth."

    ground_truth = warehouse.create_ground_truth(
        query=query, answer=answer, additional_notes=additional_notes
    )

    assert ground_truth is not None
    assert ground_truth["query"] == query
    assert ground_truth["answer"] == answer
    assert ground_truth["additional_notes"] == additional_notes
    assert "id" in ground_truth
    assert "created_at" in ground_truth
    assert "updated_at" in ground_truth

    # Cleanup
    warehouse.delete_ground_truth(ground_truth["id"])


def test_create_ground_truth_without_notes(warehouse):
    """Test creating a ground truth without additional notes."""
    query = "What is 2+2?"
    answer = "2+2 equals 4."

    ground_truth = warehouse.create_ground_truth(query=query, answer=answer)

    assert ground_truth is not None
    assert ground_truth["query"] == query
    assert ground_truth["answer"] == answer
    assert "id" in ground_truth

    # Cleanup
    warehouse.delete_ground_truth(ground_truth["id"])


def test_get_ground_truth(warehouse):
    """Test getting a specific ground truth by ID."""
    # First create a ground truth
    query = "What is Python?"
    answer = "Python is a programming language."
    created_gt = warehouse.create_ground_truth(query=query, answer=answer)

    try:
        # Get the ground truth
        retrieved_gt = warehouse.get_ground_truth(created_gt["id"])

        assert retrieved_gt is not None
        assert retrieved_gt["id"] == created_gt["id"]
        assert retrieved_gt["query"] == query
        assert retrieved_gt["answer"] == answer
    finally:
        # Cleanup
        warehouse.delete_ground_truth(created_gt["id"])


def test_get_ground_truth_not_found(warehouse):
    """Test getting a non-existent ground truth raises an error."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    with pytest.raises(CRFAPIError):
        warehouse.get_ground_truth(fake_id)


def test_update_ground_truth_query(warehouse):
    """Test updating only the query field of a ground truth."""
    # Create a ground truth
    original_query = "What is the weather?"
    original_answer = "I don't have access to weather data."
    created_gt = warehouse.create_ground_truth(query=original_query, answer=original_answer)

    try:
        # Update only the query
        new_query = "What is the weather today?"
        updated_gt = warehouse.update_ground_truth(
            ground_truth_id=created_gt["id"], query=new_query
        )

        assert updated_gt["query"] == new_query
        assert updated_gt["answer"] == original_answer  # Should remain unchanged
    finally:
        # Cleanup
        warehouse.delete_ground_truth(created_gt["id"])


def test_update_ground_truth_answer(warehouse):
    """Test updating only the answer field of a ground truth."""
    # Create a ground truth
    original_query = "What is AI?"
    original_answer = "AI is artificial intelligence."
    created_gt = warehouse.create_ground_truth(query=original_query, answer=original_answer)

    try:
        # Update only the answer
        new_answer = (
            "AI (Artificial Intelligence) is the simulation of human intelligence by machines."
        )
        updated_gt = warehouse.update_ground_truth(
            ground_truth_id=created_gt["id"], answer=new_answer
        )

        assert updated_gt["query"] == original_query  # Should remain unchanged
        assert updated_gt["answer"] == new_answer
    finally:
        # Cleanup
        warehouse.delete_ground_truth(created_gt["id"])


def test_update_ground_truth_additional_notes(warehouse):
    """Test updating only the additional_notes field of a ground truth."""
    # Create a ground truth
    query = "What is machine learning?"
    answer = "Machine learning is a subset of AI."
    created_gt = warehouse.create_ground_truth(query=query, answer=answer)

    try:
        # Update only the additional notes
        new_notes = "This answer was verified by an expert."
        updated_gt = warehouse.update_ground_truth(
            ground_truth_id=created_gt["id"], additional_notes=new_notes
        )

        assert updated_gt["additional_notes"] == new_notes
        assert updated_gt["query"] == query  # Should remain unchanged
        assert updated_gt["answer"] == answer  # Should remain unchanged
    finally:
        # Cleanup
        warehouse.delete_ground_truth(created_gt["id"])


def test_update_ground_truth_all_fields(warehouse):
    """Test updating all fields of a ground truth at once."""
    # Create a ground truth
    original_query = "What is Django?"
    original_answer = "Django is a web framework."
    original_notes = "Original notes"
    created_gt = warehouse.create_ground_truth(
        query=original_query, answer=original_answer, additional_notes=original_notes
    )

    try:
        # Update all fields
        new_query = "What is Django framework?"
        new_answer = "Django is a high-level Python web framework."
        new_notes = "Updated notes with more details"
        updated_gt = warehouse.update_ground_truth(
            ground_truth_id=created_gt["id"],
            query=new_query,
            answer=new_answer,
            additional_notes=new_notes,
        )

        assert updated_gt["query"] == new_query
        assert updated_gt["answer"] == new_answer
        assert updated_gt["additional_notes"] == new_notes
    finally:
        # Cleanup
        warehouse.delete_ground_truth(created_gt["id"])


def test_delete_ground_truth(warehouse):
    """Test deleting a ground truth."""
    # Create a ground truth
    query = "What is testing?"
    answer = "Testing is the process of verifying software functionality."
    created_gt = warehouse.create_ground_truth(query=query, answer=answer)

    # Delete the ground truth
    warehouse.delete_ground_truth(created_gt["id"])

    # Verify it's deleted by trying to get it
    with pytest.raises(CRFAPIError):
        warehouse.get_ground_truth(created_gt["id"])


def test_delete_ground_truth_not_found(warehouse):
    """Test deleting a non-existent ground truth raises an error."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    with pytest.raises(CRFAPIError):
        warehouse.delete_ground_truth(fake_id)


def test_ground_truth_full_lifecycle(warehouse):
    """Test the complete lifecycle: create, read, update, delete."""
    # Create
    query = "What is the lifecycle test?"
    answer = "This is a lifecycle test."
    created_gt = warehouse.create_ground_truth(query=query, answer=answer)
    ground_truth_id = created_gt["id"]

    try:
        # Read
        retrieved_gt = warehouse.get_ground_truth(ground_truth_id)
        assert retrieved_gt["id"] == ground_truth_id
        assert retrieved_gt["query"] == query
        assert retrieved_gt["answer"] == answer

        # Update
        updated_query = "What is the updated lifecycle test?"
        updated_answer = "This is an updated lifecycle test."
        updated_gt = warehouse.update_ground_truth(
            ground_truth_id=ground_truth_id, query=updated_query, answer=updated_answer
        )
        assert updated_gt["query"] == updated_query
        assert updated_gt["answer"] == updated_answer

        # Verify update persisted
        retrieved_gt_after_update = warehouse.get_ground_truth(ground_truth_id)
        assert retrieved_gt_after_update["query"] == updated_query
        assert retrieved_gt_after_update["answer"] == updated_answer

    finally:
        # Delete
        warehouse.delete_ground_truth(ground_truth_id)

        # Verify deletion
        with pytest.raises(CRFAPIError):
            warehouse.get_ground_truth(ground_truth_id)


def test_list_ground_truths_after_creation(warehouse):
    """Test that list_ground_truths includes newly created ground truths."""
    # Get initial count
    initial_truths = warehouse.list_ground_truths()
    initial_count = len(initial_truths)

    # Create a new ground truth
    created_gt = warehouse.create_ground_truth(
        query="Test query for listing", answer="Test answer for listing"
    )

    try:
        # Get updated list
        updated_truths = warehouse.list_ground_truths()
        updated_count = len(updated_truths)

        # Should have one more ground truth
        assert updated_count == initial_count + 1

        # Verify the created one is in the list
        ground_truth_ids = [gt["id"] for gt in updated_truths]
        assert created_gt["id"] in ground_truth_ids
    finally:
        # Cleanup
        warehouse.delete_ground_truth(created_gt["id"])
