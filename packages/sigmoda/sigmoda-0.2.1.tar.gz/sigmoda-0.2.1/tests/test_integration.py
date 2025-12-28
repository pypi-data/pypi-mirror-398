import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import sigmoda.client as client
import sigmoda.config as config


class _Handler(BaseHTTPRequestHandler):
    received = []

    def do_POST(self):  # noqa: N802 - stdlib hook
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        _Handler.received.append(
            {"path": self.path, "headers": dict(self.headers), "body": body}
        )
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_args, **_kwargs):  # noqa: D401
        # Silence noisy default logging.
        return


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    _Handler.received = []
    config._config = None  # type: ignore[attr-defined]
    monkeypatch.setattr(client, "_dispatch", client._queue_dispatch)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client._event_queue = None  # type: ignore[attr-defined]
    client._worker_thread = None  # type: ignore[attr-defined]
    client._worker_stop.clear()  # type: ignore[attr-defined]
    yield
    config._config = None  # type: ignore[attr-defined]


def test_log_event_sends_http_request_to_ingest():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        api_url = f"http://127.0.0.1:{server.server_port}"
        config.init(project_key="proj_key", api_url=api_url, env="test", max_retries=0, timeout=1.0)

        client.log_event(
            provider="test",
            model="model",
            type="chat_completion",
            prompt="p",
            response="r",
            metadata={"hello": "world"},
        )
        client.flush(timeout=2.0)

        assert len(_Handler.received) == 1
        req = _Handler.received[0]
        assert req["path"] == "/api/v1/events"
        assert req["headers"].get("X-Project-Key") == "proj_key"

        payload = json.loads(req["body"].decode("utf-8"))
        assert payload["provider"] == "test"
        assert payload["env"] == "test"
        assert payload["metadata"]["hello"] == "world"
        assert payload["schema_version"] == 1
        assert payload["sdk"]["name"] == "sigmoda"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)

