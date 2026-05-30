"""
build.py — Compile project/ scripts và tạo manifest cho GitHub Releases.

Chạy trên Mac/Linux trước khi release:
    python3 build.py              # compile .pyc (default)
    python3 build.py --pyarmor    # obfuscate với PyArmor (bảo vệ source)

Upload lên GitHub Releases:
    python3 build.py --upload
    python3 build.py --pyarmor --upload
"""
import os
import ssl
import sys
import json
import shutil
import hashlib
import py_compile
import argparse
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Fix SSL cert issue on macOS (build tool only — not used in launcher)
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

PROJECT_DIR = Path(__file__).parent / "project"
DIST_DIR = Path(__file__).parent / "dist"
DIST_PROJECT_DIR = DIST_DIR / "project"
MANIFEST_FILE = DIST_DIR / "scripts-manifest.json"

EXCLUDE = {"encoding_fix", "selenium_best_practices", "__init__"}

GITHUB_REPO = "AlanTruong43/cipher43-tool"
RELEASE_TAG = f"scripts-{datetime.now().strftime('%Y%m%d')}"

BASE_DIR = Path(__file__).parent
CORE_FILES = [
    "api_server.py",
    "launcher.py",
    "adapters/__init__.py",
    "adapters/base.py",
    "adapters/genlogin.py",
    "adapters/gologin.py",
    "adapters/gpm.py",
    "adapters/gpmglobal.py",
]


def md5(path: Path) -> str:
    h = hashlib.md5()
    h.update(path.read_bytes())
    return h.hexdigest()


def get_python_tag() -> str:
    v = sys.version_info
    return f"cpython-{v.major}{v.minor}"


def compile_scripts():
    """Compile .py → .pyc (standard bytecode)."""
    if DIST_PROJECT_DIR.exists():
        shutil.rmtree(DIST_PROJECT_DIR)
    DIST_PROJECT_DIR.mkdir(parents=True)

    py_tag = get_python_tag()
    scripts = []

    for src in sorted(PROJECT_DIR.glob("*.py")):
        name = src.stem
        if name in EXCLUDE:
            continue

        pyc_name = f"{name}.{py_tag}.pyc"
        dst = DIST_PROJECT_DIR / pyc_name

        try:
            py_compile.compile(str(src), cfile=str(dst), doraise=True)
            size = dst.stat().st_size
            scripts.append({
                "name": name,
                "file": pyc_name,
                "md5": md5(dst),
                "size": size,
                "type": "pyc",
            })
            print(f"  OK  {src.name} → {pyc_name} ({size:,} bytes)")
        except py_compile.PyCompileError as e:
            print(f"  ERR {src.name}: {e}")
            sys.exit(1)

    return scripts


