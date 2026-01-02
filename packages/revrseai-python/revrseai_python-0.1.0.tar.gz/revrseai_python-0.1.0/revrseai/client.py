import requests
import os

from revrseai.models import Task, TaskDetailed, Response, Info
from revrseai.exceptions import (
    RevrseAIError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    APIError,
)

_BASE_URL = "https://api.revrse.ai"


class RevrseAI:

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("REVRSE_AI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required")

    def _request(self, endpoint: str, data: dict | None = None, method: str | None = None, params: dict | None = None):
        url = f"{_BASE_URL}{endpoint}"
        headers = {
            "X-API-Key": self.api_key
        }
        method = method or ('POST' if data else 'GET')
        response = requests.request(
            method, url, json=data, headers=headers, params=params)

        self._handle_response_errors(response)
        return response.json()

    def _handle_response_errors(self, response: requests.Response) -> None:
        """Check response for errors and raise appropriate exceptions."""
        if response.ok:
            return

        status_code = response.status_code
        try:
            error_data = response.json()
            detail = error_data.get("detail", str(error_data))
        except Exception:
            detail = response.text or "Unknown error"

        if status_code == 401:
            raise AuthenticationError(detail, status_code, detail)
        elif status_code == 403:
            raise AuthorizationError(detail, status_code, detail)
        elif status_code == 404:
            raise NotFoundError(detail, status_code, detail)
        elif status_code == 422:
            raise ValidationError(detail, status_code, detail)
        elif status_code == 429:
            raise RateLimitError(detail, status_code, detail)
        elif status_code >= 500:
            raise ServerError(detail, status_code, detail)
        else:
            raise APIError(detail, status_code, detail)

    def get_tasks(self) -> list[Task]:
        return self._request("/api/tasks")

    def get_task(self, task_id: str) -> TaskDetailed:
        response = self._request(
            f"/api/tasks/{task_id}", params={"include_details": True})
        task = TaskDetailed.model_validate(response)
        task._client = self
        for endpoint in task.endpoints:
            endpoint._client = self
        return task

    def get_task_basic(self, task_id: str) -> Task:
        response = self._request(
            f"/api/tasks/{task_id}", params={"include_details": False})
        task = Task.model_validate(response)
        task._client = self
        return task

    def generate(self, task: str, secrets: dict | None = None) -> Task:
        result = Task.model_validate(self._request("/generate", data={
            "task": task,
            "secrets": secrets
        }))
        result._client = self
        return result

    def execute(self, app: str | None = None, task_id: str | None = None, endpoint_id: str | None = None, endpoint: str | None = None, data: dict | None = None) -> Response:
        if app is None and task_id is None and endpoint_id is None:
            raise ValueError("Either app, task_id, or endpoint_id is required")
        if endpoint_id is not None:
            return self.execute_from_endpoint_id(endpoint_id, data)
        elif task_id is not None:
            return self.execute_from_task_id(task_id, endpoint, data)
        else:
            return Response.model_validate(self._request(f"/execute", data={
                "app": app,
                "endpoint": endpoint,
                "data": data
            }))

    def execute_from_task_id(self, task_id: str, endpoint: str, data: dict | None = None) -> Response:
        return Response.model_validate(self._request(f"/execute/{task_id}/{endpoint}", data=data))

    def execute_from_endpoint_id(self, endpoint_id: str, data: dict | None = None) -> Response:
        return Response.model_validate(self._request(f"/execute/{endpoint_id}", data=data))

    def info(self, query: str) -> Info:
        info = Info.model_validate(self._request(
            "/api/info", params={"query": query}))
        for endpoint in info.endpoints:
            endpoint._client = self
        return info
