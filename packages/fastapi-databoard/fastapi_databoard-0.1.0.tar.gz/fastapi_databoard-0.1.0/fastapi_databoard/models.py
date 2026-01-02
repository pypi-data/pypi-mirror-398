# fastapi_databoard/models.py
from typing import Dict, Any, Literal
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for query execution"""
    query: str
    query_type: Literal["sql", "alchemy"] = "sql"


class RecordUpdate(BaseModel):
    """Request model for updating a record"""
    primary_key: Dict[str, Any]
    data: Dict[str, Any]


class RecordDelete(BaseModel):
    """Request model for deleting a record"""
    primary_key: Dict[str, Any]