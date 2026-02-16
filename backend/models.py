from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class Fact(BaseModel):
    id: str = Field(..., description="Unique fact ID, e.g., FACT_001")
    symptom: str
    cause: str
    treatment: str
    precaution: str


class AskRequest(BaseModel):
    query: str
    top_k: Optional[int] = Field(default=4, ge=1, le=8)


class AskResponse(BaseModel):
    answer: str
    facts_used: List[str]
    retrieved_facts: List[Fact]
    verified: bool
    tokens_used: Dict[str, int]


class VerifyRequest(BaseModel):
    answer: str
    facts_used: List[str]


class VerifyResponse(BaseModel):
    verified: bool
    answer: str