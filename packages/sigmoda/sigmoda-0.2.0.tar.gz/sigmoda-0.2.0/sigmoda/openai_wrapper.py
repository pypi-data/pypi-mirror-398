import logging
import os
import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import openai

from .client import log_event
from . import config as _config_mod

logger = logging.getLogger(__name__)


_openai_client: Any = None
_openai_client_key: Optional[Tuple[int, Optional[str], Optional[str]]] = None


def _env_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _sigmoda_disabled_fast() -> bool:
    cfg = getattr(_config_mod, "_config", None)
    if cfg is not None:
        return bool(getattr(cfg, "disabled", False))
    return _env_truthy(os.getenv("SIGMODA_DISABLED"))


def _sigmoda_capture_content_fast() -> bool:
    cfg = getattr(_config_mod, "_config", None)
    if cfg is None:
        return False
    return bool(getattr(cfg, "capture_content", False))


def _get_openai_api_key() -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key.strip():
        return api_key.strip()
    api_key_attr = getattr(openai, "api_key", None)
    if api_key_attr and str(api_key_attr).strip():
        return str(api_key_attr).strip()
    return None


def _ensure_sigmoda_config() -> Optional[Any]:
    cfg = getattr(_config_mod, "_config", None)
    if cfg is not None:
        return cfg
    if _sigmoda_disabled_fast():
        return None
    project_key = os.getenv("SIGMODA_PROJECT_KEY") or os.getenv("SIGMODA_API_KEY")
    if project_key and project_key.strip():
        return _config_mod.init()
    raise ValueError(
        "Sigmoda is not initialized. Set SIGMODA_PROJECT_KEY (or SIGMODA_API_KEY), "
        "or call sigmoda.init(...). To disable logging, set SIGMODA_DISABLED=1."
    )


def _preflight_check() -> None:
    if _get_openai_api_key() is None:
        raise ValueError(
            "Missing OPENAI_API_KEY. Set the OPENAI_API_KEY environment variable "
            "or set openai.api_key before calling sigmoda.openai.*."
        )
    if _sigmoda_disabled_fast():
        return
    _ensure_sigmoda_config()


def _safe_log_event(**kwargs: Any) -> None:
    try:
        log_event(**kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Sigmoda logging failed (ignored): %s", exc)


def _get_openai_client() -> Any:
    """
    Lazily create (and cache) an OpenAI client for openai>=1.x.
    Returns None if the OpenAI client class is not available (legacy SDK).
    """
    OpenAI = getattr(openai, "OpenAI", None)
    if OpenAI is None:
        return None

    global _openai_client, _openai_client_key
    key = (os.getpid(), getattr(openai, "api_key", None), os.getenv("OPENAI_API_KEY"))
    if _openai_client is None or _openai_client_key != key:
        _openai_client_key = key
        api_key = getattr(openai, "api_key", None)
        if api_key:
            _openai_client = OpenAI(api_key=api_key)
        else:
            _openai_client = OpenAI()
    return _openai_client


def _openai_chat_completion_create(**params: Any) -> Any:
    """
    Calls the OpenAI chat completions API (openai>=1,<3), with a legacy fallback.
    """
    client = _get_openai_client()
    if client is not None:
        return client.chat.completions.create(**params)

    legacy = getattr(openai, "ChatCompletion", None)
    if legacy is not None and hasattr(legacy, "create"):
        return legacy.create(**params)

    raise RuntimeError("sigmoda requires openai>=1,<3. Please upgrade the OpenAI Python package.")


def _openai_responses_create(**params: Any) -> Any:
    """
    Calls the OpenAI Responses API (openai>=1,<3), with a legacy fallback.
    """
    client = _get_openai_client()
    if client is not None:
        return client.responses.create(**params)

    legacy = getattr(openai, "responses", None)
    if legacy is not None and hasattr(legacy, "create"):
        return legacy.create(**params)

    raise RuntimeError("sigmoda requires openai>=1,<3. Please upgrade the OpenAI Python package.")


def _extract_prompt(messages: Any) -> str:
    if not messages:
        return ""
    if isinstance(messages, list):
        parts = []
        for item in messages:
            if not isinstance(item, dict):
                parts.append(str(item))
                continue
            role = item.get("role") or ""
            content = item.get("content")
            content_str = _content_to_text(content)
            prefix = f"{role}: " if role else ""
            parts.append(prefix + content_str)
        return "\n".join(parts)
    return str(messages)


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, list):
        text_parts = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") == "text":
                    text_parts.append(str(c.get("text", "")))
                elif "text" in c:
                    text_parts.append(str(c["text"]))
            elif isinstance(c, str):
                text_parts.append(c)
        return " ".join(filter(None, text_parts))
    return str(content)


