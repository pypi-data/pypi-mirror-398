# ruff: noqa: S101, T201, E501, PLR2004, PLR0915
import time
from datetime import UTC, datetime
from typing import List, Optional

from pydantic import BaseModel


class Skill(BaseModel):
    """
    A skill required for a job position.

    This model represents a specific skill with its name and optional description.
    """

    name: str
    description: Optional[str] = None


class JobDescription(BaseModel):
    """
    A job description posting.

    This model represents a job posting with its title, company, and required skills.
    """

    title: str
    company: str
    required_skills: List[Skill]


tagging_tree = {
    "id": "job-location",
    "name": "Job Location",
    "children": [
        {
            "id": "in-person",
            "name": "In-Person",
            "children": [
                {
                    "id": "north-america",
                    "name": "North America",
                    "children": [
                        {
                            "id": "new-york",
                            "name": "New York",
                            "children": [],
                            "description": "In-person jobs located in New York.",
                            "extraction_instruction": "Categorize jobs mentioning 'New York' as location for in-person roles.",
                        },
                        {
                            "id": "san-francisco",
                            "name": "San Francisco",
                            "children": [],
                            "description": "In-person jobs located in San Francisco.",
                            "extraction_instruction": "Categorize jobs mentioning 'San Francisco' as location for in-person roles.",
                        },
                        {
                            "id": "los-angeles",
                            "name": "Los Angeles",
                            "children": [],
                            "description": "In-person jobs located in Los Angeles.",
                            "extraction_instruction": "Categorize jobs mentioning 'Los Angeles' as location for in-person roles.",
                        },
                    ],
                    "description": "Identifies the North American region for in-person jobs.",
                    "extraction_instruction": "Classify jobs based on references to North American locations.",
                },
                {
                    "id": "europe",
                    "name": "Europe",
                    "children": [],
                    "description": "Identifies European locations for in-person jobs.",
                    "extraction_instruction": "Classify jobs mentioning European countries or cities.",
                },
                {
                    "id": "asia",
                    "name": "Asia",
                    "children": [],
                    "description": "Identifies Asian locations for in-person jobs.",
                    "extraction_instruction": "Classify jobs mentioning Asian countries or cities.",
                },
            ],
            "description": "Jobs that require physical presence at a specific location.",
            "extraction_instruction": "Identify jobs requiring onsite work or physical presence at a given location.",
        },
        {
            "id": "remote",
            "name": "Remote",
            "children": [],
            "description": "Jobs that can be performed remotely from any location.",
            "extraction_instruction": "Identify jobs with terms like 'remote', 'work from home', or 'anywhere'.",
        },
    ],
    "description": "Categorizes job location as in-person or remote, with geographic breakdown for in-person roles.",
    "extraction_instruction": "Determine whether the job is in-person or remote. For in-person roles, specify the continent and city if applicable.",
}

document_tags = {
    "name": "TechnicalPosition",
    "description": "The technical or operational domain relevant to the document.",
    "possible_values": [
        "Frontend Engineer",
        "Backend Engineer",
        "Fullstack Engineer",
        "Infrastructure",
        "MLOps",
        "Sales",
        "Marketing",
    ],
    "allow_multiple_values": False,
    "allow_llm_to_infer": False,
}

default_object_payload = {
    "name": "Object retrieval",
    "description": "",
    "document_mode": "include_all",
    "document_parameters": [],
    "tags_included_mode": "include_all",
    "tags_included_parameters": [],
    "tags_excluded_mode": "exclude_none",
    "tags_excluded_parameters": [],
    "objects_included_mode": "include_all",
    "objects_included_parameters": [],
    "objects_excluded_mode": "exclude_none",
    "objects_excluded_parameters": [],
    "attributes_included_mode": "include_all",
    "attributes_included_parameters": {},
    "attributes_excluded_mode": "exclude_none",
    "attributes_excluded_parameters": {},
    "search_scope_extensions": {},
    "retrieval_mode": "semantic-objects",
    "retrieval_parameters": {
        "reformulate_query": False,
        "rerank": True,
        "mode": "hybrid",
        "n_objects": 10,
        "force_n_objects": False,
    },
}

default_agent_settings = {
    "name": "Job listing",
    "description": "",
    "agent_conversation_starter": "",
    "additional_instructions": "Just use the job search tools to look for jobs",
    "model": "gpt-4o",
    "project_brief": False,
    "knowledge_graph_mode": "do_not_inject",
    "knowledge_graph_parameters": [],
    "tags_hierarchies_mode": "inject_all",
    "tags_hierarchies_parameters": [],
    "selected_workflows_mode": "do_not_use_workflow",
    "selected_workflows": [],
    "tools": [],
}


