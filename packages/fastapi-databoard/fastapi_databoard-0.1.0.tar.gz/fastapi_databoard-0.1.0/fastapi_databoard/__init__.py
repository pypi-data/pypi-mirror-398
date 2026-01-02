# fastapi_databoard/__init__.py
"""
FastAPI DataBoard - A database administration dashboard for FastAPI applications
"""

__version__ = "0.1.0"

from .databoard import DataBoard
from .config import DataBoardConfig

__all__ = ["DataBoard", "DataBoardConfig"]