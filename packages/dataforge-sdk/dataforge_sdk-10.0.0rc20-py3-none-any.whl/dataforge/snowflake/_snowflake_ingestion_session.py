from __future__ import annotations
import json
from typing import Callable
from dataforge.snowflake._snowflake_base_session import _Snowflake_Base_Session


class _Snowflake_Ingestion_Session(_Snowflake_Base_Session):
    """Base ingestion session class for Snowflake platform.
    Class should not be instantiated by user directly: use process-specific Session classes instead
    Adds Snowpark session
    """

    def __init__(self):
        super().__init__()


    def ingest(self,df: snowflake.snowpark.dataframe.DataFrame | Callable[[], snowflake.snowpark.dataframeDataFrame] | None = None):
        """Ingest the provided DataFrame into the DataForge and update input record.

        Writes the DataFrame to raw Snowflake table

        Args:
            df (Callable[[], DataFrame] | DataFrame): parameterless def that you defined, returning the Snowpark DataFrame to ingest (recommended),
                or spark DataFrame
        """
        try:
            self._write_input_table(df)
        except Exception as e:
            self._log_fail(e)
            if self.process.startProcessFlag:
                # Fail input and process to prevent core from executing it
                failure_update_json = {
                "process_id": self.process.processId,
                "ingestion_status_code": "F"
                }
                self._pg.sql("SELECT meta.prc_iw_in_update_input_record(%s)",
                         (json.dumps(failure_update_json),), fetch=False)
        finally:
            self.close()