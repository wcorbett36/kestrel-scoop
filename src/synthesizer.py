import json
import os
import litellm
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Type, TypeVar
from src.crawler import KBConfig

# Fallback models mapping if using specific litellm prefixes 
# Gemini natively uses gemini/... prefix in LiteLLM
def format_model_name(name: str) -> str:
    if "gemini" in name and not name.startswith("gemini/"):
        return f"gemini/{name}"
    return name

T = TypeVar('T', bound=BaseModel)

class ProjectProfile(BaseModel):
    summary: str = Field(description="Condensed summary focusing on what this provides")
    dependencies: List[str] = Field(description="What this project depends on (APIs, patterns, tools)")
    gap_analysis: str = Field(description="Strategic gap analysis and observed technical debt")
    tags: List[str] = Field(default_factory=list, description="Relevant strategic tags for Obsidian (e.g., active, data-mesh)")

class StrategicView(BaseModel):
    title: str = Field(description="Thematic title of the view (e.g. 'State of Observability')")
    overview: str = Field(description="Thematic overview connecting multiple projects")
    strategic_gaps: List[str] = Field(description="Systemic or cross-cutting gaps across the ecosystem")
    tags: List[str] = Field(default_factory=list, description="Tags for Obsidian indexing")

class StrategicSynthesizer:
    def __init__(self, config: KBConfig):
        self.config = config
        self.model = format_model_name(self.config.llm_model)
        
    def _call_llm(self, prompt: str, schema: Type[T]) -> T:
        keys_list = ", ".join(schema.model_fields.keys())
        system_msg = (
            "You are a Strategic Architect. Ignore implementation details like variable names or setup instructions; "
            "focus on architectural intent, API boundaries, and business value. "
            "You MUST output RAW JSON EXACTLY matching the provided JSON schema. "
            f"The output MUST contain exactly these keys at the root level: {keys_list}."
        )
        
        try:
            schema_dump = json.dumps(schema.model_json_schema())
        except Exception:
            schema_dump = schema.schema_json()
            
        full_system_msg = f"{system_msg}\n\nSCHEMA:\n{schema_dump}"
        
        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": full_system_msg},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        
        # Robustly strip markdown JSON blocks which open-source models often inject
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            
        try:
            parsed = json.loads(content)
            
            # Llama3 sometimes renames keys or turns string-fields into objects. 
            # We must map these back into the parsed dictionary dynamically.
            if "gap_analysis" not in parsed and "strategic_gap_analysis" in parsed:
                parsed["gap_analysis"] = parsed.pop("strategic_gap_analysis")
                
            # If a field requires a string but Llama generated an object, dump it to string.
            for key, val in parsed.items():
                if key in schema.model_fields:
                    # In python 3.9+ types like `str` are directly inspectable 
                    if getattr(schema.model_fields[key], 'annotation', None) == str and not isinstance(val, str):
                        parsed[key] = json.dumps(val)

            # Fallback for missing keys
            for key in schema.model_fields.keys():
                if key not in parsed:
                    err_val = "Error mapping extracted data"
                    if getattr(schema.model_fields[key], 'annotation', None) == list or getattr(schema.model_fields[key], 'annotation', None) == List[str]:
                         err_val = []
                    parsed[key] = err_val
                    
            return schema.model_validate(parsed)
        except Exception as e:
            # Fallback debug log to trace unexpected LLM json schemas
            print(f"Failed to validate model payload:\n{content}")
            raise e

    def synthesize_node(self, project_name: str, docs_content: str) -> ProjectProfile:
        prompt = (
            f"Analyze the following documentation chunks for the project '{project_name}'.\n\n"
            f"DOCUMENTATION START\n{docs_content}\nDOCUMENTATION END\n\n"
            "Provide a strategic synthesis profiling this project. Return ONLY raw JSON."
        )
        return self._call_llm(prompt, ProjectProfile)
        
    def synthesize_view(self, profiles: Dict[str, ProjectProfile]) -> StrategicView:
        profiles_str = "\n\n".join([f"Project: {name}\nSummary: {p.summary}\nGaps: {p.gap_analysis}" for name, p in profiles.items()])
        prompt = (
            "Analyze the following set of synthesized project profiles.\n\n"
            f"PROJECTS:\n{profiles_str}\n\n"
            "Identify the overarching strategic narratives, and synthesize a cohesive thematic view. Return ONLY raw JSON."
        )
        return self._call_llm(prompt, StrategicView)
