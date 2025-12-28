import json
import queue as queue_mod
import threading
import time

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
    monkeypatch.setattr(client, "_dispatch", client._queue_dispatch)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client._event_queue = None  # type: ignore[attr-defined]
    client._worker_thread = None  # type: ignore[attr-defined]
    client._worker_stop.clear()  # type: ignore[attr-defined]


def test_metadata_normalization_edge_cases(monkeypatch):
    class BadBytes(bytes):
        def decode(self, *_args, **_kwargs):  # noqa: ANN001 - test helper
            raise ValueError("boom")

    cfg = config.init(project_key="key", env="test", debug=True, max_metadata_value_chars=3, max_metadata_items=5)

    def bad_redact(_value):  # noqa: ANN001 - test helper
        raise RuntimeError("redact failed")

    cfg.redact = bad_redact

    assert client._truncate_text("abc", 0) == ""
    assert client._normalize_metadata_value("secret", config=cfg, depth=0) == "sec"
    assert client._normalize_metadata_value(BadBytes(b"x"), config=cfg, depth=0) == "<bytes>"
    assert client._normalize_metadata_value({"a": 1}, config=cfg, depth=3).startswith("{")

    long_dict = {f"k{i}": i for i in range(30)}
    long_list = list(range(30))
    assert len(client._normalize_metadata_value(long_dict, config=cfg, depth=0)) <= 20
    assert len(client._normalize_metadata_value(long_list, config=cfg, depth=0)) <= 20

    class Obj:  # noqa: D401 - test helper
        def __str__(self):
            return "object-value"

    assert client._normalize_metadata_value(Obj(), config=cfg, depth=0).startswith("obj")