def obfuscate_scripts_pyarmor():
    """Obfuscate .py → PyArmor protected files (không đọc được source)."""
    try:
        import pyarmor  # noqa: F401
    except ImportError:
        print("ERROR: PyArmor chưa được cài. Chạy: pip install pyarmor")
        sys.exit(1)

    if DIST_PROJECT_DIR.exists():
        shutil.rmtree(DIST_PROJECT_DIR)
    DIST_PROJECT_DIR.mkdir(parents=True)

    py_tag = get_python_tag()
    scripts = []
    src_files = [s for s in sorted(PROJECT_DIR.glob("*.py")) if s.stem not in EXCLUDE]

    if not src_files:
        return scripts

    # Obfuscate tất cả scripts trong 1 lần gọi pyarmor
    # Output: dist/project/{name}.py (obfuscated) + pyarmor_runtime_*/
    result = subprocess.run(
        [sys.executable, "-m", "pyarmor.cli", "gen",
         "--output", str(DIST_PROJECT_DIR),
         *[str(f) for f in src_files]],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"PyArmor error:\n{result.stderr}")
        sys.exit(1)

    # Collect obfuscated .py files
    for src in src_files:
        name = src.stem
        obf_file = DIST_PROJECT_DIR / f"{name}.py"
        if not obf_file.exists():
            print(f"  WARN  {name}.py không tìm thấy sau obfuscation")
            continue
        # Rename để giữ naming convention tương thích với launcher sync
        dst_name = f"{name}.{py_tag}.pyarmor.py"
        dst = DIST_PROJECT_DIR / dst_name
        obf_file.rename(dst)
        size = dst.stat().st_size
        scripts.append({
            "name": name,
            "file": dst_name,
            "md5": md5(dst),
            "size": size,
            "type": "pyarmor",
        })
        print(f"  OK  {src.name} → {dst_name} ({size:,} bytes)")

    # Đóng gói pyarmor_runtime thành zip để distribute
    runtime_dirs = list(DIST_PROJECT_DIR.glob("pyarmor_runtime_*"))
    if runtime_dirs:
        runtime_dir = runtime_dirs[0]
        runtime_zip = DIST_DIR / "pyarmor_runtime.zip"
        shutil.make_archive(str(DIST_DIR / "pyarmor_runtime"), "zip", str(DIST_PROJECT_DIR), runtime_dir.name)
        runtime_size = runtime_zip.stat().st_size
        scripts.append({
            "name": "__runtime__",
            "file": "pyarmor_runtime.zip",
            "md5": md5(runtime_zip),
            "size": runtime_size,
            "type": "pyarmor_runtime",
        })
        print(f"  OK  pyarmor_runtime → pyarmor_runtime.zip ({runtime_size:,} bytes)")
        # Move zip vào DIST_PROJECT_DIR để upload cùng chỗ
        shutil.move(str(runtime_zip), str(DIST_PROJECT_DIR / "pyarmor_runtime.zip"))
        scripts[-1]["file"] = "pyarmor_runtime.zip"

    return scripts


