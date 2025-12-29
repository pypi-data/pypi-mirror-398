from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


class Response(BaseModel):
    status_code: int = Field(alias="statusCode")
    headers: Optional[Dict[str, str]] = None
    body: Optional[Any] = None

    model_config = ConfigDict(
        populate_by_name=True,
    )
