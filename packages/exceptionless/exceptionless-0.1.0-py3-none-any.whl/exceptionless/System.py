import platform
import os
import traceback
from datetime import datetime
from typing import Dict, Any

import requests

from exceptionless.ExceptionlessStatics import EXCEPTIONLESS_API_ROOT
from exceptionless.ExceptionlessUtils import ExceptionlessUtils
from exceptionless.exception.ExceptionlessError import ExceptionlessError

class ExceptionSystem:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ExceptionSystem, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.api_key = ""
            self.user_info = {}
            self.device_info = {}

            ## SETUP ##
            self._initialized = True

    def initialize(self, api_key: str, user_info: dict):
        if ExceptionlessUtils.validate_api_key(api_key):
            self.api_key = api_key
            self.user_info = user_info

            self.device_info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "python_version": platform.python_version(),
                "machine": platform.machine(),
                "hostname": platform.node(),
                "pid": os.getpid()
            }

            self.log("Initialized Exceptionless SDK.")
        else:
            raise RuntimeError("An invalid Exceptionless API key was specified, please ensure it's correct and retry.")

    def log(self, message: str):
        print(f"[Exceptionless] {message}")

    def _send_data(self, error: Exception, device_info: dict = None, user_info: dict = None, extra_data: dict = None) -> dict:
        body: Dict[str, Any] = {
            "type": "error",
            "message": str(error),
            "date": datetime.utcnow().isoformat() + "Z",
            "@stack": "".join(traceback.format_exception(type(error), error, error.__traceback__))
        }

        # doesn't seem to work right now, TODO: fix
        if user_info:
            body["@user"] = user_info
        if device_info:
            body["@environment"] = device_info  # e.g. {"os":"...", "device":"...", "version":"..."}
        if extra_data:
            body["data"] = extra_data

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(f"{EXCEPTIONLESS_API_ROOT}/events", json=body, headers=headers)
        if response.status_code == 202:
            return response.json() if response.text else {}

        raise ExceptionlessError(f"Failed to send to Exceptionless: {response.status_code} - {response.text}")

    def send(self, ex: Exception) -> dict:
        """Sends an exception event to Exceptionless."""
        return self._send_data(
            error=ex,
            device_info=self.device_info,
            #user_info=self.user_info, # doesn't seem to work right now
            extra_data=self.user_info,
        )