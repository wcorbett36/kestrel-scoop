import pytest
import json
from pathlib import Path
from src.manifest import ManifestTracker

def test_manifest_tracker_new_file(tmp_path):
    manifest_file = tmp_path / ".kb_manifest.json"
    tracker = ManifestTracker(str(manifest_file))
    
    test_file = tmp_path / "test.md"
    test_file.write_text("Hello World!")
    
    assert tracker.is_changed(test_file) == True

def test_manifest_tracker_unchanged_file(tmp_path):
    manifest_file = tmp_path / ".kb_manifest.json"
    tracker = ManifestTracker(str(manifest_file))
    
    test_file = tmp_path / "test.md"
    test_file.write_text("Hello World!")
    
    tracker.update_record(test_file)
    
    # Reload tracker
    tracker2 = ManifestTracker(str(manifest_file))
    assert tracker2.is_changed(test_file) == False
    
def test_manifest_tracker_modified_file(tmp_path):
    manifest_file = tmp_path / ".kb_manifest.json"
    tracker = ManifestTracker(str(manifest_file))
    
    test_file = tmp_path / "test.md"
    test_file.write_text("Hello World!")
    
    tracker.update_record(test_file)
    
    test_file.write_text("Hello World! Edited.")
    
    assert tracker.is_changed(test_file) == True
