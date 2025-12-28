import networkx as nx
from sayou.core.callbacks import BaseCallback


class GraphTracer(BaseCallback):
    def __init__(self):
        self.graph = nx.DiGraph()
        self._execution_stack = ["Root"]
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
            comp_node = f"Comp:{component_name}_{len(self._execution_stack)}"

            color = "#a5b1c2"
            size = 15
            if "Pipeline" in component_name:
                color = "#ff6b81"
                size = 20
            elif "Generator" in component_name or "Fetcher" in component_name:
                color = "#2ed573"
            elif "Parser" in component_name or "Converter" in component_name:
                color = "#eccc68"
            elif "Splitter" in component_name:
                color = "#70a1ff"

            if not self.graph.has_node(comp_node):
                self.graph.add_node(
                    comp_node, label=component_name, shape="dot", color=color, size=size
                )
            parent_node = self._execution_stack[-1]

            if "Generator" in parent_node and "Pipeline" in component_name:
                for ancestor in reversed(self._execution_stack):
                    if "Pipeline" in ancestor and "Connector" not in ancestor:
                        parent_node = ancestor
                        break
            self.graph.add_edge(parent_node, comp_node)
            self._execution_stack.append(comp_node)

            data_id = self._get_data_id(input_data)
            if data_id:
                data_node_id = f"Data:{data_id}"
                if not self.graph.has_node(data_node_id):
                    label_text = str(data_id)
                    if len(label_text) > 20:
                        label_text = label_text[:17] + "..."
                    self.graph.add_node(
                        data_node_id,
                        label=label_text,
                        shape="square",
                        size=8,
                        color="#57606f",
                    )
                self.graph.add_edge(comp_node, data_node_id)

        except Exception as e:
            print(f"!!! TRACER ERROR: {e}")

    def on_finish(self, component_name, result_data, success, **kwargs):
        try:
            if len(self._execution_stack) > 1:
                if component_name in self._execution_stack[-1]:
                    self._execution_stack.pop()
                else:
                    for i in range(len(self._execution_stack) - 1, 0, -1):
                        if component_name in self._execution_stack[i]:
                            self._execution_stack = self._execution_stack[:i]
                            break
        except Exception as e:
            print(f"!!! TRACER POP ERROR: {e}")

    def _get_data_id(self, data):
        if isinstance(data, dict):
            return data.get("source") or data.get("uri") or data.get("filename")

        uri = getattr(data, "uri", None)
        if uri:
            return uri

        source = getattr(data, "source", None)
        if source:
            return source

        filename = getattr(data, "filename", None)
        if filename:
            return filename

        return None

    def _get_data_id_from_result(self, data):
        if hasattr(data, "task") and hasattr(data.task, "uri"):
            return data.task.uri
        return None
