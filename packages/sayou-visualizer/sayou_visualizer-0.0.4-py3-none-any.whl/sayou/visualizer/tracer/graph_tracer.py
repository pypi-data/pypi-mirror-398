import networkx as nx
from sayou.core.callbacks import BaseCallback


class GraphTracer(BaseCallback):
    def __init__(self):
        self.graph = nx.DiGraph()
        self.graph.add_node(
            "Root",
            label="Sayou Pipeline",
            color="#ffffff",
            shape="dot",
            size=25,
            font={"size": 20, "color": "black"},
        )

    def on_start(self, component_name, input_data, **kwargs):
        try:
            comp_node = f"Comp:{component_name}"

            color = "#a5b1c2"
            size = 15

            if "ConnectorPipeline" in component_name:
                color = "#ffffff"
                size = 20
            elif "Generator" in component_name:
                color = "#00d2d3"
                size = 15
            elif "Fetcher" in component_name:
                color = "#ff9f43"
                size = 15

            if not self.graph.has_node(comp_node):
                self.graph.add_node(
                    comp_node, label=component_name, shape="dot", color=color, size=size
                )

                if "Pipeline" in component_name:
                    self.graph.add_edge("Root", comp_node)
                else:
                    parent = "Comp:ConnectorPipeline"
                    if not self.graph.has_node(parent):
                        parent = "Root"
                    self.graph.add_edge(parent, comp_node)

            data_id = self._get_data_id(input_data)
            if data_id:
                label_text = str(data_id)
                if len(label_text) > 25:
                    label_text = label_text[:22] + "..."

                node_id = f"Data:{data_id}"
                if not self.graph.has_node(node_id):
                    self.graph.add_node(
                        node_id,
                        label=label_text,
                        title=str(data_id),
                        shape="dot",
                        size=8,
                        color={"background": "#57606f", "border": "#57606f"},
                    )

                self.graph.add_edge(comp_node, node_id)

        except Exception as e:
            print(f"!!! TRACER ERROR: {e}")

    def on_finish(self, component_name, result_data, success, **kwargs):
        try:
            data_id = self._get_data_id_from_result(result_data)
            if data_id:
                node_id = f"Data:{data_id}"
                if self.graph.has_node(node_id):
                    color = "#54a0ff" if success else "#ff6b6b"
                    self.graph.nodes[node_id]["color"] = color
                    self.graph.nodes[node_id]["size"] = 10
        except Exception as e:
            print(f"!!! TRACER ERROR in on_finish: {e}")
            pass

    def _get_data_id(self, data):
        if isinstance(data, dict):
            return data.get("source") or data.get("uri")
        if hasattr(data, "uri"):
            return data.uri
        if hasattr(data, "source"):
            return data.source
        return None

    def _get_data_id_from_result(self, data):
        if hasattr(data, "task") and hasattr(data.task, "uri"):
            return data.task.uri
        return None
