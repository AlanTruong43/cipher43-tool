# -*- coding: utf-8 -*-
import encoding_fix  # Fix Windows console encoding - must be first import

import json
import time
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions
from x_farmer import XFarmer


def _load_config():
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def run(profile_data):
    debug_address = profile_data["remote_debugging_address"]
    profile_name = profile_data.get("profile_name", "unknown")
    _log = profile_data.get("_log_callback") or (lambda msg: print(f"[{profile_name}] {msg}"))

    _log(f"Connecting to browser at: {debug_address}...")

    stats = {}
    target_tab = None
    try:
        co = ChromiumOptions().set_address(debug_address)
        page = ChromiumPage(co)
        _log("Connected!")

        for tab in page.get_tabs():
            try:
                tab.handle_alert(accept=True)
            except Exception:
                pass
            try:
                url = tab.url
            except Exception:
                continue
            if not url.startswith("chrome-extension://") and not url.startswith("chrome://"):
                target_tab = tab
                break
        if target_tab is None:
            target_tab = page.new_tab()
            _log("No active tab, opened new tab")
        else:
            _log(f"Using tab: {target_tab.url}")

        try:
            target_tab.set.alert.auto_handle(on_off=True, accept=True)
        except Exception:
            pass
        try:
            target_tab.handle_alert(accept=True)
        except Exception:
            pass

        try:
            target_tab.handle_alert(accept=True)
        except Exception:
            pass
        target_tab.get("https://x.com/home")
        time.sleep(3)
        login_btn = target_tab.ele('xpath://*[text()="Đăng nhập vào X"]', timeout=5)
        if login_btn:
            _log("NOT LOGGED IN — bỏ qua farming")
        else:
            _log("Logged in — bắt đầu farming...")
            config = _load_config()
            farmer = XFarmer(target_tab, config, profile_tag=profile_name, log_callback=_log)
            stats = farmer.farm()
            _log(f"Done — {stats['processed']} tweets, {stats['liked']} liked, {stats['commented']} commented")

        return stats

    except Exception as e:
        _log(f"ERROR: {e}")
        raise
    finally:
        if target_tab is not None:
            _log("Truy cập anotepad để xác nhận...")
            _ANOTEPAD = "https://anotepad.com/notes/d65ngf8f"
            navigated = False
            for _ in range(3):
                try:
                    target_tab.handle_alert(accept=True)
                except Exception:
                    pass
                try:
                    target_tab.get(_ANOTEPAD)
                    navigated = True
                    break
                except Exception:
                    try:
                        target_tab.run_js(f"window.location.href = '{_ANOTEPAD}'")
                        time.sleep(3)
                        navigated = True
                        break
                    except Exception:
                        time.sleep(1)
            if navigated:
                try:
                    confirm = target_tab.ele('xpath://*[text()="Cipher 43 Lab"]', timeout=15)
                    if confirm:
                        _log("✅ Xác nhận thành công — Cipher 43 Lab")
                    else:
                        _log("⚠️ Không tìm thấy xác nhận trên anotepad")
                except Exception as e:
                    _log(f"Anotepad check lỗi: {e}")
            else:
                _log("❌ Không thể điều hướng đến anotepad")
        _log("Browser left open.")


if __name__ == "__main__":
    test_profile = {
        "profile_name": "Test",
        "remote_debugging_address": "127.0.0.1:53378",
    }
    run(test_profile)
