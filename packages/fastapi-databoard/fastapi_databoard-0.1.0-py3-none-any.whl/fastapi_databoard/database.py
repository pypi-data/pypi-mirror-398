# fastapi_databoard/database.py
from typing import Union, List, Dict, Any
from sqlalchemy import inspect, text, MetaData, Table, select, update, delete as sql_delete, func, insert, Boolean, Integer, Float, Numeric, DateTime, Date
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import json
from datetime import datetime, date
from decimal import Decimal


class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, engine: Union[Engine, AsyncEngine], is_async: bool):
        self.engine = engine
        self.is_async = is_async
        self.metadata = MetaData()
        self._table_cache = {}
        
    def _get_table(self, table_name: str) -> Table:
        """Get or create a table object with caching"""
        if table_name not in self._table_cache:
            autoload_target = (
                getattr(self.engine, "sync_engine", self.engine)
                if self.is_async else self.engine
            )
            self._table_cache[table_name] = Table(
                table_name,
                self.metadata,
                autoload_with=autoload_target,
                extend_existing=True
            )
        return self._table_cache[table_name]
        
    async def get_tables(self) -> List[str]:
        """Get list of all tables in the database"""
        if self.is_async:
            async with self.engine.connect() as conn:
                result = await conn.run_sync(
                    lambda sync_conn: inspect(sync_conn).get_table_names()
                )
                return sorted(result)
        else:
            with self.engine.connect() as conn:
                return sorted(inspect(conn).get_table_names())
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a table"""
        if self.is_async:
            async with self.engine.connect() as conn:
                def get_schema(sync_conn):
                    inspector = inspect(sync_conn)
                    columns = inspector.get_columns(table_name)
                    pk = inspector.get_pk_constraint(table_name)
                    
                    # Convert column info to serializable format
                    serialized_columns = []
                    for col in columns:
                        serialized_columns.append({
                            'name': col['name'],
                            'type': str(col['type']),
                            'nullable': col['nullable'],
                            'default': str(col['default']) if col['default'] is not None else None,
                            'autoincrement': col.get('autoincrement', False),
                        })
                    
                    return {
                        "columns": serialized_columns,
                        "primary_key": pk.get("constrained_columns", [])
                    }
                return await conn.run_sync(get_schema)
        else:
            with self.engine.connect() as conn:
                inspector = inspect(conn)
                columns = inspector.get_columns(table_name)
                pk = inspector.get_pk_constraint(table_name)
                
                # Convert column info to serializable format
                serialized_columns = []
                for col in columns:
                    serialized_columns.append({
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable'],
                        'default': str(col['default']) if col['default'] is not None else None,
                        'autoincrement': col.get('autoincrement', False),
                    })
                
                return {
                    "columns": serialized_columns,
                    "primary_key": pk.get("constrained_columns", [])
                }
    
    async def get_table_data(
        self, 
        table_name: str, 
        page: int = 1, 
        page_size: int = 50
    ) -> Dict[str, Any]:
        """Get paginated data from a table"""
        offset = (page - 1) * page_size
        
        if self.is_async:
            async with self.engine.connect() as conn:
                def fetch(sync_conn):
                    table = Table(table_name, self.metadata, autoload_with=sync_conn, extend_existing=True)
                    count_q = select(func.count()).select_from(table)
                    data_q = select(table).offset(offset).limit(page_size)
                    total = sync_conn.scalar(count_q)
                    result = sync_conn.execute(data_q)
                    rows = result.fetchall()
                    keys = result.keys()
                    data = []
                    for row in rows:
                        row_dict = {}
                        for col in keys:
                            row_dict[col] = self._serialize_value(row._mapping[col])
                        data.append(row_dict)
                    return total, data
                total, data = await conn.run_sync(fetch)
        else:
            with self.engine.connect() as conn:
                table = self._get_table(table_name)
                count_query = select(func.count()).select_from(table)
                data_query = select(table).offset(offset).limit(page_size)
                total = conn.scalar(count_query)
                result = conn.execute(data_query)
                rows = result.fetchall()
                
                data = []
                for row in rows:
                    row_dict = {}
                    for col in result.keys():
                        row_dict[col] = self._serialize_value(row._mapping[col])
                    data.append(row_dict)
        
        return {
            "data": data,
            "total": total or 0,
            "page": page,
            "page_size": page_size,
            "total_pages": ((total or 0) + page_size - 1) // page_size if total else 0
        }
    
    async def execute_query(
        self, 
        query_string: str, 
        query_type: str = "sql"
    ) -> Dict[str, Any]:
        """Execute a custom query"""
        try:
            query = text(query_string)
            
            if self.is_async:
                async with self.engine.connect() as conn:
                    result = await conn.execute(query)
                    
                    # Check if it's a SELECT query
                    if query_string.strip().upper().startswith("SELECT"):
                        rows = result.fetchall()
                        data = []
                        for row in rows:
                            row_dict = {}
                            for col in result.keys():
                                row_dict[col] = self._serialize_value(row._mapping[col])
                            data.append(row_dict)
                        
                        return {
                            "success": True,
                            "data": data,
                            "row_count": len(data)
                        }
                    else:
                        await conn.commit()
                        return {
                            "success": True,
                            "message": "Query executed successfully",
                            "rows_affected": result.rowcount
                        }
            else:
                with self.engine.connect() as conn:
                    result = conn.execute(query)
                    
                    if query_string.strip().upper().startswith("SELECT"):
                        rows = result.fetchall()
                        data = []
                        for row in rows:
                            row_dict = {}
                            for col in result.keys():
                                row_dict[col] = self._serialize_value(row._mapping[col])
                            data.append(row_dict)
                        
                        return {
                            "success": True,
                            "data": data,
                            "row_count": len(data)
                        }
                    else:
                        conn.commit()
                        return {
                            "success": True,
                            "message": "Query executed successfully",
                            "rows_affected": result.rowcount
                        }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_record(
        self, 
        table_name: str, 
        primary_key: Dict[str, Any], 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a record"""
        try:
            if self.is_async:
                async with self.engine.connect() as conn:
                    def do_update(sync_conn):
                        table = Table(table_name, self.metadata, autoload_with=sync_conn, extend_existing=True)
                        where_clause = None
                        for key, value in primary_key.items():
                            col = table.c[key]
                            condition = col == self._convert_for_column(col, value)
                            where_clause = condition if where_clause is None else where_clause & condition
                        processed_data = {}
                        for key, value in data.items():
                            col = table.c[key]
                            processed_data[key] = self._convert_for_column(col, value)
                        stmt = update(table).where(where_clause).values(**processed_data)
                        result = sync_conn.execute(stmt)
                        sync_conn.commit()
                        return result.rowcount
                    rows = await conn.run_sync(do_update)
                    return {"success": True, "rows_affected": rows}
            else:
                with self.engine.connect() as conn:
                    table = self._get_table(table_name)
                    where_clause = None
                    for key, value in primary_key.items():
                        col = table.c[key]
                        condition = col == self._convert_for_column(col, value)
                        where_clause = condition if where_clause is None else where_clause & condition
                    processed_data = {}
                    for key, value in data.items():
                        col = table.c[key]
                        processed_data[key] = self._convert_for_column(col, value)
                    stmt = update(table).where(where_clause).values(**processed_data)
                    result = conn.execute(stmt)
                    conn.commit()
                    return {"success": True, "rows_affected": result.rowcount}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def delete_record(
        self, 
        table_name: str, 
        primary_key: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delete a record"""
        try:
            if self.is_async:
                async with self.engine.connect() as conn:
                    def do_delete(sync_conn):
                        table = Table(table_name, self.metadata, autoload_with=sync_conn, extend_existing=True)
                        where_clause = None
                        for key, value in primary_key.items():
                            col = table.c[key]
                            condition = col == self._convert_for_column(col, value)
                            where_clause = condition if where_clause is None else where_clause & condition
                        stmt = sql_delete(table).where(where_clause)
                        result = sync_conn.execute(stmt)
                        sync_conn.commit()
                        return result.rowcount
                    rows = await conn.run_sync(do_delete)
                    return {"success": True, "rows_affected": rows}
            else:
                with self.engine.connect() as conn:
                    table = self._get_table(table_name)
                    where_clause = None
                    for key, value in primary_key.items():
                        col = table.c[key]
                        condition = col == self._convert_for_column(col, value)
                        where_clause = condition if where_clause is None else where_clause & condition
                    stmt = sql_delete(table).where(where_clause)
                    result = conn.execute(stmt)
                    conn.commit()
                    return {"success": True, "rows_affected": result.rowcount}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_record(
        self, 
        table_name: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new record"""
        # Convert data types
        processed_data = {}
        for key, value in data.items():
            if value == '' or value == 'null':
                processed_data[key] = None
            else:
                processed_data[key] = value
        
        try:
            if self.is_async:
                async with self.engine.connect() as conn:
                    def do_insert(sync_conn):
                        table = Table(table_name, self.metadata, autoload_with=sync_conn, extend_existing=True)
                        values = {k: self._convert_for_column(table.c[k], v) for k, v in processed_data.items()}
                        stmt = insert(table).values(**values)
                        result = sync_conn.execute(stmt)
                        sync_conn.commit()
                        inserted_pk = result.inserted_primary_key if hasattr(result, 'inserted_primary_key') else None
                        return list(inserted_pk) if inserted_pk else None
                    inserted_id = await conn.run_sync(do_insert)
                    return {"success": True, "inserted_id": inserted_id, "message": "Record created successfully"}
            else:
                with self.engine.connect() as conn:
                    table = self._get_table(table_name)
                    values = {k: self._convert_for_column(table.c[k], v) for k, v in processed_data.items()}
                    stmt = insert(table).values(**values)
                    result = conn.execute(stmt)
                    conn.commit()
                    inserted_pk = result.inserted_primary_key if hasattr(result, 'inserted_primary_key') else None
                    return {
                        "success": True,
                        "inserted_id": list(inserted_pk) if inserted_pk else None,
                        "message": "Record created successfully"
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _serialize_value(self, value):
        """Serialize value for JSON"""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        return str(value)

    def _convert_for_column(self, column, value):
        if value == '' or value == 'null':
            return None
        if isinstance(column.type, Boolean):
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                v = value.lower()
                if v in ('true', '1', 'yes', 'y', 't'):
                    return True
                if v in ('false', '0', 'no', 'n', 'f'):
                    return False
            return value
        if isinstance(column.type, Integer):
            if isinstance(value, str):
                try:
                    return int(value)
                except Exception:
                    return value
            return value
        if isinstance(column.type, (Float, Numeric)):
            if isinstance(value, str):
                try:
                    return float(value)
                except Exception:
                    return value
            return value
        if isinstance(column.type, DateTime):
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value)
                except Exception:
                    return value
            return value
        if isinstance(column.type, Date):
            if isinstance(value, str):
                try:
                    return date.fromisoformat(value)
                except Exception:
                    return value
            return value
        return value