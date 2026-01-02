import os
from typing import Any

import requests

from revrseai.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from revrseai.models import Info, Response, Task, TaskDetailed

_BASE_URL = "https://api.revrse.ai"


class RevrseAI:
    """Client for interacting with the RevrseAI API.

    This client provides methods to generate, execute, and manage tasks
    through the RevrseAI platform.

    Attributes:
        api_key: The API key used for authentication.
    """

    def __init__(self, api_key: str | None = None):
        """Initialize the RevrseAI client.

        Args:
            api_key: The API key for authentication. If not provided,
                will attempt to read from the REVRSE_AI_API_KEY environment variable.

        Raises:
            ValueError: If no API key is provided and none is found in
                environment variables.
        """
        self.api_key = api_key or os.getenv("REVRSE_AI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required")

    def _request(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        method: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make an HTTP request to the RevrseAI API.

        Args:
            endpoint: The API endpoint path (e.g., "/api/tasks").
            data: Optional JSON body data for POST requests.
            method: HTTP method. Defaults to POST if data provided, GET otherwise.
            params: Optional query parameters.

        Returns:
            The JSON response from the API.

        Raises:
            AuthenticationError: If authentication fails (401).
            AuthorizationError: If access is denied (403).
            NotFoundError: If the resource is not found (404).
            ValidationError: If request validation fails (422).
            RateLimitError: If rate limit is exceeded (429).
            ServerError: If a server error occurs (5xx).
            APIError: For other API errors.
        """
        url = f"{_BASE_URL}{endpoint}"
        headers = {"X-API-Key": self.api_key}
        method = method or ("POST" if data else "GET")
        response = requests.request(
            method, url, json=data, headers=headers, params=params
        )

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
        """Retrieve all tasks associated with the authenticated user.

        Returns:
            A list of Task objects representing all available tasks.
        """
        return [Task.model_validate(t) for t in self._request("/api/tasks")]

    def get_task(self, task_id: str) -> TaskDetailed:
        """Retrieve a task with full details including messages and endpoints.

        Args:
            task_id: The unique identifier of the task to retrieve.

        Returns:
            A TaskDetailed object containing the task with all associated
            messages and endpoints.
        """
        response = self._request(
            f"/api/tasks/{task_id}", params={"include_details": True}
        )
        task = TaskDetailed.model_validate(response)
        task._client = self
        for endpoint in task.endpoints:
            endpoint._client = self
        return task

    def get_task_basic(self, task_id: str) -> Task:
        """Retrieve a task without detailed information.

        This is a lighter-weight alternative to get_task() when you don't
        need the full task details like messages and endpoints.

        Args:
            task_id: The unique identifier of the task to retrieve.

        Returns:
            A Task object containing basic task information.
        """
        response = self._request(
            f"/api/tasks/{task_id}", params={"include_details": False}
        )
        task = Task.model_validate(response)
        task._client = self
        return task

    def generate(self, task: str, secrets: dict[str, Any] | None = None) -> Task:
        """Generate a new task from a natural language description.

        This initiates the AI-powered API generation process, which explores
        the app and builds the necessary API endpoints to accomplish the task.

        Args:
            task: A natural language description of what you want to accomplish.
            secrets: Optional dictionary of secrets (e.g., passwords) needed
                for the task execution.

        Returns:
            A Task object representing the newly created task. Use wait_till_done()
            to wait for generation to complete.
        """
        result = Task.model_validate(
            self._request("/generate", data={"task": task, "secrets": secrets})
        )
        result._client = self
        return result

    def execute(
        self,
        app: str | None = None,
        task_id: str | None = None,
        endpoint_id: str | None = None,
        endpoint: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> Response:
        """Execute an API endpoint with the provided data.

        This is a unified method for executing endpoints. You can specify
        the target endpoint using one of three approaches:
        - By app name and endpoint name
        - By task_id and endpoint name
        - By endpoint_id directly

        Args:
            app: The name of the app to execute against.
            task_id: The task ID containing the endpoint to execute.
            endpoint_id: The direct endpoint ID to execute.
            endpoint: The endpoint name (required when using app or task_id).
            data: Optional input data to pass to the endpoint.

        Returns:
            A Response object containing the execution result.

        Raises:
            ValueError: If neither app, task_id, nor endpoint_id is provided,
                or if endpoint is missing when using task_id.
        """
        if app is None and task_id is None and endpoint_id is None:
            raise ValueError("Either app, task_id, or endpoint_id is required")
        if endpoint_id is not None:
            return self.execute_from_endpoint_id(endpoint_id, data)
        elif task_id is not None:
            if endpoint is None:
                raise ValueError("endpoint is required when using task_id")
            return self.execute_from_task_id(task_id, endpoint, data)
        else:
            return Response.model_validate(
                self._request(
                    "/execute", data={"app": app, "endpoint": endpoint, "data": data}
                )
            )

    def execute_from_task_id(
        self, task_id: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> Response:
        """Execute an endpoint by task ID and endpoint name.

        Args:
            task_id: The unique identifier of the task.
            endpoint: The name of the endpoint to execute within the task.
            data: Optional input data to pass to the endpoint.

        Returns:
            A Response object containing the execution result.
        """
        return Response.model_validate(
            self._request(f"/execute/{task_id}/{endpoint}", data=data)
        )

    def execute_from_endpoint_id(
        self, endpoint_id: str, data: dict[str, Any] | None = None
    ) -> Response:
        """Execute an endpoint directly by its unique ID.

        Args:
            endpoint_id: The unique identifier of the endpoint to execute.
            data: Optional input data to pass to the endpoint.

        Returns:
            A Response object containing the execution result.
        """
        return Response.model_validate(
            self._request(f"/execute/{endpoint_id}", data=data)
        )

    def info(self, query: str) -> Info:
        """Retrieve information about an app and its available endpoints.

        Args:
            query: The app name or search query to look up.

        Returns:
            An Info object containing app details and a list of available endpoints.
        """
        info = Info.model_validate(self._request("/api/info", params={"query": query}))
        for endpoint in info.endpoints:
            endpoint._client = self
        return info
