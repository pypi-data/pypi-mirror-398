from __future__ import annotations
from fastapi import HTTPException

import base64
import io
import os
import socket
import threading
import webbrowser
from dataclasses import dataclass
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from .analyzer import Analyzer


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    text: str
    chart_base64_png: Optional[str] = None
    table_preview: Optional[list] = None  # list of dict rows


@dataclass
class WebConfig:
    host: str = "127.0.0.1"
    port: int = 0  # 0 means "pick a free port"
    open_browser: bool = True


def _pick_free_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def create_app(analyzer: Analyzer) -> FastAPI:
    app = FastAPI(title="AskCSV")

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index():
        index_path = os.path.join(static_dir, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(req: ChatRequest):
        try:
            res = analyzer.ask(req.prompt)
        except Exception as e:
            # return a readable error to the frontend
            raise HTTPException(status_code=400, detail=str(e))

        chart_b64 = None
        if res.fig is not None:
            buf = io.BytesIO()
            res.fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
            buf.seek(0)
            chart_b64 = base64.b64encode(buf.read()).decode("utf-8")

        preview = None
        if res.table is not None:
            preview = res.table.head(20).to_dict(orient="records")

        return ChatResponse(text=res.text, chart_base64_png=chart_b64, table_preview=preview)


    return app


def run_web(
    csv_path: str,
    api_key: str,
    model: str = "gemini-1.5-flash",
    privacy_mode: str = "profile_summary",
    sample_rows: int = 40,
    config: WebConfig = WebConfig(),
) -> None:
    analyzer = Analyzer(
        csv_path=csv_path,
        api_key=api_key,
        model=model,
        privacy_mode=privacy_mode,  # type: ignore
        sample_rows=sample_rows,
    )
    app = create_app(analyzer)

    port = config.port or _pick_free_port(config.host)
    url = f"http://{config.host}:{port}"

    def _open():
        if config.open_browser:
            webbrowser.open(url)

    threading.Timer(0.7, _open).start()

    uvicorn.run(app, host=config.host, port=port, log_level="info")
