"""
launcher.py — Cipher 43 Tool launcher với terminal menu và auto-update.

Chức năng:
  - Verify tool_token với BE khi start
  - Auto-sync scripts (.pyc) từ GitHub Releases
  - Start/Stop api_server
  - Terminal menu: [1] Start/Stop [2] Sync [3] Scripts [4] Config [5] Log [0] Thoát
"""
import os
import sys
import json
import time
import signal
import hashlib
import platform
import subprocess
import urllib.request
from pathlib import Path
from datetime import datetime

VERSION = "1.0.0"

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
PROJECT_DIR = BASE_DIR / "project"
LOG_FILE = BASE_DIR / "api_server.log"
API_SERVER = BASE_DIR / "api_server.py"

BE_URL_DEFAULT = "https://cipher-43-lab-be-production.up.railway.app"
MANIFEST_FALLBACK = "https://github.com/AlanTruong43/cipher43-tool/releases/latest/download/scripts-manifest.json"
GITHUB_RELEASE_BASE = "https://github.com/AlanTruong43/cipher43-tool/releases/latest/download"

_server_proc = None


# ─── Config ────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=4, ensure_ascii=False), encoding="utf-8")


# ─── Network helpers ───────────────────────────────────────────────────────

def http_get_json(url: str, timeout: int = 10) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"cipher43-tool/{VERSION}"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def http_download(url: str, dest: Path, timeout: int = 30) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"cipher43-tool/{VERSION}"})
        with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
            f.write(r.read())
        return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    h.update(path.read_bytes())
    return h.hexdigest()


# ─── Token & BE ────────────────────────────────────────────────────────────

