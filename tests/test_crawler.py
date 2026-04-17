import pytest
import yaml
from pathlib import Path
from src.crawler import DocCrawler, KBConfig
from src.manifest import ManifestTracker

def setup_mock_project(base_dir: Path):
    project_dir = base_dir / "obs-service"
    project_dir.mkdir()
    
    readme = project_dir / "README.md"
    readme.write_text("# Observability Service\n")
    
    docs_dir = project_dir / "docs"
    docs_dir.mkdir()
    arch = docs_dir / "architecture.md"
    arch.write_text("## Architecture\n")
    
    return project_dir

def test_crawler_initial_run(tmp_path):
    project_dir = setup_mock_project(tmp_path)
    
    config_file = tmp_path / "config.yaml"
    config_data = {
        "output_dir": str(tmp_path / "wiki"),
        "llm_model": "gemini-1.5-pro",
        "projects": [
            {
                "name": "Data-Observability-Svc",
                "path": str(project_dir),
                "include": ["README.md", "docs/**/*.md"]
            }
        ]
    }
    config_file.write_text(yaml.dump(config_data))
    
    manifest_file = tmp_path / ".manifest.json"
    tracker = ManifestTracker(str(manifest_file))
    config = KBConfig(str(config_file))
    
    buffer_dir = tmp_path / ".buffer"
    crawler = DocCrawler(config, tracker, buffer_dir=str(buffer_dir))
    
    results = crawler.process()
    
    # We expect 2 files to have been crawled
    assert "Data-Observability-Svc" in results
    buffered_files = results["Data-Observability-Svc"]
    assert len(buffered_files["changed"]) == 2
    
    # Let's verify they actually got copied
    assert (buffer_dir / "Data-Observability-Svc" / "README.md").exists()
    assert (buffer_dir / "Data-Observability-Svc" / "docs" / "architecture.md").exists()
    
    # Mark them in the tracker as processed. (In real life, this would happen AFTER synthesis)
    tracker.update_file_record(project_dir / "README.md")
    tracker.update_file_record(project_dir / "docs" / "architecture.md")
    
    # Re-run crawler
    results2 = crawler.process()
    assert len(results2["Data-Observability-Svc"]["changed"]) == 0
