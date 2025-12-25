"""
AIRUN SDK Data Models

Pydantic models for API request/response validation.
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic_core import ValidationError


class BaseResponse(BaseModel):
    """Base model for API responses."""
    success: bool
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime

    def dict(self, **kwargs):
        """Compatibility method for Pydantic v1/v2"""
        try:
            # Try Pydantic v2 method
            return self.model_dump(**kwargs)
        except AttributeError:
            # Fallback for older versions
            return super().dict(**kwargs)


class APIResponse(BaseResponse):
    """Generic API response with data payload."""
    data: Optional[Dict[str, Any]] = None


class ChatOptions(BaseModel):
    """Options for chat requests."""
    # LLM Settings
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1)
    top_p: Optional[float] = Field(None, ge=0, le=1)
    frequency_penalty: Optional[float] = Field(None, ge=-2, le=2)
    presence_penalty: Optional[float] = Field(None, ge=-2, le=2)
    system_prompt: Optional[str] = None

    # Session Settings
    session_id: Optional[str] = None
    type: Optional[str] = "chat"
    history: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None
    first: Optional[bool] = True

    # Feature Flags
    rag: Optional[bool] = False
    web: Optional[bool] = False
    enable_health_analysis: Optional[bool] = False

    # RAG Settings
    rag_search_scope: Optional[str] = "personal"
    rag_scope: Optional[str] = None  # Legacy, maps to rag_search_scope

    # Advanced Options
    reasoning_level: Optional[str] = "medium"
    mentioned_documents: Optional[List[str]] = None
    mentioned_document_content: Optional[str] = None

    # Image Analysis
    image: Optional[str] = None

    # User Context (optional, typically from API key)
    user_id: Optional[str] = None
    username: Optional[str] = None

    # Nested options for frontend compatibility
    enable_rag: Optional[bool] = None  # Maps to options.enableRag
    enable_web_search: Optional[bool] = None  # Maps to options.enableWebSearch
    enable_health_analysis: Optional[bool] = None  # Maps to options.enableHealthAnalysis


class CodeOptions(BaseModel):
    """Options for code generation requests."""
    language: Optional[str] = None
    framework: Optional[str] = None
    style: Optional[str] = None
    include_tests: Optional[bool] = False
    include_docs: Optional[bool] = False


class RAGOptions(BaseModel):
    """Options for RAG search requests."""
    limit: Optional[int] = Field(10, ge=1, le=100)
    include_sources: Optional[bool] = True
    similarity_threshold: Optional[float] = Field(0.7, ge=0, le=1)


class WebSearchOptions(BaseModel):
    """Options for web search requests."""
    limit: Optional[int] = Field(10, ge=1, le=50)
    region: Optional[str] = None
    language: Optional[str] = None
    safe_search: Optional[str] = Field("moderate", pattern="^(strict|moderate|off)$")
    include_images: Optional[bool] = False


class ReportOptions(BaseModel):
    """Options for report generation requests."""
    format: Optional[str] = Field("pdf", pattern="^(pdf|docx|html|markdown)$")
    language: Optional[str] = "en"
    template: Optional[str] = None
    include_toc: Optional[bool] = True
    include_summary: Optional[bool] = True


class MemoryData(BaseModel):
    """Data for memory storage."""
    memory_type: str
    key: str
    value: Union[str, Dict[str, Any], List[Any]]
    user_id: Optional[str] = None


class SessionCreate(BaseModel):
    """Data for session creation."""
    type: Optional[str] = "chat"
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionUpdate(BaseModel):
    """Data for session updates."""
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SystemPrompt(BaseModel):
    """System prompt data."""
    system_prompt: str
    version: Optional[str] = "1.0"


class ApiKeyCreate(BaseModel):
    """Data for API key creation."""
    name: str
    permissions: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class WebhookCreate(BaseModel):
    """Data for webhook creation."""
    url: str
    events: List[str]
    secret: Optional[str] = None
    active: Optional[bool] = True


# Response Models
class ChatResponse(BaseModel):
    """Chat completion response."""
    response: str
    session_id: Optional[str] = None
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


class CodeResponse(BaseModel):
    """Code generation response."""
    code: str
    language: Optional[str] = None
    filename: Optional[str] = None
    explanation: Optional[str] = None


class RAGSearchResponse(BaseModel):
    """RAG search response."""
    results: List[Dict[str, Any]]
    query: Optional[str] = None
    total_results: Optional[int] = None
    search_scope: Optional[str] = None


class WebSearchResponse(BaseModel):
    """Web search response."""
    results: List[Dict[str, Any]]
    query: Optional[str] = None
    total_results: Optional[int] = None
    search_time: Optional[float] = None


class ReportResponse(BaseModel):
    """Report generation response."""
    report_id: Optional[str] = None
    status: Optional[str] = None
    download_url: Optional[str] = None
    format: Optional[str] = None


class MemoryResponse(BaseModel):
    """Memory storage/retrieval response."""
    memories: List[Dict[str, Any]]
    total_count: Optional[int] = None


class SessionResponse(BaseModel):
    """Session data response."""
    session_id: str
    type: Optional[str] = None
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionListResponse(BaseModel):
    """List of sessions response."""
    sessions: List[SessionResponse]
    total_count: Optional[int] = None


class ApiKeyResponse(BaseModel):
    """API key response."""
    key_id: str
    api_key: Optional[str] = None  # Only returned on creation
    name: str
    permissions: Optional[List[str]] = None
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    active: bool


class WebhookResponse(BaseModel):
    """Webhook response."""
    webhook_id: int
    url: str
    events: List[str]
    active: bool
    created_at: datetime
    last_triggered: Optional[datetime] = None


class UserResponse(BaseModel):
    """User information response."""
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class StatusResponse(BaseModel):
    """Service status response."""
    status: str
    version: Optional[str] = None
    services: Optional[Dict[str, str]] = None
    uptime: Optional[float] = None