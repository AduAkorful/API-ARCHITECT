from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Any
import re

class SchemaField(BaseModel):
    name: str
    type: str
    required: bool = True

class EndpointSpec(BaseModel):
    path: str
    method: Literal["GET", "POST", "PUT", "DELETE"]
    model_name: str
    schema_fields: List[SchemaField]

class GeminiSpec(BaseModel):
    service_name: str = Field(..., max_length=50)
    endpoint: EndpointSpec
    storage: Optional[Any] = None

    @field_validator("service_name")
    @classmethod
    def validate_service_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("service_name must be lowercase, numbers, and hyphens only.")
        return v
