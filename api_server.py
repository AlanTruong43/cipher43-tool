# -*- coding: utf-8 -*-
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
import importlib.util
from pathlib import Path
import logging
import uvicorn
import socket
import json
import re
import requests as http_requests

from adapters import get_adapter

logging.basicConfig(level=logging.INFO)
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
    import time
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


def run_automation_task(script_name: str, profile_data: dict):
    import sys
    try:
        project_path = Path(__file__).parent / "project" / f"{script_name}.py"
        if not project_path.exists():
            logger.error(f"Script '{script_name}.py' không tồn tại trong thư mục project/")
            return

        project_dir = str(project_path.parent)
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)

        host, port = profile_data["remote_debugging_address"].split(":")
        if not check_port(host, int(port)):
            logger.error(f"Port {port} không phản hồi. Browser đã mở chưa?")
            return

        spec = importlib.util.spec_from_file_location(script_name, project_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "run"):
            logger.info(f"Bắt đầu '{script_name}' tại {profile_data['remote_debugging_address']}")
            module.run(profile_data)
            logger.info(f"Hoàn thành '{script_name}' tại {profile_data['remote_debugging_address']}")
        else:
            logger.error(f"Script '{script_name}.py' không có hàm run()")

    except Exception as e:
        logger.error(f"Task '{script_name}' thất bại: {e}", exc_info=True)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "online"}


@app.get("/scripts")
async def list_scripts():
    scripts = sorted([
        p.stem for p in (Path(__file__).parent / "project").glob("*.py")
        if p.stem not in EXCLUDE_SCRIPTS
    ])
    return {"scripts": scripts}


@app.api_route("/callback/profile-ready", methods=["GET", "POST"])
async def genlogin_callback(request: Request, background_tasks: BackgroundTasks):
    """
    Genlogin gọi endpoint này sau khi profile mở xong (cấu hình Call API trong profile settings).
    Tự lấy debug address và chạy script từ tool_token trong config.json.
    """
    try:
        body = await request.json()
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
        # Genlogin không gửi data → query /running để lấy tất cả profiles đang mở
        try:
            config = load_config()
            adapter = get_adapter(config["browser"], config)
            res = http_requests.get(
                "http://127.0.0.1:55550/backend/profiles/running",
                headers={"Authorization": f"Bearer {adapter.token}"},
                timeout=5,
            )
            for p in res.json().get("data", []):
                pname = p.get("name", "").strip()
                pport = p.get("port")
                if pname and pport:
                    to_run.append((pname, f"127.0.0.1:{pport}"))
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

        payload = verify_token(tool_token, config["be_url"], config.get("user_email", ""))
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
