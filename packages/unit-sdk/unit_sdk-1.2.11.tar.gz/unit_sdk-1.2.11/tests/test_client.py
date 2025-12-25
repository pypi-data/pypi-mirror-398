# Copyright 2025 PageKey Solutions, LLC

import io
import json
from pathlib import Path
from unittest.mock import Mock, patch
from pydantic import ValidationError
import pytest
from unit_sdk import UnitClient
from unit_sdk.client import (
    ProcessInputFormatException,
    ProcessResult,
    RunProcessException,
    RunProcessResponse,
    StoreRoleNotFoundException,
)


@patch("unit_sdk.client.sys")
@pytest.mark.parametrize(
    "stdin_content",
    [
        "",  # completely blank
        "not json",  # invalid JSON
    ],
)
def test_init_with_invalid_json_raises_error(mock_sys, stdin_content):
    # Arrange.
    mock_sys.stdin = io.StringIO(stdin_content)

    # Act, Assert.
    with pytest.raises(
        ProcessInputFormatException,
        match=f"Invalid Unit metadata format: {stdin_content}",
    ):
        UnitClient()


@patch("unit_sdk.client.sys")
@pytest.mark.parametrize(
    "stdin_content",
    [
        "{}",  # empty JSON
        '{"inputs": {}}',  # inputs present but empty
        '{"stores": {}}',  # JSON with wrong top-level key
    ],
)
def test_init_with_invalid_format_raises_error(mock_sys, stdin_content):
    # Arrange.
    mock_sys.stdin = io.StringIO(stdin_content)

    # Act, Assert.
    with pytest.raises(ValidationError):
        UnitClient()


@patch("unit_sdk.client.sys")
def test_get_input_with_inputs_in_stdin_returns_the_input(mock_sys):
    # Arrange.
    mock_sys.stdin = io.StringIO(
        json.dumps(
            {
                "inputs": {"__version__": "v1.0.0"},
                "stores": {},
            }
        )
    )
    client = UnitClient()

    # Act, Assert.
    assert client.get_input("__version__") == "v1.0.0"


@patch("unit_sdk.client.sys")
def test_get_store_path_by_role_returns_store_when_role_exists(mock_sys):
    # Arrange.
    mock_sys.stdin = io.StringIO(
        json.dumps(
            {
                "inputs": {},
                "stores": {
                    "app": {
                        "name": "my-store",
                        "path": "path",
                    },
                },
            }
        )
    )
    client = UnitClient()

    # Act.
    store = client.get_store_path_by_role("app")

    # Assert.
    assert store == Path("/stores/path")


@patch("unit_sdk.client.sys")
def test_get_store_path_by_role_raises_exception_when_role_not_found(mock_sys):
    # Arrange.
    mock_sys.stdin = io.StringIO(
        json.dumps(
            {
                "inputs": {},
                "stores": {},
            }
        )
    )
    client = UnitClient()

    # Act, Assert.
    with pytest.raises(StoreRoleNotFoundException):
        client.get_store_path_by_role("nonexistent_role")


@patch("unit_sdk.client.requests")
@patch("unit_sdk.client.sys")
def test_run_process_with_app_and_process_sends_request(mock_sys, mock_requests):
    # Arrange.
    mock_token = "fake-token"
    mock_sys.stdin = io.StringIO(
        json.dumps(
            {
                "inputs": {
                    "__token__": mock_token,
                },
                "stores": {},
            }
        )
    )
    expected_result = ProcessResult(
        stdout='{"version": "v1.0.0"}',
        stderr="",
    )
    expected_url = (
        "http://host.containers.internal:8000/api/apps/update/run/get-versions"
    )
    mock_response = Mock()
    mock_response.content = RunProcessResponse(result=expected_result).model_dump_json()
    mock_requests.post.return_value = mock_response
    client = UnitClient()

    # Act.
    result = client.run_process("update", "get-versions", {})

    # Assert.
    assert result.stdout == expected_result.stdout
    assert result.stderr == expected_result.stderr
    mock_requests.post.assert_called_once_with(
        expected_url,
        headers={"Cookie": f"unit_token={mock_token}"},
        files={"_": (None, "")},
        timeout=60,
    )


@patch("unit_sdk.client.requests")
@patch("unit_sdk.client.sys")
def test_run_process_with_invalid_response_raises_exception(mock_sys, mock_requests):
    # Arrange.
    mock_token = "fake-token"
    mock_sys.stdin = io.StringIO(
        json.dumps(
            {
                "inputs": {
                    "__token__": mock_token,
                },
                "stores": {},
            }
        )
    )
    mock_response = Mock()
    mock_response.content = "some non-json string"
    mock_response.status_code = 404
    mock_requests.post.return_value = mock_response
    client = UnitClient()

    # Act.
    with pytest.raises(
        RunProcessException,
        match=r"Failed to parse response from Unit \(404\): some non-json string",
    ):
        client.run_process("update", "get-versions", {})


@patch("unit_sdk.client.requests")
@patch("unit_sdk.client.sys")
def test_run_process_with_wrong_kwargs_raises_exception(mock_sys, mock_requests):
    # Arrange.
    mock_token = "fake-token"
    mock_sys.stdin = io.StringIO(
        json.dumps(
            {
                "inputs": {
                    "__token__": mock_token,
                },
                "stores": {},
            }
        )
    )
    mock_response = Mock()
    mock_response.content = '{"wrong": "kwarg"}'
    mock_response.status_code = 200
    mock_requests.post.return_value = mock_response
    client = UnitClient()

    # Act.
    with pytest.raises(
        RunProcessException,
        match=r'Failed to parse response from Unit \(200\): {"wrong": "kwarg"}',
    ):
        client.run_process("update", "get-versions", {})


@patch("unit_sdk.client.requests")
@patch("unit_sdk.client.sys")
def test_run_process_with_one_input_passes_only_that_input(mock_sys, mock_requests):
    # Arrange.
    mock_token = "fake-token"
    mock_sys.stdin = io.StringIO(
        json.dumps(
            {
                "inputs": {
                    "__token__": mock_token,
                },
                "stores": {},
            }
        )
    )
    expected_result = ProcessResult(
        stdout='{"version": "v1.0.0"}',
        stderr="",
    )
    expected_url = (
        "http://host.containers.internal:8000/api/apps/update/run/get-versions"
    )
    mock_response = Mock()
    mock_response.content = RunProcessResponse(result=expected_result).model_dump_json()
    mock_requests.post.return_value = mock_response
    client = UnitClient()

    # Act.
    result = client.run_process("update", "get-versions", {"some-input": "some-value"})

    # Assert.
    assert result.stdout == expected_result.stdout
    assert result.stderr == expected_result.stderr
    mock_requests.post.assert_called_once_with(
        expected_url,
        headers={"Cookie": f"unit_token={mock_token}"},
        files={
            "_": (None, ""),
            "some-input": (None, "some-value"),
        },
        timeout=60,
    )
