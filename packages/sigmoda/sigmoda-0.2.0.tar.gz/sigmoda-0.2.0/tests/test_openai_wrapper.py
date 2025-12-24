import pytest

import sigmoda.client as client
import sigmoda.config as config
from sigmoda import openai_wrapper


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    config._config = None  # type: ignore[attr-defined]
    monkeypatch.setattr(client, "_dispatch", client._queue_dispatch)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client._event_queue = None  # type: ignore[attr-defined]
    client._worker_thread = None  # type: ignore[attr-defined]
    client._worker_stop.clear()  # type: ignore[attr-defined]
    monkeypatch.setattr(openai_wrapper, "_openai_client", None)
    monkeypatch.setattr(openai_wrapper, "_openai_client_key", None)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.delenv("SIGMODA_PROJECT_KEY", raising=False)
    monkeypatch.delenv("SIGMODA_API_KEY", raising=False)
    monkeypatch.delenv("SIGMODA_DISABLED", raising=False)
    yield
    config._config = None  # type: ignore[attr-defined]
    monkeypatch.setattr(client, "_dispatch", client._queue_dispatch)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client._event_queue = None  # type: ignore[attr-defined]
    client._worker_thread = None  # type: ignore[attr-defined]
    client._worker_stop.clear()  # type: ignore[attr-defined]
    monkeypatch.setattr(openai_wrapper, "_openai_client", None)
    monkeypatch.setattr(openai_wrapper, "_openai_client_key", None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SIGMODA_PROJECT_KEY", raising=False)
    monkeypatch.delenv("SIGMODA_API_KEY", raising=False)
    monkeypatch.delenv("SIGMODA_DISABLED", raising=False)


def test_chat_completion_logs_event(monkeypatch):
    config.init(project_key="key", project_id="proj", env="test")
    captured = {}

    def capture(payload, api_url, project_key):
        captured["payload"] = payload
        captured["api_url"] = api_url
        captured["project_key"] = project_key

    monkeypatch.setattr(client, "_dispatch", capture)

    fake_response = {
        "choices": [
            {"message": {"content": "Hi there!", "tool_calls": [{"function": {"name": "lookup_user"}}]}}
        ],
        "usage": {"prompt_tokens": 4, "completion_tokens": 6},
    }

    def fake_create(**kwargs):
        return fake_response

    if getattr(openai_wrapper.openai, "OpenAI", None) is not None:
        class FakeOpenAI:  # noqa: D101 - test helper
            def __init__(self, *args, **kwargs):
                class FakeCompletions:  # noqa: D101 - test helper
                    @staticmethod
                    def create(**kw):  # noqa: ANN001 - test helper
                        return fake_create(**kw)

                class FakeChat:  # noqa: D101 - test helper
                    completions = FakeCompletions

                self.chat = FakeChat()

        monkeypatch.setattr(openai_wrapper.openai, "OpenAI", FakeOpenAI)
    else:
        monkeypatch.setattr(openai_wrapper.openai.ChatCompletion, "create", fake_create)

    resp = openai_wrapper.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
        sigmoda_metadata={"route": "support"},
    )

    assert resp is fake_response
    payload = captured["payload"]
    assert captured["project_key"] == "key"
    assert payload["provider"] == "openai"
    assert payload["model"] == "gpt-4"
    assert payload["status"] == "ok"
    assert payload["tokens_in"] == 4
    assert payload["tokens_out"] == 6
    assert "Hello" in payload["prompt"]
    assert payload["response"] == "Hi there!"
    assert payload["metadata"]["route"] == "support"
    assert payload["metadata"]["_sigmoda"]["tool_call_names"] == ["lookup_user"]
    assert payload["metadata"]["_sigmoda"]["stream"] is False


def test_chat_completions_surface_delegates(monkeypatch):
    monkeypatch.setenv("SIGMODA_DISABLED", "1")
    called = {}

    def fake(**kwargs):
        called["kwargs"] = kwargs
        return {"choices": [{"message": {"content": "ok"}}], "usage": {}}

    monkeypatch.setattr(openai_wrapper.ChatCompletion, "create", fake)

    resp = openai_wrapper.chat.completions.create(model="gpt-4", messages=[])
    assert resp["choices"][0]["message"]["content"] == "ok"
    assert called["kwargs"]["model"] == "gpt-4"


def test_init_twice_does_not_double_log(monkeypatch):
    config.init(project_key="key", project_id="proj", env="test")
    config.init(project_key="key2", project_id="proj", env="test")

    calls = {"n": 0}

    def capture(payload, api_url, project_key):
        calls["n"] += 1

    monkeypatch.setattr(client, "_dispatch", capture)

    fake_response = {"choices": [{"message": {"content": "ok"}}], "usage": {}}
    monkeypatch.setattr(openai_wrapper, "_openai_chat_completion_create", lambda **_kw: fake_response)

    resp = openai_wrapper.chat.completions.create(model="gpt-4", messages=[], sigmoda_metadata={})
    assert resp is fake_response
    assert calls["n"] == 1


