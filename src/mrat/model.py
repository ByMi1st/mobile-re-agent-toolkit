"""Public data models for probe generation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class JavaMethodSpec:
    """A fully qualified Java method selected for runtime observation."""

    class_name: str
    method_name: str
    overload: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.class_name or "." not in self.class_name:
            raise ValueError("class_name must be a fully qualified Java class")
        if not self.method_name:
            raise ValueError("method_name must not be empty")
        if any(not item for item in self.overload):
            raise ValueError("overload entries must not be empty")


@dataclass(frozen=True)
class ProbeContext:
    """Optional identifiers used to correlate a probe with an experiment."""

    scene_id: str | None = None
    request_id: str | None = None
    observation_mode: str = "natural"

    def __post_init__(self) -> None:
        if self.observation_mode not in {"natural", "controlled"}:
            raise ValueError("observation_mode must be natural or controlled")

