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
import platform

# Fix Windows console encoding for Vietnamese text
if platform.system() == "Windows":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import json
import time
import signal
import hashlib
import subprocess
import urllib.request
from pathlib import Path
from datetime import datetime

VERSION = "1.1.0"

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
PROJECT_DIR = BASE_DIR / "project"
LOG_FILE = BASE_DIR / "api_server.log"
API_SERVER = BASE_DIR / "api_server.py"

BE_URL_DEFAULT = "https://cipher-43-lab-be-production.up.railway.app"
MANIFEST_FALLBACK = "https://github.com/AlanTruong43/cipher43-tool/releases/latest/download/scripts-manifest.json"
GITHUB_RELEASE_BASE = "https://github.com/AlanTruong43/cipher43-tool/releases/latest/download"
CORE_MANIFEST_FALLBACK = "https://github.com/AlanTruong43/cipher43-tool/releases/latest/download/core-manifest.json"

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
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": f"cipher43-tool/{VERSION}"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def http_download(url: str, dest: Path, timeout: int = 30) -> bool:
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": f"cipher43-tool/{VERSION}"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r, open(dest, "wb") as f:
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
    if not token:
        return None
    import urllib.error
    data = json.dumps({"token": token, "user_email": user_email}).encode()
    req = urllib.request.Request(
        f"{BE_URL_DEFAULT}/api/tools/verify-token",
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": f"cipher43-tool/{VERSION}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"success": False, "message": f"HTTP {e.code}"}
    except Exception:
        return None


def get_manifest_url(cfg: dict) -> str:
    """Lấy manifest URL từ BE (có verify token), fallback về URL GitHub trực tiếp."""
    token = cfg.get("tool_token", "")
    if token:
        result = http_get_json(f"{BE_URL_DEFAULT}/api/tools/scripts/manifest?token={token}")
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


def start_server() -> bool:
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
        try:
            _server_proc.wait(timeout=5)
        except Exception:
            _server_proc.kill()
        _server_proc = None
    else:
        # Fallback: kill by port
        try:
            if platform.system() == "Windows":
                out = subprocess.check_output(
                    "netstat -ano | findstr :8000 | findstr LISTENING", shell=True
                ).decode()
                for line in out.splitlines():
                    parts = line.split()
                    if parts and parts[-1].isdigit():
                        subprocess.run(["taskkill", "/PID", parts[-1], "/F"], capture_output=True)
            else:
                subprocess.run(["pkill", "-f", "api_server.py"], capture_output=True)
        except Exception:
            pass

    # Poll until port is actually free (max 6s)
    for _ in range(12):
        time.sleep(0.5)
        if not is_server_running():
            return


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
    updated = 0

    for s in manifest["scripts"]:
        name = s["name"]
        remote_file = s["file"]
        expected_md5 = s["md5"]

        # Dùng tên file từ manifest trực tiếp (hỗ trợ cả .pyc và PyArmor)
        local_path = PROJECT_DIR / remote_file

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
            # Extract pyarmor runtime zip vào project/
            if s.get("type") == "pyarmor_runtime":
                try:
                    import zipfile
                    with zipfile.ZipFile(local_path, "r") as zf:
                        zf.extractall(PROJECT_DIR)
                    if not silent:
                        print("OK (extracted)")
                except Exception as e:
                    if not silent:
                        print(f"OK (extract failed: {e})")
            else:
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


# ─── Core file sync ────────────────────────────────────────────────────────

def get_core_manifest_url(cfg: dict) -> str:
    token = cfg.get("tool_token", "")
    if token:
        result = http_get_json(f"{BE_URL_DEFAULT}/api/tools/core/manifest?token={token}")
        if result and result.get("success") and result.get("manifestUrl"):
            return result["manifestUrl"]
    return CORE_MANIFEST_FALLBACK


def _restart_launcher():
    """Thay thế process hiện tại bằng launcher mới (os.execv — không tạo thêm process)."""
    import os
    os.execv(sys.executable, [sys.executable, str(BASE_DIR / "launcher.py")])


