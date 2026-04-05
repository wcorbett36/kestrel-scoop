import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, Union

class ManifestTracker:
    def __init__(self, manifest_file: str = ".kb_manifest.json"):
        self.manifest_path = Path(manifest_file)
        self.manifest: Dict[str, str] = self._load_manifest()
        
    def _load_manifest(self) -> Dict[str, str]:
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {} # If corrupted, start fresh
        return {}
        
    def _save_manifest(self) -> None:
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2)
            
    def _compute_hash(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
        
    def is_changed(self, file_path: Union[str, Path]) -> bool:
        """
        Checks if a file has changed since the last manifest save.
        Returns True if changed or new, False if unchanged.
        """
        path = Path(file_path)
        if not path.is_file():
            return False
            
        file_hash = self._compute_hash(path)
        str_path = str(path)
        
        # Check against recorded hash
        if self.manifest.get(str_path) == file_hash:
            return False
            
        return True
        
    def update_record(self, file_path: Union[str, Path]) -> None:
        """Updates the hash record for a file and saves immediately."""
        path = Path(file_path)
        if not path.is_file():
            return
            
        file_hash = self._compute_hash(path)
        self.manifest[str(path)] = file_hash
        self._save_manifest()
