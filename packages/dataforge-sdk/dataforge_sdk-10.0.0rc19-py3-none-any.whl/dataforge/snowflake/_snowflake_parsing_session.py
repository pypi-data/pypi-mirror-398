from __future__ import annotations
from typing import Callable
from ._snowflake_base_session import _Snowflake_Base_Session


class _Snowflake_Parsing_Session(_Snowflake_Base_Session):
    """Implements run method for Databricks.
    """


    def run(self,df: snowflake.snowpark.dataframe.DataFrame | Callable[[], snowflake.snowpark.dataframeDataFrame] | None = None):
        """Save parsed file from the provided DataFrame, and upload it into the DataForge data lake.

        Writes the DataFrame to parsed Parquet file,
        updates the input record with status, file size, record count, and notifies
        the Core API of process completion. On failure, updates logs and flags the input and process
        records as failed.

        Args:
            df (DataFrame): parameterless def that you defined, returning the Spark DataFrame containing parsed file data (recommended),
                or spark DataFrame
        """
        try:
            self._write_input_table(df)

        except Exception as e:
            self._log_fail(e)
            if self.process.startProcessFlag:
                self._end_process("F")

