import atexit
import json
import logging
import os
import queue
import random
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from importlib import metadata
from typing import Any, Dict, Optional, Tuple

import requests

from .config import get_config

logger = logging.getLogger(__name__)
_pid = os.getpid()
try:
    _SDK_VERSION = metadata.version("sigmoda")
except metadata.PackageNotFoundError:  # pragma: no cover
    _SDK_VERSION = "unknown"

EventItem = Tuple[Dict[str, Any], str, str]  # (payload, api_url, project_key)

_event_queue: Optional["queue.Queue[EventItem]"] = None
_worker_thread: Optional[threading.Thread] = None
_worker_stop = threading.Event()


@dataclass
class Stats:
    enqueued: int = 0
    dropped_queue_full: int = 0
    dropped_sampled: int = 0
    dropped_payload_too_large: int = 0
    sent: int = 0
    failed: int = 0
    retries: int = 0


_stats = Stats()
_stats_lock = threading.Lock()


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate_text(value: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(value) <= max_chars:
        return value
    return value[:max_chars]


def _normalize_metadata_value(value: Any, *, config: Any, depth: int) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        if config.redact is not None:
            try:
                value = config.redact(value)
            except Exception as exc:  # noqa: BLE001
                if config.debug:
                    logger.debug("Sigmoda redact(metadata) failed: %s", exc)
        return _truncate_text(value, int(config.max_metadata_value_chars))

    if isinstance(value, bytes):
        try:
            return _normalize_metadata_value(value.decode("utf-8", errors="replace"), config=config, depth=depth)
        except Exception:  # noqa: BLE001
            return "<bytes>"

    if depth >= 3:
        return _truncate_text(str(value), int(config.max_metadata_value_chars))

    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for i, (k, v) in enumerate(value.items()):
            if i >= 20:
                break
            out[str(k)] = _normalize_metadata_value(v, config=config, depth=depth + 1)
        return out

    if isinstance(value, (list, tuple, set)):
        out_list = []
        for i, item in enumerate(value):
            if i >= 20:
                break
            out_list.append(_normalize_metadata_value(item, config=config, depth=depth + 1))
        return out_list

    return _truncate_text(str(value), int(config.max_metadata_value_chars))


def _sanitize_metadata(metadata_value: Any, *, config: Any) -> Dict[str, Any]:
    if metadata_value is None:
        return {}
    if not isinstance(metadata_value, dict):
        return {"value": _normalize_metadata_value(metadata_value, config=config, depth=0)}

    allow = set(config.metadata_allowlist) if config.metadata_allowlist else None
    deny = set(config.metadata_denylist) if config.metadata_denylist else None

    out: Dict[str, Any] = {}
    for i, (k, v) in enumerate(metadata_value.items()):
        if i >= int(config.max_metadata_items):
            break
        key = str(k)
        if allow is not None and key not in allow:
            continue
        if deny is not None and key in deny:
            continue
        out[key] = _normalize_metadata_value(v, config=config, depth=0)

    max_bytes = int(config.max_metadata_bytes)
    if max_bytes <= 0:
        return {}

    def size_bytes(obj: Dict[str, Any]) -> int:
        try:
            return len(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8"))
        except Exception:  # noqa: BLE001
            return max_bytes + 1

    if size_bytes(out) <= max_bytes:
        return out

    trimmed = dict(out)
    for key in list(out.keys())[::-1]:
        trimmed.pop(key, None)
        if size_bytes(trimmed) <= max_bytes:
            return trimmed

    return {}


def _payload_size_bytes(payload: Dict[str, Any]) -> int:
    try:
        return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8"))
    except Exception:  # noqa: BLE001
        return 0


def _inc_stat(name: str, amount: int = 1) -> None:
    with _stats_lock:
        setattr(_stats, name, getattr(_stats, name) + amount)


def get_stats() -> Dict[str, int]:
    """
    Returns basic counters for debugging and monitoring drop/retry behavior.
    """
    with _stats_lock:
        stats: Dict[str, int] = asdict(_stats)

    q = _event_queue
    stats["queue_size"] = q.qsize() if q is not None else 0
    stats["queue_max_size"] = q.maxsize if q is not None else 0
    stats["pid"] = os.getpid()
    return stats


def _is_retryable_status(status_code: int) -> bool:
    return status_code >= 500 or status_code in (408, 409, 429)


def _send_event(payload: Dict[str, Any], api_url: str, project_key: str) -> None:
    """
    Best-effort network send with small retries and backoff.
    Never raises (callers should treat as fire-and-forget).
    """
    config = get_config()
    url = f"{api_url.rstrip('/')}/api/v1/events"
    headers = {"Content-Type": "application/json", "X-Project-Key": project_key}
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)

    for attempt in range(config.max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, data=body, timeout=config.timeout)
            if 200 <= resp.status_code < 300:
                _inc_stat("sent")
                return

            if not _is_retryable_status(resp.status_code):
                _inc_stat("failed")
                if config.debug:
                    logger.debug("Sigmoda event rejected status=%s", resp.status_code)
                return

            _inc_stat("retries")
        except Exception as exc:  # noqa: BLE001 - best effort, never break app
            _inc_stat("retries")
            if config.debug:
                logger.debug("Sigmoda event send error: %s", exc)

        if attempt >= config.max_retries:
            break

        backoff = (config.backoff_base * (2**attempt)) + (random.random() * config.backoff_base)
        time.sleep(backoff)

    _inc_stat("failed")


def _worker_loop() -> None:
    while True:
        if _worker_stop.is_set():
            return

        q = _event_queue
        if q is None:
            time.sleep(0.05)
            continue

        try:
            payload, api_url, project_key = q.get(timeout=0.1)
        except queue.Empty:
            continue

        try:
            _send_event(payload, api_url, project_key)
        except Exception as exc:  # noqa: BLE001 - defensive
            try:
                config = get_config()
            except Exception:  # noqa: BLE001
                config = None
            if config is not None and config.debug:
                logger.debug("Sigmoda worker failed to send event: %s", exc)
        finally:
            q.task_done()


def _ensure_worker_started() -> None:
    global _event_queue, _worker_thread, _pid, _stats
    current_pid = os.getpid()
    if current_pid != _pid:
        _pid = current_pid
        _event_queue = None
        _worker_thread = None
        _worker_stop.clear()
        with _stats_lock:
            _stats = Stats()

    config = get_config()

    if _event_queue is None:
        maxsize = max(1, int(config.max_queue_size))
        _event_queue = queue.Queue(maxsize=maxsize)

    if _worker_thread is None or not _worker_thread.is_alive():
        _worker_stop.clear()
        _worker_thread = threading.Thread(target=_worker_loop, name="sigmoda-worker", daemon=True)
        _worker_thread.start()


def flush(timeout: Optional[float] = None) -> None:
    """
    Best-effort flush of pending events in the background queue.

    If timeout is None, waits until the queue is fully drained.
    """
    q = _event_queue
    if q is None:
        return

    if timeout is None:
        q.join()
        return

    deadline = time.monotonic() + max(0.0, float(timeout))
    while q.unfinished_tasks:  # noqa: SLF001 - using Queue internals for timed join
        if time.monotonic() >= deadline:
            return
        time.sleep(0.01)


def _queue_dispatch(payload: Dict[str, Any], api_url: str, project_key: str) -> None:
    _ensure_worker_started()
    q = _event_queue
    if q is None:
        return

    try:
        q.put_nowait((payload, api_url, project_key))
        _inc_stat("enqueued")
    except queue.Full:
        _inc_stat("dropped_queue_full")
        config = get_config()
        if config.debug:
            logger.debug("Sigmoda queue full; dropping event.")


# Allows tests to monkeypatch the dispatching mechanism.
_dispatch = _queue_dispatch


def _atexit_flush() -> None:
    try:
        flush(timeout=1.0)
    except Exception:  # noqa: BLE001
        return


atexit.register(_atexit_flush)


def log_event(
    *,
    provider: str,
    model: str,
    type: str,
    prompt: str,
    response: str,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
    duration_ms: Optional[float] = None,
    status: str = "ok",
    error_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
) -> None:
    """
    Log a single event to Sigmoda.
    """
    config = get_config()
    if config.disabled:
        return

    if config.sample_rate < 1.0:
        if random.random() >= float(config.sample_rate):
            _inc_stat("dropped_sampled")
            return

    prompt_value = prompt
    response_value = response
    if not config.capture_content:
        prompt_value = ""
        response_value = ""
    elif config.redact is not None:
        try:
            prompt_value = config.redact(prompt_value)
        except Exception as exc:  # noqa: BLE001
            if config.debug:
                logger.debug("Sigmoda redact(prompt) failed: %s", exc)
        try:
            response_value = config.redact(response_value)
        except Exception as exc:  # noqa: BLE001
            if config.debug:
                logger.debug("Sigmoda redact(response) failed: %s", exc)

    prompt_value = _truncate_text(prompt_value, int(config.max_prompt_chars))
    response_value = _truncate_text(response_value, int(config.max_response_chars))
    metadata_sanitized = _sanitize_metadata(metadata or {}, config=config)

    payload: Dict[str, Any] = {
        "schema_version": config.schema_version,
        "sdk": {"name": "sigmoda", "version": _SDK_VERSION},
        "env": config.env,
        "timestamp": timestamp or _timestamp(),
        "provider": provider,
        "model": model,
        "type": type,
        "prompt": prompt_value,
        "response": response_value,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "duration_ms": duration_ms,
        "status": status,
        "error_type": error_type,
        "metadata": metadata_sanitized,
    }
    if config.project_id is not None:
        payload["project_id"] = config.project_id

    max_bytes = int(config.max_payload_bytes)
    if max_bytes > 0:
        size = _payload_size_bytes(payload)
        if size > max_bytes:
            payload["metadata"] = {}
            size = _payload_size_bytes(payload)
        for _ in range(5):
            if size <= max_bytes:
                break
            prompt_str = str(payload.get("prompt", ""))
            response_str = str(payload.get("response", ""))
            if not prompt_str and not response_str:
                _inc_stat("dropped_payload_too_large")
                return
            payload["prompt"] = prompt_str[: max(0, len(prompt_str) // 2)]
            payload["response"] = response_str[: max(0, len(response_str) // 2)]
            size = _payload_size_bytes(payload)
        if size > max_bytes:
            _inc_stat("dropped_payload_too_large")
            return

    try:
        _dispatch(payload, config.api_url, config.project_key)
    except Exception as exc:  # noqa: BLE001 - defensive, should be rare
        logger.debug("Sigmoda dispatch failed: %s", exc)
