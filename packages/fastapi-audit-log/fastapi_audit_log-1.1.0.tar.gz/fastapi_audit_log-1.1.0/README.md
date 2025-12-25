# FastAPI Audit Log

`fastapi-audit-log` is a middleware package for **FastAPI** that automatically logs API requests and responses to a database. It supports **MySQL, PostgreSQL, Oracle**, and **SQLite**.

## Features

- Logs requests and responses for POST, PUT, PATCH, DELETE methods
- Skips files in multipart/form-data
- Background DB writes for non-blocking performance
- Automatic cleanup of old logs (configurable retention)
- Exclude specific paths (e.g., `/health`, `/users`)
- Works with MySQL, PostgreSQL, Oracle, SQLite

## Installation

```bash
# Install main package
pip install fastapi-audit-log

# Optional database drivers
pip install fastapi-audit-log[mysql]      # MySQL
pip install fastapi-audit-log[postgres]   # PostgreSQL
pip install fastapi-audit-log[oracle]     # Oracle