def test_extractions(client, input_pdfs_dir):
    """Test the complete workflow from document upload to retrieval."""
    # Step 0: Create a warehouse
    warehouse = client.create_warehouse(
        name=f"Test Extractions Warehouse {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}",
        brief="Test Warehouse Brief",
        default_llm_model="gpt-4o-mini",
    )

    try:
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

        chunks_table = warehouse.get_table("chunks")
        latest_chunks_table_version = chunks_table.list_versions()[0]

        blocks_table = warehouse.get_table("blocks")
        latest_blocks_table_version = blocks_table.list_versions()[0]

        # Create an object extractor
        object_extractor = warehouse.create_object_extractor(
            name="Test Object Extractor",
            extraction_prompt="Extract the job description from the provided job offer",
            extractable_object=JobDescription,
            llm_model="gpt-5-nano",
            add_anchoring_object=True,
            block_grouping_config={"type": "page_window", "window_size_pages": 5},
            brief="Extract the job description from the provided job offer",
            blocks_table_version=latest_blocks_table_version["id"],
            compute_alerts=False,
        )
        assert object_extractor["id"] is not None, "Object extractor not created"
        object_extractor_task = warehouse.run_object_extractor(
            object_extractor_id=object_extractor["id"]
        )

        # Create a tag extractor
        tag_extractor = warehouse.create_tag_extractor(
            name="Test Tag Extractor",
            tagging_tree=tagging_tree,
            llm_model="gpt-5-nano",
            enforce_single_tag=True,
            chunks_table_version=latest_chunks_table_version["id"],
            brief="Extract the job location from the provided job description",
            compute_alerts=False,
            extraction_prompt="Extract the job location from the provided job description",
        )
        assert tag_extractor["id"] is not None, "Tag extractor not created"
        tag_extractor_task = warehouse.run_tag_extractor(tag_extractor_id=tag_extractor["id"])

        document_tags_table = warehouse.create_document_tags_table(
            table_name="Test Document Tags Table", document_tags=[document_tags]
        )
        assert document_tags_table.table_id is not None, "Document tags table not created"

        document_tags_extraction_task = warehouse.run_document_tags_extraction(
            table_id=document_tags_table.table_id,
            mode="recreate-all",
            llm_model="gpt-5-nano",
            should_push_to_graph=True,
        )

        document_tags_extraction_task.wait_for_completion()
        assert document_tags_extraction_task.status == "completed", (
            f"Document tags extraction failed with status: {document_tags_extraction_task.status}"
        )
        object_extractor_task.wait_for_completion()
        assert object_extractor_task.status == "completed", (
            f"Object extractor failed with status: {object_extractor_task.status}"
        )
        tag_extractor_task.wait_for_completion()
        assert tag_extractor_task.status == "completed", (
            f"Tag extractor failed with status: {tag_extractor_task.status}"
        )

        # Now we push the two tables to retrieval
        object_extractor_table = warehouse.get_table(
            f"extracted_objects_extractor_{object_extractor['id']}"
        )
        push_objects_task = object_extractor_table.push_to_retrieval()
        tag_extractor_table = warehouse.get_table(f"extracted_tags_extractor_{tag_extractor['id']}")
        push_tags_task = tag_extractor_table.push_to_retrieval()

        push_objects_task.wait_for_completion()
        assert push_objects_task.status == "completed", (
            f"Push objects task failed with status: {push_objects_task.status}"
        )
        push_tags_task.wait_for_completion()
        assert push_tags_task.status == "completed", (
            f"Push tags task failed with status: {push_tags_task.status}"
        )

        # Now we do some retrieval
        results = warehouse.retrieve_with_semantic_search(
            query="Backend jobs", n_objects=10, indexes=["objects"]
        )

        assert len(results) > 0, "No results found from retrieval"

        # Retrieve objects tool
        retrieve_objects_tool = warehouse.create_tool(tool=default_object_payload)

        tool_results = warehouse.run_tool(
            tool_id=retrieve_objects_tool["id"], input={"query": "Backend jobs", "top_k": 10}
        )
        assert len(tool_results) > 0, "No results found from tool run"

        # Create an agent settings
        settings = {**default_agent_settings, "tools": [retrieve_objects_tool["id"]]}
        agent_settings = warehouse.create_agent_settings(settings=settings)
        assert agent_settings["id"] is not None, "Agent settings not created"

        # Create a conversation and make sure the tool call results do not contain the json_object
        agent = warehouse.get_playground_agent(agent_settings_id=agent_settings["id"])
        convo_result = agent.create_conversation_and_send_message(
            message_text="Find me a backend job"
        )
        conversation_id = convo_result["conversation_id"]
        full_conversation = warehouse.get_conversation(conversation_id=conversation_id)
        chat = full_conversation["chat_history"]
        tool_calls = [msg for msg in chat if msg["type"] == "tool_call"]
        assert "json_object" not in tool_calls[0]["results"][0]

        # Test the chunk retrieval with filtering
        results = warehouse.retrieve_with_semantic_search(
            query="Backend jobs",
            n_objects=10,
            indexes=["chunks"],
            included_tags=[{"id": "new-york", "is_document_tags": False}],
        )
        assert len(results) > 0, "No results found from chunk retrieval"
        assert len(results) < 5, "Expected less than 5 results from chunk retrieval"
        results = warehouse.retrieve_with_semantic_search(
            query="Backend jobs",
            n_objects=100,
            indexes=["chunks"],
            included_tags=[{"id": "Fullstack Engineer", "is_document_tags": True}],
        )
        assert len(results) < 30, "Expected less than 30 results from chunk retrieval"

    finally:
        client.delete_warehouse(warehouse.id)
