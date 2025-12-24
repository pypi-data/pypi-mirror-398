from .postgres_connection import PostgresConnection


class SystemConfiguration:
    datalakePath: str | None
    dataLakeSchemaName: str
    dataLakeDbName: str | None
    targetParquetFileSize: int | None
    coreUri: str
    saas_flag: bool

    def __init__(self, pg: PostgresConnection):
        conf = pg.sql("SELECT meta.prc_get_system_configuration('sparky')")
        dl_path = conf.get('data-lake-path')
        self.datalakePath = dl_path.replace("s3://", "s3a://") if dl_path else "@DATAFORGE"
        self.dataLakeSchemaName = conf['datalake-schema-name']
        self.targetParquetFileSize = conf.get('target-parquet-file-size')
        self.saas_flag = conf['architecture'] == "saas"
        self.coreUri = f"https://{conf['api-url']}" if self.saas_flag else f"http://{conf['etl-url']}:7131"
        self.dataLakeDbName = conf.get('datalake-db-name')

