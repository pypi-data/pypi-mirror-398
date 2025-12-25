# ruff: noqa: DTZ005, C901, PLR0912, E501, ANN003, D205, D105
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests

from .base import BaseAPIClient
from .exception import CRFAPIError

logger = logging.getLogger(__name__)


class PlaygroundAgent(BaseAPIClient):
    def __init__(
        self,
        base_url: str,
        token: str,
        warehouse_id: str,
        agent_settings_id: str,
        **kwargs,
    ):
        super().__init__(base_url, token)
        self.warehouse_id = warehouse_id
        self.agent_settings_id = agent_settings_id
        # Store any additional agent attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _get_headers_without_content_type(self):
        return {"Authorization": f"Token {self.token}"}

    def create_conversation(self, conversation_instructions: Optional[str] = None) -> dict:
        """
        Create a new playground conversation

        Args:
            conversation_instructions: Optional specific instructions for this conversation.
                                     These instructions will override agent settings and
                                     cannot be updated after creation.

        """
        url = f"{self.base_url}/api/v1/projects/{self.warehouse_id}/playground-conversations/"
        data = {
            "name": f"Playground {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "type": "playground",
            "agent_settings": self.agent_settings_id,
        }

        # Add conversation instructions if provided
        if conversation_instructions:
            data["conversation_instructions"] = conversation_instructions

        response = requests.post(url, headers=self._get_headers(), json=data)
        response.raise_for_status()
        return response.json()

    def send_message(self, conversation_id: str, message_text: str, **kwargs) -> str:
        """Send a message to a conversation and return the assistant's response"""
        if kwargs:
            import warnings

            warnings.warn(
                "Passing additional keyword arguments to send_message is deprecated and will be removed in the future.",
                DeprecationWarning,
                stacklevel=2,
            )
        url = f"{self.base_url}/api/v1/projects/{self.warehouse_id}/playground-conversations/{conversation_id}/send_message_stream/"
        data = {"message": message_text}

        # Enable streaming for the request
        response = requests.post(url, headers=self._get_headers(), json=data, stream=True)
        response.raise_for_status()

        # Process streaming response - only keep the last message
        last_message = None
        for line in response.iter_lines(decode_unicode=True):
            if line:
                # Handle Server-Sent Events format
                if line.startswith("data: "):
                    try:
                        # Extract JSON data from SSE format
                        json_data = line[6:]  # Remove 'data: ' prefix
                        if json_data.strip() == "[DONE]":
                            break
                        event_data = json.loads(json_data)

                        # Look for the streaming_completed event which contains the final response
                        if event_data.get("type_streaming") == "streaming_completed":
                            # Extract the assistant's message from chat_history
                            chat_history = event_data.get("payload", {}).get("chat_history", [])
                            for msg in reversed(chat_history):  # Start from the end
                                if msg.get("role") == "assistant" and msg.get("type") == "message":
                                    last_message = msg.get("content", "")
                                    break
                        elif event_data.get("type_streaming") == "streaming_in_progress":
                            # Keep track of the latest message during streaming
                            payload = event_data.get("payload", {})
                            if (
                                payload.get("type") == "message"
                                and payload.get("role") == "assistant"
                            ):
                                last_message = payload.get("content", "")

                    except json.JSONDecodeError:
                        continue
                elif line.startswith("event: "):
                    # Handle event type if needed
                    continue
                elif line.strip() == "":
                    # Empty line separator in SSE
                    continue
                else:
                    # Try to parse as regular JSON (fallback)
                    try:
                        event_data = json.loads(line)

                        # Apply same logic for non-SSE format
                        if event_data.get("type_streaming") == "streaming_completed":
                            chat_history = event_data.get("payload", {}).get("chat_history", [])
                            for msg in reversed(chat_history):
                                if msg.get("role") == "assistant" and msg.get("type") == "message":
                                    last_message = msg.get("content", "")
                                    break
                    except json.JSONDecodeError:
                        continue

        return last_message or ""

    def create_conversation_and_send_message(
        self,
        message_text: str,
        conversation_instructions: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
        batch_size: int = 10,
    ) -> dict:
        """
        Create a new conversation and send a message
        Returns conversation details with the assistant's response

        Args:
            message_text: The message to send to the conversation
            conversation_instructions: Optional specific instructions for this conversation.
                                     These instructions will override agent settings and
                                     cannot be updated after creation.
            file_paths: Optional list of file paths to upload to the conversation before sending the message
            batch_size: Number of files to upload per batch (default: 10)

        """
        conversation = self.create_conversation(conversation_instructions)
        conversation_id = conversation["id"]

        # Upload files if provided
        if file_paths:
            self.upload_local_documents_to_conversation(conversation_id, file_paths, batch_size)

        answer = self.send_message(conversation_id, message_text)
        conversation = self._get_conversation(conversation_id)

        return {
            "conversation_id": conversation_id,
            "query": message_text,
            "answer": answer,
            "agent_settings_id": self.agent_settings_id,
            "conversation_instructions": conversation_instructions,
        }

    def _get_conversation(self, conversation_id: str) -> dict:
        """Get conversation details by ID"""
        url = f"{self.base_url}/api/v1/projects/{self.warehouse_id}/playground-conversations/{conversation_id}/"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def list_conversations(self) -> list[dict]:
        """List all playground conversations for this agent"""
        url = f"{self.base_url}/api/v1/projects/{self.warehouse_id}/playground-conversations/"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json().get("results", [])

    def get_conversation_history(self, conversation_id: str) -> list[dict]:
        """Get the full conversation history"""
        conversation = self._get_conversation(conversation_id)
        return conversation.get("chat_history", [])

    def get_conversation_instructions(self, conversation_id: str) -> Optional[str]:
        """Get the conversation-specific instructions for a conversation"""
        conversation = self._get_conversation(conversation_id)
        return conversation.get("conversation_instructions")

    def upload_local_documents_to_conversation(
        self, conversation_id: str, file_paths: List[str], batch_size: int = 10
    ) -> List[dict]:
        """Upload local documents to a conversation"""
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
                    f"{self.base_url}/api/v1/projects/{self.warehouse_id}/playground-conversations/"
                    f"{conversation_id}/local-documents/bulk-upload/",
                    headers=self._get_headers_without_content_type(),
                    files=files_to_upload,
                )
                if response.status_code != 201:  # noqa: PLR2004
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

    def list_local_documents_for_conversation(self, conversation_id: str) -> List[dict]:
        """List all local documents for a conversation"""
        url = (
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/playground-conversations/"
            f"{conversation_id}/local-documents/"
        )
        return self._get_paginated_data(url)

    def delete_local_document_from_conversation(
        self, conversation_id: str, local_document_id: str
    ) -> None:
        """Delete a local document from a conversation"""
        response = requests.delete(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/playground-conversations/"
            f"{conversation_id}/local-documents/{local_document_id}/",
            headers=self._get_headers(),
        )
        if response.status_code != 204:  # noqa: PLR2004
            raise CRFAPIError(response.json(), response)

    def __repr__(self):
        return (
            f"PlaygroundAgent(agent_settings_id='{self.agent_settings_id}', "
            f"warehouse_id='{self.warehouse_id}')"
        )

    def __str__(self):
        return f"PlaygroundAgent: {self.agent_settings_id} (warehouse: {self.warehouse_id})"
