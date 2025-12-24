import os
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple, Union


def _env_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def _env_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


@dataclass
class Config:
    project_key: str
    project_id: Optional[str] = None
    env: str = "prod"
    api_url: str = "https://api.sigmoda.com"
    timeout: Union[float, Tuple[float, float]] = 2.0
    max_retries: int = 2
    backoff_base: float = 0.25
    max_queue_size: int = 1000
    sample_rate: float = 1.0
    capture_content: bool = False
    redact: Optional[Callable[[str], str]] = None
    max_prompt_chars: int = 8000
    max_response_chars: int = 8000
    max_metadata_items: int = 50
    max_metadata_bytes: int = 8192
    max_metadata_value_chars: int = 1024
    max_payload_bytes: int = 100_000
    metadata_allowlist: Optional[Sequence[str]] = None
    metadata_denylist: Optional[Sequence[str]] = None
    schema_version: int = 1
    disabled: bool = False
    debug: bool = False


_config: Optional[Config] = None


def init(
    project_key: Optional[str] = None,
    project_id: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    env: Optional[str] = None,
    api_url: Optional[str] = None,
    timeout: Union[float, Tuple[float, float]] = 2.0,
    max_retries: int = 2,
    backoff_base: float = 0.25,
    max_queue_size: int = 1000,
    sample_rate: Optional[float] = None,
    capture_content: Optional[bool] = None,
    redact: Optional[Callable[[str], str]] = None,
    max_prompt_chars: int = 8000,
    max_response_chars: int = 8000,
    max_metadata_items: int = 50,
    max_metadata_bytes: int = 8192,
    max_metadata_value_chars: int = 1024,
    max_payload_bytes: Optional[int] = None,
    metadata_allowlist: Optional[Sequence[str]] = None,
    metadata_denylist: Optional[Sequence[str]] = None,
    schema_version: int = 1,
    disabled: Optional[bool] = None,
    debug: Optional[bool] = None,
) -> Config:
    """
    Initialize the Sigmoda SDK with required settings.
    """
    if disabled is None:
        disabled = _env_truthy(os.getenv("SIGMODA_DISABLED"))
    if debug is None:
        debug = _env_truthy(os.getenv("SIGMODA_DEBUG"))

    if project_key is None and api_key is not None:
        project_key = api_key

    if project_key is None:
        project_key = os.getenv("SIGMODA_PROJECT_KEY") or os.getenv("SIGMODA_API_KEY")
    if project_id is None:
        project_id = os.getenv("SIGMODA_PROJECT_ID") or project_id
    if env is None:
        env = os.getenv("SIGMODA_ENV", "prod")
    if api_url is None:
        api_url = os.getenv("SIGMODA_API_URL", "https://api.sigmoda.com")

    env_lower = str(env).strip().lower()
    if capture_content is None:
        capture_content = env_lower not in {"prod", "production"}

    if sample_rate is None:
        sample_rate = _env_float(os.getenv("SIGMODA_SAMPLE_RATE"))
    if sample_rate is None:
        sample_rate = 1.0
    sample_rate = float(sample_rate)
    if sample_rate < 0.0:
        sample_rate = 0.0
    if sample_rate > 1.0:
        sample_rate = 1.0

    if max_payload_bytes is None:
        max_payload_bytes = _env_int(os.getenv("SIGMODA_MAX_PAYLOAD_BYTES"))
    if max_payload_bytes is None:
        max_payload_bytes = 100_000

    if not disabled and (not project_key or not project_key.strip()):
        raise ValueError("Sigmoda project_key is required.")
    if project_id is not None and not str(project_id).strip():
        project_id = None

    global _config
    _config = Config(
        project_key=(project_key or "").strip(),
        project_id=project_id,
        env=env or "prod",
        api_url=api_url or "https://api.sigmoda.com",
        timeout=timeout,
        max_retries=max_retries,
        backoff_base=backoff_base,
        max_queue_size=max_queue_size,
        sample_rate=sample_rate,
        capture_content=bool(capture_content),
        redact=redact,
        max_prompt_chars=max_prompt_chars,
        max_response_chars=max_response_chars,
        max_metadata_items=max_metadata_items,
        max_metadata_bytes=max_metadata_bytes,
        max_metadata_value_chars=max_metadata_value_chars,
        max_payload_bytes=int(max_payload_bytes),
        metadata_allowlist=metadata_allowlist,
        metadata_denylist=metadata_denylist,
        schema_version=schema_version,
        disabled=bool(disabled),
        debug=bool(debug),
    )
    return _config


def get_config() -> Config:
    if _config is None:
        raise RuntimeError("Sigmoda SDK is not initialized. Call sigmoda.init(...) first.")
    return _config
