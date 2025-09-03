"""
Pydantic models for the multi-organizational RAG system
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class CompanyCreate(BaseModel):
    company_id: str = Field(..., description="Unique company identifier")
    name: str = Field(..., description="Company name")
    description: Optional[str] = None

class CompanyInfo(BaseModel):
    company_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    file_count: int = 0
    last_updated: Optional[datetime] = None

class FileUploadRequest(BaseModel):
    company_id: str = Field(..., description="Company ID for file isolation")

class FileInfo(BaseModel):
    file_id: str
    filename: str
    original_filename: str
    company_id: str
    size: int
    extension: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class QueryRequest(BaseModel):
    query: str = Field(..., description="The question to ask")
    company_id: str = Field(..., description="Company ID for data isolation")
    file_id: Optional[str] = Field(None, description="Optional file ID to query specific document")
    session_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []
    max_results: Optional[int] = 5

class CompanyQueryRequest(BaseModel):
    query: str = Field(..., description="The question to ask")
    company_id: str = Field(..., description="Company ID for data isolation")
    session_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []
    max_results: Optional[int] = 5

class FileChatRequest(BaseModel):
    query: str = Field(..., description="The question to ask")
    file_id: str = Field(..., description="File ID to chat with")
    session_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []
    max_results: Optional[int] = 5

class QueryResponse(BaseModel):
    response: str
    company_id: str
    session_id: str
    timestamp: datetime
    sources: Optional[List[str]] = []
    file_info: Optional[Dict[str, str]] = None  # For file-specific queries

class BuildStatus(BaseModel):
    status: str  # "idle", "building", "completed", "error"
    message: str
    company_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    progress: Optional[float] = None  # 0.0 to 1.0

class ChatMessage(BaseModel):
    message: str
    sender: str  # "user" or "bot"
    timestamp: datetime
    session_id: str
    company_id: str

class HealthCheck(BaseModel):
    status: str
    version: str
    rag_initialized: bool
    companies_loaded: int
    api_keys_available: int
    timestamp: datetime

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime

# Enums
class FileStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"

class BuildStatusEnum(str, Enum):
    IDLE = "idle"
    BUILDING = "building"
    COMPLETED = "completed"
    ERROR = "error"
