# sayou-visualizer

[![PyPI version](https://img.shields.io/pypi/v/sayou-visualizer.svg?color=blue)](https://pypi.org/project/sayou-visualizer/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)

**The Interactive Observability Engine for Sayou Fabric.**

`sayou-visualizer` provides a transparent layer to monitor and visualize the execution flow of Sayou components. By attaching to any pipeline, it transforms invisible execution logs into intuitive, interactive **HTML Knowledge Graphs**.

It separates the logic of **Observation** (Tracer) from **Presentation** (Renderer), allowing you to debug complex pipelines and visualize data lineage without modifying your core logic.

## 💡 Core Philosophy

**"Trace the Process, Render the Insight."**

Observability should not be an afterthought. We decouple the responsibility into two roles:

1. **Tracer (Recorder)**: The "Camera". It silently observes events (`on_start`, `on_finish`) from the pipeline via the Callback system and builds an internal graph structure.

2. **Renderer (Painter)**: The "Canvas". It takes the recorded graph and generates human-readable artifacts (e.g., Interactive HTML, Static Images).

This separation enables a Non-intrusive Monitoring experience, where visualization is just a plug-and-play feature.

## 📦 Installation

```bash
pip install sayou-visualizer
```

## ⚡ Quick Start

The `VisualizerPipeline` acts as a facade, easily attaching to other pipelines to generate reports.

```python
from sayou.connector.pipeline import ConnectorPipeline
from sayou.visualizer.pipeline import VisualizerPipeline

def main():
    connector = ConnectorPipeline()

    viz = VisualizerPipeline()
    viz.attach_to(connector)

    print("🚀 Running Pipeline...")
    iterator = connector.run("http://example.com")
    for packet in iterator:
        print(f"Processed: {packet.task.uri}")

    print("🎨 Generating Report...")
    viz.report("examples/pipeline_flow.html")

if __name__ == "__main__":
    main()
```

## 🔑 Key Concepts

### Tracers
* **`GraphTracer`**: Listens to pipeline events and constructs a `NetworkX` Directed Acyclic Graph (DAG) in real-time. It distinguishes between Components (Generator/Fetcher) and Data (Tasks).

### Renderers
* **`PyVisRenderer`**: Converts the internal graph into an interactive HTML file powered by `Vis.js`. Features physics-based layout and modern dark UI.
* **`RichRenderer`** (_Planned_): Displays a tree-structure summary directly in the console using the `Rich` library.

## 🤝 Contributing

We welcome contributions for new Renderers (e.g., `MatplotlibRenderer`, `StreamlitRenderer`) or specialized Tracers for new components!

## 📜 License

Apache 2.0 License © 2025 Sayouzone