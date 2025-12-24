from __future__ import annotations
from typing import Callable
from ._databricks_base_session import _Databricks_Base_Session


class _Databricks_Parsing_Session(_Databricks_Base_Session):
    """Implements run method for Databricks.
    """


    def run(self,df: pyspark.sql.DataFrame | Callable[[], pyspark.sql.DataFrame] | None = None):
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
            if not self._is_open:
                raise Exception("Session is closed")
            if callable(df):
                result_df = df()  # call it to get the DataFrame
            else:
                result_df = df

            if result_df is None or result_df.isEmpty():
                file_size, row_count = (0, 0)
            else:
                dest_file_path = f"{self._systemConfiguration.datalakePath}/source_{self.process.sourceId}/parsed/parsed_input_{self.process.inputId}"
                file_size, row_count = self._write_parsed_data(result_df, dest_file_path)
            input_update_json = {
                "file_size": file_size,
                "input_id": self.process.inputId,
                "record_counts": {"Total": row_count}
            }
            self._end_process('P' if row_count > 0 else 'Z', input_update_json)

        except Exception as e:
            self._log_fail(e)
            self._end_process("F")

