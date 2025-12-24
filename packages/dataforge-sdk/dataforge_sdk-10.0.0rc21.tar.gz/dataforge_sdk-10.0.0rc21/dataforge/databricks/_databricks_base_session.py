from __future__ import annotations
import json
import re


from dataforge._base_session import _Base_Session


class _Databricks_Base_Session(_Base_Session):
    """Base session class for Databricks platform.
    Class should not be instantiated by user directly: use process-specific Session classes instead
    Adds Spark session, DBUtilsto Base_Session
    """


    def __init__(self):
        from pyspark.sql import SparkSession, DataFrame
        self.spark = SparkSession.builder.getOrCreate()
        self.dbutils = self._get_dbutils()
        pg_connection_string_read = self.dbutils.secrets.get("sparky", "pg_read")
        core_jwt_token = self.dbutils.secrets.get("sparky", "coreJWT")
        try:
            process_id = self.dbutils.widgets.get("process_id")
        except Exception:
            process_id = None

        super().__init__(pg_connection_string_read, core_jwt_token, process_id)
        self.process_parameters["start_process_flag"] = True
        self.logger.info(f"Initialized databricks base session for {self.__class__.__name__} with parameters {self.process_parameters}")


    def _get_dbutils(self):
        from pyspark.dbutils import DBUtils
        return DBUtils(self.spark)



    def _write_parsed_data(self, in_df: pyspark.sql.DataFrame, dest_file_path: str) -> tuple[int, int]:
        """Process input DataFrame, write to Parquet, and update metadata.

        Args:
            in_df (DataFrame): Input Spark DataFrame to process and write.
            dest_file_path (str): Destination path for saving Parquet file.

        Returns:
            tuple[int, int]: A tuple containing the total file size in bytes and the number of records written.

        Raises:
            Exception: If duplicate columns are detected or metadata update fails.
        """
        from pyspark.sql.functions import monotonically_increasing_id, lit
        from pyspark.sql.types import LongType


        self.log("Data read successfully. Checking schema.")

        select_list = self._pg.sql("SELECT sparky.get_select_list(%s)", (self.process.sourceId,))
        df_sel = in_df.selectExpr(*select_list)
        self.log(f"Applied select list {select_list}")

        # Duplicate column check
        cols = df_sel.columns
        dup_columns = [col for col in set(cols) if cols.count(col) > 1]
        if dup_columns:
            raise Exception(f"Duplicate columns detected: {', '.join(dup_columns)}")

        # Cast binary/void to string
        binary_casts = [
            f"CAST(`{f.name}` AS STRING) `{f.name}`" if f.dataType.typeName() in ("binary", "void")
            else f"`{f.name}`"
            for f in df_sel.schema.fields
        ]
        df = df_sel.selectExpr(*binary_casts)

        # Schema as JSON array
        schema = []
        for f in df.schema.fields:
            field_name = f.name.lower() if self.process.forceCaseInsensitive else f.name

            if f.dataType.simpleString().startswith("struct"):
                spark_type = "StructType"
            elif f.dataType.simpleString().startswith("array"):
                spark_type = "ArrayType"
            elif f.dataType.simpleString().startswith("decimal"):
                spark_type = "DecimalType"
            else:
                spark_type = type(f.dataType).__name__

            attr_schema = json.loads(f.dataType.json())
            self.logger.info(f"Column `{field_name}` schema: {attr_schema}")
            schema.append({
                "name": field_name,
                "spark_type": spark_type,
                "schema": attr_schema
            })

        self.log("Schema read successfully. Updating source raw metadata.")

        metadata_update_json = {
            "source_id": self.process.sourceId,
            "input_id": self.process.inputId,
            "raw_attributes": schema,
            "ingestion_type": "sparky"
        }

        result = self._pg.sql("SELECT meta.prc_n_normalize_raw_attribute(%s)", [json.dumps(metadata_update_json)])
        if "error" in result:
            raise Exception(result["error"])

        normalize_attributes = result["normalized_metadata"]

        self.log("Source metadata updated. Renaming and upcasting attributes")

        cast_rename_expr = []
        for att in normalize_attributes:
            base_expr = att.get("upcast_expr") or att["raw_attribute_name"]
            if att["raw_attribute_name"] != att["column_alias"] or self.process.forceCaseInsensitive:
                base_expr += f" AS {att['column_alias']}"
            cast_rename_expr.append(base_expr)

        self.logger.info("Normalized SQL: " + ", ".join(cast_rename_expr))
        df_update = df.selectExpr(*cast_rename_expr)

        if self.process.parameters.get("generate_row_id", False):
            self.logger.info("Added s_row_id to data.")
            df_final = df_update.withColumn("s_row_id", monotonically_increasing_id())
        else:
            self.logger.info("generate_row_id = false, added null s_row_id.")
            df_final = df_update.withColumn("s_row_id", lit(None).cast(LongType()))

        self.log("Writing file")
        df_final.write.format("parquet").mode("overwrite").save(dest_file_path)
        self.log(f"Wrote file {dest_file_path}")

        row_count = self.spark.read.format("parquet").load(dest_file_path).count()
        self.log(f"{row_count} records counted")

        file_size = sum(f.size for f in self.dbutils.fs.ls(dest_file_path))
        return file_size, row_count

