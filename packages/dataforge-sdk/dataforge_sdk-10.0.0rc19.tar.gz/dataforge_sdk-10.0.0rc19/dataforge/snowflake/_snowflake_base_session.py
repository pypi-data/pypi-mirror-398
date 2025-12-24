from __future__ import annotations
from typing import Callable
from dataforge._base_session import _Base_Session
import sys

class _Snowflake_Base_Session(_Base_Session):
    """Base session class for Snowflake platform.
    Class should not be instantiated by user directly: use process-specific Session classes instead
    Adds Snowpark session
    """

    def __init__(self):
        from snowflake.snowpark.context import get_active_session
        self.snowpark_session = get_active_session()
        pg_connection_string_read = self.snowpark_session.sql("SELECT get_secret('DATAFORGE_PG_READ')").first(1)[0][0]
        core_jwt_token = self.snowpark_session.sql("SELECT get_secret('DATAFORGE_CORE_JWT')").first(1)[0][0]
        params = self.parse_key_value_args()
        process_id = params.get('process_id')
        self.input_id = params.get('input_id')

        super().__init__(pg_connection_string_read, core_jwt_token, process_id)

        self.process_parameters["start_process_flag"] = process_id is None

        self.logger.info(f"Initialized Snowflake base session for {self.__class__.__name__} with parameters {self.process_parameters}")

    def _write_input_table(self,df: snowflake.snowpark.dataframe.DataFrame | Callable[[],
        snowflake.snowpark.dataframeDataFrame] | None = None) -> snowflake.snowpark.dataframe.DataFrame:
        from snowflake.snowpark.types import StructType, StructField, StringType
        if not self._is_open:
            raise Exception("Session is closed")
        if df is None:
            # create empty df
            result_df = df = self.snowpark_session.create_dataframe([], StructType([StructField("id", StringType())]))
        else:
            if callable(df):
                result_df = df()  # call it to get the DataFrame
            else:
                result_df = df
        table = f"{self._systemConfiguration.dataLakeDbName}.{self._systemConfiguration.dataLakeSchemaName}.RAW_INPUT_{self.process.inputId}"
        self.log(f"Writing dataframe to table {table}")
        result_df.write.save_as_table(
            table_name=table,
            mode="overwrite",
            table_type="transient"
        )
        self.log(f"Table {table} written")
        if self.process.startProcessFlag:
            # process started by IngestionSession, tell Core to continue and not run Notebook
            self._pg.sql("SELECT sparky.sdk_complete_manual_process(%s)", [self.process.processId], fetch=False)

    @staticmethod
    def parse_key_value_args():
        """
        Parse command line arguments formatted as key=value into a dict.
        Example: python script.py foo=123 bar=hello

        Returns: {'foo': '123', 'bar': 'hello'}
        """
        argv = sys.argv
        params: dict[str,str] = {}
        for arg in argv:
            if "=" in arg:
                key, value = arg.split("=", 1)  # split only on first '='
                params[key] = value
        return params
