class ProcessRecord:
    processId: int
    logId: int
    operationType: str
    sourceId: int
    inputId: int
    process: dict
    parameters: dict
    forceCaseInsensitive: bool
    connectionId: int
    startProcessFlag: bool

    def __init__(self, process):
        self.process = process
        self.processId = process['process_id']
        self.logId = process['log_id']
        self.operationType = process['operation_type']
        self.startProcessFlag = process['start_process_flag']
        self.inputId = process['input_id']
        self.sourceId = process['source_id']
        self.connectionId = process.get('connection_id')
        self.parameters = process['parameters']
        self.forceCaseInsensitive = self.parameters.get('force_case_insensitive', False)