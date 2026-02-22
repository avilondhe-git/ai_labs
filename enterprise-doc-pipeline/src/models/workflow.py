from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow processing status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(BaseModel):
    """Individual step in a workflow"""
    step_name: str
    status: WorkflowStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class DocumentWorkflow(BaseModel):
    """Complete workflow for document processing"""
    workflow_id: str
    document_id: str
    workflow_type: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    
    steps: List[WorkflowStep] = []
    current_step: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    retry_count: int = 0
    max_retries: int = 3
    
    class Config:
        use_enum_values = True
