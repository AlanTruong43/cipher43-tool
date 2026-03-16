# -*- coding: utf-8 -*-
"""
Cipher 43 Tool — Automation API Server
User chỉ cần truyền debug port, server tự kết nối và thực thi script.
Tương thích với mọi antidetect browser: GPM, AdsPower, Multilogin, v.v.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import importlib.util
from pathlib import Path
import logging
import uvicorn
import socket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API_Server")

app = FastAPI(title="Cipher 43 Tool — Automation API")

# CORS — cho phép browser gọi API từ bất kỳ trang web nào
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Private Network Access — Chrome yêu cầu header này khi trang web gọi vào localhost
@app.middleware("http")
async def add_private_network_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


class AutomationRequest(BaseModel):
    remote_debugging_address: str
    profile_id: str = "unknown"
    profile_name: str = "unknown"


def check_port(host: str, port: int, retries: int = 5, delay: float = 1.0) -> bool:
    """Kiểm tra port có đang lắng nghe không, thử lại nếu chưa sẵn sàng"""
    import time
    for attempt in range(retries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        if result == 0:
            return True
        if attempt < retries - 1:
            print(f">>> [INFO] Port {port} chưa sẵn sàng, thử lại ({attempt + 1}/{retries})...")
            time.sleep(delay)
    return False


def run_automation_task(project_name: str, profile_data: dict):
    """Chạy script automation trong background"""
    try:
        project_path = Path(f"project/{project_name}.py")
        if not project_path.exists():
            print(f">>> [ERROR] Script '{project_name}.py' không tồn tại trong thư mục project/")
            return

        host, port = profile_data["remote_debugging_address"].split(":")
        if not check_port(host, port):
            print(f">>> [ERROR] Port {port} không phản hồi. Browser đã mở chưa?")
            return

        spec = importlib.util.spec_from_file_location(project_name, project_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "run"):
            print(f">>> [INFO] Bắt đầu '{project_name}' tại {profile_data['remote_debugging_address']}")
            module.run(profile_data)
        else:
            print(f">>> [ERROR] Script '{project_name}.py' không có hàm run()")

    except Exception as e:
        print(f">>> [ERROR] Task thất bại: {str(e)}")


@app.get("/scripts")
async def list_scripts():
    """Trả về danh sách scripts có trong thư mục project/"""
    scripts = sorted([
        p.stem for p in Path("project").glob("*.py")
        if p.stem != "selenium_best_practices"  # bỏ file docs
    ])
    return {"scripts": scripts}


@app.get("/")
async def root():
    return {
        "status": "online",
        "usage": {
            "GET": "/execute/{script}?port=9222&host=127.0.0.1",
            "POST": "/execute/{script}  body: { remote_debugging_address, profile_id, profile_name }",
            "extra_params": "Truyền thêm bất kỳ param nào qua query string, sẽ được forward vào script",
            "example": "/execute/twitter?port=9222",
            "example_with_data": "/execute/import_key_okx?port=9222&mnemonic=word1+word2&password=abc123"
        }
    }


@app.get("/execute/{project_name}")
async def execute_get(
    project_name: str,
    background_tasks: BackgroundTasks,
    request: Request,
    port: str = Query(..., description="Chrome remote debugging port"),
    host: str = Query("127.0.0.1", description="Host address"),
):
    """
    Thực thi script automation.
    Truyền port debug của browser đang chạy, server tự kết nối và chạy script.
    """
    debug_address = f"{host}:{port}"

    if not check_port(host, port):
        raise HTTPException(
            status_code=502,
            detail=f"Port {port} không phản hồi. Hãy chắc chắn browser đang mở."
        )

    # Gom tất cả extra params (trừ port, host) để forward vào script
    extra_params = {
        k: v for k, v in request.query_params.items()
        if k not in ("port", "host")
    }

    profile_data = {
        "remote_debugging_address": debug_address,
        "profile_id": extra_params.pop("profile_id", "unknown"),
        "profile_name": extra_params.pop("profile_name", "unknown"),
        **extra_params
    }

    background_tasks.add_task(run_automation_task, project_name, profile_data)
    return {
        "status": "queued",
        "script": project_name,
        "address": debug_address,
        "params": extra_params
    }


@app.post("/execute/{project_name}")
async def execute_post(
    project_name: str,
    data: AutomationRequest,
    background_tasks: BackgroundTasks,
    request: Request,
):
    """POST method — dùng khi cần truyền dữ liệu nhạy cảm (mnemonic, password)"""
    host, port = data.remote_debugging_address.split(":")

    if not check_port(host, port):
        raise HTTPException(
            status_code=502,
            detail=f"Port {port} không phản hồi. Hãy chắc chắn browser đang mở."
        )

    # Merge body + extra query params
    extra_params = {
        k: v for k, v in request.query_params.items()
    }

    profile_data = {
        "remote_debugging_address": data.remote_debugging_address,
        "profile_id": data.profile_id,
        "profile_name": data.profile_name,
        **extra_params
    }

    background_tasks.add_task(run_automation_task, project_name, profile_data)
    return {
        "status": "queued",
        "script": project_name,
        "address": data.remote_debugging_address
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
