# """
# Models package for AI Study Assistant
# Database models and Pydantic schemas for API validation
# """

# # Future expansion - currently empty but ready for:
# # - Document models
# # - User models  
# # - Chat history models
# # - Pydantic schemas

# from typing import List, Optional, Dict, Any
# from pydantic import BaseModel
# from datetime import datetime

# class DocumentChunk(BaseModel):
#     content: str
#     chunk_id: str
#     source: str
#     metadata: Optional[Dict[str, Any]] = {}

# class UploadResponse(BaseModel):
#     success: bool
#     doc_id: str
#     message: str

# class AskResponse(BaseModel):
#     success: bool
#     question: str
#     answer: str
#     context_sources: List[str]

# class DocumentInfo(BaseModel):
#     doc_id: str
#     filename: str
#     chunks: int
#     created_at: Optional[datetime] = None

# __all__ = ["DocumentChunk", "UploadResponse", "AskResponse", "DocumentInfo"]
"""
Models package for AI Study Assistant
Pydantic schemas for API request/response validation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    content: str
    chunk_id: str
    source: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    success: bool
    doc_id: str
    message: str
    chunk_count: int = 0


class AskRequest(BaseModel):
    question: str
    user_id: str = "default_user"


class AskResponse(BaseModel):
    success: bool
    question: str
    answer: str
    context_sources: List[str] = Field(default_factory=list)


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    chunks: int
    created_at: Optional[datetime] = None


class DocumentListResponse(BaseModel):
    success: bool
    documents: List[DocumentInfo] = Field(default_factory=list)


class StatsResponse(BaseModel):
    success: bool
    total_documents: int
    total_chunks: int
    avg_chunks_per_doc: float


__all__ = [
    "DocumentChunk",
    "UploadResponse",
    "AskRequest",
    "AskResponse",
    "DocumentInfo",
    "DocumentListResponse",
    "StatsResponse",
]
