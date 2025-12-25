from pyvis.network import Network
from sayou.core.base_component import BaseComponent


class PyVisRenderer(BaseComponent):
    component_name = "PyVisRenderer"

    def render(self, graph, output_path="pipeline_report.html"):
        net = Network(
            height="100vh",
            width="100%",
            bgcolor="#1e1e1e",
            font_color="#c7c7c7",
            directed=True,
        )
        net.from_nx(graph)

        net.set_options(
            """
        var options = {
            "nodes": {
                "borderWidth": 0,
                "borderWidthSelected": 2,
                "shadow": {
                    "enabled": true,
                    "color": "rgba(0,0,0,0.5)",
                    "size": 10,
                    "x": 5,
                    "y": 5
                },
                "font": {
                    "face": "Roboto, Helvetica, Arial",
                    "size": 14,
                    "color": "#ffffff",
                    "strokeWidth": 0,
                    "strokeColor": "#ffffff"
                }
            },
            "edges": {
                "color": {
                    "color": "#505050",
                    "highlight": "#ffffff",
                    "hover": "#ffffff",
                    "opacity": 0.5
                },
                "arrows": {
                    "to": { "enabled": true, "scaleFactor": 0.5 }
                },
                "smooth": {
                    "type": "continuous",
                    "roundness": 0.5
                }
            },
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -80,
                    "centralGravity": 0.005,
                    "springLength": 150,
                    "springConstant": 0.18,
                    "damping": 0.9
                },
                "maxVelocity": 40,
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based",
                "stabilization": {
                    "enabled": true,
                    "iterations": 1000,
                    "updateInterval": 25
                }
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 200
            }
        }
        """
        )

        net.save_graph(output_path)
        self._log(f"Visualization saved to: {output_path}")
