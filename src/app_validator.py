from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str
    error: Optional[str]