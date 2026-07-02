# File: models/schemas.py
# Why: Stable API contracts keep the surface area predictable during alpha.
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., description="Developer question")
    top_k: int = Field(5, ge=1, le=10)


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]


class FeedbackRequest(BaseModel):
    query: str
    answer: str
    helpful: bool
    notes: Optional[str] = None
