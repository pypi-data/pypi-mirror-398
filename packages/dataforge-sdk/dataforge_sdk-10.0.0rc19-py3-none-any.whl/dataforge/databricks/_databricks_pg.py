"""Postgres utilities for data operations.

This module provides functions to execute SQL queries against a Postgres database
using Spark JDBC for reads and a direct write connection for write operations.
"""
from __future__ import annotations
from dataforge.postgres_connection import PostgresConnection


class DataBricksPg:


    def __init__(self):
        from pyspark.dbutils import DBUtils
        from pyspark.sql import SparkSession, DataFrame
        from .postgres_connection import PostgresConnection

        self.spark = SparkSession.builder.getOrCreate()
        self.dbutils = DBUtils(spark)
        self.pg_connection_string_read = dbutils.secrets.get("sparky", "pg_read")

    def update(self,query: str):
        """Execute an update SQL query on the DataForge metastore Postgres database.

        Args:
            query (str): SQL query string to execute.

        Returns:
            None

        Raises:
            Exception: If write connection cannot be established or SQL execution fails.
        """
        pg = self._get_pg_write_connection()
        pg.sql(query, fetch=False)

    def execute(self,query: str):
        """Alias for update() to execute write SQL queries.

        Args:
            query (str): SQL query string to execute.

        Returns:
            None
        """
        self.update(query)

    def select(self,query: str) -> "DataFrame":
        """Execute a SELECT SQL query on the DataForge metastore Postgres database and return a DataFrame with results.

        Args:
            query (str): SQL SELECT query string.

        Returns:
            DataFrame: Spark DataFrame containing query results.

        Raises:
            Exception: If Spark fails to load data or connection issues.
        """
        return self.spark.read.format("jdbc") \
            .option("url", self.pg_connection_string_read) \
            .option("query", query) \
            .load()

    def pull(self,source_id: int):
        """Trigger new ingestion (pull data) on DataForge source for a given source ID.

        Args:
            source_id (int): Identifier for the source to pull.

        Returns:
            None

        Raises:
            Exception: If write connection cannot be established or SQL execution fails.
        """
        pg = self._get_pg_write_connection()
        pg.sql("SELECT meta.svc_pull_source(%s, %s)", (source_id,'sdk'), fetch=False)


    def _get_pg_write_connection(self) -> PostgresConnection:
        """Internal method to retrieve a PostgresConnection for write operations using secured secrets.

        Returns:
            PostgresConnection: Connection object for executing write queries.

        Raises:
            Exception: If the 'pg_write' secret is not defined in the 'sparky' scope.
        """
        secrets = self.dbutils.secrets.list("sparky")
        if any(secret.key == "pg_write" for secret in secrets):
            conn_string = self.dbutils.secrets.get("sparky", "pg_write")
            return PostgresConnection(conn_string + "&application_name=sdk-pg")
        else:
            raise Exception("pg_write secret is not defined in sparky scope")