def test_chat_completion_streaming_logs_on_completion(monkeypatch):
    config.init(project_key="key", project_id="proj", env="test")
    captured = {}

    def capture(payload, api_url, project_key):
        captured["payload"] = payload

    monkeypatch.setattr(client, "_dispatch", capture)

    chunks = [
        {"choices": [{"delta": {"content": "Hi "}}], "usage": {"prompt_tokens": 1}},
        {"choices": [{"delta": {"content": "there", "tool_calls": [{"function": {"name": "tool_a"}}]}}], "usage": {"completion_tokens": 2}},
    ]

    def fake_create(**kwargs):
        assert kwargs.get("stream") is True
        return iter(chunks)

    monkeypatch.setattr(openai_wrapper, "_openai_chat_completion_create", fake_create)

    stream = openai_wrapper.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
        stream=True,
        sigmoda_metadata={"route": "stream"},
    )

    yielded = list(stream)
    assert yielded == chunks

    payload = captured["payload"]
    assert payload["status"] == "ok"
    assert payload["response"] == "Hi there"
    assert payload["tokens_in"] == 1
    assert payload["tokens_out"] == 2
    assert payload["metadata"]["_sigmoda"]["stream"] is True
    assert payload["metadata"]["_sigmoda"]["tool_call_names"] == ["tool_a"]


def test_stream_not_consumed_does_not_log(monkeypatch):
    config.init(project_key="key", project_id="proj", env="test")
    captured = {}

    def capture(payload, api_url, project_key):
        captured["payload"] = payload

    monkeypatch.setattr(client, "_dispatch", capture)

    chunks = [{"choices": [{"delta": {"content": "Hi"}}], "usage": {}}]
    monkeypatch.setattr(openai_wrapper, "_openai_chat_completion_create", lambda **_kw: iter(chunks))

    stream = openai_wrapper.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
        stream=True,
        sigmoda_metadata={"route": "stream"},
    )
    assert captured == {}
    del stream
    assert captured == {}


def test_wrapper_does_not_break_if_not_initialized(monkeypatch):
    monkeypatch.setenv("SIGMODA_DISABLED", "1")
    captured = {}

    def capture(*_args, **_kwargs):
        captured["called"] = True

    monkeypatch.setattr(client, "_dispatch", capture)

    fake_response = {"choices": [{"message": {"content": "ok"}}], "usage": {}}
    monkeypatch.setattr(openai_wrapper, "_openai_chat_completion_create", lambda **_kw: fake_response)

    resp = openai_wrapper.chat.completions.create(model="gpt-4", messages=[], sigmoda_metadata={})
    assert resp is fake_response
    assert captured == {}


def test_wrapper_disabled_env_is_noop(monkeypatch):
    monkeypatch.setenv("SIGMODA_DISABLED", "1")
    captured = {}

    def capture(*_args, **_kwargs):
        captured["called"] = True

    monkeypatch.setattr(client, "_dispatch", capture)

    fake_response = {"choices": [{"message": {"content": "ok"}}], "usage": {}}
    monkeypatch.setattr(openai_wrapper, "_openai_chat_completion_create", lambda **_kw: fake_response)

    resp = openai_wrapper.chat.completions.create(model="gpt-4", messages=[])
    assert resp is fake_response
    assert captured == {}


def test_chat_completion_logs_error_then_raises(monkeypatch):
    config.init(project_key="key", project_id="proj", env="test")
    captured = {}

    def capture(payload, api_url, project_key):
        captured["payload"] = payload
        captured["api_url"] = api_url
        captured["project_key"] = project_key

    monkeypatch.setattr(client, "_dispatch", capture)

    def fake_create(**kwargs):
        raise RuntimeError("boom")

    if getattr(openai_wrapper.openai, "OpenAI", None) is not None:
        class FakeOpenAI:  # noqa: D101 - test helper
            def __init__(self, *args, **kwargs):
                class FakeCompletions:  # noqa: D101 - test helper
                    @staticmethod
                    def create(**kw):  # noqa: ANN001 - test helper
                        return fake_create(**kw)

                class FakeChat:  # noqa: D101 - test helper
                    completions = FakeCompletions

                self.chat = FakeChat()

        monkeypatch.setattr(openai_wrapper.openai, "OpenAI", FakeOpenAI)
    else:
        monkeypatch.setattr(openai_wrapper.openai.ChatCompletion, "create", fake_create)

    with pytest.raises(RuntimeError):
        openai_wrapper.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            sigmoda_metadata={"route": "support"},
        )

    payload = captured["payload"]
    assert payload["status"] == "error"
    assert payload["error_type"] == "RuntimeError"
    assert payload["response"] == ""


