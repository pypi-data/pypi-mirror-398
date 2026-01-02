# FastAPI DataBoard

A beautiful, intuitive database administration dashboard for FastAPI applications. Similar to Django Admin but designed specifically for FastAPI with support for both synchronous and asynchronous SQLAlchemy engines.



## Features

* ✨ **Auto-Discovery**: Automatically discovers all tables in your database.
* 📊 **Beautiful UI**: Clean, modern interface with a responsive layout.
* 🔍 **Query Console**: Execute custom SQL queries (SELECT, UPDATE, DELETE) directly from the browser.
* ✏️ **Full CRUD**: Create, Read, Update, and Delete records via intuitive modals.
* 📄 **Smart Pagination**: Built-in pagination handled at the database level.
* 🔄 **Dual Support**: Fully compatible with `create_engine` (Sync) and `create_async_engine` (Async).

---

## Installation

```bash
pip install fastapi-databoard

```

**For PostgreSQL support:**

```bash
# For Async (asyncpg)
pip install fastapi-databoard[async] asyncpg

# For Sync (psycopg2)
pip install psycopg2-binary

```

---

## Quick Start Examples

DataBoard adapts to your engine type automatically.

### Asynchronous Setup (main.py)

Ideal for modern FastAPI apps using `asyncpg`.

```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from fastapi_databoard import DataBoard, DataBoardConfig

app = FastAPI()

DATABASE_URL = "postgresql+asyncpg://postgres:12345@localhost:5432/postgres"
engine = create_async_engine(DATABASE_URL)

config = DataBoardConfig(
    title="Databoard",
    mount_path="/databoard",
    page_size=50,
    enable_query_execution=True,
    enable_edit=True,
    enable_delete=True,
    enable_create=True,
)

databoard = DataBoard(engine=engine, config=config)
databoard.mount(app)

```

### Synchronous Setup (main2.py)

Ideal for standard applications using `psycopg2`.

```python
from fastapi import FastAPI
from sqlalchemy import create_engine
from fastapi_databoard import DataBoard, DataBoardConfig

app = FastAPI()

DATABASE_URL = "postgresql+psycopg2://postgres:12345@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)

config = DataBoardConfig(
    title="Databoard",
    mount_path="/databoard",
    page_size=50,
    enable_query_execution=True,
    enable_edit=True,
    enable_delete=True,
    enable_create=True,
)

databoard = DataBoard(engine=engine, config=config)
databoard.mount(app)

```

---

## Configuration Reference

You can customize the dashboard behavior using the `DataBoardConfig` class:

| Property | Default | Description |
| --- | --- | --- |
| **title** | `"DataBoard"` | Title shown in sidebar and browser tab. |
| **mount_path** | `"/databoard"` | The URL path to access the UI. |
| **page_size** | `50` | Number of records displayed per page. |
| **enable_query_execution** | `True` | Shows the SQL console for raw queries. |
| **enable_edit** | `True` | Allows editing existing table records. |
| **enable_delete** | `True` | Allows deleting records from the UI. |
| **enable_create** | `True` | Shows the "+ New Record" button. |

---

## Usage Guide

### Browsing Tables

Select a table from the sidebar. The dashboard fetches the schema and data dynamically.

### Executing Raw SQL

Use the **Query Console** at the top.

* **SELECT**: Results will populate the main data table. To keep "Edit" and "Delete" icons active, ensure you include the table's Primary Key in your column selection.
* **INSERT/UPDATE/DELETE**: The UI will report the number of affected rows.

### Record Management

* Click the **Pencil Icon** (edit) to open the update modal.
* Click the **Trash Icon** (delete) to remove a row.
* Click **+ New Record** to manually insert data.

---

## Security

> [!WARNING]
> **Security Risk**: DataBoard provides full access to your database. In production environments, always protect the mount path using FastAPI Dependencies (e.g., OAuth2, API Keys, or Basic Auth).

---
