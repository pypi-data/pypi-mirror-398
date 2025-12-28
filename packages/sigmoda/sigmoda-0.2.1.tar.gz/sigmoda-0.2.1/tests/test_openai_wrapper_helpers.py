import types

import pytest

import sigmoda.client as client
import sigmoda.config as config
import sigmoda.openai_wrapper as ow


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    config._config = None  # type: ignore[attr-defined]
    monkeypatch.setattr(client, "_dispatch", client._queue_dispatch)
    monkeypatch.setattr(client, "_stats", client.Stats())
    client._event_queue = None  # type: ignore[attr-defined]
    client._worker_thread = None  # type: ignore[attr-defined]
    client._worker_stop.clear()  # type: ignore[attr-defined]
    monkeypatch.setattr(ow, "_openai_client", None)
    monkeypatch.setattr(ow, "_openai_client_key", None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SIGMODA_PROJECT_KEY", raising=False)
    monkeypatch.delenv("SIGMODA_API_KEY", raising=False)
    monkeypatch.delenv("SIGMODA_DISABLED", raising=False)
    monkeypatch.delenv("SIGMODA_ENV", raising=False)
    yield
    config._config = None  # type: ignore[attr-defined]
    monkeypatch.setattr(ow, "_openai_client", None)
    monkeypatch.setattr(ow, "_openai_client_key", None)


def test_env_and_preflight_helpers(monkeypatch):
    assert ow._env_truthy(None) is False
    assert ow._env_truthy("Yes") is True

    assert ow._sigmoda_capture_content_fast() is False
    config.init(project_key="key", env="test", capture_content=True, disabled=True)
    assert ow._sigmoda_disabled_fast() is True
    assert ow._sigmoda_capture_content_fast() is True
    config._config = None  # type: ignore[attr-defined]
    monkeypatch.setenv("SIGMODA_DISABLED", "1")
    assert ow._sigmoda_disabled_fast() is True

    monkeypatch.setenv("OPENAI_API_KEY", " key ")
    assert ow._get_openai_api_key() == "key"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(ow.openai, "api_key", " api ")
    assert ow._get_openai_api_key() == "api"

    monkeypatch.setenv("SIGMODA_DISABLED", "1")
    assert ow._ensure_sigmoda_config() is None

    monkeypatch.delenv("SIGMODA_DISABLED", raising=False)
    with pytest.raises(ValueError):
        ow._ensure_sigmoda_config()

    monkeypatch.setenv("SIGMODA_PROJECT_KEY", "proj")
    assert ow._ensure_sigmoda_config() is not None

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(ow.openai, "api_key", None)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        ow._preflight_check()

    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("SIGMODA_DISABLED", "1")
    ow._preflight_check()


def test_safe_log_event_swallow(monkeypatch):
    monkeypatch.setattr(ow, "log_event", lambda **_kw: (_ for _ in ()).throw(RuntimeError("boom")))
    ow._safe_log_event(provider="x")


def test_get_openai_client_paths(monkeypatch):
    monkeypatch.setattr(ow.openai, "OpenAI", None)
    assert ow._get_openai_client() is None

    created = {}

    class FakeOpenAI:  # noqa: D401 - test helper
        def __init__(self, api_key=None):
            created["api_key"] = api_key

    monkeypatch.setattr(ow.openai, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(ow.openai, "api_key", "k1")
    client1 = ow._get_openai_client()
    assert created["api_key"] == "k1"
    assert ow._get_openai_client() is client1

    created.clear()
    monkeypatch.setattr(ow.openai, "api_key", None)
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    client2 = ow._get_openai_client()
    assert created["api_key"] is None
    assert client2 is not None


def test_openai_create_fallbacks(monkeypatch):
    class FakeCompletions:  # noqa: D401 - test helper
        @staticmethod
        def create(**_kw):
            return {"ok": True}

    class FakeChat:  # noqa: D401 - test helper
        completions = FakeCompletions()

    class FakeClient:  # noqa: D401 - test helper
        chat = FakeChat()

    monkeypatch.setattr(ow, "_get_openai_client", lambda: FakeClient())
    assert ow._openai_chat_completion_create(model="x") == {"ok": True}

    monkeypatch.setattr(ow, "_get_openai_client", lambda: None)

    class LegacyChat:  # noqa: D401 - test helper
        @staticmethod
        def create(**_kw):
            return {"legacy": True}

    monkeypatch.setattr(ow.openai, "ChatCompletion", LegacyChat, raising=False)
    assert ow._openai_chat_completion_create(model="x") == {"legacy": True}

    monkeypatch.setattr(ow.openai, "ChatCompletion", None)
    with pytest.raises(RuntimeError):
        ow._openai_chat_completion_create(model="x")

    class FakeResponses:  # noqa: D401 - test helper
        @staticmethod
        def create(**_kw):
            return {"ok": True}

    class FakeClientResp:  # noqa: D401 - test helper
        responses = FakeResponses()

    monkeypatch.setattr(ow, "_get_openai_client", lambda: FakeClientResp())
    assert ow._openai_responses_create(model="x") == {"ok": True}

    monkeypatch.setattr(ow, "_get_openai_client", lambda: None)

    class LegacyResponses:  # noqa: D401 - test helper
        @staticmethod
        def create(**_kw):
            return {"legacy": True}

    monkeypatch.setattr(ow.openai, "responses", LegacyResponses, raising=False)
    assert ow._openai_responses_create(model="x") == {"legacy": True}

    monkeypatch.setattr(ow.openai, "responses", None)
    with pytest.raises(RuntimeError):
        ow._openai_responses_create(model="x")


def test_openai_create_with_retries(monkeypatch):
    monkeypatch.setattr(ow, "_openai_chat_completion_create", lambda **_kw: "patched")
    resp, retries = ow._openai_chat_completion_create_with_retries(model="x")
    assert resp == "patched"
    assert retries is None

    class RawResp:  # noqa: D401 - test helper
        retries_taken = "2"

        def parse(self):
            return {"parsed": True}

    class RawWrapper:  # noqa: D401 - test helper
        @staticmethod
        def create(**_kw):
            return RawResp()

    class FakeCompletions:  # noqa: D401 - test helper
        with_raw_response = RawWrapper()

    class FakeChat:  # noqa: D401 - test helper
        completions = FakeCompletions()

    class FakeClient:  # noqa: D401 - test helper
        chat = FakeChat()

    monkeypatch.setattr(ow, "_openai_chat_completion_create", ow._OPENAI_CHAT_COMPLETION_CREATE_ORIGINAL)
    monkeypatch.setattr(ow, "_get_openai_client", lambda: FakeClient())
    parsed, retries = ow._openai_chat_completion_create_with_retries(model="x")
    assert parsed == {"parsed": True}
    assert retries == 2

    monkeypatch.setattr(ow, "_openai_responses_create", lambda **_kw: "patched")
    resp, retries = ow._openai_responses_create_with_retries(model="x")
    assert resp == "patched"
    assert retries is None

    class RawResp2:  # noqa: D401 - test helper
        retries_taken = 3

        def parse(self):
            return {"parsed": True}

    class RawWrapper2:  # noqa: D401 - test helper
        @staticmethod
        def create(**_kw):
            return RawResp2()

    class FakeResponses:  # noqa: D401 - test helper
        with_raw_response = RawWrapper2()

    class FakeClient2:  # noqa: D401 - test helper
        responses = FakeResponses()

    monkeypatch.setattr(ow, "_openai_responses_create", ow._OPENAI_RESPONSES_CREATE_ORIGINAL)
    monkeypatch.setattr(ow, "_get_openai_client", lambda: FakeClient2())
    parsed, retries = ow._openai_responses_create_with_retries(model="x")
    assert parsed == {"parsed": True}
    assert retries == 3


def test_disabled_paths_use_openai_create(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    config.init(project_key="key", env="test", disabled=True)

    monkeypatch.setattr(ow, "_openai_chat_completion_create", lambda **_kw: {"disabled": True})
    assert ow.ChatCompletion.create(model="x", messages=[]) == {"disabled": True}

    monkeypatch.setattr(ow, "_openai_responses_create", lambda **_kw: {"disabled": True})
    assert ow.Responses.create(model="x", input="hi") == {"disabled": True}


def test_responses_error_and_tool_names(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    config.init(project_key="key", env="test", capture_content=True)

    captured = []
    monkeypatch.setattr(ow, "log_event", lambda **kw: captured.append(kw))

    class Err(Exception):
        def __init__(self):
            self.request = types.SimpleNamespace(headers={"x-stainless-retry-count": "2"})

    def boom(**_kw):  # noqa: ANN001 - test helper
        raise Err()

    monkeypatch.setattr(ow, "_openai_responses_create_with_retries", boom)
    with pytest.raises(Err):
        ow.Responses.create(model="x", input="hi", sigmoda_metadata={"route": "r"})
    assert captured[-1]["status"] == "error"
    assert captured[-1]["metadata"]["_sigmoda"]["openai_retries"] == 2

    fake_response = {
        "output_text": "ok",
        "usage": {"input_tokens": 1, "output_tokens": 2},
        "output": [{"type": "tool_call", "name": "tool1"}],
    }
    monkeypatch.setattr(ow, "_openai_responses_create_with_retries", lambda **_kw: (fake_response, 1))
    resp = ow.Responses.create(model="x", input="hi", sigmoda_metadata={"route": "r"})
    assert resp == fake_response
    assert captured[-1]["metadata"]["_sigmoda"]["tool_call_names"] == ["tool1"]

def test_extract_and_merge_helpers():
    prompt = ow._extract_prompt([{"role": "user", "content": [{"type": "text", "text": "hi"}, {"text": "there"}]}, "x"])
    assert "user:" in prompt
    assert ow._extract_prompt("hi") == "hi"

    assert ow._content_to_text(None) == ""
    assert ow._content_to_text(["a"]) == "a"
    response = {"choices": [{"message": {"content": [{"text": "ok"}]}}]}
    assert ow._extract_response_text(response) == "ok"

    class MessageObj:  # noqa: D401 - test helper
        content = "hello"

    class ChoiceObj:  # noqa: D401 - test helper
        message = MessageObj()

    class RespObj:  # noqa: D401 - test helper
        choices = [ChoiceObj()]

    assert ow._extract_response_text(RespObj()) == "hello"

    class BadResp:  # noqa: D401 - test helper
        def get(self, _key):
            raise RuntimeError("boom")

    assert ow._extract_response_text(BadResp()) == ""
    assert ow._extract_response_text({}) == ""

    class BadChoices:  # noqa: D401 - test helper
        def __getattribute__(self, name):
            if name == "choices":
                raise RuntimeError("boom")
            return super().__getattribute__(name)

    assert ow._extract_response_text(BadChoices()) == ""

    class MessageGet:  # noqa: D401 - test helper
        def get(self, _key):
            return "hola"

    class ChoiceObj2:  # noqa: D401 - test helper
        message = MessageGet()

    class RespObj2:  # noqa: D401 - test helper
        choices = [ChoiceObj2()]

    assert ow._extract_response_text(RespObj2()) == "hola"

    class ChoiceObjDict:  # noqa: D401 - test helper
        message = {"content": "dict"}

    assert ow._extract_response_text(types.SimpleNamespace(choices=[ChoiceObjDict()])) == "dict"

    usage = {"input_tokens": 1, "output_tokens": 2}
    assert ow._extract_usage({"usage": usage}) == {"prompt_tokens": 1, "completion_tokens": 2}

    class UsageObj:  # noqa: D401 - test helper
        prompt_tokens = 3
        completion_tokens = 4

    assert ow._extract_usage(types.SimpleNamespace(usage=UsageObj())) == {
        "prompt_tokens": 3,
        "completion_tokens": 4,
    }

    class UsageDict:  # noqa: D401 - test helper
        def model_dump(self):
            return {"input_tokens": 5, "output_tokens": 6}

    assert ow._extract_usage(types.SimpleNamespace(usage=UsageDict())) == {
        "prompt_tokens": 5,
        "completion_tokens": 6,
    }

    class UsageBad:  # noqa: D401 - test helper
        def to_dict(self):
            raise RuntimeError("boom")

    assert ow._extract_usage(types.SimpleNamespace(usage=UsageBad())) == {
        "prompt_tokens": None,
        "completion_tokens": None,
    }

    class UsageEmpty:  # noqa: D401 - test helper
        pass

    assert ow._extract_usage(types.SimpleNamespace(usage=UsageEmpty())) == {
        "prompt_tokens": None,
        "completion_tokens": None,
    }

    resp_tools = {
        "choices": [
            {"message": {"tool_calls": [{"function": {"name": "a"}}, {"function": {"name": "a"}}]}}
        ]
    }
    assert ow._extract_tool_call_names(resp_tools) == ["a"]

    class BadGet:  # noqa: D401 - test helper
        def get(self, _key):
            raise RuntimeError("boom")

    assert ow._extract_tool_call_names(BadGet()) == []
    assert ow._extract_tool_call_names({}) == []

    class BadChoicesTool:  # noqa: D401 - test helper
        def __getattribute__(self, name):
            if name == "choices":
                raise RuntimeError("boom")
            return super().__getattribute__(name)

    assert ow._extract_tool_call_names(BadChoicesTool()) == []

    class MsgObj:  # noqa: D401 - test helper
        tool_calls = [types.SimpleNamespace(function=types.SimpleNamespace(name="fn"))]

    class ChoiceObj3:  # noqa: D401 - test helper
        message = MsgObj()

    assert ow._extract_tool_call_names(types.SimpleNamespace(choices=[ChoiceObj3()])) == ["fn"]

    class ChoiceObjNone:  # noqa: D401 - test helper
        message = None

    assert ow._extract_tool_call_names(types.SimpleNamespace(choices=[ChoiceObjNone()])) == []

    meta = ow._merge_sigmoda_metadata({"route": "x", "_sigmoda": {"old": True}}, {"new": True})
    assert meta["_sigmoda"]["old"] is True
    assert meta["_sigmoda"]["new"] is True
    assert ow._merge_sigmoda_metadata("x", {"a": 1})["value"] == "x"


def test_responses_helpers():
    assert ow._responses_input_to_text(None) == ""
    assert ow._responses_input_to_text("hi") == "hi"
    parts = ow._responses_input_to_text(
        [
            {"role": "user", "text": "hi"},
            {"role": "assistant", "content": ""},
            "tail",
        ]
    )
    assert "user:" in parts

    assert ow._responses_input_to_text({"text": "yo"}) == "yo"
    assert ow._responses_input_to_text({"input_text": "hello"}) == "hello"
    assert ow._responses_input_to_text(123) == "123"

    prompt = ow._extract_responses_prompt({"instructions": "Do it", "input": "Now"})
    assert "Do it" in prompt and "Now" in prompt

    prompt = ow._extract_responses_prompt({"messages": [{"role": "user", "content": "hi"}]})
    assert "user:" in prompt

    out = ow._extract_responses_output_text({"output_text": "ok"})
    assert out == "ok"

    out = ow._extract_responses_output_text({"output": [{"text": "a"}, {"output_text": "b"}]})
    assert "a" in out and "b" in out

    assert ow._extract_responses_output_text({}) == ""

    class OutObj:  # noqa: D401 - test helper
        output_text = "c"

    out = ow._extract_responses_output_text(types.SimpleNamespace(output=[OutObj()]))
    assert out == "c"

    output = [
        {"type": "tool_call", "name": "t1", "function": {"name": "fn1"}},
        types.SimpleNamespace(type="function_call", name="t2", tool=types.SimpleNamespace(name="fn2")),
    ]
    names = ow._extract_responses_tool_call_names({"output": output})
    assert "t1" in names and "fn1" in names and "t2" in names and "fn2" in names
    assert ow._extract_responses_tool_call_names(types.SimpleNamespace(output=None)) == []


def test_response_event_helpers():
    assert ow._response_event_type({"event": "x"}) == "x"
    assert ow._response_event_type(types.SimpleNamespace(type="y")) == "y"
    assert ow._response_event_delta_text({"delta": "hi"}) == "hi"
    assert ow._response_event_delta_text({"delta": {"text": "yo"}}) == "yo"
    assert ow._response_event_delta_text({"text": "z"}) == "z"

    class DeltaObj:  # noqa: D401 - test helper
        text = "obj"

    assert ow._response_event_delta_text(types.SimpleNamespace(delta=DeltaObj())) == "obj"
    assert ow._response_event_delta_text(types.SimpleNamespace(delta="yo")) == "yo"
    assert ow._response_event_delta_text(types.SimpleNamespace(text="tt")) == "tt"
    assert ow._response_event_delta_text({"delta": 1}) == ""
    assert ow._response_event_delta_text(types.SimpleNamespace(delta=None)) == ""
    assert ow._response_event_response({"response": {"ok": True}}) == {"ok": True}
    assert ow._response_event_response(types.SimpleNamespace(response="r")) == "r"


def test_retry_helpers():
    assert ow._coerce_int(None) is None
    assert ow._coerce_int(1) == 1
    assert ow._coerce_int("2") == 2
    assert ow._coerce_int("x") is None

    class Headers:  # noqa: D401 - test helper
        def get(self, key):
            if key == "x-stainless-retry-count":
                return None
            if key == "X-Stainless-Retry-Count":
                return "4"
            return None

    assert ow._extract_openai_retries_from_headers(Headers()) == 4

    class WeirdDict(dict):  # noqa: D401 - test helper
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._first = True

        def __getattribute__(self, name):
            if name == "get":
                first = object.__getattribute__(self, "_first")
                if first:
                    object.__setattr__(self, "_first", False)
                    raise AttributeError("no get")
            return super().__getattribute__(name)

    assert ow._extract_openai_retries_from_headers(WeirdDict({"X-Stainless-Retry-Count": "5"})) == 5

    class BadHeaders:  # noqa: D401 - test helper
        def get(self, _key):
            raise RuntimeError("boom")

    assert ow._extract_openai_retries_from_headers(BadHeaders()) is None

    req = types.SimpleNamespace(headers={"x-stainless-retry-count": "6"})
    resp = types.SimpleNamespace(request=req, headers={"x-stainless-retry-count": "7"})
    stream = types.SimpleNamespace(response=resp)
    assert ow._extract_openai_retries_from_stream(stream) == 6
    stream2 = types.SimpleNamespace(response=types.SimpleNamespace(request=None, headers={"X-Stainless-Retry-Count": "8"}))
    assert ow._extract_openai_retries_from_stream(stream2) == 8

    exc = types.SimpleNamespace(request=req)
    assert ow._extract_openai_retries_from_exc(exc) == 6
    exc2 = types.SimpleNamespace(response=resp)
    assert ow._extract_openai_retries_from_exc(exc2) == 6
    exc3 = types.SimpleNamespace(response=types.SimpleNamespace(request=None, headers={"X-Stainless-Retry-Count": "9"}))
    assert ow._extract_openai_retries_from_exc(exc3) == 9

    internal = {}
    ow._maybe_add_retry_metadata(internal, None)
    ow._maybe_add_retry_metadata(internal, 3)
    assert internal["openai_retries"] == 3


def test_stream_chunk_and_stream_classes(monkeypatch):
    chunk = {"choices": [{"delta": {"content": "hi", "tool_calls": [{"function": {"name": "tool"}}]}}]}
    content, tools = ow._stream_chunk_content_and_tools(chunk)
    assert content == "hi"
    assert tools == ["tool"]

    class DeltaObj:  # noqa: D401 - test helper
        content = "yo"
        tool_calls = [types.SimpleNamespace(function=types.SimpleNamespace(name="tool2"))]

    class ChoiceObj:  # noqa: D401 - test helper
        delta = DeltaObj()

    obj_chunk = types.SimpleNamespace(choices=[ChoiceObj()])
    content, tools = ow._stream_chunk_content_and_tools(obj_chunk)
    assert content == "yo"
    assert tools == ["tool2"]

    class BadChunk:  # noqa: D401 - test helper
        def get(self, _key):
            raise RuntimeError("boom")

    assert ow._stream_chunk_content_and_tools(BadChunk()) == ("", [])
    class BadDict(dict):  # noqa: D401 - test helper
        def get(self, _key):
            raise RuntimeError("boom")

    assert ow._stream_chunk_content_and_tools(BadDict()) == ("", [])
    assert ow._stream_chunk_content_and_tools({"choices": [{"delta": None}]}) == ("", [])

    captured = []
    monkeypatch.setattr(ow, "log_event", lambda **kw: captured.append(kw))

    chunks = [
        {"choices": [{"delta": {"content": "Hi "}}], "usage": {"prompt_tokens": 1}},
        {"choices": [{"delta": {"content": "there"}}], "usage": {"completion_tokens": 2}},
    ]
    stream = ow._LoggedStream(
        stream=iter(chunks),
        start=0.0,
        model="m",
        prompt_text="p",
        sigmoda_metadata={"route": "r"},
        capture_content=True,
        openai_retries=2,
    )
    list(stream)
    assert captured[-1]["status"] == "ok"

    class Explode:  # noqa: D401 - test helper
        def __init__(self):
            self._done = False

        def __iter__(self):
            return self

        def __next__(self):
            if not self._done:
                self._done = True
                return {
                    "choices": [
                        {"delta": {"content": "x", "tool_calls": [{"function": {"name": "toolx"}}]}}
                    ],
                    "usage": {},
                }
            raise RuntimeError("boom")

    err_stream = ow._LoggedStream(
        stream=Explode(),
        start=0.0,
        model="m",
        prompt_text="p",
        sigmoda_metadata={},
        capture_content=True,
    )
    with pytest.raises(RuntimeError):
        list(err_stream)

    class Closable:  # noqa: D401 - test helper
        def close(self):
            raise RuntimeError("close")

        def __iter__(self):
            return iter([])

    ow._LoggedStream(
        stream=Closable(),
        start=0.0,
        model="m",
        prompt_text="p",
        sigmoda_metadata={},
        capture_content=True,
    ).close()

    events = [
        {"type": "response.output_text.delta", "delta": "Hi "},
        {
            "type": "response.completed",
            "response": {
                "output_text": "Hi there",
                "usage": {"input_tokens": 1, "output_tokens": 2},
                "output": [{"type": "tool_call", "name": "toolx"}],
            },
        },
    ]
    rstream = ow._LoggedResponsesStream(
        stream=iter(events),
        start=0.0,
        model="m",
        prompt_text="p",
        sigmoda_metadata={"route": "r"},
        capture_content=True,
        openai_retries=1,
    )
    list(rstream)
    assert captured[-1]["status"] == "ok"

    class Explode2:  # noqa: D401 - test helper
        def __init__(self):
            self._done = False

        def __iter__(self):
            return self

        def __next__(self):
            if not self._done:
                self._done = True
                return {
                    "type": "response.completed",
                    "response": {"output": [{"type": "tool_call", "name": "tool_err"}]},
                }
            raise RuntimeError("boom")

    err_rstream = ow._LoggedResponsesStream(
        stream=Explode2(),
        start=0.0,
        model="m",
        prompt_text="p",
        sigmoda_metadata={},
        capture_content=True,
    )
    with pytest.raises(RuntimeError):
        list(err_rstream)

    ow._LoggedResponsesStream(
        stream=Closable(),
        start=0.0,
        model="m",
        prompt_text="p",
        sigmoda_metadata={},
        capture_content=True,
    ).close()

    # Cover StopIteration path with buffered content (no response.completed).
    buffered = ow._LoggedResponsesStream(
        stream=iter([{"delta": {"text": "buf"}}]),
        start=0.0,
        model="m",
        prompt_text="p",
        sigmoda_metadata={},
        capture_content=True,
    )
    list(buffered)