def _extract_response_text(response: Any) -> str:
    try:
        choices = response.get("choices") if isinstance(response, dict) else getattr(response, "choices", None)
    except Exception:  # noqa: BLE001
        choices = None
    if not choices:
        return ""
    first = choices[0]
    if isinstance(first, dict):
        message = first.get("message") or {}
        content = message.get("content")
        return _content_to_text(content)
    # If choice is an object with message attr
    message = getattr(first, "message", None)
    content = None
    if isinstance(message, dict):
        content = message.get("content")
    elif hasattr(message, "get"):
        content = message.get("content")
    elif hasattr(message, "content"):
        content = getattr(message, "content")
    return _content_to_text(content)


def _extract_usage(response: Any) -> Dict[str, Optional[int]]:
    usage = None
    if isinstance(response, dict):
        usage = response.get("usage")
    else:
        usage = getattr(response, "usage", None)
    if usage is None:
        return {"prompt_tokens": None, "completion_tokens": None}

    if isinstance(usage, dict):
        prompt_tokens = usage.get("prompt_tokens")
        if prompt_tokens is None:
            prompt_tokens = usage.get("input_tokens")
        completion_tokens = usage.get("completion_tokens")
        if completion_tokens is None:
            completion_tokens = usage.get("output_tokens")
        return {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}

    prompt_tokens = getattr(usage, "prompt_tokens", None)
    if prompt_tokens is None:
        prompt_tokens = getattr(usage, "input_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    if completion_tokens is None:
        completion_tokens = getattr(usage, "output_tokens", None)
    if prompt_tokens is not None or completion_tokens is not None:
        return {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}

    for method_name in ("to_dict", "model_dump", "dict"):
        method = getattr(usage, method_name, None)
        if not callable(method):
            continue
        try:
            usage_dict = method()
        except Exception:  # noqa: BLE001
            continue
        if isinstance(usage_dict, dict):
            prompt_tokens = usage_dict.get("prompt_tokens")
            if prompt_tokens is None:
                prompt_tokens = usage_dict.get("input_tokens")
            completion_tokens = usage_dict.get("completion_tokens")
            if completion_tokens is None:
                completion_tokens = usage_dict.get("output_tokens")
            return {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            }

    return {"prompt_tokens": None, "completion_tokens": None}


def _extract_tool_call_names(response: Any) -> List[str]:
    try:
        choices = response.get("choices") if isinstance(response, dict) else getattr(response, "choices", None)
    except Exception:  # noqa: BLE001
        choices = None
    if not choices:
        return []

    names: List[str] = []
    for choice in choices:
        message = None
        if isinstance(choice, dict):
            message = choice.get("message")
        else:
            message = getattr(choice, "message", None)
        if message is None:
            continue

        tool_calls = None
        if isinstance(message, dict):
            tool_calls = message.get("tool_calls")
        else:
            tool_calls = getattr(message, "tool_calls", None)

        if tool_calls:
            for tc in tool_calls:
                fn = None
                if isinstance(tc, dict):
                    fn = tc.get("function")
                else:
                    fn = getattr(tc, "function", None)
                if isinstance(fn, dict):
                    name = fn.get("name")
                else:
                    name = getattr(fn, "name", None)
                if name:
                    names.append(str(name))

    # Dedupe while keeping order
    seen: Set[str] = set()
    out: List[str] = []
    for n in names:
        if n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out


def _responses_input_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: List[str] = []
        for item in value:
            if isinstance(item, dict):
                role = item.get("role") or ""
                content = item.get("content")
                if content is None and "text" in item:
                    content = item.get("text")
                content_str = _content_to_text(content)
                prefix = f"{role}: " if role else ""
                if content_str:
                    parts.append(prefix + content_str)
                else:
                    parts.append(prefix + str(item))
            else:
                parts.append(str(item))
        return "\n".join(filter(None, parts))
    if isinstance(value, dict):
        content = value.get("content")
        if content is None and "text" in value:
            content = value.get("text")
        if content is None and "input_text" in value:
            content = value.get("input_text")
        return _content_to_text(content)
    return str(value)


def _extract_responses_prompt(params: Dict[str, Any]) -> str:
    parts: List[str] = []
    instructions = params.get("instructions")
    if instructions:
        parts.append(str(instructions))
    input_value = params.get("input")
    if input_value is not None:
        input_text = _responses_input_to_text(input_value)
        if input_text:
            parts.append(input_text)
    if not parts and "messages" in params:
        parts.append(_extract_prompt(params.get("messages")))
    return "\n".join(filter(None, parts))


def _extract_responses_output_text(response: Any) -> str:
    output_text = None
    output = None
    if isinstance(response, dict):
        output_text = response.get("output_text")
        output = response.get("output")
    else:
        output_text = getattr(response, "output_text", None)
        output = getattr(response, "output", None)

    if output_text is not None:
        return str(output_text)
    if not output:
        return ""

    parts: List[str] = []
    for item in output:
        if isinstance(item, dict):
            content = item.get("content")
            if content is None and "text" in item:
                content = item.get("text")
            if content is None and "output_text" in item:
                content = item.get("output_text")
            parts.append(_content_to_text(content))
        else:
            content = getattr(item, "content", None)
            if content is None:
                content = getattr(item, "text", None)
            if content is None:
                content = getattr(item, "output_text", None)
            parts.append(_content_to_text(content))
    return "\n".join(filter(None, parts))


def _extract_responses_tool_call_names(response: Any) -> List[str]:
    output = None
    if isinstance(response, dict):
        output = response.get("output")
    else:
        output = getattr(response, "output", None)
    if not output:
        return []

    tool_names: List[str] = []
    for item in output:
        if isinstance(item, dict):
            item_type = str(item.get("type") or "")
            if "tool" in item_type or "function" in item_type:
                name = item.get("name") or item.get("tool_name")
                if name:
                    tool_names.append(str(name))
                fn = item.get("function") or item.get("tool")
                if isinstance(fn, dict):
                    fn_name = fn.get("name")
                    if fn_name:
                        tool_names.append(str(fn_name))
        else:
            item_type = str(getattr(item, "type", "") or "")
            if "tool" in item_type or "function" in item_type:
                name = getattr(item, "name", None) or getattr(item, "tool_name", None)
                if name:
                    tool_names.append(str(name))
                fn = getattr(item, "function", None) or getattr(item, "tool", None)
                if fn is not None:
                    fn_name = getattr(fn, "name", None)
                    if fn_name:
                        tool_names.append(str(fn_name))

    return tool_names


def _response_event_type(event: Any) -> Optional[str]:
    if isinstance(event, dict):
        return event.get("type") or event.get("event")
    return getattr(event, "type", None) or getattr(event, "event", None)


def _response_event_delta_text(event: Any) -> str:
    if isinstance(event, dict):
        delta = event.get("delta")
        if isinstance(delta, str):
            return delta
        if isinstance(delta, dict) and "text" in delta:
            return str(delta.get("text") or "")
        text = event.get("text")
        if isinstance(text, str):
            return text
        return ""
    delta = getattr(event, "delta", None)
    if isinstance(delta, str):
        return delta
    if delta is not None and hasattr(delta, "text"):
        return str(getattr(delta, "text") or "")
    text = getattr(event, "text", None)
    if isinstance(text, str):
        return text
    return ""


def _response_event_response(event: Any) -> Any:
    if isinstance(event, dict):
        return event.get("response")
    return getattr(event, "response", None)


def _merge_sigmoda_metadata(user_metadata: Any, internal: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(user_metadata, dict):
        out.update(user_metadata)
    elif user_metadata is not None:
        out["value"] = str(user_metadata)

    existing = out.get("_sigmoda")
    if isinstance(existing, dict):
        existing.update(internal)
        out["_sigmoda"] = existing
    else:
        out["_sigmoda"] = internal
    return out


def _stream_chunk_content_and_tools(chunk: Any) -> Tuple[str, List[str]]:
    """
    Extracts assistant delta content and tool-call names from a chat.completions stream chunk.
    """
    try:
        choices = chunk.get("choices") if isinstance(chunk, dict) else getattr(chunk, "choices", None)
    except Exception:  # noqa: BLE001
        choices = None
    if not choices:
        return "", []

    first = choices[0]
    delta = None
    if isinstance(first, dict):
        delta = first.get("delta")
    else:
        delta = getattr(first, "delta", None)
    if delta is None:
        return "", []

    content = ""
    if isinstance(delta, dict):
        content = str(delta.get("content") or "")
        tool_calls = delta.get("tool_calls") or []
    else:
        content = str(getattr(delta, "content", "") or "")
        tool_calls = getattr(delta, "tool_calls", None) or []

    tool_names: List[str] = []
    for tc in tool_calls:
        fn = None
        if isinstance(tc, dict):
            fn = tc.get("function")
        else:
            fn = getattr(tc, "function", None)
        if isinstance(fn, dict):
            name = fn.get("name")
        else:
            name = getattr(fn, "name", None)
        if name:
            tool_names.append(str(name))

    return content, tool_names


class ChatCompletion:
    @staticmethod
    def create(**kwargs: Any):
        params = dict(kwargs)
        sigmoda_metadata = params.pop("sigmoda_metadata", None)
        model = params.get("model", "")
        stream = bool(params.get("stream") is True)

        _preflight_check()

        start = time.perf_counter()
        try:
            if _sigmoda_disabled_fast():
                return _openai_chat_completion_create(**params)
            capture_content = _sigmoda_capture_content_fast()
            prompt_text = _extract_prompt(params.get("messages")) if capture_content else ""
            response = _openai_chat_completion_create(**params)
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.perf_counter() - start) * 1000
            _safe_log_event(
                provider="openai",
                model=model,
                type="chat_completion",
                prompt=_extract_prompt(params.get("messages")) if _sigmoda_capture_content_fast() else "",
                response="",
                tokens_in=None,
                tokens_out=None,
                duration_ms=duration_ms,
                status="error",
                error_type=exc.__class__.__name__,
                metadata=_merge_sigmoda_metadata(sigmoda_metadata, {"stream": stream}),
            )
            raise

        if stream:
            return _LoggedStream(
                stream=response,
                start=start,
                model=model,
                prompt_text=prompt_text,
                sigmoda_metadata=sigmoda_metadata,
                capture_content=capture_content,
            )

        duration_ms = (time.perf_counter() - start) * 1000
        usage = _extract_usage(response)
        response_text = _extract_response_text(response) if capture_content else ""
        tool_call_names = _extract_tool_call_names(response)

        internal = {"stream": False}
        if tool_call_names:
            internal["tool_call_names"] = tool_call_names
        _safe_log_event(
            provider="openai",
            model=model,
            type="chat_completion",
            prompt=prompt_text,
            response=response_text,
            tokens_in=usage.get("prompt_tokens"),
            tokens_out=usage.get("completion_tokens"),
            duration_ms=duration_ms,
            status="ok",
            metadata=_merge_sigmoda_metadata(sigmoda_metadata, internal),
        )
        return response


class Responses:
    @staticmethod
    def create(**kwargs: Any):
        params = dict(kwargs)
        sigmoda_metadata = params.pop("sigmoda_metadata", None)
        model = params.get("model", "")
        stream = bool(params.get("stream") is True)

        _preflight_check()

        start = time.perf_counter()
        try:
            if _sigmoda_disabled_fast():
                return _openai_responses_create(**params)
            capture_content = _sigmoda_capture_content_fast()
            prompt_text = _extract_responses_prompt(params) if capture_content else ""
            response = _openai_responses_create(**params)
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.perf_counter() - start) * 1000
            _safe_log_event(
                provider="openai",
                model=model,
                type="response",
                prompt=_extract_responses_prompt(params) if _sigmoda_capture_content_fast() else "",
                response="",
                tokens_in=None,
                tokens_out=None,
                duration_ms=duration_ms,
                status="error",
                error_type=exc.__class__.__name__,
                metadata=_merge_sigmoda_metadata(sigmoda_metadata, {"stream": stream}),
            )
            raise

        if stream:
            return _LoggedResponsesStream(
                stream=response,
                start=start,
                model=model,
                prompt_text=prompt_text,
                sigmoda_metadata=sigmoda_metadata,
                capture_content=capture_content,
            )

        duration_ms = (time.perf_counter() - start) * 1000
        usage = _extract_usage(response)
        response_text = _extract_responses_output_text(response) if capture_content else ""
        tool_call_names = _extract_responses_tool_call_names(response)

        internal = {"stream": False}
        if tool_call_names:
            internal["tool_call_names"] = tool_call_names
        _safe_log_event(
            provider="openai",
            model=model,
            type="response",
            prompt=prompt_text,
            response=response_text,
            tokens_in=usage.get("prompt_tokens"),
            tokens_out=usage.get("completion_tokens"),
            duration_ms=duration_ms,
            status="ok",
            metadata=_merge_sigmoda_metadata(sigmoda_metadata, internal),
        )
        return response


