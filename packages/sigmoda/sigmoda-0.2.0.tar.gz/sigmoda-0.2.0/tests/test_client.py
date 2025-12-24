import pytest

import sigmoda.client as client
import sigmoda.config as config


@pytest.fixture(autouse=True)
def reset_config(monkeypatch):
    config._config = None  # type: ignore[attr-defined]
    monkeypatch.setattr(client, "_dispatch", client._queue_dispatch)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client._event_queue = None  # type: ignore[attr-defined]
    client._worker_thread = None  # type: ignore[attr-defined]
    client._worker_stop.clear()  # type: ignore[attr-defined]
    yield
    config._config = None  # type: ignore[attr-defined]
    monkeypatch.setattr(client, "_dispatch", client._queue_dispatch)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client._event_queue = None  # type: ignore[attr-defined]
    client._worker_thread = None  # type: ignore[attr-defined]
    client._worker_stop.clear()  # type: ignore[attr-defined]


def test_log_event_does_not_raise_on_dispatch_failure(monkeypatch):
    config.init(project_key="key", project_id="proj")

    def boom(*args, **kwargs):
        raise RuntimeError("dispatch failed")

    monkeypatch.setattr(client, "_dispatch", boom)

    # Should not raise even though dispatch fails
    client.log_event(
        provider="test",
        model="model",
        type="chat_completion",
        prompt="p",
        response="r",
        tokens_in=1,
        tokens_out=1,
        duration_ms=10,
        status="ok",
    )


def test_log_event_builds_payload_with_project_id(monkeypatch):
    config.init(project_key="key", project_id="proj")
    captured = {}

    def capture(payload, api_url, project_key):
        captured["payload"] = payload
        captured["api_url"] = api_url
        captured["project_key"] = project_key

    monkeypatch.setattr(client, "_dispatch", capture)

    client.log_event(
        provider="test",
        model="model",
        type="chat_completion",
        prompt="p",
        response="r",
    )

    assert captured["project_key"] == "key"
    assert captured["api_url"] == "https://api.sigmoda.com"
    assert captured["payload"]["project_id"] == "proj"


def test_capture_content_false_drops_prompt_and_response(monkeypatch):
    config.init(project_key="key", capture_content=False)
    captured = {}

    def capture(payload, api_url, project_key):
        captured["payload"] = payload

    monkeypatch.setattr(client, "_dispatch", capture)

    client.log_event(
        provider="test",
        model="model",
        type="chat_completion",
        prompt="secret prompt",
        response="secret response",
    )

    assert captured["payload"]["prompt"] == ""
    assert captured["payload"]["response"] == ""


def test_redact_function_is_applied(monkeypatch):
    config.init(project_key="key", env="test", redact=lambda s: "[REDACTED]")
    captured = {}

    def capture(payload, api_url, project_key):
        captured["payload"] = payload

    monkeypatch.setattr(client, "_dispatch", capture)

    client.log_event(
        provider="test",
        model="model",
        type="chat_completion",
        prompt="secret prompt",
        response="secret response",
    )

    assert captured["payload"]["prompt"] == "[REDACTED]"
    assert captured["payload"]["response"] == "[REDACTED]"


def test_disabled_mode_noops(monkeypatch):
    config.init(disabled=True)
    called = {"count": 0}

    def capture(*args, **kwargs):
        called["count"] += 1

    monkeypatch.setattr(client, "_dispatch", capture)

    client.log_event(
        provider="test",
        model="model",
        type="chat_completion",
        prompt="p",
        response="r",
    )

    assert called["count"] == 0


def test_metadata_is_sanitized_and_truncated(monkeypatch):
    config.init(project_key="key", max_metadata_items=1, max_metadata_value_chars=5)
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
        metadata={"keep": "123456789", "drop": "x"},
    )

    md = captured["payload"]["metadata"]
    assert list(md.keys()) == ["keep"]
    assert md["keep"] == "12345"


def test_metadata_allowlist_and_denylist(monkeypatch):
    config.init(project_key="key", metadata_allowlist=["a", "b"], metadata_denylist=["b"])
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
        metadata={"a": "1", "b": "2", "c": "3"},
    )

    assert captured["payload"]["metadata"] == {"a": "1"}


def test_retry_policy_retries_on_5xx(monkeypatch):
    config.init(project_key="key", api_url="http://localhost", max_retries=2, backoff_base=0.0)

    monkeypatch.setattr(client, "_stats", client.Stats())
    monkeypatch.setattr(client.time, "sleep", lambda *_args, **_kwargs: None)

    calls = {"n": 0}

    class Resp:  # noqa: D101 - test helper
        def __init__(self, status_code):
            self.status_code = status_code

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        return Resp(500)

    monkeypatch.setattr(client.requests, "post", fake_post)

    client._send_event({"x": "y"}, "http://localhost", "key")

    assert calls["n"] == 3  # initial + 2 retries
    stats = client.get_stats()
    assert stats["retries"] >= 2
    assert stats["failed"] >= 1


def test_queue_drop_increments_counter(monkeypatch):
    config.init(project_key="key", max_queue_size=1)
    monkeypatch.setattr(client, "_stats", client.Stats())
    import queue as queue_mod  # noqa: PLC0415 - test-only import

    client._event_queue = queue_mod.Queue(maxsize=1)  # type: ignore[attr-defined]
    monkeypatch.setattr(client, "_ensure_worker_started", lambda: None)

    client._queue_dispatch({"x": 1}, "http://localhost", "key")
    client._queue_dispatch({"x": 2}, "http://localhost", "key")

    stats = client.get_stats()
    assert stats["enqueued"] == 1
    assert stats["dropped_queue_full"] == 1