def test_preflight_missing_openai_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("SIGMODA_DISABLED", "1")
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        openai_wrapper.chat.completions.create(model="gpt-4", messages=[])


def test_preflight_missing_sigmoda_key_raises(monkeypatch):
    monkeypatch.delenv("SIGMODA_PROJECT_KEY", raising=False)
    monkeypatch.delenv("SIGMODA_API_KEY", raising=False)
    with pytest.raises(ValueError, match="SIGMODA_PROJECT_KEY"):
        openai_wrapper.chat.completions.create(model="gpt-4", messages=[])


def test_auto_init_from_env(monkeypatch):
    monkeypatch.setenv("SIGMODA_PROJECT_KEY", "key")
    monkeypatch.setenv("SIGMODA_ENV", "test")

    captured = {}

    def capture(payload, api_url, project_key):
        captured["payload"] = payload
        captured["api_url"] = api_url
        captured["project_key"] = project_key

    monkeypatch.setattr(client, "_dispatch", capture)

    fake_response = {"choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}}
    monkeypatch.setattr(openai_wrapper, "_openai_chat_completion_create", lambda **_kw: fake_response)

    resp = openai_wrapper.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": "Hello"}])
    assert resp is fake_response
    assert captured["payload"]["provider"] == "openai"
    assert captured["payload"]["status"] == "ok"


def test_responses_logs_event(monkeypatch):
    config.init(project_key="key", project_id="proj", env="test")
    captured = {}

    def capture(payload, api_url, project_key):
        captured["payload"] = payload
        captured["api_url"] = api_url
        captured["project_key"] = project_key

    monkeypatch.setattr(client, "_dispatch", capture)

    fake_response = {
        "output_text": "Hello there!",
        "usage": {"input_tokens": 3, "output_tokens": 2},
    }

    def fake_create(**kwargs):
        return fake_response

    if getattr(openai_wrapper.openai, "OpenAI", None) is not None:
        class FakeOpenAI:  # noqa: D101 - test helper
            def __init__(self, *args, **kwargs):
                class FakeResponses:  # noqa: D101 - test helper
                    @staticmethod
                    def create(**kw):  # noqa: ANN001 - test helper
                        return fake_create(**kw)

                self.responses = FakeResponses()

        monkeypatch.setattr(openai_wrapper.openai, "OpenAI", FakeOpenAI)
    else:
        class FakeResponses:  # noqa: D101 - test helper
            @staticmethod
            def create(**kw):  # noqa: ANN001 - test helper
                return fake_create(**kw)

        monkeypatch.setattr(openai_wrapper.openai, "responses", FakeResponses)

    resp = openai_wrapper.responses.create(
        model="gpt-4o",
        input="Hello",
        instructions="Be friendly.",
        sigmoda_metadata={"route": "responses"},
    )

    assert resp is fake_response
    payload = captured["payload"]
    assert payload["provider"] == "openai"
    assert payload["type"] == "response"
    assert payload["tokens_in"] == 3
    assert payload["tokens_out"] == 2
    assert "Hello" in payload["prompt"]
    assert "Be friendly." in payload["prompt"]
    assert payload["response"] == "Hello there!"


def test_responses_streaming_logs_on_completion(monkeypatch):
    config.init(project_key="key", project_id="proj", env="test")
    captured = {}

    def capture(payload, api_url, project_key):
        captured["payload"] = payload
        captured["api_url"] = api_url
        captured["project_key"] = project_key

    monkeypatch.setattr(client, "_dispatch", capture)

    events = [
        {"type": "response.output_text.delta", "delta": "Hi "},
        {"type": "response.output_text.delta", "delta": "there"},
        {
            "type": "response.completed",
            "response": {"output_text": "Hi there", "usage": {"input_tokens": 1, "output_tokens": 2}},
        },
    ]

    monkeypatch.setattr(openai_wrapper, "_openai_responses_create", lambda **_kw: iter(events))

    stream = openai_wrapper.responses.create(
        model="gpt-4o",
        input="Hello",
        stream=True,
        sigmoda_metadata={"route": "stream"},
    )

    yielded = list(stream)
    assert yielded == events

    payload = captured["payload"]
    assert payload["status"] == "ok"
    assert payload["response"] == "Hi there"
    assert payload["tokens_in"] == 1
    assert payload["tokens_out"] == 2
    assert payload["metadata"]["_sigmoda"]["stream"] is True
