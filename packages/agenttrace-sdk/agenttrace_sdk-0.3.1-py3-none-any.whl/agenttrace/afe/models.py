from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class AFEDetection(BaseModel):
    id: Optional[str] = None
    job_id: str
    trace_id: str
    failure_type: str
    confidence: float = 1.0
    created_at: Optional[datetime] = None

class AFECandidate(BaseModel):
    id: Optional[str] = None
    detection_id: str
    type: str  # 'prompt_patch', 'code_patch', 'config_change'
    summary: str
    diff: Optional[str] = None
    confidence: float
    status: str = 'pending'
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

class RCAResult(BaseModel):
    root_cause: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