def verify_token(cfg: dict) -> dict | None:
    """Gọi BE verify-token, trả về {"scriptName", "toolName"} hoặc None."""
    token = cfg.get("tool_token", "")
    user_email = cfg.get("user_email", "")
    be_url = cfg.get("be_url", BE_URL_DEFAULT)
    if not token:
        return None
    try:
        import urllib.parse
        data = json.dumps({"token": token, "user_email": user_email}).encode()
        req = urllib.request.Request(
            f"{be_url}/api/tools/verify-token",
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": f"cipher43-tool/{VERSION}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def get_manifest_url(cfg: dict) -> str:
    """Lấy manifest URL từ BE (có verify token), fallback về URL GitHub trực tiếp."""
    token = cfg.get("tool_token", "")
    be_url = cfg.get("be_url", BE_URL_DEFAULT)
    if token:
        result = http_get_json(f"{be_url}/api/tools/scripts/manifest?token={token}")
        if result and result.get("success") and result.get("manifestUrl"):
            return result["manifestUrl"]
    return MANIFEST_FALLBACK


# ─── Server management ─────────────────────────────────────────────────────

def is_server_running() -> bool:
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/", headers={"User-Agent": "cipher43-launcher"})
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def start_server(cfg: dict) -> bool:
    global _server_proc
    if is_server_running():
        return True

    python = sys.executable
    log = open(LOG_FILE, "a", encoding="utf-8")
    log.write(f"\n[{datetime.now().isoformat()}] === launcher start ===\n")
    log.flush()

    kwargs = {}
    if platform.system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    _server_proc = subprocess.Popen(
        [python, str(API_SERVER)],
        cwd=str(BASE_DIR),
        stdout=log,
        stderr=log,
        **kwargs,
    )

    # Poll tối đa 8s
    for _ in range(16):
        time.sleep(0.5)
        if is_server_running():
            return True
        if _server_proc.poll() is not None:
            break
    return False


def stop_server():
    global _server_proc
    if _server_proc and _server_proc.poll() is None:
        if platform.system() == "Windows":
            _server_proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            _server_proc.terminate()
        _server_proc.wait(timeout=5)
        _server_proc = None
        return

    # Fallback: kill by port
    try:
        if platform.system() == "Windows":
            out = subprocess.check_output("netstat -ano | findstr :8000", shell=True).decode()
            for line in out.splitlines():
                parts = line.split()
                if parts and parts[-1].isdigit():
                    subprocess.run(["taskkill", "/PID", parts[-1], "/F"], capture_output=True)
                    break
        else:
            subprocess.run(["pkill", "-f", "api_server.py"], capture_output=True)
    except Exception:
        pass


# ─── Script sync ───────────────────────────────────────────────────────────

def get_python_tag() -> str:
    v = sys.version_info
    return f"cpython-{v.major}{v.minor}"


def sync_scripts(cfg: dict, silent: bool = False) -> int:
    """Download scripts mới/thay đổi. Trả về số file đã cập nhật."""
    if not silent:
        print("\nFetching manifest...")

    manifest_url = get_manifest_url(cfg)
    manifest = http_get_json(manifest_url)

    if not manifest or "scripts" not in manifest:
        if not silent:
            print("  Không lấy được manifest. Kiểm tra kết nối hoặc token.")
        return 0

    PROJECT_DIR.mkdir(exist_ok=True)
    py_tag = get_python_tag()
    updated = 0

    for s in manifest["scripts"]:
        name = s["name"]
        remote_file = s["file"]
        expected_md5 = s["md5"]

        # Tên file local khớp với Python version hiện tại
        local_name = f"{name}.{py_tag}.pyc"
        local_path = PROJECT_DIR / local_name

        # Kiểm tra nếu đã có và MD5 khớp
        if local_path.exists() and md5_file(local_path) == expected_md5:
            if not silent:
                print(f"  UP-TO-DATE  {name}")
            continue

        if not silent:
            print(f"  DOWNLOADING {name}...", end=" ", flush=True)

        url = f"{GITHUB_RELEASE_BASE}/{remote_file}"
        tmp = local_path.with_suffix(".tmp")
        if http_download(url, tmp):
            tmp.replace(local_path)
            updated += 1
            if not silent:
                print("OK")
        else:
            if tmp.exists():
                tmp.unlink()
            if not silent:
                print("FAILED")

    if not silent:
        print(f"\n{updated} script(s) updated. Version: {manifest.get('version', '?')}")

    return updated


# ─── Display helpers ───────────────────────────────────────────────────────

def clear():
    os.system("cls" if platform.system() == "Windows" else "clear")


def status_line() -> str:
    if is_server_running():
        return "● RUNNING  (port 8000)"
    return "○ STOPPED"


def pending_updates(cfg: dict) -> int:
    """Đếm số scripts có update (so sánh manifest với local)."""
    try:
        manifest_url = get_manifest_url(cfg)
        manifest = http_get_json(manifest_url, timeout=5)
        if not manifest or "scripts" not in manifest:
            return 0
        py_tag = get_python_tag()
        count = 0
        for s in manifest["scripts"]:
            local = PROJECT_DIR / f"{s['name']}.{py_tag}.pyc"
            if not local.exists() or md5_file(local) != s["md5"]:
                count += 1
        return count
    except Exception:
        return 0


def draw_menu(user_info: str, cfg: dict, updates: int = 0):
    width = 44
    border = "═" * width
    print(f"╔{border}╗")
    print(f"║  Cipher 43 Tool v{VERSION:<{width - 19}}║")
    print(f"║  {user_info:<{width - 2}}║")
    print(f"╠{border}╣")
    status = status_line()
    print(f"║  Status: {status:<{width - 10}}║")
    print(f"╠{border}╣")
    sync_label = f"[2] Sync scripts" + (f" ({updates} updates)" if updates > 0 else "")
    print(f"║  [1] Start / Stop server{' ' * (width - 25)}║")
    print(f"║  {sync_label:<{width - 2}}║")
    print(f"║  [3] Xem scripts đã cài{' ' * (width - 24)}║")
    print(f"║  [4] Cài đặt (config.json){' ' * (width - 27)}║")
    print(f"║  [5] Xem log{' ' * (width - 13)}║")
    print(f"║  [0] Thoát{' ' * (width - 11)}║")
    print(f"╚{border}╝")


# ─── Menu actions ──────────────────────────────────────────────────────────

def action_toggle_server(cfg: dict):
    if is_server_running():
        print("\nStopping server...")
        stop_server()
        time.sleep(1)
        print("Stopped." if not is_server_running() else "Still running — try again.")
    else:
        print("\nStarting server...")
        ok = start_server(cfg)
        print("Server started on port 8000." if ok else "Failed to start. Xem log [5] để biết lỗi.")
    input("\nEnter để tiếp tục...")


def action_sync(cfg: dict):
    was_running = is_server_running()
    if was_running:
        print("\nDừng server để sync...")
        stop_server()
        time.sleep(1)
    sync_scripts(cfg, silent=False)
    if was_running:
        print("\nKhởi động lại server...")
        start_server(cfg)
    input("\nEnter để tiếp tục...")


def action_list_scripts():
    print()
    py_tag = get_python_tag()
    files = sorted(PROJECT_DIR.glob(f"*.{py_tag}.pyc")) if PROJECT_DIR.exists() else []
    if not files:
        print("Chưa có script nào. Chọn [2] Sync để tải về.")
    else:
        print(f"{'Tên script':<30} {'Size':>10}  {'Ngày cập nhật'}")
        print("-" * 60)
        for f in files:
            name = f.name.replace(f".{py_tag}.pyc", "")
            stat = f.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"{name:<30} {stat.st_size:>8,}B  {mtime}")
    input("\nEnter để tiếp tục...")


