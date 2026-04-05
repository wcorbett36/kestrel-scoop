import pytest
from pathlib import Path
from src.obsidian import ObsidianFormatter
from src.synthesizer import ProjectProfile, StrategicView

def test_obsidian_formatter_init(tmp_path):
    out_dir = tmp_path / "wiki"
    formatter = ObsidianFormatter(str(out_dir))
    
    assert (out_dir / "01_Project_Nodes").exists()
    assert (out_dir / "02_Strategic_Views").exists()
    assert (out_dir / "03_Maps").exists()
    assert (out_dir / "04_Assets").exists()

def test_write_project_node(tmp_path):
    out_dir = tmp_path / "wiki"
    formatter = ObsidianFormatter(str(out_dir))
    
    profile = ProjectProfile(
        summary="A test node",
        dependencies=["sysA", "sysB"],
        gap_analysis="Needs more tests",
        tags=["test-tag"]
    )
    
    path = formatter.write_project_node("NodeAlpha", profile)
    
    assert path.exists()
    content = path.read_text()
    
    assert "tags:" in content
    assert "- project" in content
    assert "- test-tag" in content
    assert "# NodeAlpha" in content
    assert "A test node" in content
    assert "sysA" in content

def test_write_strategic_view(tmp_path):
    out_dir = tmp_path / "wiki"
    formatter = ObsidianFormatter(str(out_dir))
    
    view = StrategicView(
        title="Overall Strategy",
        overview="It is looking good",
        strategic_gaps=["Major risk"],
        tags=["risk-management"]
    )
    
    path = formatter.write_strategic_view("Overall Strategy", view)
    
    assert path.exists()
    assert path.name == "Overall_Strategy.md"
    content = path.read_text()
    
    assert "strategic_focus: Overall Strategy" in content
    assert "# Overall Strategy" in content
    assert "It is looking good" in content

def test_write_moc(tmp_path):
    out_dir = tmp_path / "wiki"
    formatter = ObsidianFormatter(str(out_dir))
    
    path = formatter.write_moc(
        nodes=["NodeAlpha", "NodeBeta"],
        views=["Overall Strategy"]
    )
    
    assert path.exists()
    content = path.read_text()
    
    assert "[[Overall_Strategy]]" in content
    assert "[[NodeAlpha]]" in content
