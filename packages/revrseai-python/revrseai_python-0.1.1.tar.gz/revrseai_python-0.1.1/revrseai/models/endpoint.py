import json
from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import BaseModel, Field, PrivateAttr, field_validator

from .response import Response
from .schema import SchemaObject

if TYPE_CHECKING:
    from revrseai.client import RevrseAI


class Endpoint(BaseModel):
    """Information about an API endpoint."""

    _client: "RevrseAI | None" = PrivateAttr(default=None)

    id: UUID = Field(..., description="The unique identifier for the endpoint")
    name: str = Field(description="The name of the endpoint")
    description: str | None = Field(
        default=None, description="Description of what this endpoint does"
    )
    input_schema: SchemaObject = Field(
        description="JSON schema for the input parameters"
    )
    output_schema: SchemaObject = Field(
        description="JSON schema for the output response"
    )

    @field_validator("input_schema", "output_schema", mode="before")
    @classmethod
    def parse_schema(cls, v: Any) -> SchemaObject:
        """Validate and parse schema fields into SchemaObject instances.

        Args:
            v: The raw schema value, either a dict or SchemaObject.

        Returns:
            A SchemaObject instance parsed from the input.

        Raises:
            ValueError: If the input is neither a dict nor a SchemaObject.
        """
        if isinstance(v, dict):
            return SchemaObject.from_dict(v)
        if not isinstance(v, SchemaObject):
            raise ValueError(f"Expected dict or SchemaObject, got {type(v)}")
        return v

    def execute(self, data: dict[str, Any] | None = None) -> Response:
        """Execute this endpoint with the provided input data.

        Args:
            data: Optional input data matching the endpoint's input_schema.

        Returns:
            A Response object containing the execution result.

        Raises:
            ValueError: If the client is not set on this endpoint instance.
        """
        if self._client is None:
            raise ValueError("Client not set. Cannot execute endpoint.")
        return self._client.execute_from_endpoint_id(str(self.id), data=data)

    def example_data(self) -> dict[str, Any]:
        """Generate example input data based on the endpoint's input schema.

        Returns:
            A dictionary containing example values for all input fields.
        """
        return dict(self.input_schema.example_data())

    def example_response(self) -> dict[str, Any]:
        """Generate example response data based on the endpoint's output schema.

        Returns:
            A dictionary containing example values for all output fields.
        """
        return dict(self.output_schema.example_data())

    def make_markdown_documentation(self) -> str:
        """Generate markdown documentation for this API endpoint.

        Creates comprehensive documentation including input/output schemas,
        code examples, and example responses.

        Returns:
            A formatted markdown string documenting the API endpoint.
        """
        lines = [f"# {self.name}", ""]

        if self.description:
            lines.extend([f"> {self.description}", ""])

        # Input section
        lines.extend(["## Input", ""])
        lines.append(self.input_schema.to_markdown_table())

        # Build Python snippet for example request
        example_json = json.dumps(self.example_data(), indent=4)
        # Indent the data dict to align with the data= parameter
        indented_data = "\n".join(
            "    " + line if i > 0 else line
            for i, line in enumerate(example_json.split("\n"))
        )

        snippet = f'''from revrseai import RevrseAI

client = RevrseAI("YOUR_API_KEY")
resp = client.execute(
    endpoint_id="{self.id}",
    data={indented_data}
)
print(resp)'''

        lines.extend(["", "### Code Example", "", "```python"])
        lines.append(snippet)
        lines.extend(["```", ""])

        # Output section
        lines.extend(["## Output", ""])
        lines.append(self.output_schema.to_markdown_table())
        lines.extend(["", "### Example Response", "", "```json"])
        lines.append(json.dumps(self.example_response(), indent=2))
        lines.extend(["```"])

        return "\n".join(lines)

    def print_markdown_documentation(self) -> None:
        """Print the endpoint's markdown documentation to stdout."""
        print(self.make_markdown_documentation())

    def export_markdown_documentation(self, filename: str) -> None:
        """Export the endpoint's markdown documentation to a file.

        Args:
            filename: The path to the file where documentation will be written.
        """
        with open(filename, "w") as f:
            f.write(self.make_markdown_documentation())
