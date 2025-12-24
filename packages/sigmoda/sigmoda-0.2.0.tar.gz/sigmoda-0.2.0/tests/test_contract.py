import pytest

import sigmoda.client as client
import sigmoda.config as config


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    config._config = None  # type: ignore[attr-defined]
    monkeypatch.setattr(client, "_dispatch", client._queue_dispatch)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client._event_queue = None  # type: ignore[attr-defined]
    client._worker_thread = None  # type: ignore[attr-defined]
    client._worker_stop.clear()  # type: ignore[attr-defined]
    yield
    config._config = None  # type: ignore[attr-defined]


def test_event_payload_contract_minimum_fields(monkeypatch):
    config.init(project_key="key", project_id="proj", env="test")
    captured = {}

    def capture(payload, api_url, project_key):
        captured["payload"] = payload

    monkeypatch.setattr(client, "_dispatch", capture)

    client.log_event(
        provider="test",
        model="model",
        type="chat_completion",
        prompt="p",
        response="r",
        tokens_in=None,
        tokens_out=5,
        duration_ms=12.5,
        status="ok",
        metadata={"k": "v"},
    )

    payload = captured["payload"]

    # Versioning and tags
    assert payload["schema_version"] == 1
    assert payload["sdk"]["name"] == "sigmoda"
    assert payload["env"] == "test"

    # Required MVP fields
    for key in ("timestamp", "provider", "model", "type", "prompt", "response", "status", "metadata"):
        assert key in payload

    assert payload["provider"] == "test"
    assert payload["tokens_in"] is None
    assert payload["tokens_out"] == 5
    assert payload["duration_ms"] == 12.5
    assert payload["metadata"]["k"] == "v"

    # Optional project id
    assert payload["project_id"] == "proj"
