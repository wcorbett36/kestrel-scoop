import pytest
from src.synthesizer import StrategicSynthesizer, ProjectProfile, StrategicView
from src.crawler import KBConfig
from unittest.mock import patch, MagicMock

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
