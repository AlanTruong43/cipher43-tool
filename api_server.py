# -*- coding: utf-8 -*-
"""
Cipher 43 Tool — Automation API Server
User chỉ cần truyền debug port, server tự kết nối và thực thi script.
Tương thích với mọi antidetect browser: GPM, GoLogin, v.v.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import importlib.util
from pathlib import Path
import logging
import uvicorn
import socket
import json
import requests as http_requests

from adapters import get_adapter
from excel_reader import read_excel
from git_updater import git_pull

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API_Server")

CONFIG_PATH = Path(__file__).parent / "config.json"
EXCLUDE_SCRIPTS = {"selenium_best_practices"}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise RuntimeError("config.json không tồn tại. Vui lòng tạo file config.json.")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))


def verify_token(tool_token: str, be_url: str) -> dict:
    """Gọi BE để xác thực tool token. Trả về payload nếu hợp lệ, raise nếu không."""
    try:
        res = http_requests.post(
            f"{be_url}/api/tools/verify-token",
            json={"token": tool_token},
            timeout=10,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Không thể kết nối BE: {e}")
    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")
    return res.json()


app = FastAPI(title="Cipher 43 Tool — Automation API")

# Cache debug addresses populated by Genlogin's built-in "Call API" callback
# key: profile_name.strip().lower(), value: "127.0.0.1:{port}"
profile_debug_cache: dict[str, str] = {}

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


# ── Models ────────────────────────────────────────────────────────────────────

class AutomationRequest(BaseModel):
    remote_debugging_address: str
    profile_id: str = "unknown"
    profile_name: str = "unknown"


class RunRequest(BaseModel):
    tool_token: str
    excel_path: str
    extra_params: dict = {}


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
    """Chạy script automation trong background"""
    import sys
    try:
        project_path = Path(__file__).parent / "project" / f"{script_name}.py"
        if not project_path.exists():
            logger.error(f"Script '{script_name}.py' không tồn tại trong thư mục project/")
            return

        # Ensure project/ dir is on sys.path so `import encoding_fix` works
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
        else:
            logger.error(f"Script '{script_name}.py' không có hàm run()")

    except Exception as e:
        logger.error(f"Task '{script_name}' thất bại: {e}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "online"}


@app.api_route("/callback/profile-ready", methods=["GET", "POST"])
async def genlogin_callback(request: Request, background_tasks: BackgroundTasks):
    """
    Genlogin gọi endpoint này sau khi profile mở xong.
    1. Lấy debug address của profile (từ payload hoặc query /running)
    2. Cache vào profile_debug_cache
    3. Tự chạy script từ tool_token trong config.json — không cần Extension
    """
    import re as _re
    import requests as _req

    # Parse payload
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

    # Extract port from wsEndpoint if needed
    if not port and ws_endpoint:
        m = _re.search(r":(\d+)/", ws_endpoint)
        if m:
            port = m.group(1)

    # Build list of (profile_name, debug_address) to run
    to_run = []

    if profile_name and port:
        debug_address = f"127.0.0.1:{port}"
        profile_debug_cache[str(profile_name).strip().lower()] = debug_address
        to_run.append((str(profile_name).strip(), debug_address))
        logger.info(f"Callback: profile '{profile_name}' → {debug_address}")
    else:
        # Fallback: query Genlogin /running to get all open profiles
        try:
            config = load_config()
            adapter = get_adapter(config["browser"], config)
            res = _req.get(
                "http://127.0.0.1:55550/backend/profiles/running",
                headers={"Authorization": f"Bearer {adapter.token}"},
                timeout=5,
            )
            for p in res.json().get("data", []):
                pname = p.get("name", "").strip()
                pport = p.get("port")
                if pname and pport:
                    addr = f"127.0.0.1:{pport}"
                    profile_debug_cache[pname.lower()] = addr
                    to_run.append((pname, addr))
            logger.info(f"Callback fallback: found {len(to_run)} running profiles")
        except Exception as e:
            logger.warning(f"Callback fallback query failed: {e}")

    if not to_run:
        logger.warning(f"Callback: không tìm được profile nào để chạy. data={data}")
        return {"status": "ignored", "received": data}

    # Lấy script_name từ tool_token trong config.json
    try:
        config = load_config()
        tool_token = config.get("tool_token", "")
        if not tool_token:
            logger.warning("Callback: tool_token chưa cấu hình trong config.json")
            return {"status": "cached", "profiles": [n for n, _ in to_run], "script": None}

        payload = verify_token(tool_token, config["be_url"])
        script_name = payload.get("scriptName", "")
        if not script_name:
            logger.warning("Callback: token không có scriptName")
            return {"status": "cached", "profiles": [n for n, _ in to_run], "script": None}
    except Exception as e:
        logger.warning(f"Callback: xác thực token thất bại: {e}")
        return {"status": "cached", "profiles": [n for n, _ in to_run], "script": None}

    # Queue script cho từng profile
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


@app.get("/callback/cache")
async def get_callback_cache():
    """Debug: xem danh sách profiles đã được cache qua callback."""
    return {"cached_profiles": list(profile_debug_cache.keys()), "count": len(profile_debug_cache)}


@app.get("/scripts")
async def list_scripts():
    scripts = sorted([
        p.stem for p in (Path(__file__).parent / "project").glob("*.py")
        if p.stem not in EXCLUDE_SCRIPTS
    ])
    return {"scripts": scripts}


@app.get("/profiles")
async def list_profiles(token: str = Query(..., description="Tool token")):
    """Trả về danh sách profiles từ antidetect browser đang cấu hình."""
    config = load_config()
    verify_token(token, config["be_url"])
    adapter = get_adapter(config["browser"], config)
    try:
        profiles = adapter.list_profiles()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Không thể lấy danh sách profiles: {e}")
    return {"profiles": profiles}


@app.get("/tool-info")
async def tool_info(token: str = Query(..., description="Tool token")):
    """Validate token + trả về tool info + danh sách profiles. Extension gọi sau khi user paste token."""
    config = load_config()
    payload = verify_token(token, config["be_url"])
    adapter = get_adapter(config["browser"], config)
    try:
        profiles = adapter.list_profiles()
    except Exception as e:
        profiles = []
        logger.warning(f"Không lấy được profiles: {e}")
    return {
        "toolName": payload.get("toolName", ""),
        "scriptName": payload.get("scriptName", ""),
        "profiles": profiles,
    }


@app.post("/run")
async def run_from_excel(body: RunRequest, background_tasks: BackgroundTasks):
    """
    Đọc Excel, với mỗi hàng tự lấy debug port theo profile_name rồi chạy script.
    Pull code mới nhất từ git trước khi chạy.
    """
    config = load_config()
    payload = verify_token(body.tool_token, config["be_url"])
    script_name = payload.get("scriptName", "")
    if not script_name:
        raise HTTPException(status_code=400, detail="Token không chứa scriptName hợp lệ")

    # Pull code mới nhất
    try:
        pull_result = git_pull()
        logger.info(f"git pull: {pull_result}")
    except Exception as e:
        logger.warning(f"git pull thất bại (tiếp tục với code hiện tại): {e}")

    # Đọc Excel
    try:
        rows = read_excel(body.excel_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi đọc Excel: {e}")

    if not rows:
        raise HTTPException(status_code=400, detail="File Excel không có dữ liệu")

    adapter = get_adapter(config["browser"], config)
    queued = []
    errors = []

    for row in rows:
        profile_name = row.get("profile_name", "").strip()
        if not profile_name:
            errors.append({"row": row, "error": "Thiếu profile_name"})
            continue

        try:
            debug_address = adapter.get_debug_address(profile_name, cache=profile_debug_cache)
        except Exception as e:
            errors.append({"profile_name": profile_name, "error": str(e)})
            continue

        profile_data = {
            "remote_debugging_address": debug_address,
            "profile_name": profile_name,
            **row,
            **body.extra_params,
        }
        background_tasks.add_task(run_automation_task, script_name, profile_data)
        queued.append(profile_name)

    return {
        "status": "queued",
        "script": script_name,
        "queued_profiles": queued,
        "errors": errors,
    }


# ── Legacy endpoints (giữ lại tương thích) ───────────────────────────────────

@app.get("/execute/{project_name}")
async def execute_get(
    project_name: str,
    background_tasks: BackgroundTasks,
    request: Request,
    port: str = Query(...),
    host: str = Query("127.0.0.1"),
):
    debug_address = f"{host}:{port}"
    if not check_port(host, int(port)):
        raise HTTPException(status_code=502, detail=f"Port {port} không phản hồi.")

    extra_params = {k: v for k, v in request.query_params.items() if k not in ("port", "host")}
    profile_data = {
        "remote_debugging_address": debug_address,
        "profile_id": extra_params.pop("profile_id", "unknown"),
        "profile_name": extra_params.pop("profile_name", "unknown"),
        **extra_params,
    }
    background_tasks.add_task(run_automation_task, project_name, profile_data)
    return {"status": "queued", "script": project_name, "address": debug_address}


@app.post("/execute/{project_name}")
async def execute_post(
    project_name: str,
    data: AutomationRequest,
    background_tasks: BackgroundTasks,
    request: Request,
):
    host, port = data.remote_debugging_address.split(":")
    if not check_port(host, int(port)):
        raise HTTPException(status_code=502, detail=f"Port {port} không phản hồi.")

    extra_params = dict(request.query_params)
    profile_data = {
        "remote_debugging_address": data.remote_debugging_address,
        "profile_id": data.profile_id,
        "profile_name": data.profile_name,
        **extra_params,
    }
    background_tasks.add_task(run_automation_task, project_name, profile_data)
    return {"status": "queued", "script": project_name, "address": data.remote_debugging_address}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
