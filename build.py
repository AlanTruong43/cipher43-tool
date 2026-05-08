"""
build.py — Compile project/ scripts thành .pyc và tạo manifest cho GitHub Releases.

Chạy trên Mac/Linux trước khi release:
    python3 build.py

Output trong dist/:
    dist/scripts-manifest.json
    dist/project/twitter.cpython-311.pyc
    dist/project/gmail.cpython-311.pyc
    ...

Upload lên GitHub Releases:
    python3 build.py --upload
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


def md5(path: Path) -> str:
    h = hashlib.md5()
    h.update(path.read_bytes())
    return h.hexdigest()


def get_python_tag() -> str:
    v = sys.version_info
    return f"cpython-{v.major}{v.minor}"


def compile_scripts():
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
            })
            print(f"  OK  {src.name} → {pyc_name} ({size:,} bytes)")
        except py_compile.PyCompileError as e:
            print(f"  ERR {src.name}: {e}")
            sys.exit(1)

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
                return json.loads(r.read().decode()), r.status
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

    def upload_asset(path: Path, name: str):
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

    print(f"\nDone! https://github.com/{GITHUB_REPO}/releases/tag/{tag}")
    print(f"\nDone! https://github.com/{GITHUB_REPO}/releases/tag/{tag}")


def main():
    parser = argparse.ArgumentParser(description="Build cipher43-tool scripts release")
    parser.add_argument("--upload", action="store_true", help="Upload to GitHub Releases after build")
    args = parser.parse_args()

    print("=== cipher43-tool build ===\n")
    print("Compiling scripts...")
    scripts = compile_scripts()

    if not scripts:
        print("No scripts found in project/")
        sys.exit(1)

    manifest = build_manifest(scripts)

    if args.upload:
        upload_release(manifest)
    else:
        print("\nRun with --upload to publish to GitHub Releases.")


if __name__ == "__main__":
    main()
