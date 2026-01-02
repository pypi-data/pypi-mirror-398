import time
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field, PrivateAttr

from .endpoint import Endpoint
from .message import Message

if TYPE_CHECKING:
    from revrseai.client import RevrseAI


class TaskStage(str, Enum):
    """Enum for task stage types."""

    ANALYZE_TASK = "analyze_task"
    EXPLORE_APP = "explore_app"
    BUILD_API = "build_api"
    EXECUTE = "execute"
    DONE = "done"


class Task(BaseModel):
    _client: "RevrseAI | None" = PrivateAttr(default=None)

    id: UUID = Field(..., description="The unique identifier for the task")
    title: str = Field(..., description="The title of the task")
    description: str = Field(..., description="The description of the task")
    current_action: str = Field(..., description="The current action of the task")
    task_stage: TaskStage = Field(..., description="The stage of the task")
    created_at: datetime = Field(
        ..., description="The timestamp when the task was created"
    )

    def update(self) -> "Task":
        """Fetch fresh task data and update all fields."""
        if self._client is None:
            raise ValueError("Client not set. Cannot update task.")
        fresh = self._client.get_task_basic(str(self.id))
        for field in self.__class__.model_fields:
            setattr(self, field, getattr(fresh, field))
        return self

    def get_detailed(self) -> "TaskDetailed":
        """Fetch the detailed version of this task."""
        if self._client is None:
            raise ValueError("Client not set. Cannot get detailed task.")
        return self._client.get_task(str(self.id))

    def wait_till_done(self) -> "TaskDetailed":
        """Wait until the task is done and return the detailed task."""
        while self.task_stage != TaskStage.DONE:
            self.update()
            time.sleep(10)
        return self.get_detailed()


class TaskDetailed(Task):
    messages: list[Message] = Field(..., description="The messages for the task")
    endpoints: list[Endpoint] = Field(..., description="The endpoints for the task")

    def update(self) -> "TaskDetailed":
        """Fetch fresh task data and update all fields."""
        if self._client is None:
            raise ValueError("Client not set. Cannot update task.")
        fresh = self._client.get_task(str(self.id))
        for field in self.__class__.model_fields:
            setattr(self, field, getattr(fresh, field))
        for endpoint in self.endpoints:
            endpoint._client = self._client
        return self

    def make_markdown_documentation(self) -> str:
        """Generate markdown documentation for the task and all its API endpoints.

        Returns:
            A formatted markdown string documenting the task and its API endpoints.
        """
        lines = [f"# {self.title}", ""]

        if self.description:
            lines.extend([f"> {self.description}", ""])

        lines.extend(["## Endpoints", ""])

        for endpoint in self.endpoints:
            lines.append(endpoint.make_markdown_documentation())
            lines.append("")

        return "\n".join(lines)

    def print_markdown_documentation(self) -> None:
        """Print the task's markdown documentation to stdout."""
        print(self.make_markdown_documentation())

    def export_markdown_documentation(self, filename: str) -> None:
        """Export the task's markdown documentation to a file.

        Args:
            filename: The path to the file where documentation will be written.
        """
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.make_markdown_documentation())