def sync_core(cfg: dict, silent: bool = False) -> int:
    """Download core files mới/thay đổi. Trả về số file đã cập nhật."""
    if not silent:
        print("\nFetching core manifest...")

    manifest_url = get_core_manifest_url(cfg)
    manifest = http_get_json(manifest_url)

    if not manifest or "files" not in manifest:
        if not silent:
            print("  Không lấy được core manifest. Bỏ qua.")
        return 0

    updated = 0
    launcher_updated = False

    for f in manifest["files"]:
        local_path = BASE_DIR / f["name"]
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if local_path.exists() and md5_file(local_path) == f["md5"]:
            if not silent:
                print(f"  UP-TO-DATE  {f['name']}")
            continue

        if not silent:
            print(f"  DOWNLOADING {f['name']}...", end=" ", flush=True)

        url = f"{GITHUB_RELEASE_BASE}/{f['file']}"
        tmp = local_path.with_suffix(local_path.suffix + ".tmp")
        if http_download(url, tmp):
            tmp.replace(local_path)
            updated += 1
            if f["name"] == "launcher.py":
                launcher_updated = True
            if not silent:
                print("OK")
        else:
            if tmp.exists():
                tmp.unlink()
            if not silent:
                print("FAILED")

    if not silent:
        print(f"\n{updated} core file(s) updated. Version: {manifest.get('version', '?')}")

    if launcher_updated:
        if not silent:
            print("launcher.py đã được cập nhật — khởi động lại...")
        _restart_launcher()

    return updated


# ─── Display helpers ───────────────────────────────────────────────────────

def clear():
    os.system("cls" if platform.system() == "Windows" else "clear")


def safe_input(prompt: str = "") -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""


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
        count = 0
        for s in manifest["scripts"]:
            local = PROJECT_DIR / s["file"]
            if not local.exists() or md5_file(local) != s["md5"]:
                count += 1
        return count
    except Exception:
        return 0


def draw_menu(user_info: str, updates: int = 0):
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
    print(f"║  [5] Xem log theo profile{' ' * (width - 26)}║")
    print(f"║  [0] Thoát{' ' * (width - 11)}║")
    print(f"╚{border}╝")


# ─── Menu actions ──────────────────────────────────────────────────────────

def action_toggle_server():
    if is_server_running():
        print("\nStopping server...")
        stop_server()
        print("Stopped." if not is_server_running() else "Still running — try again.")
    else:
        print("\nStarting server...")
        ok = start_server()
        print("Server started on port 8000." if ok else "Failed to start. Xem log [5] để biết lỗi.")
    safe_input("\nEnter để tiếp tục...")


def action_sync(cfg: dict):
    was_running = is_server_running()
    if was_running:
        print("\nDừng server để sync...")
        stop_server()
        time.sleep(1)

    print("\nSync core files...")
    sync_core(cfg, silent=False)   # nếu launcher.py update → tự restart

    print("\nSync scripts...")
    sync_scripts(cfg, silent=False)

    if was_running:
        print("\nKhởi động lại server...")
        start_server()
    safe_input("\nEnter để tiếp tục...")


def action_list_scripts():
    print()
    files = sorted(PROJECT_DIR.glob("*")) if PROJECT_DIR.exists() else []
    # Show only script files, not runtime/encoding files
    script_files = [
        f for f in files
        if f.suffix in (".py", ".pyc") and not f.name.startswith("__")
        and "encoding_fix" not in f.name and "pyarmor_runtime" not in f.name
    ]
    if not script_files:
        print("Chưa có script nào. Chọn [2] Sync để tải về.")
    else:
        print(f"{'Tên script':<30} {'Size':>10}  {'Ngày cập nhật'}")
        print("-" * 60)
        for f in script_files:
            # Strip cpython tag and extension to get clean name
            name = f.name.split(".")[0]
            stat = f.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"{name:<30} {stat.st_size:>8,}B  {mtime}")
    safe_input("\nEnter để tiếp tục...")


def _config_script_settings(cfg: dict, script_name: str):
    if script_name == "twitter":
        farming = cfg.get("farming", {})
        print("\n--- Cài đặt Twitter Farming ---")

        like_prob = farming.get("like_probability", 0.4)
        val = safe_input(f"Tỷ lệ Like (0.0-1.0) [{like_prob}]: ").strip()
        if val:
            try:
                like_prob = max(0.0, min(1.0, float(val)))
            except ValueError:
                pass

        comment_prob = farming.get("comment_probability", 0.2)
        val = safe_input(f"Tỷ lệ Comment (0.0-1.0) [{comment_prob}]: ").strip()
        if val:
            try:
                comment_prob = max(0.0, min(1.0, float(val)))
            except ValueError:
                pass

        cfg["farming"] = {**farming, "like_probability": like_prob, "comment_probability": comment_prob}
        print(f"  Like: {like_prob:.0%}  Comment: {comment_prob:.0%}")


