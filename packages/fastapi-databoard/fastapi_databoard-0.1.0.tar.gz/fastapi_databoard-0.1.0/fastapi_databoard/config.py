# fastapi_databoard/config.py
from typing import Optional
from pydantic import BaseModel


class DataBoardConfig(BaseModel):
    """Configuration for DataBoard"""
    
    title: str = "DataBoard"
    description: str = "Database Administration Dashboard"
    mount_path: str = "/databoard"
    page_size: int = 50
    max_page_size: int = 1000
    enable_query_execution: bool = True
    enable_edit: bool = True
    enable_delete: bool = True
    enable_create: bool = True
    theme: str = "light"  # light or dark
    secret_key: Optional[str] = None  # For future authentication
    allowed_tables: Optional[list[str]] = None  # Restrict to specific tables
    excluded_tables: Optional[list[str]] = None  # Exclude specific tables
    
    class Config:
        arbitrary_types_allowed = True