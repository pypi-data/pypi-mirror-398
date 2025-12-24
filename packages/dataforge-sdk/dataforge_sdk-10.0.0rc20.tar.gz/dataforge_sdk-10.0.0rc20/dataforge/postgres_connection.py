import logging
import sys
import psycopg2
from .utils import _setup_logger


class PostgresConnection:
    logger: logging.Logger
    def __init__(self, connection_string: str, logger: logging.Logger | None = None):
        try:
            if logger:
                self.logger = logger
            else:
                self.logger = _setup_logger("PG")
            self.connect(connection_string)

        except Exception as e:
            logger.error(f"Error connecting to Postgres: {e}")
            raise
            # sys.exit(1)

    def sql(self, query: str, params=None, fetch=True):
        try:
            # Execute a query
            cur = self.conn.cursor()
            cur.execute(query, params)
            # Retrieve query results
            res = cur.fetchone() if fetch else [None]
            cur.close()
            return res[0]
        except Exception as e:
            self.logger.error(f"Error executing query {query}({params}) on Postgres: {e}")
            # sys.exit(1)
            raise

    def connect(self, connection_string: str):
        # Execute a query
        try:
            self.conn = psycopg2.connect(connection_string.removeprefix('jdbc:'))
            self.conn.set_session(autocommit=True)
            self.sql("select 1")  # execute test query
            # Change connection
        except Exception as e:
            self.logger.error(f"Error connecting to Postgres database or insufficient permissions. Details: {e}")
            # sys.exit(1)
            raise

    def close(self ):
        self.conn.close()