def build_manifest(scripts: list) -> dict:
    bundle_hash = hashlib.md5(
        "".join(s["md5"] for s in scripts).encode()
    ).hexdigest()

    manifest = {
        "version": datetime.now().strftime("%Y%m%d-%H%M"),
        "bundleHash": bundle_hash,
        "scripts": scripts,
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\nManifest: {MANIFEST_FILE}")
    print(f"  version={manifest['version']}  scripts={len(scripts)}  bundleHash={bundle_hash[:8]}...")
    return manifest


def build_core_manifest() -> tuple:
    """Copy core files vào dist/core/ và tạo core-manifest.json."""
    core_dist = DIST_DIR / "core"
    if core_dist.exists():
        shutil.rmtree(core_dist)
    core_dist.mkdir(parents=True)

    files = []
    for rel in CORE_FILES:
        src = BASE_DIR / rel
        if not src.exists():
            print(f"  SKIP  {rel} (không tìm thấy)")
            continue
        # GitHub assets không hỗ trợ slash → dùng __ làm separator
        flat_name = rel.replace("/", "__")
        dst = core_dist / flat_name
        shutil.copy2(src, dst)
        files.append({
            "name": rel,          # đường dẫn local để đặt file
            "file": flat_name,    # tên asset trên GitHub Releases
            "md5": md5(dst),
            "size": dst.stat().st_size,
        })
        print(f"  OK  {rel} → {flat_name}")

    core_manifest = {
        "version": datetime.now().strftime("%Y%m%d-%H%M"),
        "files": files,
    }
    core_manifest_path = DIST_DIR / "core-manifest.json"
    core_manifest_path.write_text(json.dumps(core_manifest, indent=2, ensure_ascii=False))
    print(f"\nCore manifest: {core_manifest_path}  files={len(files)}")
    return core_manifest, core_dist


def upload_release(manifest: dict):
    import urllib.request
    import urllib.error

    tag = RELEASE_TAG
    title = f"Scripts {manifest['version']}"

    # Get token from env or git credential
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        try:
            result = subprocess.run(
                ["git", "credential", "fill"],
                input=b"protocol=https\nhost=github.com\n",
                capture_output=True,
            )
            for line in result.stdout.decode().splitlines():
                if line.startswith("password="):
                    token = line.split("=", 1)[1].strip()
                    break
        except Exception:
            pass

    if not token:
        print("\nERROR: Không tìm được GitHub token.")
        print("Set GH_TOKEN env var hoặc đăng nhập git credential.")
        sys.exit(1)

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "cipher43-build",
        "Content-Type": "application/json",
    }

    def gh_api(method: str, path: str, body=None, binary_data=None, content_type="application/json"):
        url = f"https://api.github.com{path}" if not path.startswith("https://") else path
        data = json.dumps(body).encode() if body else binary_data
        h = dict(headers)
        if binary_data:
            h["Content-Type"] = content_type
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, context=_ssl_ctx) as r:
                body = r.read().decode()
                return (json.loads(body) if body.strip() else {}), r.status
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            return json.loads(body) if body else {}, e.code

    # Create release
    print(f"\nCreating GitHub Release {tag}...")
    resp, status = gh_api("POST", f"/repos/{GITHUB_REPO}/releases", {
        "tag_name": tag,
        "name": title,
        "body": f"Scripts bundle {manifest['version']}",
        "make_latest": "true",
    })

    if status == 422 and "already_exists" in str(resp):
        # Release exists — get upload URL
        print("Release đã tồn tại, lấy upload URL...")
        resp, _ = gh_api("GET", f"/repos/{GITHUB_REPO}/releases/tags/{tag}")

    upload_url_template = resp.get("upload_url", "")
    if not upload_url_template:
        print(f"ERROR: Không lấy được upload_url. Response: {resp}")
        sys.exit(1)

    # upload_url format: https://uploads.github.com/repos/.../assets{?name,label}
    upload_base = upload_url_template.split("{")[0]

    # Lấy danh sách assets hiện có để xóa trước khi upload
    release_id = resp.get("id", "")
    existing_assets = {}
    if release_id:
        assets_resp, _ = gh_api("GET", f"/repos/{GITHUB_REPO}/releases/{release_id}/assets")
        if isinstance(assets_resp, list):
            for a in assets_resp:
                existing_assets[a["name"]] = a["id"]

    def delete_existing(name: str):
        asset_id = existing_assets.get(name)
        if asset_id:
            gh_api("DELETE", f"/repos/{GITHUB_REPO}/releases/assets/{asset_id}")

    def upload_asset(path: Path, name: str):
        delete_existing(name)
        print(f"Uploading {name}...", end=" ", flush=True)
        data = path.read_bytes()
        url = f"{upload_base}?name={name}"
        resp, status = gh_api("POST", url, binary_data=data, content_type="application/octet-stream")
        if status in (200, 201):
            print("OK")
        else:
            print(f"FAILED (HTTP {status}): {resp.get('errors', resp.get('message', ''))}")

    upload_asset(MANIFEST_FILE, "scripts-manifest.json")
    for script in manifest["scripts"]:
        upload_asset(DIST_PROJECT_DIR / script["file"], script["file"])

    # Upload core manifest + core files
    core_manifest_path = DIST_DIR / "core-manifest.json"
    if core_manifest_path.exists():
        upload_asset(core_manifest_path, "core-manifest.json")
        core_dist = DIST_DIR / "core"
        for f in json.loads(core_manifest_path.read_text())["files"]:
            p = core_dist / f["file"]
            if p.exists():
                upload_asset(p, f["file"])

    print(f"\nDone! https://github.com/{GITHUB_REPO}/releases/tag/{tag}")


def main():
    parser = argparse.ArgumentParser(description="Build cipher43-tool scripts release")
    parser.add_argument("--upload", action="store_true", help="Upload to GitHub Releases after build")
    parser.add_argument("--pyarmor", action="store_true", help="Obfuscate with PyArmor instead of .pyc")
    args = parser.parse_args()

    print("=== cipher43-tool build ===\n")
    if args.pyarmor:
        print("Obfuscating scripts with PyArmor...")
        scripts = obfuscate_scripts_pyarmor()
    else:
        print("Compiling scripts to .pyc...")
        scripts = compile_scripts()

    if not scripts:
        print("No scripts found in project/")
        sys.exit(1)

    manifest = build_manifest(scripts)

    print("\nBuilding core manifest...")
    build_core_manifest()

    if args.upload:
        upload_release(manifest)
    else:
        print("\nRun with --upload to publish to GitHub Releases.")


if __name__ == "__main__":
    main()
