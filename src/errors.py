"""Structured errors for the K-Compiler build pipeline (fail-fast, actionable context)."""

from enum import Enum
from typing import Optional


class SynthesisStep(str, Enum):
    PREFLIGHT = "preflight"
    READ_FILE = "read_file"
    MAP_CHUNK = "map_chunk"
    REDUCE = "reduce"
    SINGLE_SHOT = "single_shot"
    EMPTY_FALLBACK = "empty_fallback"
    STRATEGIC_VIEW = "strategic_view"


class BuildError(Exception):
    """Raised when a build step fails; carries step context for CLI messaging."""

    def __init__(
        self,
        step: SynthesisStep,
        message: str,
        *,
        project_name: Optional[str] = None,
        detail: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> None:
        self.step = step
        self.message = message
        self.project_name = project_name
        self.detail = detail
        self.hint = hint
        super().__init__(self._format())

    def _format(self) -> str:
        parts: list[str] = [f"[{self.step.value}] {self.message}"]
        if self.project_name:
            parts.append(f"project={self.project_name}")
        if self.detail:
            parts.append(f"detail={self.detail}")
        return " | ".join(parts)
