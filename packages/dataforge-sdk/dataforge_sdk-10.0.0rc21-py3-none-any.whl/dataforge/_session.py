import os


def _is_databricks_environment() -> bool:
    """Detect whether the current runtime is Databricks."""
    spark_obj = globals().get("spark")
    if spark_obj is not None:
        spark_class_name = getattr(getattr(spark_obj, "__class__", None), "__name__", None)
        if spark_class_name == "SparkSession":
            return True
    if os.environ.get("DATABRICKS_RUNTIME_VERSION"):
        return True
    try:
        from pyspark.sql import SparkSession  # type: ignore
    except ImportError:
        return False
    try:
        return SparkSession.getActiveSession() is not None
    except Exception:
        return False


if _is_databricks_environment():
    from dataforge.databricks._databricks_base_session import _Databricks_Base_Session
    from dataforge.databricks._databricks_ingestion_session import _Databricks_Ingestion_Session
    from dataforge.databricks._databricks_parsing_session import _Databricks_Parsing_Session

    _Session = _Databricks_Base_Session
    _Ingestion_Session = _Databricks_Ingestion_Session
    _Parsing_Session = _Databricks_Parsing_Session
    _platform = "databricks"
else:
    from dataforge.snowflake._snowflake_base_session import _Snowflake_Base_Session
    from dataforge.snowflake._snowflake_ingestion_session import _Snowflake_Ingestion_Session
    from dataforge.snowflake._snowflake_parsing_session import _Snowflake_Parsing_Session

    _Session = _Snowflake_Base_Session
    _Ingestion_Session = _Snowflake_Ingestion_Session
    _Parsing_Session = _Snowflake_Parsing_Session
    _platform = "snowflake"