def test_sanitize_metadata_branches(monkeypatch):
    cfg = config.init(project_key="key", env="test", max_metadata_items=2, max_metadata_bytes=100)
    original_dumps = client.json.dumps

    assert client._sanitize_metadata(None, config=cfg) == {}
    assert client._sanitize_metadata("x", config=cfg) == {"value": "x"}

    cfg.metadata_allowlist = ["a", "b"]
    cfg.metadata_denylist = ["b"]
    data = client._sanitize_metadata({"a": "1", "b": "2", "c": "3"}, config=cfg)
    assert data == {"a": "1"}

    cfg.max_metadata_bytes = 0
    assert client._sanitize_metadata({"a": "1"}, config=cfg) == {}

    cfg.max_metadata_bytes = 5
    # Force size_bytes exception.
    monkeypatch.setattr(client.json, "dumps", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert client._sanitize_metadata({"a": "1"}, config=cfg) == {}

    # Force trim path where a single item fits but multiple don't.
    def fake_dumps(obj, **_kwargs):  # noqa: ANN001 - test helper
        return "x" * (20 if len(obj) > 1 else 5)

    monkeypatch.setattr(client.json, "dumps", fake_dumps)
    cfg = config.init(project_key="key", env="test", max_metadata_items=2, max_metadata_bytes=10)
    trimmed = client._sanitize_metadata({"a": "1", "b": "2", "c": "3"}, config=cfg)
    assert trimmed != {}
    monkeypatch.setattr(client.json, "dumps", original_dumps)


def test_payload_size_and_drop_paths(monkeypatch):
    cfg = config.init(project_key="key", env="test", capture_content=True, max_payload_bytes=400)
    captured = {}
    original_dumps = client.json.dumps

    def capture(payload, _api_url, _project_key):
        captured["payload"] = payload

    monkeypatch.setattr(client, "_dispatch", capture)

    big_meta = {"big": "x" * 500}
    client.log_event(
        provider="test",
        model="model",
        type="chat",
        prompt="hi",
        response="there",
        metadata=big_meta,
    )
    assert captured["payload"]["metadata"] == {}

    # Drop when prompt/response already empty and still too large.
    config.init(project_key="key", env="test", capture_content=True, max_payload_bytes=1)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client.log_event(
        provider="test",
        model="model",
        type="chat",
        prompt="",
        response="",
        metadata={"x": "y"},
    )
    stats = client.get_stats()
    assert stats["dropped_payload_too_large"] >= 1

    monkeypatch.setattr(client.json, "dumps", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert client._payload_size_bytes({"x": "y"}) == 0
    monkeypatch.setattr(client.json, "dumps", original_dumps)

    # Trim path with prompt/response halves then drop.
    config.init(project_key="key", env="test", capture_content=True, max_payload_bytes=1)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client.log_event(
        provider="test",
        model="model",
        type="chat",
        prompt="p" * 50,
        response="r" * 50,
        metadata={},
    )
    stats = client.get_stats()
    assert stats["dropped_payload_too_large"] >= 1


def test_sampling_and_redact_errors(monkeypatch):
    cfg = config.init(project_key="key", env="test", sample_rate=0.0, debug=True)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client.log_event(
        provider="test",
        model="model",
        type="chat",
        prompt="p",
        response="r",
    )
    assert client.get_stats()["dropped_sampled"] == 1

    def bad_redact(_value):  # noqa: ANN001 - test helper
        raise RuntimeError("redact failed")

    cfg = config.init(project_key="key", env="test", capture_content=True, debug=True, redact=bad_redact)
    monkeypatch.setattr(client, "_dispatch", lambda *_a, **_k: None)
    client.log_event(
        provider="test",
        model="model",
        type="chat",
        prompt="secret",
        response="secret",
    )


def test_dispatch_and_send_event_branches(monkeypatch):
    cfg = config.init(project_key="key", env="test", api_url="http://localhost", max_retries=0, debug=True)

    class Resp:  # noqa: D401 - test helper
        def __init__(self, status_code):
            self.status_code = status_code

    monkeypatch.setattr(client.requests, "post", lambda *_a, **_k: Resp(400))
    monkeypatch.setattr(client, "_stats", client.Stats())
    client._send_event({"x": "y"}, cfg.api_url, cfg.project_key)
    assert client.get_stats()["failed"] >= 1

    def boom(*_a, **_k):  # noqa: ANN001 - test helper
        raise RuntimeError("boom")

    monkeypatch.setattr(client.requests, "post", boom)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client._send_event({"x": "y"}, cfg.api_url, cfg.project_key)
    assert client.get_stats()["retries"] >= 1

    def bad_dispatch(*_a, **_k):  # noqa: ANN001 - test helper
        raise RuntimeError("dispatch failed")

    monkeypatch.setattr(client, "_dispatch", bad_dispatch)
    client.log_event(
        provider="test",
        model="model",
        type="chat",
        prompt="p",
        response="r",
    )


def test_queue_and_worker_paths(monkeypatch):
    config.init(project_key="key", env="test", debug=True, max_queue_size=1)

    monkeypatch.setattr(client, "_ensure_worker_started", lambda: None)
    client._event_queue = None  # type: ignore[attr-defined]
    client._queue_dispatch({"x": 1}, "http://localhost", "key")

    client._event_queue = queue_mod.Queue(maxsize=1)  # type: ignore[attr-defined]
    client._queue_dispatch({"x": 1}, "http://localhost", "key")
    client._queue_dispatch({"x": 2}, "http://localhost", "key")

    client._worker_stop.clear()
    client._event_queue = queue_mod.Queue()  # type: ignore[attr-defined]
    client._event_queue.put(({"x": "y"}, "http://localhost", "key"))

    def boom(*_a, **_k):  # noqa: ANN001 - test helper
        raise RuntimeError("boom")

    monkeypatch.setattr(client, "_send_event", boom)
    config.init(project_key="key", env="test", debug=True)

    thread = threading.Thread(target=client._worker_loop, daemon=True)
    thread.start()
    client._event_queue.join()
    client._worker_stop.set()
    thread.join(timeout=1.0)

    # Cover q is None path (sleep + continue).
    client._worker_stop.clear()
    client._event_queue = None  # type: ignore[attr-defined]
    thread = threading.Thread(target=client._worker_loop, daemon=True)
    thread.start()
    time.sleep(0.06)
    client._worker_stop.set()
    thread.join(timeout=1.0)

    # Cover get_config failure inside worker exception path.
    client._worker_stop.clear()
    client._event_queue = queue_mod.Queue()  # type: ignore[attr-defined]
    client._event_queue.put(({"x": "y"}, "http://localhost", "key"))
    monkeypatch.setattr(client, "_send_event", boom)
    monkeypatch.setattr(client, "get_config", lambda: (_ for _ in ()).throw(RuntimeError("no config")))
    thread = threading.Thread(target=client._worker_loop, daemon=True)
    thread.start()
    client._event_queue.join()
    client._worker_stop.set()
    thread.join(timeout=1.0)


def test_flush_and_atexit_paths(monkeypatch):
    config.init(project_key="key", env="test")
    client._event_queue = None  # type: ignore[attr-defined]
    client.flush()

    client._event_queue = queue_mod.Queue()  # type: ignore[attr-defined]
    client.flush(timeout=None)
    client._event_queue.put(({"x": "y"}, "http://localhost", "key"))
    client.flush(timeout=0)
    client._event_queue = queue_mod.Queue()  # type: ignore[attr-defined]

    monkeypatch.setattr(client, "flush", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")))
    client._atexit_flush()


def test_pid_reset_in_worker_started(monkeypatch):
    config.init(project_key="key", env="test")
    client._event_queue = queue_mod.Queue()  # type: ignore[attr-defined]
    old_pid = client._pid
    monkeypatch.setattr(client.os, "getpid", lambda: old_pid + 1)
    client._ensure_worker_started()
