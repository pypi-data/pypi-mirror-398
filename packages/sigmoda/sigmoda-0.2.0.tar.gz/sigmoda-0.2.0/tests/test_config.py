import importlib

import pytest

import sigmoda.config as config


@pytest.fixture(autouse=True)
def reset_config():
    config._config = None  # type: ignore[attr-defined]
    yield
    config._config = None  # type: ignore[attr-defined]


def test_init_sets_config():
    cfg = config.init(project_key="key123", project_id="proj123", env="dev", api_url="http://localhost")
    assert cfg.project_key == "key123"
    assert cfg.project_id == "proj123"
    assert cfg.env == "dev"
    assert cfg.api_url == "http://localhost"
    assert config.get_config().project_id == "proj123"


def test_init_accepts_api_key_alias():
    cfg = config.init(api_key="key123", project_id="proj123")
    assert cfg.project_key == "key123"
    assert cfg.project_id == "proj123"


def test_init_requires_api_key():
    with pytest.raises(ValueError):
        config.init(project_key="", project_id="proj123")


def test_get_config_without_init_raises():
    config._config = None  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError):
        config.get_config()


def test_init_reads_env_vars(monkeypatch):
    monkeypatch.setenv("SIGMODA_PROJECT_KEY", "env_key")
    monkeypatch.setenv("SIGMODA_PROJECT_ID", "env_proj")
    monkeypatch.setenv("SIGMODA_ENV", "stage")
    monkeypatch.setenv("SIGMODA_API_URL", "http://localhost")

    cfg = config.init()
    assert cfg.project_key == "env_key"
    assert cfg.project_id == "env_proj"
    assert cfg.env == "stage"
    assert cfg.api_url == "http://localhost"


def test_disabled_env_allows_init_without_key(monkeypatch):
    monkeypatch.setenv("SIGMODA_DISABLED", "1")

    cfg = config.init()
    assert cfg.disabled is True


def test_capture_content_defaults_off_in_prod():
    cfg = config.init(project_key="key", env="prod")
    assert cfg.capture_content is False


def test_capture_content_defaults_on_in_non_prod():
    cfg = config.init(project_key="key", env="dev")
    assert cfg.capture_content is True
