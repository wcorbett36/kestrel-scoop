import yaml
from pathlib import Path
from datetime import datetime
from src.synthesizer import ProjectProfile, StrategicView

class ObsidianFormatter:
    def __init__(self, output_dir: str = "./wiki"):
        self.output_dir = Path(output_dir)
        self._init_vault()

    def _init_vault(self):
        """Creates the strategic vault structure."""
        (self.output_dir / "01_Project_Nodes").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "02_Strategic_Views").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "03_Maps").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "04_Assets").mkdir(parents=True, exist_ok=True)

    def _generate_frontmatter(self, tags: list[str], strategic_focus: str = "") -> str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        fm = {
            "tags": tags,
            "last_compiled": date_str,
        }
        if strategic_focus:
            fm["strategic_focus"] = strategic_focus
            
        yaml_str = yaml.dump(fm, sort_keys=False)
        return f"---\n{yaml_str}---\n"

    def write_project_node(self, project_name: str, profile: ProjectProfile) -> Path:
        content = self._generate_frontmatter(tags=["project"] + profile.tags)
        content += f"# {project_name}\n\n"
        content += f"## Summary\n{profile.summary}\n\n"
        content += f"## Dependencies\n"
        for dep in profile.dependencies:
            content += f"- {dep}\n"
        content += f"\n## Strategic Gap Analysis\n{profile.gap_analysis}\n"

        file_path = self.output_dir / "01_Project_Nodes" / f"{project_name}.md"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def write_strategic_view(self, view_name: str, view: StrategicView) -> Path:
        content = self._generate_frontmatter(tags=["strategic-view"] + view.tags, strategic_focus=view.title)
        content += f"# {view.title}\n\n"
        content += f"## Overview\n{view.overview}\n\n"
        content += f"## Ecosystem Gaps\n"
        for gap in view.strategic_gaps:
            content += f"- {gap}\n"

        # Sanitize filename
        safe_name = view_name.replace(" ", "_")
        file_path = self.output_dir / "02_Strategic_Views" / f"{safe_name}.md"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def write_moc(self, nodes: list[str], views: list[str]) -> Path:
        content = self._generate_frontmatter(tags=["moc", "index"])
        content += "# Master Map of Content\n\n"
        
        content += "## Strategic Views\n"
        for v in views:
            safe = v.replace(" ", "_")
            content += f"- [[{safe}]]\n"
            
        content += "\n## Project Nodes\n"
        for n in nodes:
            content += f"- [[{n}]]\n"
            
        file_path = self.output_dir / "03_Maps" / "Index.md"
        file_path.write_text(content, encoding="utf-8")
        return file_path
