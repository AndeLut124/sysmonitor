import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from ..core.collector import MetricCollector
from dataclasses import asdict


class APIServer:
    """HTTP + WebSocket сервер."""

    def __init__(self, collector: MetricCollector, web_dir: Path):
        self.collector = collector
        self.web_dir = web_dir
        self.app = FastAPI(title="System Monitor")

        # Монтируем статику
        static_dir = web_dir / "static"
        static_dir.mkdir(parents=True, exist_ok=True)
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        # Роуты
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            template_path = self.web_dir / "templates" / "index.html"
            return template_path.read_text(encoding="utf-8")

        @self.app.get("/api/current")
        async def current_metrics():
            snapshot = self.collector.get_latest()
            if snapshot is None:
                snapshot = self.collector.collect()
            return self._snapshot_to_dict(snapshot)

        @self.app.get("/api/history")
        async def history():
            return [self._snapshot_to_dict(s) for s in self.collector.get_history()]

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    try:
                        snapshot = self.collector.collect()
                        await websocket.send_text(
                            json.dumps(self._snapshot_to_dict(snapshot), default=str)
                        )
                        await asyncio.sleep(1)
                    except Exception:
                        break
            except WebSocketDisconnect:
                pass
            except Exception:
                pass

    def _snapshot_to_dict(self, snapshot) -> dict:
        """Конвертирует snapshot в словарь для JSON."""
        d = asdict(snapshot)
        d["timestamp"] = snapshot.timestamp.isoformat()
        return d

    def run(self, host: str = "0.0.0.0", port: int = 8080):
        import uvicorn
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="warning",
            access_log=False
        )