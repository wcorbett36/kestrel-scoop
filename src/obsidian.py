import yaml
from pathlib import Path
from datetime import datetime
from src.synthesizer import ProjectProfile, StrategicView
from src.ontology import ProjectOntologyState

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
        (self.output_dir / "05_Ontologies").mkdir(parents=True, exist_ok=True)

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

    def write_ontology_state(self, project_name: str, state: ProjectOntologyState) -> Path:
        content = self._generate_frontmatter(tags=["ontology", "state", project_name], strategic_focus=state.schema_definition.ontology_name)
        content += f"# Ontology State: {project_name}\n\n"
        
        content += "## Schema Definition\n"
        content += f"**Domain:** {state.schema_definition.ontology_name}\n"
        content += f"**Focus:** {state.schema_definition.extraction_focus}\n\n"
        
        content += "### Core Entities Tracked\n"
        for entity in state.schema_definition.entities:
            content += f"- {entity}\n"
            
        content += "\n### Structural Relationships\n"
        for rel in state.schema_definition.relationships:
            content += f"- {rel}\n"
            
        content += "\n## Harvested Knowledge Graph\n"
        content += "### Project Entities Discovered\n"
        for ent in state.key_entities:
            content += f"- {ent}\n"
            
        content += "\n### Fact Index (Derived Assertions)\n"
        for fact in state.aggregated_facts:
            content += f"- {fact}\n"

        file_path = self.output_dir / "05_Ontologies" / f"{project_name}_ontology.md"
        file_path.write_text(content, encoding="utf-8")
        
        # Also write the raw pure YAML dump for programmatic ingestion
        dump_path = self.output_dir / "05_Ontologies" / f"{project_name}_ontology.yaml"
        dump_path.write_text(yaml.dump(state.model_dump(), sort_keys=False), encoding="utf-8")
        
        return file_path