def action_config(cfg: dict) -> dict:
    from adapters import ANTIDETECT_CHOICES
    print("\n=== Cài đặt ===\n")

    ai_cfg = cfg.get("ai_provider", {})
    ai_type = ai_cfg.get("type", "gemini")
    ai_key  = ai_cfg.get("api_key", "")

    # Nếu config đã đầy đủ → hiện summary, cho verify ngay
    if cfg.get("tool_token") and cfg.get("user_email") and cfg.get("browser"):
        browser_label = next((l for _, k, l in ANTIDETECT_CHOICES if k == cfg.get("browser")), cfg.get("browser", ""))
        key_display = (ai_key[:6] + "...") if len(ai_key) > 6 else (ai_key or "[chưa có]")
        print(f"  Token   : {cfg['tool_token']}")
        print(f"  Email   : {cfg['user_email']}")
        print(f"  Browser : {browser_label}")
        print(f"  AI      : {ai_type.upper()}  key={key_display}")
        print()
        choice = safe_input("Nhấn Enter để xác thực lại, hoặc [s] để sửa: ").strip().lower()
        if choice != "s":
            print("\nĐang xác thực...")
            result = verify_token(cfg)
            if not result or not result.get("success"):
                msg = result.get("message", "Không kết nối được BE") if result else "Không kết nối được BE"
                print(f"Lỗi: {msg}")
            else:
                print(f"Xác thực thành công! Tool: {result.get('toolName', '')}")
            safe_input("\nEnter để tiếp tục...")
            return cfg

    # Form đầy đủ (config chưa có hoặc user chọn sửa)
    for key, label in [
        ("tool_token", "Tool Token (c43_xxx)"),
        ("user_email", "Email đăng ký trên cipher43.com"),
    ]:
        current = cfg.get(key, "")
        display = f"[{current}]" if current else "[chưa có]"
        val = safe_input(f"{label} {display}: ").strip()
        if val:
            cfg[key] = val

    # Antidetect selection
    print("\nChọn antidetect browser:")
    for num, key, label in ANTIDETECT_CHOICES:
        print(f"  [{num}] {label}")
    current_browser = cfg.get("browser", "")
    current_label = next((l for _, k, l in ANTIDETECT_CHOICES if k == current_browser), current_browser)
    display = f"[{current_label}]" if current_label else "[chưa chọn]"
    choice = safe_input(f"Chọn số {display}: ").strip()
    selected = next((k for n, k, _ in ANTIDETECT_CHOICES if n == choice), None)
    if selected:
        cfg["browser"] = selected

    # AI provider selection
    print("\nChọn AI provider:")
    print("  [1] DEMO")
    print("  [2] Gemini (Google)")
    ai_display = f"[{ai_type.upper()}]"
    ai_choice = safe_input(f"Chọn số {ai_display}: ").strip()
    if ai_choice == "1":
        ai_type = "demo"
    elif ai_choice == "2":
        ai_type = "gemini"

    key_display = (ai_key[:6] + "...") if len(ai_key) > 6 else (ai_key or "[chưa có]")
    new_key = safe_input(f"API Key {key_display}: ").strip()
    if new_key:
        ai_key = new_key

    default_model = "gpt-4.1-nano" if ai_type == "demo" else "gemini-2.0-flash"
    current_model = ai_cfg.get("model", default_model)
    new_model = safe_input(f"Model [{current_model}]: ").strip()

    cfg["ai_provider"] = {
        **ai_cfg,
        "type": ai_type,
        "api_key": ai_key,
        "model": new_model if new_model else current_model,
    }

    # Validate token + email trước khi lưu
    if cfg.get("tool_token") and cfg.get("user_email"):
        print("\nĐang xác thực...")
        result = verify_token(cfg)
        if not result or not result.get("success"):
            msg = result.get("message", "Không kết nối được BE") if result else "Không kết nối được BE"
            print(f"Lỗi: {msg}")
            print("Vui lòng kiểm tra lại Token và Email rồi thử lại.")
            safe_input("\nEnter để tiếp tục...")
            return cfg
        print(f"Xác thực thành công! Tool: {result.get('toolName', '')}")
        script_name = result.get("scriptName", "")
    else:
        script_name = ""

    # Script-specific settings
    _config_script_settings(cfg, script_name)

    save_config(cfg)
    print("Đã lưu cài đặt.")
    safe_input("\nEnter để tiếp tục...")
    return cfg


def action_log():
    print()
    if not LOG_FILE.exists():
        print("Chưa có log file.")
        safe_input("\nEnter để tiếp tục...")
        return
    lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = lines[-50:] if len(lines) > 50 else lines
    print(f"--- {LOG_FILE.name} (50 dòng cuối) ---")
    print("\n".join(tail))
    safe_input("\nEnter để tiếp tục...")


def _fmt_status(status: str) -> str:
    return {"running": "● RUNNING", "done": "✅ DONE", "error": "❌ ERROR"}.get(status, status)


