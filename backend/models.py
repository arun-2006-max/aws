"""Pydantic models for request/response validation."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# ── Auth ──────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str = ""  # Optional for demo

class LoginResponse(BaseModel):
    token: str
    user_id: str
    email: str


# ── Chat ──────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model: str
    sources: List[Dict[str, Any]] = []
    latency_ms: int
    cached: bool = False


# ── Debug ─────────────────────────────────────────────────────────────
class DebugRequest(BaseModel):
    code: str
    error: str
    language: Optional[str] = "python"
    session_id: Optional[str] = None

class DebugResponse(BaseModel):
    debug_analysis: str
    model: str
    latency_ms: int
    sources: List[Dict[str, Any]] = []


# ── Learning Analysis ─────────────────────────────────────────────────
class LearningAnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    model: str
    interactions_analysed: int


# ── Progress ──────────────────────────────────────────────────────────
class ProgressResponse(BaseModel):
    user_id: str
    progress: Dict[str, Any]
    knowledge_gaps: List[Dict[str, Any]]
    interaction_stats: Dict[str, Any]


# ── Feedback ──────────────────────────────────────────────────────────
class FeedbackRequest(BaseModel):
    interaction_timestamp: int
    rating: int  # 1 or -1
