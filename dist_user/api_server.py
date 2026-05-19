# -*- coding: utf-8 -*-
import sys
import io
import platform

if platform.system() == "Windows":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import importlib.util
from pathlib import Path
import logging
import uvicorn
import socket
import json
import re
import time
import asyncio
import threading
from datetime import datetime
from collections import deque
import requests as http_requests

from adapters import get_adapter

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
logger = logging.getLogger("API_Server")

CONFIG_PATH = Path(__file__).parent / "config.json"
EXCLUDE_SCRIPTS = {"selenium_best_practices", "encoding_fix"}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise RuntimeError("config.json không tồn tại.")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))


def verify_token(tool_token: str, be_url: str, user_email: str = "") -> dict:
    try:
        res = http_requests.post(
            f"{be_url}/api/tools/verify-token",
            json={"token": tool_token, "user_email": user_email},
            timeout=10,
        )
    except Exception as e:
        raise RuntimeError(f"Không thể kết nối BE: {e}")
    if res.status_code != 200:
        data = res.json()
        raise RuntimeError(data.get("message", "Token không hợp lệ hoặc đã hết hạn"))
    return res.json()


# ── Task Status Manager ────────────────────────────────────────────────────────

class TaskManager:
    def __init__(self):
        self._lock = threading.Lock()
        # {profile_name: {status, script, started_at, finished_at, stats, logs, error}}
        self._tasks: dict[str, dict] = {}

    def start(self, profile_name: str, script: str):
        with self._lock:
            self._tasks[profile_name] = {
                "status": "running",
                "script": script,
                "started_at": datetime.now().isoformat(),
                "finished_at": None,
                "stats": {},
                "logs": deque(maxlen=200),
                "error": None,
            }

    def log(self, profile_name: str, message: str):
        with self._lock:
            task = self._tasks.get(profile_name)
            if task:
                task["logs"].append({
                    "ts": datetime.now().strftime("%H:%M:%S"),
                    "msg": message,
                })

    def finish(self, profile_name: str, stats: dict):
        with self._lock:
            task = self._tasks.get(profile_name)
            if task:
                task["status"] = "done"
                task["finished_at"] = datetime.now().isoformat()
                task["stats"] = stats

    def error(self, profile_name: str, err: str):
        with self._lock:
            task = self._tasks.get(profile_name)
            if task:
                task["status"] = "error"
                task["finished_at"] = datetime.now().isoformat()
                task["error"] = err

    def get_all(self) -> dict:
        with self._lock:
            result = {}
            for name, t in self._tasks.items():
                result[name] = {
                    "status": t["status"],
                    "script": t["script"],
                    "started_at": t["started_at"],
                    "finished_at": t["finished_at"],
                    "stats": t["stats"],
                    "logs": list(t["logs"]),
                    "error": t["error"],
                }
            return result

    def get_one(self, profile_name: str) -> dict | None:
        with self._lock:
            t = self._tasks.get(profile_name)
            if not t:
                return None
            return {
                "status": t["status"],
                "script": t["script"],
                "started_at": t["started_at"],
                "finished_at": t["finished_at"],
                "stats": t["stats"],
                "logs": list(t["logs"]),
                "error": t["error"],
            }

    def clear_done(self):
        with self._lock:
            self._tasks = {
                k: v for k, v in self._tasks.items()
                if v["status"] == "running"
            }


task_manager = TaskManager()


# ── Profile log interceptor ────────────────────────────────────────────────────

class ProfileLogHandler(logging.Handler):
    """Intercepts log records tagged with profile_name and forwards to TaskManager."""
    def emit(self, record):
        profile = getattr(record, "profile_name", None)
        if profile:
            task_manager.log(profile, self.format(record))


_profile_handler = ProfileLogHandler()
_profile_handler.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger().addHandler(_profile_handler)


app = FastAPI(title="Cipher 43 Tool — Automation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_private_network_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


# ── Helpers ───────────────────────────────────────────────────────────────────

def check_port(host: str, port: int, retries: int = 5, delay: float = 1.0) -> bool:
    for attempt in range(retries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        if result == 0:
            return True
        if attempt < retries - 1:
            logger.info(f"Port {port} chưa sẵn sàng, thử lại ({attempt + 1}/{retries})...")
            time.sleep(delay)
    return False


def _find_script_path(script_name: str) -> Path | None:
    """Find script: .py → .pyc → PyArmor .pyarmor.py, in priority order."""
    project_dir = Path(__file__).parent / "project"
    import sys
    v = sys.version_info
    py_tag = f"cpython-{v.major}{v.minor}"

    candidates = [
        project_dir / f"{script_name}.py",
        project_dir / f"{script_name}.{py_tag}.pyc",
        project_dir / f"{script_name}.{py_tag}.pyarmor.py",
    ]
    for p in candidates:
        if p.exists():
            return p
    # Fallback glob for any cpython tag
    for p in project_dir.glob(f"{script_name}.cpython-*.pyc"):
        return p
    for p in project_dir.glob(f"{script_name}.cpython-*.pyarmor.py"):
        return p
    return None


def run_automation_task(script_name: str, profile_data: dict):
    import sys
    profile_name = profile_data.get("profile_name", "unknown")
    task_manager.start(profile_name, script_name)

    def _log(msg: str):
        task_manager.log(profile_name, msg)
        logger.info(msg)

    try:
        script_path = _find_script_path(script_name)
        if not script_path:
            _log(f"❌ Script '{script_name}' không tồn tại trong thư mục project/")
            task_manager.error(profile_name, f"Script '{script_name}' not found")
            return

        project_dir = str(script_path.parent)
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)

        host, port = profile_data["remote_debugging_address"].split(":")
        if not check_port(host, int(port)):
            msg = f"❌ Port {port} không phản hồi. Browser đã mở chưa?"
            _log(msg)
            task_manager.error(profile_name, msg)
            return

        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "run"):
            msg = f"❌ Script '{script_name}' không có hàm run()"
            _log(msg)
            task_manager.error(profile_name, msg)
            return

        # Inject log callback so scripts can push logs to TaskManager
        profile_data["_log_callback"] = _log

        _log(f"▶ Bắt đầu '{script_name}'")
        result = module.run(profile_data)
        stats = result if isinstance(result, dict) else {}
        task_manager.finish(profile_name, stats)
        _log(f"✅ Hoàn thành — {stats}")

    except Exception as e:
        err = str(e)
        task_manager.error(profile_name, err)
        logger.error(f"Task '{script_name}' thất bại: {e}", exc_info=True)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "online"}


