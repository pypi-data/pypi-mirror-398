import json
import queue
import threading

import websocket
from sayou.core.callbacks import BaseCallback


class WebSocketTracer(BaseCallback):

    def __init__(self, server_url: str):
        self.server_url = server_url
        self.queue = queue.Queue()
        self.running = True

        self.worker_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self.worker_thread.start()

    def on_start(self, component_name, input_data, **kwargs):
        payload = {
            "type": "START",
            "component": component_name,
            "data": self._serialize(input_data),
        }
        self.queue.put(payload)

    def on_finish(self, component_name, result_data, success, **kwargs):
        payload = {
            "type": "FINISH",
            "component": component_name,
            "success": success,
            "data": self._serialize(result_data),
        }
        self.queue.put(payload)

    def _sender_loop(self):
        ws = None
        try:
            ws = websocket.create_connection(self.server_url)

            while self.running:
                try:
                    payload = self.queue.get(timeout=1.0)

                    ws.send(json.dumps(payload))

                except queue.Empty:
                    continue
        except Exception as e:
            print(f"!!! WebSocket Connection Error: {e}")
        finally:
            if ws:
                ws.close()

    def _serialize(self, data):
        if hasattr(data, "uri"):
            return data.uri
        if isinstance(data, dict):
            return str(data)
        return str(data)
