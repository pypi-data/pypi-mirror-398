import io
import json
import pytest
from unittest.mock import MagicMock

import sliq.api as api


def test_call_status_normalizes_succeeded_from_status_string(monkeypatch):
    """If the API returns 'succeeded' as a status string but succeeded flag False,
    call_status should normalize to succeeded True.
    """
    # Mock response of requests.post to simulate server returning inconsistent data
    mocked_response = MagicMock()
    mocked_response.status_code = 200
    mocked_response.json.return_value = {
        "is_complete": True,
        "succeeded": False,
        "status": "succeeded",
        "message": "Cleaning complete",
    }

    def fake_post(*args, **kwargs):
        return mocked_response

    monkeypatch.setattr(api.requests, "post", fake_post)

    status = api.call_status(
        api_key="test",
        execution_name="exec-1",
        dataset_key="obj-1",
        user_id="user-1",
        job_id="job-1",
        dataset_name="test-dataset",
    )
    assert status["is_complete"] is True
    assert status["succeeded"] is True
    assert status["status"] == "succeeded"


def test_call_status_normalizes_uppercase_status_string(monkeypatch):
    """If the API returns an uppercase 'SUCCEEDED' string, call_status returns normalized 'succeeded' and succeeded True."""
    mocked_response = MagicMock()
    mocked_response.status_code = 200
    mocked_response.json.return_value = {
        "is_complete": True,
        "succeeded": False,
        "status": "SUCCEEDED",
        "message": "Cleaning complete",
    }

    def fake_post(*args, **kwargs):
        return mocked_response

    monkeypatch.setattr(api.requests, "post", fake_post)

    status = api.call_status(
        api_key="test",
        execution_name="exec-1",
        dataset_key="obj-1",
        user_id="user-1",
        job_id="job-1",
        dataset_name="test-dataset",
    )
    assert status["is_complete"] is True
    assert status["succeeded"] is True
    assert status["status"] == "succeeded"
