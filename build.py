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
import sys
import json
import shutil
import hashlib
import py_compile
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

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
    tag = RELEASE_TAG
    title = f"Scripts {manifest['version']}"

    # Check gh CLI available
    if shutil.which("gh") is None:
        print("\nERROR: gh CLI not found. Install: https://cli.github.com/")
        sys.exit(1)

    # Create release (skip if exists)
    print(f"\nCreating GitHub Release {tag}...")
    subprocess.run(
        ["gh", "release", "create", tag,
         "--repo", GITHUB_REPO,
         "--title", title,
         "--notes", f"Scripts bundle {manifest['version']}",
         "--latest"],
        check=False  # ignore if tag already exists
    )

    # Upload manifest
    print("Uploading scripts-manifest.json...")
    subprocess.run(
        ["gh", "release", "upload", tag,
         "--repo", GITHUB_REPO,
         str(MANIFEST_FILE),
         "--clobber"],
        check=True
    )

    # Upload each .pyc
    for script in manifest["scripts"]:
        pyc_path = DIST_PROJECT_DIR / script["file"]
        print(f"Uploading {script['file']}...")
        subprocess.run(
            ["gh", "release", "upload", tag,
             "--repo", GITHUB_REPO,
             str(pyc_path),
             "--clobber"],
            check=True
        )

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
