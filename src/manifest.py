import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, Union, Any, List

class ManifestTracker:
    def __init__(self, manifest_file: str = ".kb_manifest.json"):
        self.manifest_path = Path(manifest_file)
        self.manifest: Dict[str, Any] = self._load_manifest()
        
    def _load_manifest(self) -> Dict[str, Any]:
        default = {"version": 2, "files": {}, "projects": {}}
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Migrate v1 to v2 if necessary
                    if "version" not in data or data["version"] < 2:
                        migrated_files = {}
                        # In v1, data was simply Dict[str, str] mapping paths to hashes
                        for path, h in data.items():
                            if isinstance(h, str):
                                migrated_files[path] = {"hash": h, "chunks": []}
                        return {"version": 2, "files": migrated_files, "projects": {}}
                    return data
            except json.JSONDecodeError:
                return default # If corrupted, start fresh
        return default
        
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
        
        file_record = self.manifest["files"].get(str_path)
        if file_record and file_record.get("hash") == file_hash:
            # File matches the recorded hash, skip
            return False
            
        return True

    def get_file_chunks(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Retrieves cached chunk dictionaries for a given file path."""
        file_record = self.manifest["files"].get(str(file_path), {})
        return file_record.get("chunks", [])
        
    def update_file_record(self, file_path: Union[str, Path], chunks: List[Dict[str, Any]] = None) -> None:
        """Updates the hash record and cached chunks for a file, saving immediately."""
        path = Path(file_path)
        if not path.is_file():
            return
            
        file_hash = self._compute_hash(path)
        str_path = str(path)
        
        self.manifest["files"][str_path] = {
            "hash": file_hash,
            "chunks": chunks or []
        }
        self._save_manifest()

    def get_project_profile(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached profile dictionary for an unchanged project."""
        proj_record = self.manifest["projects"].get(project_name)
        if proj_record:
            return proj_record.get("profile")
        return None

    def update_project_profile(self, project_name: str, profile_dict: Dict[str, Any]) -> None:
        """Updates the cached project profile and saves immediately."""
        if project_name not in self.manifest["projects"]:
            self.manifest["projects"][project_name] = {}
        self.manifest["projects"][project_name]["profile"] = profile_dict
        self._save_manifest()
