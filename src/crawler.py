import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, List
from src.manifest import ManifestTracker

class KBConfig:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @property
    def output_dir(self) -> str:
        return self.config.get("output_dir", "./wiki")

    @property
    def llm_model(self) -> str:
        return self.config.get("llm_model", "gemini-1.5-pro")

    @property
    def projects(self) -> List[Dict[str, Any]]:
        return self.config.get("projects", [])

    @property
    def chunk_repo_synthesis(self) -> bool:
        """When True, map/reduce per file (and segments) then merge to ProjectProfile."""
        return bool(self.config.get("chunk_repo_synthesis", True))

    @property
    def max_chunk_chars(self) -> int:
        """Split files longer than this into multiple map calls (character budget, rough tokens)."""
        v = self.config.get("max_chunk_chars")
        if v is None:
            return 48_000
        return max(1, int(v))

class DocCrawler:
    def __init__(self, config: KBConfig, tracker: ManifestTracker, buffer_dir: str = ".kb_buffer"):
        self.config = config
        self.tracker = tracker
        self.buffer_dir = Path(buffer_dir)
        self._init_buffer()

    def _init_buffer(self) -> None:
        """Ensures the context buffer directory exists and is clean."""
        if self.buffer_dir.exists():
            shutil.rmtree(self.buffer_dir)
        self.buffer_dir.mkdir(parents=True, exist_ok=True)

    def process(self) -> Dict[str, Dict[str, List[Any]]]:
        """
        Crawls the configured projects and copies changed files to the context buffer.
        Returns a mapping of project names to their file state:
          { "changed": [(source_path, dest_path), ...], "unchanged": [source_path, ...] }
        """
        results_by_project = {}

        for project in self.config.projects:
            name = project.get("name")
            base_str_path = project.get("path", "")
            base_path = Path(base_str_path).expanduser().resolve()
            includes = project.get("include", [])

            changed = []
            unchanged = []

            for pattern in includes:
                # Resolve globs from the base path context
                for matched_file in base_path.rglob(pattern) if "**" in pattern else base_path.glob(pattern):
                    if matched_file.is_file():
                        # Only handle md files as per specification constraints
                        if matched_file.suffix.lower() not in [".md"]:
                            continue
                            
                        if self.tracker.is_changed(matched_file):
                            buffered_path = self._copy_to_buffer(name, base_path, matched_file)
                            changed.append((matched_file, buffered_path))
                        else:
                            unchanged.append(matched_file)

            results_by_project[name] = {"changed": changed, "unchanged": unchanged}

        return results_by_project

    def _copy_to_buffer(self, project_name: str, base_path: Path, target_file: Path) -> Path:
        """Copies the target_file to the buffer, preserving relative structure under the project name."""
        try:
            rel_path = target_file.relative_to(base_path)
        except ValueError:
            # If the file is not strictly under the base_path for some reason, just use its name
            rel_path = Path(target_file.name)

        dest_path = self.buffer_dir / project_name / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target_file, dest_path)
        return dest_path
