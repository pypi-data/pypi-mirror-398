import asyncio
import json
from datetime import datetime

import websockets


async def log_handler(websocket):
    print(f"🟢 Client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            data = json.loads(message)
            timestamp = datetime.now().strftime("%H:%M:%S")

            # 받은 데이터 이쁘게 출력
            event_type = data.get("type", "UNKNOWN")
            component = data.get("component", "UnknownComp")
            payload = data.get("data", "")

            icon = "⚡"
            if event_type == "START":
                icon = "▶️ "
            elif event_type == "FINISH":
                icon = "✅"
            elif event_type == "ERROR":
                icon = "❌"

            print(f"[{timestamp}] {icon} [{component}] {event_type}")
            print(f"      └─ Data: {payload}")
            print("-" * 40)

    except websockets.exceptions.ConnectionClosed:
        print("🔴 Client disconnected")


async def main():
    print("📡 WebSocket Server listening on ws://localhost:8765...")
    async with websockets.serve(log_handler, "localhost", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")
