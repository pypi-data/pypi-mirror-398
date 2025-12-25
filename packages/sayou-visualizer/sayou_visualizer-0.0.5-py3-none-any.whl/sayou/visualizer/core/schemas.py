from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class VisualizationTask:
    data: Any
    data_type: str
    meta: Dict[str, Any] = field(default_factory=dict)
    recommended_renderer: Optional[str] = None


@dataclass
class VisualizationResult:
    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None
