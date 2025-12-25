from sayou.core.base_component import BaseComponent

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

    def attach_to(self, target_pipeline: BaseComponent, mode: str = "report", **kwargs):
        """
        Connects this visualizer to a target pipeline (Connector, Refinery, etc.).
        """
        if mode == "report":
            self._graph_tracer = GraphTracer()
            target_pipeline.add_callback(self._graph_tracer)
            self._log("Attached GraphTracer for HTML reporting.")

        elif mode == "live":
            self._rich_tracer = RichConsoleTracer()
            target_pipeline.add_callback(self._rich_tracer)
            self._log("Attached RichConsoleTracer for live monitoring.")

        elif mode == "websocket":
            url = kwargs.get("url")
            if not url:
                raise ValueError("WebSocket mode requires a 'url' parameter.")

            self._ws_tracer = WebSocketTracer(server_url=url)
            target_pipeline.add_callback(self._ws_tracer)
            self._log(f"Attached WebSocketTracer to {url}")

    def report(self, output_path: str = "report.html", **kwargs):
        if self._graph_tracer.graph.number_of_nodes() == 0:
            self._log("No events recorded. The graph is empty.", level="warning")
            return

        self._log(
            f"Generating report with {self._graph_tracer.graph.number_of_nodes()} nodes..."
        )
        self._renderer = PyVisRenderer()
        self._renderer.render(self._graph_tracer.graph, output_path, **kwargs)

    def save_live_log(self, output_path="live_status.html"):
        if self._rich_tracer:
            self._rich_tracer.save_html(output_path)
            self._log(f"Live log saved to: {output_path}")
        else:
            self._log(
                "RichTracer is not active. Use attach_to(..., mode='live')",
                level="warning",
            )
