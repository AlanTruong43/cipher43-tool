#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cipher 43 Tool - Auto-update Launcher
User chỉ cần chạy: python launcher.py
Launcher tự động:
  1. Check git có update không
  2. Pull code mới từ GitHub
  3. Install dependencies
  4. Run api_server.py
"""

import subprocess
import sys
import os
from pathlib import Path

TOOL_DIR = Path(__file__).parent
REPO_URL = "https://github.com/yourusername/cipher43-tool.git"  # Change this

def run_command(cmd, description=""):
    """Run shell command và print output"""
    if description:
        print(f"\n{'='*60}")
        print(f"► {description}")
        print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
        if result.returncode != 0:
            print(f"⚠ Command failed: {cmd}")
            return False
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def init_repo():
    """Init git repo nếu chưa có"""
    if not (TOOL_DIR / ".git").exists():
        print(f"► Initializing git repository at {TOOL_DIR}...")
        run_command(f"cd {TOOL_DIR} && git init && git remote add origin {REPO_URL}", "Git Init")
        run_command(f"cd {TOOL_DIR} && git pull origin main", "Pulling initial code")


def update_code():
    """Pull code mới nhất từ GitHub"""
    run_command(f"cd {TOOL_DIR} && git fetch origin", "Fetching from GitHub")
    run_command(f"cd {TOOL_DIR} && git reset --hard origin/main", "Updating to latest code")


def install_dependencies():
    """Install Python dependencies"""
    requirements_file = TOOL_DIR / "requirements.txt"
    if requirements_file.exists():
        run_command(f"pip3 install -r {requirements_file}", "Installing dependencies")
    else:
        print("⚠ requirements.txt not found, skipping dependency installation")


def check_config():
    """Check if config.json exists"""
    config_file = TOOL_DIR / "config.json"
    if not config_file.exists():
        print(f"\n⚠ WARNING: config.json not found!")
        print(f"   Please create {config_file} with your configuration")
        print(f"   Example:")
        print(f"   {{\n      \"browser\": \"genlogin\",\n      \"api_key\": \"your_api_key\",\n      \"be_url\": \"https://cipher43lab.com/api\"\n   }}")
        return False
    return True


def run_server():
    """Run api_server.py"""
    server_file = TOOL_DIR / "api_server.py"
    if not server_file.exists():
        print(f"✗ api_server.py not found at {server_file}")
        return False

    print(f"\n{'='*60}")
    print(f"► Starting Cipher 43 Tool Server")
    print(f"{'='*60}")
    print(f"Server running at http://127.0.0.1:8000")
    print(f"Press Ctrl+C to stop\n")

    try:
        subprocess.run(f"cd {TOOL_DIR} && python3 api_server.py", shell=True)
        return True
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        return True
    except Exception as e:
        print(f"✗ Error running server: {e}")
        return False


def main():
    """Main launcher flow"""
    print(f"\n{'='*60}")
    print(f"⚡ Cipher 43 Tool - Launcher v1.0")
    print(f"{'='*60}")
    print(f"Working directory: {TOOL_DIR}\n")

    # Step 1: Initialize repo if needed
    print("Step 1/4: Checking git repository...")
    init_repo()

    # Step 2: Update code
    print("\nStep 2/4: Updating code from GitHub...")
    update_code()

    # Step 3: Install dependencies
    print("\nStep 3/4: Installing dependencies...")
    install_dependencies()

    # Step 4: Check config
    print("\nStep 4/4: Checking configuration...")
    if not check_config():
        print("\n✗ Please create config.json and try again")
        sys.exit(1)

    # Run server
    print("\n✓ All checks passed!\n")
    run_server()


if __name__ == "__main__":
    main()
