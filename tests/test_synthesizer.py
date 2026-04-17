import pytest
from src.synthesizer import (
    StrategicSynthesizer,
    ProjectProfile,
    StrategicView,
    DocChunkSummary,
    split_text_segments,
    _parse_json_object,
)
from src.crawler import KBConfig
from unittest.mock import patch, MagicMock

import httpx

# Create a mock LiteLLM completion response struct
class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

@pytest.fixture
def mock_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("output_dir: './wiki'\nllm_model: 'gemini-1.5-pro'")
    return KBConfig(str(config_file))

def test_llm_retries_on_transient(mock_config, monkeypatch):
    monkeypatch.setenv("LLM_MAX_RETRIES", "1")
    mock_json = '{"summary": "S", "dependencies": [], "gap_analysis": "x", "tags": []}'
    with patch("src.synthesizer.time.sleep", MagicMock()):
        with patch("src.synthesizer.litellm.completion") as mock_completion:
            mock_completion.side_effect = [
                httpx.ConnectError("boom", request=MagicMock()),
                MockResponse(mock_json),
            ]
            synthesizer = StrategicSynthesizer(mock_config)
            result = synthesizer.synthesize_node("P", "docs")
    assert result.summary == "S"
    assert mock_completion.call_count == 2


@patch("src.synthesizer.litellm.completion")
def test_synthesize_node(mock_completion, mock_config):
    # Mock LLM JSON output matching the ProjectProfile schema
    mock_json = '{"summary": "Test Summary", "dependencies": ["API"], "gap_analysis": "None", "tags": ["test"]}'
    mock_completion.return_value = MockResponse(mock_json)
    
    synthesizer = StrategicSynthesizer(mock_config)
    result = synthesizer.synthesize_node("TestProject", "Test documentation info")
    
    assert isinstance(result, ProjectProfile)
    assert result.summary == "Test Summary"
    assert result.tags == ["test"]
    mock_completion.assert_called_once()

@patch("src.synthesizer.litellm.completion")
def test_synthesize_view(mock_completion, mock_config):
    # Mock LLM JSON output matching StrategicView schema
    mock_json = '{"title": "Thematic View", "overview": "Overview text", "strategic_gaps": ["Big Gap"], "tags": ["theme"]}'
    mock_completion.return_value = MockResponse(mock_json)
    
    synthesizer = StrategicSynthesizer(mock_config)
    profiles = {
        "ProjA": ProjectProfile(summary="A", dependencies=[], gap_analysis="Gap A", tags=[]),
        "ProjB": ProjectProfile(summary="B", dependencies=[], gap_analysis="Gap B", tags=[]),
    }
    
    result = synthesizer.synthesize_view(profiles)
    
    assert isinstance(result, StrategicView)
    assert result.title == "Thematic View"
    mock_completion.assert_called_once()


def test_parse_json_object_allows_trailing_text():
    raw = '{"a": 1}\n\nSome explanation after JSON.'
    assert _parse_json_object(raw) == {"a": 1}


def test_split_text_segments():
    assert split_text_segments("abc", 10) == ["abc"]
    long = "a" * 100
    parts = split_text_segments(long, 30)
    assert len(parts) == 4
    assert "".join(parts) == long


def test_kbconfig_chunk_defaults(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("output_dir: './wiki'\nllm_model: 'gemini-1.5-pro'\n")
    cfg = KBConfig(str(p))
    assert cfg.chunk_repo_synthesis is True
    assert cfg.max_chunk_chars == 48_000
    p.write_text(
        "output_dir: './wiki'\nllm_model: 'x'\nchunk_repo_synthesis: false\nmax_chunk_chars: 100\n"
    )
    cfg2 = KBConfig(str(p))
    assert cfg2.chunk_repo_synthesis is False
    assert cfg2.max_chunk_chars == 100


@patch("src.synthesizer.litellm.completion")
def test_map_reduce_synthesis(mock_completion, mock_config):
    chunk_a = '{"source_label": "a.md", "summary": "S1", "topics": ["t1"], "local_gaps": "g1"}'
    chunk_b = '{"source_label": "b.md", "summary": "S2", "topics": ["t2"], "local_gaps": "g2"}'
    merged = '{"summary": "Merged", "dependencies": [], "gap_analysis": "G", "tags": ["m"]}'
    mock_completion.side_effect = [
        MockResponse(chunk_a),
        MockResponse(chunk_b),
        MockResponse(merged),
    ]
    synthesizer = StrategicSynthesizer(mock_config)
    c1 = synthesizer.synthesize_chunk("a.md", "doc one")
    c2 = synthesizer.synthesize_chunk("b.md", "doc two")
    assert isinstance(c1, DocChunkSummary)
    result = synthesizer.synthesize_node_from_chunks("Proj", [c1, c2])
    assert isinstance(result, ProjectProfile)
    assert result.summary == "Merged"
    assert mock_completion.call_count == 3


@patch("src.synthesizer.litellm.completion")
def test_synthesize_node_legacy_single_call(mock_completion, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "output_dir: './wiki'\nllm_model: 'gemini-1.5-pro'\nchunk_repo_synthesis: false\n"
    )
    cfg = KBConfig(str(config_file))
    mock_json = '{"summary": "S", "dependencies": [], "gap_analysis": "x", "tags": []}'
    mock_completion.return_value = MockResponse(mock_json)
    synthesizer = StrategicSynthesizer(cfg)
    out = synthesizer.synthesize_node("P", "all docs")
    assert out.summary == "S"
    mock_completion.assert_called_once()
