import time

from sayou.connector.pipeline import ConnectorPipeline

from sayou.visualizer.pipeline import VisualizerPipeline


def main():
    # 1. 파이프라인 생성
    connector = ConnectorPipeline()

    # 2. Visualizer를 WebSocket 모드로 부착
    # (터미널 A에서 띄운 서버 주소 입력)
    viz = VisualizerPipeline()
    viz.attach_to(connector, mode="websocket", url="ws://localhost:8765")

    print("🚀 Running Pipeline with WebSocket Streaming...")

    # 3. 실행 (데이터가 발생할 때마다 서버로 날아감)
    # 테스트를 위해 간단한 URL 사용
    iterator = connector.run("http://example.com")

    for packet in iterator:
        print(f"Processed locally: {packet.task.uri}")
        # 너무 빨라서 눈으로 못 볼까 봐 약간의 지연 추가 (선택사항)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
