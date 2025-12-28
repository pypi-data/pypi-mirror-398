import pytest

import sigmoda.config as config


@pytest.fixture(autouse=True)
def reset_config():
    config._config = None  # type: ignore[attr-defined]
    yield
    config._config = None  # type: ignore[attr-defined]


def test_env_parsers_and_clamps(monkeypatch):
    assert config._env_float("bad") is None
    assert config._env_int("bad") is None

    cfg = config.init(project_key="k", sample_rate=-1)
    assert cfg.sample_rate == 0.0

    cfg = config.init(project_key="k", sample_rate=2)
    assert cfg.sample_rate == 1.0


def test_blank_project_id_becomes_none():
    cfg = config.init(project_key="k", project_id="   ")
    assert cfg.project_id is None
