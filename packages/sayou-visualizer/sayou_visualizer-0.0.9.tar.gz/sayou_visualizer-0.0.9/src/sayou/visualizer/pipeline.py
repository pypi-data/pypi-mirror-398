from sayou.core.base_component import BaseComponent

from .renderer.kg_renderer import KGRenderer
from .renderer.pyvis_renderer import PyVisRenderer
from .tracer.graph_tracer import GraphTracer
from .tracer.rich_tracer import RichConsoleTracer
from .tracer.websocket_tracer import WebSocketTracer


class VisualizerPipeline(BaseComponent):
    """
    The main facade for Sayou Visualization.

    It manages the internal Tracer (recording events) and Renderer (drawing graphs),
    providing a simple interface for the user.
    """

    component_name = "VisualizerPipeline"

    def __init__(self):
        super().__init__()
        self._graph_tracer = None
        self._rich_tracer = None
        self._ws_tracer = None
        self._renderer = None
        self._kg_renderer = None

    def attach_to(self, target_pipeline: BaseComponent, mode: str = "report", **kwargs):
        """
        Connects this visualizer to a target pipeline AND its children recursively.
        """
        tracer = None
        if mode == "report":
            self._graph_tracer = GraphTracer()
            tracer = self._graph_tracer
            self._log("Attached GraphTracer for HTML reporting.")
        elif mode == "live":
            self._rich_tracer = RichConsoleTracer()
            tracer = self._rich_tracer
            self._log("Attached RichConsoleTracer for live monitoring.")
        elif mode == "websocket":
            url = kwargs.get("url")
            if not url:
                raise ValueError("WebSocket mode requires 'url'.")
            self._ws_tracer = WebSocketTracer(server_url=url)
            tracer = self._ws_tracer
            self._log(f"Attached WebSocketTracer to {url}")

        if tracer:
            self._recursive_attach(target_pipeline, tracer)
        else:
            self._log("No tracer attached. Visualizer will not record events.")

    def _recursive_attach(self, component: BaseComponent, tracer):
        """
        Helper to attach tracer to the component and all its sub-components.
        """
        if hasattr(component, "_callbacks") and tracer in component._callbacks:
            return

        component.add_callback(tracer)
        self._log(f"Attached tracer to {component.component_name}")

        for attr_name, attr_value in component.__dict__.items():
            if isinstance(attr_value, BaseComponent):
                self._recursive_attach(attr_value, tracer)

            elif isinstance(attr_value, list):
                for item in attr_value:
                    if isinstance(item, BaseComponent):
                        self._recursive_attach(item, tracer)

    def report(self, output_path: str = "report.html", **kwargs):
        if self._graph_tracer.graph.number_of_nodes() == 0:
            self._log("No events recorded. The graph is empty.", level="warning")
            return

        self._log(
            f"Generating report with {self._graph_tracer.graph.number_of_nodes()} nodes..."
        )
        self._renderer = PyVisRenderer()
        self._renderer.render(self._graph_tracer.graph, output_path, **kwargs)

    def render_kg(self, json_path: str, output_path: str = "kg_view.html"):
        """
        Visualizes the OUTPUT JSON (Knowledge Graph).
        """
        self._kg_renderer = KGRenderer()
        self._kg_renderer.render(json_path, output_path)

    def save_live_log(self, output_path="live_status.html"):
        if self._rich_tracer:
            self._rich_tracer.save_html(output_path)
            self._log(f"Live log saved to: {output_path}")
        else:
            self._log(
                "RichTracer is not active. Use attach_to(..., mode='live')",
                level="warning",
            )
