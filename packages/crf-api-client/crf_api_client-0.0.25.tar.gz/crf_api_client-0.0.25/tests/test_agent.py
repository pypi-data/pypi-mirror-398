# ruff: noqa: S101


def test_agent_create_conversation_and_send_message(warehouse):
    agent_settings = warehouse.list_agent_settings()
    agent_settings_id = agent_settings[0]["id"]
    agent = warehouse.get_playground_agent(agent_settings_id)
    answer_data = agent.create_conversation_and_send_message(
        "What are the key skills of a backend engineer?"
    )
    answer = answer_data["answer"]
    assert answer is not None
    new_answer = agent.send_message(
        answer_data["conversation_id"],
        "What are the key skills of a frontend engineer?",
    )
    assert new_answer is not None