@app.get("/scripts")
async def list_scripts():
    project_dir = Path(__file__).parent / "project"
    seen = set()
    scripts = []
    for p in sorted(project_dir.iterdir()):
        stem = p.stem.split(".")[0]  # strip cpython tag from .pyc
        if stem not in EXCLUDE_SCRIPTS and stem not in seen and not stem.startswith("_"):
            seen.add(stem)
            scripts.append(stem)
    return {"scripts": sorted(scripts)}


@app.get("/status")
async def get_status():
    return {"tasks": task_manager.get_all()}


@app.get("/status/{profile_name}")
async def get_profile_status(profile_name: str):
    task = task_manager.get_one(profile_name)
    if not task:
        return {"error": "Profile not found"}
    return task


@app.delete("/status")
async def clear_status():
    task_manager.clear_done()
    return {"ok": True}


@app.get("/status/stream/{profile_name}")
async def stream_profile_logs(profile_name: str):
    """SSE stream: push new log lines for a profile as they arrive."""
    async def event_generator():
        sent = 0
        while True:
            task = task_manager.get_one(profile_name)
            if task is None:
                yield f"data: {json.dumps({'type': 'waiting'})}\n\n"
                await asyncio.sleep(1)
                continue

            logs = task["logs"]
            if len(logs) > sent:
                for entry in logs[sent:]:
                    yield f"data: {json.dumps({'type': 'log', **entry})}\n\n"
                sent = len(logs)

            if task["status"] in ("done", "error"):
                yield f"data: {json.dumps({'type': 'done', 'status': task['status'], 'stats': task['stats'], 'error': task['error']})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.api_route("/callback/profile-ready", methods=["GET", "POST"])
async def genlogin_callback(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        if not isinstance(body, dict):
            body = {}
    except Exception:
        body = {}
    params = dict(request.query_params)
    data = {**params, **body}

    profile_name = (
        data.get("name") or data.get("profile_name")
        or data.get("profileName") or data.get("profile")
    )
    port = (
        data.get("port") or data.get("debug_port")
        or data.get("debugPort") or data.get("remotePort")
    )
    ws_endpoint = data.get("wsEndpoint") or data.get("ws_endpoint")

    if not port and ws_endpoint:
        m = re.search(r":(\d+)/", ws_endpoint)
        if m:
            port = m.group(1)

    to_run = []

    if profile_name and port:
        addr = f"127.0.0.1:{port}"
        to_run.append((str(profile_name).strip(), addr))
        logger.info(f"Callback: profile '{profile_name}' → {addr}")
    else:
        try:
            config = load_config()
            adapter = get_adapter(config.get("browser", ""))
            for p in adapter.list_profiles():
                if p.get("status") == "running" and p.get("port"):
                    to_run.append((p["name"], f"127.0.0.1:{p['port']}"))
            logger.info(f"Callback fallback: found {len(to_run)} running profiles")
        except Exception as e:
            logger.warning(f"Callback fallback query failed: {e}")

    if not to_run:
        logger.warning(f"Callback: không tìm được profile nào. data={data}")
        return {"status": "ignored", "received": data}

    try:
        config = load_config()
        tool_token = config.get("tool_token", "")
        if not tool_token:
            logger.warning("Callback: tool_token chưa cấu hình trong config.json")
            return {"status": "no_token", "profiles": [n for n, _ in to_run]}

        be_url = config.get("be_url", "https://cipher-43-lab-be-production.up.railway.app")
        payload = verify_token(tool_token, be_url, config.get("user_email", ""))
        script_name = payload.get("scriptName", "")
        if not script_name:
            logger.warning("Callback: token không có scriptName")
            return {"status": "no_script", "profiles": [n for n, _ in to_run]}
    except Exception as e:
        logger.warning(f"Callback: xác thực token thất bại: {e}")
        return {"status": "token_error", "error": str(e)}

    for pname, debug_address in to_run:
        profile_data = {
            "remote_debugging_address": debug_address,
            "profile_name": pname,
        }
        background_tasks.add_task(run_automation_task, script_name, profile_data)
        logger.info(f"Callback: queued '{script_name}' cho '{pname}'")

    return {
        "status": "queued",
        "script": script_name,
        "profiles": [n for n, _ in to_run],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
