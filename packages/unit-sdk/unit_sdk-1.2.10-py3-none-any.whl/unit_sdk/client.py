# Copyright 2025 PageKey Solutions, LLC
"""Client for interacting with PageKey Unit."""

import json
from pathlib import Path
import sys

import requests

from pydantic import BaseModel, ValidationError


class UnitStore(BaseModel):
    """Represents a Unit Store."""

    name: str
    path: Path


class UnitMetadata(BaseModel):
    """Represents the metadata passed to the current process."""

    inputs: dict[str, str]
    stores: dict[str, UnitStore]


class ProcessInputFormatException(Exception):
    """Raised when incorrect format is passed to the process."""

    def __init__(self, raw_metadata: str):
        """Initialize exception."""
        message = f"Invalid Unit metadata format: {raw_metadata}"
        super().__init__(message)


class RunProcessException(Exception):
    """Raised when there is an error while running the process."""

    def __init__(self, response: requests.Response):
        """Initialize exception."""
        message = f"Failed to parse response from Unit ({response.status_code}): {response.content}"
        super().__init__(message)


class StoreRoleNotFoundException(Exception):
    """Raised when user attempts to access a non-existant store role."""

    def __init__(self, role: str):
        """Initialize exception."""
        message = f"Store Role not found: {role}"
        super().__init__(message)


class ProcessResult(BaseModel):
    """Represents the result of running a process."""

    stdout: str
    stderr: str


class RunProcessResponse(BaseModel):
    """Represents the response from running a process."""

    result: ProcessResult


class UnitClient:
    """Client for interacting with PageKey Unit."""

    def __init__(self) -> None:
        """Read inputs to this process from stdin."""
        raw_metadata = sys.stdin.read()
        try:
            self._metadata = UnitMetadata(**json.loads(raw_metadata))
        except json.JSONDecodeError as error:
            raise ProcessInputFormatException(raw_metadata) from error

    def get_input(self, key: str) -> str:
        """Get an input passed to this process."""
        return self._metadata.inputs.get(key, "")

    def get_store_path_by_role(self, role: str) -> Path:
        """Get a store by its role."""
        if role in self._metadata.stores:
            return Path("/stores") / self._metadata.stores.get(role).path
        else:
            raise StoreRoleNotFoundException(role)

    def run_process(
        self, app: str, process: str, inputs: dict[str, str]
    ) -> ProcessResult:
        """Run another process."""
        token = self._metadata.inputs.pop("__token__")
        files = {"_": (None, "")}
        for key, value in inputs.items():
            files[key] = (None, str(value))

        response = requests.post(
            f"http://host.containers.internal:8000/api/apps/{app}/run/{process}",
            headers={
                "Cookie": f"unit_token={token}",
            },
            files=files,
            timeout=60,
        )
        try:
            data = json.loads(response.content)
            return RunProcessResponse(**data).result
        except json.JSONDecodeError as error:
            raise RunProcessException(response) from error
        except ValidationError as error:
            raise RunProcessException(response) from error
