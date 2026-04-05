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

    def process(self) -> Dict[str, List[Path]]:
        """
        Crawls the configured projects and copies changed files to the context buffer.
        Returns a mapping of project names to their buffered file paths.
        """
        buffered_files_by_project = {}

        for project in self.config.projects:
            name = project.get("name")
            base_str_path = project.get("path", "")
            base_path = Path(base_str_path).expanduser().resolve()
            includes = project.get("include", [])

            buffered_files = []

            for pattern in includes:
                # Resolve globs from the base path context
                for matched_file in base_path.rglob(pattern) if "**" in pattern else base_path.glob(pattern):
                    if matched_file.is_file():
                        # Only handle md files as per specification constraints
                        if matched_file.suffix.lower() not in [".md"]:
                            continue
                            
                        if self.tracker.is_changed(matched_file):
                            buffered_path = self._copy_to_buffer(name, base_path, matched_file)
                            buffered_files.append((matched_file, buffered_path))

            buffered_files_by_project[name] = buffered_files

        return buffered_files_by_project

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