class _LoggedStream:
    def __init__(
        self,
        *,
        stream: Any,
        start: float,
        model: str,
        prompt_text: str,
        sigmoda_metadata: Any,
        capture_content: bool,
    ) -> None:
        self._stream = stream
        self._iter = iter(stream)
        self._start = start
        self._model = model
        self._prompt_text = prompt_text
        self._sigmoda_metadata = sigmoda_metadata
        self._capture_content = capture_content
        self._buffer: List[str] = []
        self._buffer_chars = 0
        self._tool_names: List[str] = []
        self._usage_latest: Dict[str, Optional[int]] = {"prompt_tokens": None, "completion_tokens": None}
        self._done = False

    def __iter__(self):
        return self

    def __next__(self):
        try:
            chunk = next(self._iter)
        except StopIteration:
            if not self._done:
                self._done = True
                duration_ms = (time.perf_counter() - self._start) * 1000
                response_text = "".join(self._buffer) if self._capture_content else ""
                internal: Dict[str, Any] = {"stream": True}
                if self._tool_names:
                    internal["tool_call_names"] = self._tool_names
                _safe_log_event(
                    provider="openai",
                    model=self._model,
                    type="chat_completion",
                    prompt=self._prompt_text,
                    response=response_text,
                    tokens_in=self._usage_latest.get("prompt_tokens"),
                    tokens_out=self._usage_latest.get("completion_tokens"),
                    duration_ms=duration_ms,
                    status="ok",
                    metadata=_merge_sigmoda_metadata(self._sigmoda_metadata, internal),
                )
            raise
        except Exception as exc:  # noqa: BLE001
            if not self._done:
                self._done = True
                duration_ms = (time.perf_counter() - self._start) * 1000
                internal = {"stream": True}
                if self._tool_names:
                    internal["tool_call_names"] = self._tool_names
                _safe_log_event(
                    provider="openai",
                    model=self._model,
                    type="chat_completion",
                    prompt=self._prompt_text,
                    response="",
                    tokens_in=self._usage_latest.get("prompt_tokens"),
                    tokens_out=self._usage_latest.get("completion_tokens"),
                    duration_ms=duration_ms,
                    status="error",
                    error_type=exc.__class__.__name__,
                    metadata=_merge_sigmoda_metadata(self._sigmoda_metadata, internal),
                )
            raise

        usage = _extract_usage(chunk)
        if usage.get("prompt_tokens") is not None:
            self._usage_latest["prompt_tokens"] = usage.get("prompt_tokens")
        if usage.get("completion_tokens") is not None:
            self._usage_latest["completion_tokens"] = usage.get("completion_tokens")

        delta_text, delta_tools = _stream_chunk_content_and_tools(chunk)
        if delta_tools:
            for name in delta_tools:
                if name not in self._tool_names:
                    self._tool_names.append(name)

        if self._capture_content and delta_text and self._buffer_chars < 20000:
            remaining = 20000 - self._buffer_chars
            self._buffer.append(delta_text[:remaining])
            self._buffer_chars += len(delta_text[:remaining])

        return chunk

    def close(self) -> None:
        close_fn = getattr(self._stream, "close", None)
        if callable(close_fn):
            try:
                close_fn()
            except Exception:  # noqa: BLE001
                return

    def __del__(self) -> None:  # pragma: no cover
        try:
            if not self._done:
                self.close()
        except Exception:  # noqa: BLE001
            return

    def __getattr__(self, name: str) -> Any:  # pragma: no cover
        return getattr(self._stream, name)


