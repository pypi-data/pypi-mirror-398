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
    viz.report("examples/pipeline_flow_demo.html")


if __name__ == "__main__":
    main()
