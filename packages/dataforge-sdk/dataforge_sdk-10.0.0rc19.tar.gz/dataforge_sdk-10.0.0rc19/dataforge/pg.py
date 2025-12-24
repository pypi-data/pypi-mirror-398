"""Postgres utilities for data operations.

This module provides functions to execute SQL queries against a Postgres database
using Spark JDBC for reads and a direct write connection for write operations.
"""
from dataforge._session import _platform

if _platform=='databricks':
    from dataforge.databricks._databricks_pg import DataBricksPg
    pg = DataBricksPg()
