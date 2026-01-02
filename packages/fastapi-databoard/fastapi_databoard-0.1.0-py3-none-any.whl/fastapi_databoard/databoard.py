# fastapi_databoard/databoard.py
from typing import Union, Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text, MetaData, Table, select, update, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
import os
from pathlib import Path

from .config import DataBoardConfig
from .database import DatabaseManager
from .models import QueryRequest, RecordUpdate, RecordDelete


class DataBoard:
    """Main DataBoard class for FastAPI database administration"""
    
    def __init__(
        self,
        engine: Union[Engine, AsyncEngine],
        config: Optional[DataBoardConfig] = None
    ):
        self.engine = engine
        self.config = config or DataBoardConfig()
        self.is_async = hasattr(engine, 'begin')
        self.db_manager = DatabaseManager(engine, self.is_async)
        
        # Setup templates
        template_dir = Path(__file__).parent / "templates"
        self.templates = Jinja2Templates(directory=str(template_dir))
        
    def mount(self, app: FastAPI):
        """Mount DataBoard to FastAPI application"""
        
        # Static files
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            app.mount(
                f"{self.config.mount_path}/static",
                StaticFiles(directory=str(static_dir)),
                name="databoard_static"
            )
        
        # Routes
        @app.get(self.config.mount_path, response_class=HTMLResponse)
        async def databoard_home(request: Request):
            """Main dashboard page"""
            tables = await self.db_manager.get_tables()
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "config": self.config,
                    "tables": tables,
                    "mount_path": self.config.mount_path
                }
            )
        
        @app.get(f"{self.config.mount_path}/api/tables")
        async def get_tables():
            """Get list of all tables"""
            tables = await self.db_manager.get_tables()
            return {"tables": tables}
        
        @app.get(f"{self.config.mount_path}/api/table/{{table_name}}/schema")
        async def get_table_schema(table_name: str):
            """Get schema information for a table"""
            schema = await self.db_manager.get_table_schema(table_name)
            return {"schema": schema}
        
        @app.get(f"{self.config.mount_path}/api/table/{{table_name}}/data")
        async def get_table_data(
            table_name: str,
            page: int = Query(1, ge=1),
            page_size: int = Query(50, ge=1, le=1000)
        ):
            """Get paginated data from a table"""
            print("heree")
            data = await self.db_manager.get_table_data(
                table_name, page, page_size
            )
            return data
        
        @app.post(f"{self.config.mount_path}/api/query")
        async def execute_query(query_request: QueryRequest):
            """Execute a custom SQL or SQLAlchemy query"""
            if not self.config.enable_query_execution:
                raise HTTPException(403, "Query execution is disabled")
            
            result = await self.db_manager.execute_query(
                query_request.query,
                query_request.query_type
            )
            return result
        
        @app.put(f"{self.config.mount_path}/api/table/{{table_name}}/record")
        async def update_record(table_name: str, update_data: RecordUpdate):
            """Update a record in a table"""
            if not self.config.enable_edit:
                raise HTTPException(403, "Edit is disabled")
            
            result = await self.db_manager.update_record(
                table_name,
                update_data.primary_key,
                update_data.data
            )
            return result
        
        @app.delete(f"{self.config.mount_path}/api/table/{{table_name}}/record")
        async def delete_record(table_name: str, delete_data: RecordDelete):
            """Delete a record from a table"""
            if not self.config.enable_delete:
                raise HTTPException(403, "Delete is disabled")
            
            result = await self.db_manager.delete_record(
                table_name,
                delete_data.primary_key
            )
            return result
        
        @app.post(f"{self.config.mount_path}/api/table/{{table_name}}/record")
        async def create_record(table_name: str, record_data: dict):
            """Create a new record in a table"""
            if not self.config.enable_create:
                raise HTTPException(403, "Create is disabled")
            
            try:
                result = await self.db_manager.create_record(
                    table_name,
                    record_data
                )
                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }