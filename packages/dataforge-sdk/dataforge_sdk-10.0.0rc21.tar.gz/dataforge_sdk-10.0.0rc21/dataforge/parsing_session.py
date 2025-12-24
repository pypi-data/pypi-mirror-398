from __future__ import annotations

import json
from typing import Optional, Callable
from .process_record import ProcessRecord
from ._session import _Parsing_Session


class ParsingSession(_Parsing_Session):


    """Session class to manage custom parse process lifecycle.

    Initializes parse process record and provides methods to parse
    data frames and handle failures, updating metadata and notifying the Core API.
    """
    _parsing_parameters: dict
    def __init__(self, input_id: Optional[int] = None):
        """Initialize custom parse session and start a new custom parse process.

        Args:
            input_id (Optional[int]): Optional input_id of the batch for interactive testing.
                Leave blank for production use.
        """
        super().__init__()
        # initialize process
        if input_id is not None:
            self.process_parameters["input_id"] = input_id

        process = self._pg.sql("select sparky.sdk_new_parse(%s)", (json.dumps(self.process_parameters),))
        self.process = ProcessRecord(process)
        self._parsing_parameters = self._pg.sql("select meta.prc_n_start_parse(%s)",
                                                (json.dumps({"input_id": self.process.inputId}),))
        # Extract the file extension
        file_name = self._parsing_parameters["source_file_name"]
        file_extension = file_name.split(".")[-1]
        # Construct the path
        self.file_path = f"{self._systemConfiguration.datalakePath}/source_{self.process.sourceId}/raw/raw_input_{self.process.inputId}.{file_extension}"

    def custom_parameters(self):
        """Retrieve custom parsing parameters.

        Returns:
            dict: The custom parsing parameters dictionary.
        """
        return self._parsing_parameters.get('custom_parameters')



