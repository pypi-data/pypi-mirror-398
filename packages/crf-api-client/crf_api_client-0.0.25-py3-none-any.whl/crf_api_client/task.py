# ruff: noqa: ANN003, D105
import time

import requests

from .base import BaseAPIClient


class Task(BaseAPIClient):
    def __init__(
        self,
        base_url: str,
        token: str,
        warehouse_id: str,
        task_id: str,
        status: str,
        **kwargs,
    ):
        super().__init__(base_url, token)
        self.warehouse_id = warehouse_id
        self.task_id = task_id
        self.status = status
        # Store any additional task attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def abort(self) -> dict:
        """Abort this task"""
        response = requests.post(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/pipeline-runs/{self.task_id}/abort/",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def refresh(self) -> dict:
        """Refresh task data from the API and update this instance"""
        response = requests.get(
            f"{self.base_url}/api/v1/projects/{self.warehouse_id}/pipeline-runs/{self.task_id}/",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        data = response.json()

        # Update instance attributes with fresh data
        for key, value in data.items():
            if key not in ["id"]:  # Don't overwrite task_id with id
                setattr(self, key, value)

        return data

    def wait_for_completion(self) -> dict:
        """Wait for task to complete"""
        while self.status not in ["completed", "failed"]:
            self.refresh()
            time.sleep(2)
        return self.refresh()

    def __repr__(self):
        return (
            f"Task(id='{self.task_id}', status='{self.status}', warehouse_id='{self.warehouse_id}')"
        )

    def __str__(self):
        return f"Task: {self.status} ({self.task_id})"
