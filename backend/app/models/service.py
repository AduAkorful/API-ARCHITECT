from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class ServiceStatus:
    PENDING = "PENDING"
    BUILDING = "BUILDING"
    DEPLOYED = "DEPLOYED"
    FAILED = "FAILED"
    DELETING = "DELETING"

class ServiceMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    service_name: str
    prompt: str
    status: str = ServiceStatus.PENDING
    deployed_url: Optional[str] = None
    build_id: Optional[str] = None
    build_log_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    spec: Dict[str, Any]
