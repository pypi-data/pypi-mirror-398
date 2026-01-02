"""Pydantic models for messages table."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Role(str, Enum):
    """Enum for message role types."""

    USER = "user"
    AGENT = "agent"


class Message(BaseModel):
    """Base model with common fields."""

    task_id: Optional[UUID] = Field(None, description="Task identifier")
    role: Role = Field(..., description="Message role ('user' or 'agent')")
    content: str = Field(..., description="Message content")
    id: UUID = Field(..., description="Unique identifier")
    created_at: datetime = Field(...,
                                 description="Timestamp when record was created")
