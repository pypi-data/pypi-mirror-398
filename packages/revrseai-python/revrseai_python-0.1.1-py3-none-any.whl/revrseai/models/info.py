from pydantic import BaseModel, Field

from .endpoint import Endpoint


class Info(BaseModel):
    """Response model for the info route."""

    app_name: str = Field(..., description="The name of the app")
    app_image_url: str | None = Field(
        default=None, description="URL to the app's image"
    )
    app_description: str | None = Field(
        default=None, description="Description of the app"
    )
    app_title: str | None = Field(default=None, description="Title of the app")
    endpoints: list[Endpoint] = Field(
        default_factory=list, description="List of available endpoints"
    )

    def make_markdown_documentation(self) -> str:
        """Generate markdown documentation for the app and all its API endpoints.

        Returns:
            A formatted markdown string documenting the app and its API endpoints.
        """
        lines = [f"# {self.app_title or self.app_name}", ""]

        lines.extend(["## Endpoints", ""])

        for endpoint in self.endpoints:
            lines.append(endpoint.make_markdown_documentation())
            lines.append("")

        return "\n".join(lines)

    def print_markdown_documentation(self) -> None:
        """Print the app's markdown documentation to stdout."""
        print(self.make_markdown_documentation())

    def export_markdown_documentation(self, filename: str) -> None:
        """Export the app's markdown documentation to a file.

        Args:
            filename: The path to the file where documentation will be written.
        """
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.make_markdown_documentation())
