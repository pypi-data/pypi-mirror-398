from abc import abstractmethod

from sayou.core.base_component import BaseComponent

from ..core.schemas import VisualizationResult, VisualizationTask


class BaseRenderer(BaseComponent):
    component_name = "BaseRenderer"

    def render(
        self, task: VisualizationTask, output_path: str, **kwargs
    ) -> VisualizationResult:
        self._log(f"[{self.component_name}] Rendering to {output_path}...")
        try:
            return self._do_render(task, output_path, **kwargs)
        except Exception as e:
            return VisualizationResult(success=False, error=str(e))

    @abstractmethod
    def _do_render(
        self, task: VisualizationTask, output_path: str, **kwargs
    ) -> VisualizationResult:
        raise NotImplementedError