def action_log_profile():
    """Hiển thị log theo profile. Lấy data từ api_server /status."""
    print()
    if not is_server_running():
        print("Server chưa chạy. Chọn [1] Start trước.")
        safe_input("\nEnter để tiếp tục...")
        return

    data = http_get_json("http://127.0.0.1:8000/status", timeout=5)
    if not data or "tasks" not in data:
        print("Không lấy được trạng thái từ server.")
        safe_input("\nEnter để tiếp tục...")
        return

    tasks = data["tasks"]
    if not tasks:
        print("Chưa có profile nào chạy. Mở browser profile để bắt đầu.")
        safe_input("\nEnter để tiếp tục...")
        return

    profiles = list(tasks.keys())
    print("=== Profiles đã/đang chạy ===\n")
    for i, name in enumerate(profiles, 1):
        t = tasks[name]
        started = (t.get("started_at") or "")[11:19]
        print(f"  [{i}] {name:<30} {_fmt_status(t.get('status', '?')):<12} script={t.get('script', '')} started={started}")

    print()
    choice = safe_input("Chọn số profile để xem log (Enter để hủy): ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(profiles)):
        return

    profile_name = profiles[int(choice) - 1]
    task = tasks[profile_name]

    clear()
    print(f"=== Log: {profile_name} ===")
    print(f"Status   : {_fmt_status(task.get('status', '?'))}")
    print(f"Script   : {task.get('script', '')}")
    print(f"Started  : {task.get('started_at', '')}")
    if task.get("finished_at"):
        print(f"Finished : {task.get('finished_at')}")
    if task.get("stats"):
        print(f"Stats    : {task.get('stats')}")
    if task.get("error"):
        print(f"Error    : {task.get('error')}")
    print()
    print(f"--- Log entries ({len(task.get('logs', []))}) ---")
    for entry in task.get("logs", []):
        print(f"[{entry.get('ts', '')}] {entry.get('msg', '')}")

    print()
    if task.get("status") == "running":
        follow = safe_input("Profile đang chạy. Nhấn [f] để follow log (Ctrl+C để dừng), Enter để thoát: ").strip().lower()
        if follow == "f":
            _follow_profile_log(profile_name, len(task.get("logs", [])))
    else:
        safe_input("Enter để tiếp tục...")


def _follow_profile_log(profile_name: str, already_shown: int):
    """Poll /status/{profile_name} mỗi 1s, in các log mới."""
    print(f"\n--- Following {profile_name} (Ctrl+C để dừng) ---")
    sent = already_shown
    try:
        while True:
            task = http_get_json(f"http://127.0.0.1:8000/status/{profile_name}", timeout=5)
            if not task or "logs" not in task:
                time.sleep(1)
                continue
            logs = task["logs"]
            if len(logs) > sent:
                for entry in logs[sent:]:
                    print(f"[{entry.get('ts', '')}] {entry.get('msg', '')}")
                sent = len(logs)
            if task.get("status") in ("done", "error"):
                print(f"\n--- Kết thúc: {_fmt_status(task['status'])} — stats={task.get('stats')} error={task.get('error')} ---")
                safe_input("Enter để tiếp tục...")
                return
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- Dừng follow ---")
        safe_input("Enter để tiếp tục...")


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    clear()
    print("Cipher 43 Tool đang khởi động...\n")

    cfg = load_config()

    # Nếu chưa có config hoặc token chưa hợp lệ → bắt buộc cài đặt
    while not cfg.get("tool_token") or not cfg.get("user_email"):
        print("Chưa có cấu hình. Vui lòng điền thông tin:\n")
        cfg = action_config(cfg)
        if not cfg.get("tool_token") or not cfg.get("user_email"):
            print("Token và Email là bắt buộc.\n")

    # Verify token — bắt buộc pass mới tiếp tục
    print("Xác thực token...")
    info = verify_token(cfg)
    while not info or not info.get("success"):
        msg = info.get("message", "Lỗi kết nối") if info else "Không kết nối được server"
        print(f"Xác thực thất bại: {msg}")
        print("Vui lòng cập nhật lại Token và Email.\n")
        cfg = action_config(cfg)
        info = verify_token(cfg)

    tool_name = info.get("toolName", "")
    user_email = cfg.get("user_email", "")
    user_info = f"{user_email} — {tool_name}" if tool_name else user_email

    # Silent sync
    print("Đang sync core...")
    sync_core(cfg, silent=True)   # tự restart nếu launcher.py thay đổi

    print("Đang sync scripts...")
    sync_scripts(cfg, silent=True)

    # Auto-start
    if cfg.get("tool_token") and not is_server_running():
        print("Đang start server...")
        start_server()

    updates = 0

    while True:
        clear()
        draw_menu(user_info, updates)
        choice = safe_input("\nChọn: ").strip()

        if choice == "1":
            action_toggle_server()
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
            action_log_profile()
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
