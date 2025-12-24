"""IngestionSession management for DataForge SDK.

This module provides the IngestionSession class
that manages custom data ingestion process, including initialization, data writing,
metadata updates, and failure handling.

Classes:
    IngestionSession: Manages the custom ingestion process lifecycle.
"""
import json
from typing import Optional
from ._session import _Ingestion_Session
from .process_record import ProcessRecord


class IngestionSession(_Ingestion_Session):

    """Session class to manage custom ingestion process lifecycle.

    Initializes an ingestion process record and provides methods to ingest
    data frames and handle failures, updating metadata and notifying the Core API.
    """
    def __init__(self, source_name: Optional[str] = None, project_name: Optional[str] = None):
        """Initialize ingestion session and start a new ingestion process.

        Args:
            source_name (Optional[str]): Optional name of the data source being ingested.
                Used for interactive testing. Leave blank for production use.
            project_name (Optional[str]): Optional project context name. Used for interactive testing.
                Leave blank for production use.
        """
        super().__init__()
        # initialize process
        if source_name is not None:
            self.process_parameters["source_name"] = source_name
        if project_name is not None:
            self.process_parameters["project_name"] = project_name

        process = self._pg.sql("select sparky.sdk_new_ingestion(%s)", (json.dumps(self.process_parameters),))
        self.process = ProcessRecord(process)


    def latest_tracking_fields(self):
        """Get the latest tracking fields from the ingestion process record.

        Returns:
            dict: The latest tracking data from the process record, or None if not available.
        """
        return self.process.process.get("tracking")


    def fail(self, message: str):
        """Mark the ingestion as failed with a custom message.

        Logs the provided error message, updates the input and process record to failure status,
        and notifies the Core API of process completion.

        Args:
            message (str): Custom error message explaining the failure.
        """
        self.log(f"Custom Ingestion failed with error: {message}", "E")
        self._pg.sql("select meta.prc_iw_in_update_input_record(%s)",
                     [json.dumps({"process_id": self.process.processId, "ingestion_status_code" : "F"})], fetch=False)
        self._core_api_call(f"process-complete/{self.process.processId}")