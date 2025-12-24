from __future__ import annotations
import json
import re
from datetime import datetime
from typing import Callable
from dataforge.databricks._databricks_base_session import _Databricks_Base_Session


class _Databricks_Ingestion_Session(_Databricks_Base_Session):
    """Base session class for Databricks platform.
    Class should not be instantiated by user directly: use process-specific Session classes instead
    Adds Spark session, DBUtilsto Base_Session
    """

    def __init__(self):
        super().__init__()

    def ingest(self,df: pyspark.sql.DataFrame | Callable[[], pyspark.sql.DataFrame] | None = None):
        """Ingest the provided DataFrame into the DataForge and update input record.

        Writes the DataFrame to raw Parquet file,
        updates the input record with status, file size, record count, and notifies
        the Core API of process completion. On failure, updates logs and flags the input and process
        records as failed.

        Args:
            df (Callable[[], DataFrame] | DataFrame): parameterless def that you defined, returning the Spark DataFrame to ingest (recommended),
                or spark DataFrame
        """
        try:
            if not self._is_open:
                raise Exception("Session is closed")
            if df is None:
                status = "Z"
                row_count = 0
                file_size = 0
            else:
                if callable(df):
                    result_df = df()  # call it to get the DataFrame
                else:
                    result_df = df
                dest_file_path = f"{self._systemConfiguration.datalakePath}/source_{self.process.sourceId}/parsed/parsed_input_{self.process.inputId}"
                file_size, row_count = self._write_parsed_data(result_df, dest_file_path)
                status = "P" if row_count > 0 else "Z"
            input_update_json = {
                "ingestion_status_code": status,
                "extract_datetime": datetime.now().isoformat(),
                "file_size": file_size,
                "process_id": self.process.processId,
                "input_id": self.process.inputId,
                "record_counts": {"Total": row_count}
            }

            self._pg.sql("SELECT meta.prc_iw_in_update_input_record(%s)",
                         (json.dumps(input_update_json),), fetch=False)
            self.logger.info("Ingestion completed successfully")

        except Exception as e:
            self._log_fail(e)
            failure_update_json = {
                "process_id": self.process.processId,
                "ingestion_status_code": "F"
            }
            self._pg.sql("SELECT meta.prc_iw_in_update_input_record(%s)",
                         (json.dumps(failure_update_json),), fetch=False)
        finally:
            self._core_api_call(f"process-complete/{self.process.processId}")
            self.close()


