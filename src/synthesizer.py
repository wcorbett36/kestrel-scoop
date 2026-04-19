import json
import os
import time
import litellm
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Type, TypeVar, cast, Optional
from src.crawler import KBConfig


def _is_transient_llm_error(exc: BaseException) -> bool:
    """True for timeouts and connection failures; not for bad JSON or HTTP 4xx after connect."""
    try:
        import httpx
    except ImportError:
        httpx = None  # type: ignore

    cur: Optional[BaseException] = exc
    visited: set[int] = set()
    while cur is not None and id(cur) not in visited:
        visited.add(id(cur))
        if httpx is not None and isinstance(
            cur,
            (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
            ),
        ):
            return True
        name = type(cur).__name__
        if "Timeout" in name or "ConnectError" in name or name in ("APIConnectionError", "ConnectError"):
            return True
        cur = cur.__cause__
    return False

# Fallback models mapping if using specific litellm prefixes 
# Gemini natively uses gemini/... prefix in LiteLLM
def format_model_name(name: str) -> str:
    if "gemini" in name and not name.startswith("gemini/"):
        return f"gemini/{name}"
    return name

T = TypeVar('T', bound=BaseModel)


def _strip_markdown_fence(content: str) -> str:
    s = content.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    return s


def _parse_json_object(content: str) -> Dict[str, Any]:
    """
    Parse the first JSON object from model output. Handles trailing prose and
    markdown fences (open models often append text after valid JSON).
    """
    s = _strip_markdown_fence(content)
    decoder = json.JSONDecoder()
    i = s.find("{")
    if i < 0:
        raise ValueError("No JSON object found in model output")
    obj, _ = decoder.raw_decode(s, i)
    if not isinstance(obj, dict):
        raise ValueError("Expected a JSON object at root")
    return cast(Dict[str, Any], obj)


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


class DocChunkSummary(BaseModel):
    source_label: str = Field(description="Source file path or path plus segment index")
    summary: str = Field(description="Brief summary of this chunk's documentation")
    topics: List[str] = Field(default_factory=list, description="Key topics or themes in this chunk")
    local_gaps: str = Field(description="Gaps, risks, or debt mentioned in this chunk only")


def split_text_segments(text: str, max_chars: int) -> List[str]:
    """Split long text into fixed-size segments for separate map calls."""
    if max_chars < 1:
        return [text]
    if len(text) <= max_chars:
        return [text]
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


class StrategicSynthesizer:
    def __init__(self, config: KBConfig):
        self.config = config
        self.model = format_model_name(self.config.llm_model)
        
    def _call_llm(self, prompt: str, schema: Type[T], use_frontier: bool = False) -> T:
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

        completion_kwargs: Dict[str, Any] = {}
        target_model = self.model

        if use_frontier:
            target_model = format_model_name(self.config.frontier_model)
            # When using frontier, we rely on the native provider's environment variables
            # (like GEMINI_API_KEY) and avoid forcing the local API base.
        else:
            api_base = os.getenv("OPENAI_API_BASE")
            if api_base:
                completion_kwargs["api_base"] = api_base
                # Local MLX runs can exceed default HTTP timeouts on large doc batches.
                completion_kwargs["timeout"] = float(
                    os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", "1800")
                )
            # Only use OPENAI_API_KEY override for the local model if specified
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                completion_kwargs["api_key"] = api_key

        max_retries = max(0, int(os.getenv("LLM_MAX_RETRIES", "0")))
        backoff = float(os.getenv("LLM_RETRY_BACKOFF_SECONDS", "0.5"))
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = litellm.completion(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": full_system_msg},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    **completion_kwargs,
                )
                break
            except Exception as e:
                last_exc = e
                if attempt < max_retries and _is_transient_llm_error(e):
                    time.sleep(backoff * (attempt + 1))
                    continue
                raise

        assert response is not None
        content = response.choices[0].message.content.strip()

        try:
            parsed = _parse_json_object(content)
            
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

    def synthesize_chunk(self, source_label: str, docs_content: str) -> DocChunkSummary:
        prompt = (
            f"Summarize the following documentation excerpt from `{source_label}`.\n\n"
            f"DOCUMENTATION START\n{docs_content}\nDOCUMENTATION END\n\n"
            "Capture only what appears in this excerpt. Return ONLY raw JSON."
        )
        return self._call_llm(prompt, DocChunkSummary)

    def synthesize_node_from_chunks(
        self, project_name: str, chunks: List[DocChunkSummary], batch_size: int = 20
    ) -> ProjectProfile:
        if not chunks:
            return self.synthesize_node(project_name, "(no documentation content in files)")
            
        if len(chunks) <= batch_size:
            return self._reduce_chunks_to_profile(project_name, chunks)
            
        # Hierarchical reduce
        intermediate_profiles = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            intermediate_profiles.append(self._reduce_chunks_to_profile(project_name, batch))
            
        return self.merge_project_profiles(project_name, intermediate_profiles)

    def _reduce_chunks_to_profile(self, project_name: str, chunks: List[DocChunkSummary]) -> ProjectProfile:
        lines: List[str] = []
        for c in chunks:
            lines.append(
                f"--- {c.source_label} ---\n"
                f"Summary: {c.summary}\n"
                f"Topics: {', '.join(c.topics) if c.topics else '(none)'}\n"
                f"Local gaps: {c.local_gaps}\n"
            )
        bundle = "\n".join(lines)
        prompt = (
            f"Merge the following per-chunk summaries into ONE strategic profile for the project '{project_name}'. "
            "Resolve overlaps; prioritize cross-cutting themes. Return ONLY raw JSON matching the schema.\n\n"
            f"CHUNK SUMMARIES:\n{bundle}"
        )
        return self._call_llm(prompt, ProjectProfile)

    def merge_project_profiles(self, project_name: str, profiles: List[ProjectProfile]) -> ProjectProfile:
        """Merges multiple intermediate ProjectProfiles into a single final ProjectProfile."""
        if len(profiles) == 1:
            return profiles[0]
            
        lines = []
        for i, p in enumerate(profiles):
            lines.append(
                f"--- Intermediate Profile {i+1} ---\n"
                f"Summary: {p.summary}\n"
                f"Dependencies: {', '.join(p.dependencies) if p.dependencies else 'None'}\n"
                f"Gap Analysis: {p.gap_analysis}\n"
            )
        bundle = "\n".join(lines)
        prompt = (
            f"Merge the following intermediate project profiles into ONE final, cohesive strategic profile for the project '{project_name}'. "
            "Consolidate dependencies, unify the summary, and synthesize a comprehensive gap analysis. Return ONLY raw JSON matching the schema.\n\n"
            f"INTERMEDIATE PROFILES:\n{bundle}"
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
