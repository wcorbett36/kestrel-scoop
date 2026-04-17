import pytest
from unittest.mock import patch, MagicMock

from src.preflight import health_url_from_openai_api_base, check_local_llm_reachable
from src.errors import BuildError, SynthesisStep


def test_health_url_from_openai_api_base():
    assert health_url_from_openai_api_base("http://127.0.0.1:8000/v1") == "http://127.0.0.1:8000/health"
    assert health_url_from_openai_api_base("http://127.0.0.1:8000/v1/") == "http://127.0.0.1:8000/health"


@patch.dict("os.environ", {"OPENAI_API_BASE": "http://127.0.0.1:8000/v1"}, clear=False)
@patch("src.preflight.requests.get")
def test_check_local_llm_reachable_success(mock_get):
    mock_get.return_value.raise_for_status = MagicMock()
    check_local_llm_reachable()
    mock_get.assert_called_once()
    assert "health" in mock_get.call_args[0][0]


@patch.dict("os.environ", {"OPENAI_API_BASE": "http://127.0.0.1:8000/v1"}, clear=False)
@patch("src.preflight.requests.get")
def test_check_local_llm_reachable_failure(mock_get):
    import requests
    mock_get.side_effect = requests.ConnectionError("refused")
    with pytest.raises(BuildError) as exc_info:
        check_local_llm_reachable()
    assert exc_info.value.step == SynthesisStep.PREFLIGHT


def test_check_local_llm_skipped_without_env(monkeypatch):
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    check_local_llm_reachable()  # no-op
