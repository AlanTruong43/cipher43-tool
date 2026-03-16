# -*- coding: utf-8 -*-
"""
Twitter Automation Project
Automation cho các tác vụ trên Twitter/X
"""
import encoding_fix  # Fix Windows console encoding - must be first import

from DrissionPage import ChromiumPage, ChromiumOptions
import time


def run(profile_data):
    """
    Main function to run Twitter automation

    Args:
        profile_data: Dict containing:
            - profile_id: Profile ID
            - profile_name: Profile name
            - remote_debugging_address: e.g., "127.0.0.1:53378"
            - browser_location: Path to browser executable
            - driver_path: Path to ChromeDriver
    """
    debug_address = profile_data['remote_debugging_address']
    print(f">>> [TWITTER] Connecting to browser at: {debug_address}...")

    page = None

    try:
        # Kết nối vào browser đang mở qua debug port
        co = ChromiumOptions().set_address(debug_address)
        page = ChromiumPage(co)
        print(f">>> [TWITTER] Connected successfully!")

        # Step 0: Chọn tab thực tế (bỏ qua tab extension)
        print(f">>> [TWITTER] Scanning for a valid browser tab...")
        target_tab = None

        for tab in page.get_tabs():
            url = tab.url
            print(f">>> [TWITTER] Tab: {url}")
            if not url.startswith("chrome-extension://") and not url.startswith("chrome://"):
                target_tab = tab
                break

        if target_tab is None:
            print(">>> [TWITTER] No active web tab found. Creating a new one...")
            target_tab = page.new_tab()  # new_tab() trả về tab object trực tiếp
        else:
            print(f">>> [TWITTER] Selected valid tab: {target_tab.url}")

        # Dùng target_tab trực tiếp cho mọi thao tác — KHÔNG dùng page.get() / page.run_js()
        target_url = "https://x.com/home"
        print(f">>> [TWITTER] Navigating to {target_url}...")
        target_tab.get(target_url)
        print(f">>> [TWITTER] Navigation complete! URL: {target_tab.url}")

        # VISUAL FEEDBACK: Scroll down rồi lên
        print(">>> [TWITTER] Performing visual feedback (Scrolling)...")
        target_tab.run_js("window.scrollTo(0, 500);")
        time.sleep(1)
        target_tab.run_js("window.scrollTo(0, 0);")

        # Step 2: Kiểm tra trạng thái login
        print(">>> [TWITTER] Checking for login button (timeout 10s)...")
        login_btn = target_tab.ele('xpath://*[text()="Đăng nhập vào X"]', timeout=10)

        if login_btn:
            print(">>> [TWITTER] RESULT: Not logged in. Highlighting button.")
            target_tab.run_js(
                "arguments[0].style.border='5px solid red';"
                "arguments[0].style.backgroundColor='yellow';",
                login_btn
            )
        else:
            print("[OK] ALREADY LOGGED IN")
            confirm_js = """
            var div = document.createElement('div');
            div.style.position = 'fixed';
            div.style.top = '10px';
            div.style.right = '10px';
            div.style.padding = '10px';
            div.style.background = 'green';
            div.style.color = 'white';
            div.style.zIndex = '9999';
            div.style.fontSize = '20px';
            div.innerHTML = 'BOT CONNECTED SUCCESSFULLY';
            document.body.appendChild(div);
            setTimeout(function() { div.remove(); }, 5000);
            """
            target_tab.run_js(confirm_js)

            if target_tab.ele('xpath://a[@aria-label="Post"]', timeout=5):
                print("[OK] Timeline loaded")

    except Exception as e:
        print(f"[ERROR] Twitter Automation: {e}")
        raise
    finally:
        print("[INFO] Tasks finished. Browser left open.")


# Example usage if run directly
if __name__ == "__main__":
    test_profile_data = {
        "profile_id": "test_id",
        "profile_name": "Test Profile",
        "remote_debugging_address": "127.0.0.1:53378",
        "browser_location": "",
        "driver_path": ""
    }
    print("This is a test run. Use the dashboard to run this project properly.")
    # run(test_profile_data)
