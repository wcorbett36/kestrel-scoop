import json
from typing import List, Dict, Any, Type
from pydantic import BaseModel, Field
from src.synthesizer import StrategicSynthesizer
from src.crawler import KBConfig

class OntologySchemaDefinition(BaseModel):
    ontology_name: str = Field(description="Name of the ontology domain")
    entities: List[str] = Field(description="List of entity types to track (e.g., 'APIEndpoint', 'Policy', 'StrategicGoal')")
    relationships: List[str] = Field(description="List of relationships (e.g., 'implements', 'governs', 'depends_on')")
    extraction_focus: str = Field(description="Instructions on what specifically to extract")

class DocumentOntologyFacts(BaseModel):
    source_label: str = Field(description="The source document path")
    facts: List[str] = Field(description="List of factual extractions matching the ontology schema")
    entities_found: List[str] = Field(description="List of entity instances found in this chunk")

class ProjectOntologyState(BaseModel):
    project_name: str = Field(description="The name of the project")
    schema_definition: OntologySchemaDefinition = Field(description="The schema used for extraction")
    aggregated_facts: List[str] = Field(description="Merged list of high-value facts across the project")
    key_entities: List[str] = Field(description="The primary entities powering this project")

class OntologyDefiner:
    def __init__(self, synthesizer: StrategicSynthesizer):
        self.synthesizer = synthesizer

    def build_schema(self, project_name: str, high_level_summary: str) -> OntologySchemaDefinition:
        prompt = (
            f"Analyze the following overview of project '{project_name}'.\n\n"
            f"OVERVIEW: {high_level_summary}\n\n"
            f"Your task is to define a strict Knowledge Ontology schema that can be used to extract meaningful, "
            f"structured facts from its sub-components and codebase. Return ONLY raw JSON."
        )
        return self.synthesizer._call_llm(prompt, OntologySchemaDefinition, use_frontier=True)

class OntologyHarvester:
    def __init__(self, synthesizer: StrategicSynthesizer):
        self.synthesizer = synthesizer
        
    def extract_facts(self, source_label: str, content: str, schema: OntologySchemaDefinition) -> DocumentOntologyFacts:
        prompt = (
            f"Extract facts from the following chunk from `{source_label}`. "
            f"Adhere to this ontology schema filter: \nEntities: {schema.entities}\nRelationships: {schema.relationships}\nFocus: {schema.extraction_focus}\n\n"
            f"DOCUMENTATION START\n{content}\nDOCUMENTATION END\n\n"
            "Return ONLY raw JSON."
        )
        return self.synthesizer._call_llm(prompt, DocumentOntologyFacts, use_frontier=False)
        
    def merge_facts(self, project_name: str, schema: OntologySchemaDefinition, chunks: List[DocumentOntologyFacts]) -> ProjectOntologyState:
        bundle_lines = []
        for c in chunks:
            bundle_lines.append(f"Source: {c.source_label}\nFacts: {json.dumps(c.facts)}\nEntities: {json.dumps(c.entities_found)}\n")
        bundle = "\n".join(bundle_lines)
        prompt = (
            f"Merge the following extracted chunk facts into a unified ontology state for project '{project_name}'.\n"
            f"Ontology constraint focus: {schema.extraction_focus}\n\n"
            f"EXTRACTED FACTS:\n{bundle}\n\n"
            f"Return ONLY raw JSON."
        )
        # Use frontier model to do the complex structural merge
        return self.synthesizer._call_llm(prompt, ProjectOntologyState, use_frontier=True)
