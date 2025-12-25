# ruff: noqa: S101, T201, E501, PLR2004, PLR0915
import time
from datetime import UTC, datetime

from dotenv import load_dotenv

load_dotenv()


def test_complete_workflow(client, input_pdfs_dir):
    """Test the complete workflow from document upload to retrieval."""
    # Step 0: Create a warehouse
    warehouse = client.create_warehouse(
        name=f"Test Warehouse {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}",
        brief="Test Warehouse Brief",
        default_llm_model="gpt-4o-mini",
    )

    try:
        # Step 0.1: Configure chunk extractor
        chunk_extractors = warehouse.list_chunk_extractors()
        assert len(chunk_extractors) > 0, "No chunk extractors found"

        # Get the first chunk extractor
        chunk_extractor = chunk_extractors[0]
        chunk_extractor_id = chunk_extractor["id"]

        # Update chunk extractor settings
        updated_extractor = warehouse.update_chunk_extractor(
            chunk_extractor_id=chunk_extractor_id,
            maximum_chunk_size=15000,
            minimum_chunk_size=10000,
            title_section_separator_mode="none",
        )
        assert updated_extractor["maximum_chunk_size"] == 15000, (
            "Failed to update maximum chunk size"
        )
        assert updated_extractor["minimum_chunk_size"] == 10000, (
            "Failed to update minimum chunk size"
        )

        # Step 1: Get list of PDFs from input directory
        pdf_files = list(input_pdfs_dir.glob("*.pdf"))
        assert len(pdf_files) > 0, "No PDF files found in input directory"

        # Step 2: Upload documents
        upload_responses = warehouse.upload_documents(
            file_paths=[str(pdf) for pdf in pdf_files], skip_parsing=False
        )
        assert len(upload_responses) > 0, "Failed to upload documents"

        # Step 3: List tasks and wait for the latest parsing task
        time.sleep(5)  # Give some time for task to be created
        tasks = warehouse.list_tasks()
        assert len(tasks) > 0, "No tasks found"

        latest_task = tasks[0]  # Tasks are typically returned in reverse chronological order
        task_result = latest_task.wait_for_completion()
        assert task_result["status"] == "completed", (
            f"Task failed with status: {task_result['status']}"
        )

        # Step 4: Get data from chunks table and verify number of chunks
        chunks_table = warehouse.get_table("chunks")
        chunks_data = chunks_table.get_data(max_results=100, page_size=10)
        assert len(chunks_data) == len(pdf_files), (
            f"Expected {len(pdf_files)} chunks (one per file), but got {len(chunks_data)}"
        )
        # Test Parameters
        test_query = "What is this document about?"
        test_question = "What are the main topics discussed in this document?"
        n_results = 5
        indexes = ["chunks"]

        print("\n=== Testing All Retrieval Methods ===")
        sync_to_retrieval_task = warehouse.run_sync_to_retrieval()
        sync_to_retrieval_task.wait_for_completion()

        # Test 1: Semantic Search
        print("\n1. Testing Semantic Search")
        semantic_results = warehouse.retrieve_with_semantic_search(
            query=test_query, n_objects=n_results, indexes=indexes
        )
        assert len(semantic_results) > 0, "No results found from semantic search"
        print(f"Found {len(semantic_results)} semantic search results")

        # Test 3: Full Text Search
        print("\n3. Testing Full Text Search")
        fulltext_results = warehouse.retrieve_with_full_text_search(
            query=test_query,
            indexes=indexes,
            n_objects=n_results,
            question=test_question,
        )
        assert len(fulltext_results) > 0, "No results found from full text search"
        print(f"Found {len(fulltext_results)} full text search results")

        # Test 4: Hybrid Search
        print("\n4. Testing Hybrid Search")
        hybrid_results = warehouse.retrieve_with_hybrid_search(
            query=test_query,
            indexes=indexes,
            n_objects=n_results,
            question=test_question,
            rrf_k=60,
        )
        assert len(hybrid_results) > 0, "No results found from hybrid search"
        print(f"Found {len(hybrid_results)} hybrid search results")

        print("\n=== Testing Answer Generation Methods ===")

        # Test 5: Generate Answer with Semantic Search
        print("\n5. Testing Answer Generation with Semantic Search")
        semantic_answer = warehouse.generate_answer_with_semantic_search(
            question=test_question,
            query=test_query,
            n_objects=n_results,
            indexes=indexes,
        )
        assert semantic_answer is not None, "Failed to generate answer with semantic search"
        print(f"Semantic Search Answer: {semantic_answer[:200]}...")

        # Test 6: Generate Answer with Full Text Search
        print("\n6. Testing Answer Generation with Full Text Search")
        fulltext_answer = warehouse.generate_answer_with_full_text_search(
            question=test_question,
            query=test_query,
            indexes=indexes,
            n_objects=n_results,
        )
        assert fulltext_answer is not None, "Failed to generate answer with full text search"
        print(f"Full Text Search Answer: {fulltext_answer[:200]}...")

        # Test 7: Generate Answer with Hybrid Search
        print("\n7. Testing Answer Generation with Hybrid Search")
        hybrid_answer = warehouse.generate_answer_with_hybrid_search(
            question=test_question,
            query=test_query,
            indexes=indexes,
            n_objects=n_results,
            rrf_k=60,
        )
        assert hybrid_answer is not None, "Failed to generate answer with hybrid search"
        print(f"Hybrid Search Answer: {hybrid_answer[:200]}...")

    finally:
        # Cleanup
        client.delete_warehouse(warehouse.id)
