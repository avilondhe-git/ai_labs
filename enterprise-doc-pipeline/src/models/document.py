from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DocumentType(str, Enum):
    """Document classification"""
    INVOICE = "invoice"
    CONTRACT = "contract"
    RECEIPT = "receipt"
    FORM = "form"
    RESEARCH_PAPER = "research_paper"
    GENERIC = "generic"


class DocumentStatus(str, Enum):
    """Processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class ExtractedEntity(BaseModel):
    """Extracted entity from document"""
    entity_type: str
    value: str
    confidence: float
    location: Optional[Dict[str, Any]] = None


class DocumentMetadata(BaseModel):
    """Document metadata stored in Cosmos DB"""
    document_id: str = Field(..., description="Unique document ID")
    blob_path: str = Field(..., description="Path in Blob Storage")
    original_filename: str
    document_type: DocumentType
    status: DocumentStatus = DocumentStatus.UPLOADED
    
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    extracted_text: Optional[str] = None
    extracted_entities: List[ExtractedEntity] = []
    tables: List[Dict[str, Any]] = []
    
    summary: Optional[str] = None
    key_points: List[str] = []
    embeddings: Optional[List[float]] = None
    
    assigned_to: Optional[str] = None
    needs_manual_review: bool = False
    review_notes: Optional[str] = None
    
    created_by: str
    modified_by: Optional[str] = None
    
    class Config:
        use_enum_values = True


class InvoiceData(BaseModel):
    """Structured invoice data"""
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    
    line_items: List[Dict[str, Any]] = []
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    
    math_valid: bool = False
    anomalies: List[str] = []


class ContractData(BaseModel):
    """Structured contract data"""
    parties: List[str] = []
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    auto_renewal: bool = False
    
    payment_terms: Optional[str] = None
    termination_clause: Optional[str] = None
    liability_cap: Optional[str] = None
    
    obligations: List[str] = []
    deliverables: List[str] = []
    
    risk_flags: List[str] = []