class _LoggedResponsesStream:
    def __init__(
        self,
        *,
        stream: Any,
        start: float,
        model: str,
        prompt_text: str,
        sigmoda_metadata: Any,
        capture_content: bool,
    ) -> None:
        self._stream = stream
        self._iter = iter(stream)
        self._start = start
        self._model = model
        self._prompt_text = prompt_text
        self._sigmoda_metadata = sigmoda_metadata
        self._capture_content = capture_content
        self._buffer: List[str] = []
        self._buffer_chars = 0
        self._tool_names: List[str] = []
        self._usage_latest: Dict[str, Optional[int]] = {"prompt_tokens": None, "completion_tokens": None}
        self._final_response_text: Optional[str] = None
        self._done = False

    def __iter__(self):
        return self

    def __next__(self):
        try:
            event = next(self._iter)
        except StopIteration:
            if not self._done:
                self._done = True
                duration_ms = (time.perf_counter() - self._start) * 1000
                response_text = self._final_response_text
                if response_text is None:
                    response_text = "".join(self._buffer) if self._capture_content else ""
                internal: Dict[str, Any] = {"stream": True}
                if self._tool_names:
                    internal["tool_call_names"] = self._tool_names
                _safe_log_event(
                    provider="openai",
                    model=self._model,
                    type="response",
                    prompt=self._prompt_text,
                    response=response_text if self._capture_content else "",
                    tokens_in=self._usage_latest.get("prompt_tokens"),
                    tokens_out=self._usage_latest.get("completion_tokens"),
                    duration_ms=duration_ms,
                    status="ok",
                    metadata=_merge_sigmoda_metadata(self._sigmoda_metadata, internal),
                )
            raise
        except Exception as exc:  # noqa: BLE001
            if not self._done:
                self._done = True
                duration_ms = (time.perf_counter() - self._start) * 1000
                internal = {"stream": True}
                if self._tool_names:
                    internal["tool_call_names"] = self._tool_names
                _safe_log_event(
                    provider="openai",
                    model=self._model,
                    type="response",
                    prompt=self._prompt_text,
                    response="",
                    tokens_in=self._usage_latest.get("prompt_tokens"),
                    tokens_out=self._usage_latest.get("completion_tokens"),
                    duration_ms=duration_ms,
                    status="error",
                    error_type=exc.__class__.__name__,
                    metadata=_merge_sigmoda_metadata(self._sigmoda_metadata, internal),
                )
            raise

        event_type = _response_event_type(event)
        if event_type == "response.completed":
            response = _response_event_response(event)
            if response is not None:
                usage = _extract_usage(response)
                if usage.get("prompt_tokens") is not None:
                    self._usage_latest["prompt_tokens"] = usage.get("prompt_tokens")
                if usage.get("completion_tokens") is not None:
                    self._usage_latest["completion_tokens"] = usage.get("completion_tokens")
                if self._capture_content:
                    response_text = _extract_responses_output_text(response)
                    if response_text:
                        self._final_response_text = response_text
                tool_names = _extract_responses_tool_call_names(response)
                for name in tool_names:
                    if name not in self._tool_names:
                        self._tool_names.append(name)

        delta_text = ""
        if event_type is None or "delta" in event_type:
            delta_text = _response_event_delta_text(event)
        if self._capture_content and delta_text and self._buffer_chars < 20000:
            remaining = 20000 - self._buffer_chars
            self._buffer.append(delta_text[:remaining])
            self._buffer_chars += len(delta_text[:remaining])

        return event

    def close(self) -> None:
        close_fn = getattr(self._stream, "close", None)
        if callable(close_fn):
            try:
                close_fn()
            except Exception:  # noqa: BLE001
                return

    def __del__(self) -> None:  # pragma: no cover
        try:
            if not self._done:
                self.close()
        except Exception:  # noqa: BLE001
            return

    def __getattr__(self, name: str) -> Any:  # pragma: no cover
        return getattr(self._stream, name)


class _ChatCompletions:  # noqa: D101 - internal wrapper
    @staticmethod
    def create(**kwargs: Any) -> Any:
        return ChatCompletion.create(**kwargs)


class _Chat:  # noqa: D101 - internal wrapper
    def __init__(self) -> None:
        self.completions = _ChatCompletions()


chat = _Chat()


class _Responses:  # noqa: D101 - internal wrapper
    @staticmethod
    def create(**kwargs: Any) -> Any:
        return Responses.create(**kwargs)


responses = _Responses()