def action_config(cfg: dict) -> dict:
    print("\n=== Cài đặt ===")
    print("(Enter để giữ giá trị hiện tại)\n")

    fields = [
        ("tool_token", "Tool Token (c43_xxx)"),
        ("user_email", "Email đăng ký trên cipher43.com"),
        ("browser", "Loại browser [genlogin/gologin/gpm]"),
        ("be_url", "BE URL"),
    ]
    for key, label in fields:
        current = cfg.get(key, "")
        display = f"[{current}]" if current else "[chưa có]"
        val = input(f"{label} {display}: ").strip()
        if val:
            cfg[key] = val

    save_config(cfg)
    print("\nĐã lưu config.json.")
    input("Enter để tiếp tục...")
    return cfg


def action_log():
    print()
    if not LOG_FILE.exists():
        print("Chưa có log file.")
        input("\nEnter để tiếp tục...")
        return
    lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = lines[-50:] if len(lines) > 50 else lines
    print(f"--- {LOG_FILE.name} (50 dòng cuối) ---")
    print("\n".join(tail))
    input("\nEnter để tiếp tục...")


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    clear()
    print("Cipher 43 Tool đang khởi động...\n")

    cfg = load_config()

    # Nếu chưa có config → vào config ngay
    if not cfg.get("tool_token"):
        print("Chưa có cấu hình. Vui lòng điền thông tin:\n")
        cfg = action_config(cfg)

    # Verify token
    print("Xác thực token...")
    info = verify_token(cfg)
    if info and info.get("success"):
        tool_name = info.get("toolName", "")
        user_email = cfg.get("user_email", "")
        user_info = f"{user_email} — {tool_name}" if tool_name else user_email
    else:
        user_info = cfg.get("user_email", "Token chưa xác thực")
        print(f"Cảnh báo: Không xác thực được token ({user_info})")

    # Silent sync
    print("Đang sync scripts...")
    sync_scripts(cfg, silent=True)

    # Auto-start
    if cfg.get("tool_token") and not is_server_running():
        print("Đang start server...")
        start_server(cfg)

    updates = 0

    while True:
        clear()
        draw_menu(user_info, cfg, updates)
        choice = input("\nChọn: ").strip()

        if choice == "1":
            action_toggle_server(cfg)
        elif choice == "2":
            action_sync(cfg)
            updates = 0
        elif choice == "3":
            action_list_scripts()
        elif choice == "4":
            cfg = action_config(cfg)
            # Re-verify after config change
            info = verify_token(cfg)
            if info and info.get("success"):
                tool_name = info.get("toolName", "")
                user_email = cfg.get("user_email", "")
                user_info = f"{user_email} — {tool_name}" if tool_name else user_email
        elif choice == "5":
            action_log()
        elif choice == "0":
            print("\nTạm biệt!")
            break
        else:
            # Refresh updates count mỗi lần menu load lại
            updates = pending_updates(cfg)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBị ngắt bởi user.")
