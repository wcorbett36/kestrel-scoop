"""Optional health check for local OpenAI-compatible servers (e.g. MLX) before synthesis."""

import os

import requests

from src.errors import BuildError, SynthesisStep


def health_url_from_openai_api_base(api_base: str) -> str:
    """Map e.g. http://127.0.0.1:8000/v1 -> http://127.0.0.1:8000/health."""
    b = api_base.rstrip("/")
    if b.endswith("/v1"):
        b = b[:-3]
    return b + "/health"


def check_local_llm_reachable(timeout: float = 5.0) -> None:
    """
    If OPENAI_API_BASE is set, GET /health on the server root. Raises BuildError on failure.
    No-op when OPENAI_API_BASE is unset (cloud-only flows).
    """
    api_base = os.getenv("OPENAI_API_BASE")
    if not api_base:
        return
    url = health_url_from_openai_api_base(api_base)
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException as e:
        raise BuildError(
            step=SynthesisStep.PREFLIGHT,
            message=f"LLM server not reachable at {url}",
            detail=f"OPENAI_API_BASE={api_base}",
            hint="Start the local server (e.g. punchcard-modelbase-mlx: make run-server) or fix OPENAI_API_BASE.",
        ) from e
