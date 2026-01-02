from typing import Any

from pydantic import BaseModel, Field


class Response(BaseModel):
    status: int = Field(..., description="The status code of the response")
    data: dict[str, Any] = Field(..., description="The json of the response")
