"""Session management for DataForge SDK.

This module provides the Session class for managing DataForge SDK sessions,

Classes:
    CoreAPIError: Raised when a Core API call fails.
    VersionMismatchError: Raised when the SDK version does not match server expectation.
    Session: Main class for session management.
"""
import json
import traceback
from typing import Optional, Literal
import requests
import logging

from dataforge.process_record import ProcessRecord
from dataforge.system_configuration import SystemConfiguration
from dataforge.postgres_connection import PostgresConnection
from importlib.metadata import version

from .utils import _setup_logger


class CoreAPIError(Exception):
    """Exception raised when a Core API call fails."""
    pass

class VersionMismatchError(Exception):
    """Exception raised when the SDK version does not match server expectation."""
    pass

class _Base_Session:
    """Base session class for DataForge SDK operations.
    Class should not be instantiated by user directly: use process-specific Session classes instead
    Manages system configuration, Core API calls,
    logging, and process lifecycle.

    Attributes:
        logger (logging.Logger): Logger instance for session logs.
        _systemConfiguration (SystemConfiguration): System configuration loaded from Postgres.
        _pg (PostgresConnection): Postgres connection to core API database.
        process (ProcessRecord): The current process record.
        version (str): DataForge SDK version.
    """
    _systemConfiguration: SystemConfiguration
    _pg: PostgresConnection
    logger: logging.Logger
    process: ProcessRecord
    version = version("dataforge-sdk")
    core_jwt_token: str
    process_parameters: dict
    _is_open: bool = False

    def __init__(self, pg_connection_string_read: str, core_jwt_token: str, process_id: str | None):
        self.logger = _setup_logger(self.__class__.__name__)
        pg_read = PostgresConnection(f"{pg_connection_string_read}&application_name=sdk", self.logger)
        self._systemConfiguration = SystemConfiguration(pg_read)
        self.core_jwt_token = core_jwt_token
        pg_connection_string: str = self._core_api_call("core/sparky-db-connection")["connection"]
        self._pg = PostgresConnection(f"{pg_connection_string}&application_name=sdk", self.logger)
        self._is_open = True
        self._check_version()
        self.process_parameters = {
            "version": self.version,
            "packageName": "dataforge-sdk"
        }
        if process_id:
            self.process_parameters['process_id'] = int(process_id)
        self.logger.info(f"Initialized base session for {self.__class__.__name__}")


    def _core_api_call(self, route: str):
        """Make a GET request to the Core API.

        Args:
            route (str): API route to call, appended to core URI.

        Returns:
            dict: Parsed JSON response from Core API.

        Raises:
            CoreAPIError: If response status is not 200.
        """
        add_core =  "core/" if route.startswith("process-complete") and self._systemConfiguration.saas_flag else ""
        end_point = f"{self._systemConfiguration.coreUri}/{add_core}{route}"
        headers = {
            "Authorization": f"Bearer {self.core_jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.logger.debug(f"Executing core API call to {end_point}")
        response = requests.get(end_point, headers=headers)
        if response.status_code == 200:
            data = response.json() if response.content else None
            return data
        else:
            raise CoreAPIError(f"Core API call to {end_point} failed with status code {response.status_code}")

    def _check_version(self):
        """Checks that the SDK version is compatible with the server.

        Calls the database function to verify the SDK version. Raises
        VersionMismatchError if there is a version mismatch.
        """
        self.logger.info(f"Executing package dataforge-sdk version {self.version}")
        check_res = self._pg.sql("select sparky.sdk_check_version(%s,%s)", [self.version, "dataforge-sdk"])
        if check_res.get("error"):
            raise VersionMismatchError(check_res.get("error"))

    def log(self, message:str, severity: str = "I"):
        """Log a message to both the local logger and the process log in the database.

        Args:
            message (str): The log message.
            severity (str): Severity level, "I" for info, "E" for error. Defaults to "I".
        """
        match severity:
            case "I":
                self.logger.info(message)
            case "E":
                self.logger.error(message)
        payload = {"log_id": self.process.logId, "operation_type": self.process.operationType,
         "severity": severity, "message": message}
        self._pg.sql("SELECT sparky.write_log(%s)", [json.dumps(payload)], fetch=False)

    def connection_parameters(self):
        """Retrieve connection parameters for the current process.

        Returns:
            dict: Dictionary containing private and public connection parameters.
        """
        connection_id = self.process.connectionId
        self.log(f"Reading connection parameters of connection id {connection_id}")
        params = self._core_api_call(f"core/connection/{connection_id}").get("parameters")
        return {"private_connection_parameters": params.get("private_connection_parameters"),
          "public_connection_parameters": params.get("public_connection_parameters")}


    def _end_process(self, status_code: Literal['P', 'F', 'Z'] = 'P', parameters: Optional[dict] = None):
        """Private method. End the current process
        """
        payload = parameters if parameters else {}
        payload["process_id"] = self.process.processId
        payload["status_code"] = status_code
        self._pg.sql("select meta.prc_process_end(%s)", [json.dumps(payload)], fetch=False)
        self._core_api_call(f"process-complete/{self.process.processId}")
        if status_code in ('P','Z'):
            self.logger.info("Session completed successfully")
        else:
            self.logger.error("Process failed")
        self.close()

    def fail(self,message: str):
        """Fail current session and log the message.

        Args:
            message (str): The log message.
        """
        self.log(f"Process failed with error: {message}", "E")
        self._end_process("F")

    def _log_fail(self, e: Exception):
        """Log failure for the given exception.

        Args:
            e (Exception): The exception that caused the failure.
        """
        traceback.print_exception(e)
        self.log(f"Process failed with error: {e}", "E")

    def close(self):
        """Close the session."""
        self._pg.close()
        self.logger.info("Session closed")
        self._is_open = False

    def custom_parameters(self):
        """Retrieve custom parameters from the process.

        Returns:
            dict: The custom parameters dictionary from the process.
        """
        return self.process.parameters.get('custom_parameters')



