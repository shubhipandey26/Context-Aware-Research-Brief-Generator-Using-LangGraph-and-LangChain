
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

class ResearchStep(BaseModel):
    step_id: str
    description: str
    rationale: Optional[str] = None
    estimated_time_minutes: Optional[int] = Field(default=None, ge=0)

class ResearchPlan(BaseModel):
    steps: List[ResearchStep]

class SourceSummary(BaseModel):
    source_id: str
    title: str
    url: Optional[HttpUrl] = None
    summary: str
    key_findings: List[str] = Field(default_factory=list)
    published_date: Optional[str] = None  # keep string to avoid tz parsing issues
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

class FinalBrief(BaseModel):
    brief_id: str
    topic: str
    generated_at: datetime
    depth: int
    user_id: str
    summary: str
    planning_steps: List[ResearchStep]
    source_summaries: List[SourceSummary]
    synthesized_insights: List[str]
    references: List[HttpUrl]
    provenance: Optional[dict] = None
    token_usage: Optional[dict] = None
    latency_ms: Optional[int] = None
