"""OpenAPI Schema Object representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SchemaObject:
    """
    Represents an OpenAPI Schema Object (subset of JSON Schema).

    Provides structured access to schema properties.
    """

    # Common fields
    type: str | None = None
    format: str | None = None
    description: str | None = None
    title: str | None = None
    nullable: bool = False
    enum: list[Any] | None = None
    example: Any | None = None

    # Object fields
    properties: dict[str, SchemaObject] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)

    # Array fields
    items: SchemaObject | None = None

    # Escape hatch for additional/arbitrary properties
    _extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to OpenAPI dictionary format."""
        result: dict[str, Any] = {}

        if self.type:
            result["type"] = self.type
        if self.format:
            result["format"] = self.format
        if self.description:
            result["description"] = self.description
        if self.title:
            result["title"] = self.title
        if self.nullable:
            result["nullable"] = True
        if self.enum:
            result["enum"] = self.enum
        if self.example is not None:
            result["example"] = self.example

        if self.properties:
            result["properties"] = {
                name: prop.to_dict() for name, prop in self.properties.items()
            }
        if self.required:
            result["required"] = self.required

        if self.items:
            result["items"] = self.items.to_dict()

        # Add any extra properties
        result.update(self._extra)

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SchemaObject:
        """Create from dictionary."""
        # Extract known fields
        properties = {}
        if "properties" in data:
            for name, prop_data in data["properties"].items():
                properties[name] = (
                    cls.from_dict(prop_data) if isinstance(prop_data, dict) else cls()
                )

        items = None
        if "items" in data and isinstance(data["items"], dict):
            items = cls.from_dict(data["items"])

        # Collect extra fields not explicitly handled
        known_fields = {
            "type",
            "format",
            "description",
            "title",
            "nullable",
            "enum",
            "example",
            "properties",
            "required",
            "items",
        }
        extra = {k: v for k, v in data.items() if k not in known_fields}

        return cls(
            type=data.get("type"),
            format=data.get("format"),
            description=data.get("description"),
            title=data.get("title"),
            nullable=data.get("nullable", False),
            enum=data.get("enum"),
            example=data.get("example"),
            properties=properties,
            required=data.get("required", []),
            items=items,
            _extra=extra,
        )

    def example_data(self) -> Any:
        """Generate example data based on the schema structure."""
        if self.example is not None:
            return self.example

        if self.enum:
            return self.enum[0]

        if self.type == "object" or self.properties:
            return {name: prop.example_data() for name, prop in self.properties.items()}

        if self.type == "array":
            if self.items:
                return [self.items.example_data()]
            return []

        if self.type == "string":
            return "..."

        if self.type == "integer":
            return 0

        if self.type == "number":
            return 0.0

        if self.type == "boolean":
            return False

        return None

    def _format_type(self) -> str:
        """Format the type string for display."""
        type_str = self.type or "any"
        if self.format:
            type_str = f"{type_str} ({self.format})"
        if self.type == "array" and self.items:
            type_str = f"array[{self.items._format_type()}]"
        if self.nullable:
            type_str = f"{type_str}?"
        return type_str

    def to_markdown_table(self, required_fields: list[str] | None = None) -> str:
        """Generate a markdown table from schema properties."""
        if not self.properties:
            return "_No fields_"

        required_fields = required_fields or self.required or []

        lines = [
            "| Field | Type | Required | Description |",
            "|-------|------|----------|-------------|",
        ]

        for name, prop in self.properties.items():
            is_required = "Yes" if name in required_fields else "No"
            desc = prop.description or "-"
            type_str = prop._format_type()
            lines.append(f"| {name} | {type_str} | {is_required} | {desc} |")

        return "\n".join(lines)
