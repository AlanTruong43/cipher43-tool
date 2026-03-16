# -*- coding: utf-8 -*-
import encoding_fix  # BẮT BUỘC: Fix lỗi font chữ trên Windows

from DrissionPage import ChromiumPage, ChromiumOptions
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OKX_Auto")


def run(profile_data):
    """
    Script automation cho ví OKX tối ưu tốc độ và độ ổn định.
    """
    PROJECT_NAME = "OKX (v2.1)"
    mnemonic_phrase = profile_data.get('mnemonic', "buddy off slide lounge hurry ankle base spoon video coconut surge hover")
    password = profile_data.get('password', "AlanTruong@113")
    debug_address = profile_data.get('remote_debugging_address')

    logger.info(f">>> [{PROJECT_NAME}] Bắt đầu: {debug_address}...")

    page = None

    def connect_with_retry(address, retries=5):
        """Kết nối với cơ chế thử lại nếu port chưa sẵn sàng"""
        for i in range(retries):
            try:
                co = ChromiumOptions().set_address(address)
                p = ChromiumPage(co)
                _ = p.url  # test kết nối
                return p
            except Exception as e:
                logger.warning(f"Thử kết nối lần {i+1} thất bại: {str(e)[:100]}")
                time.sleep(2)
        raise Exception(f"Không thể kết nối tới trình duyệt tại {address} sau {retries} lần thử.")

    def find_okx_tab():
        """Tìm và chuyển sang tab extension OKX"""
        for tab in page.get_tabs():
            url = tab.url
            if "mcohilncbfahbmgdjkbpemcciiolgcge" in url:
                if any(x in url for x in ["offscreen.html", "background.html", "generated_background"]):
                    continue
                page.activate_tab(tab)
                return True
        return False

    def wait_for_element(locators, timeout=15, name="Element"):
        """Chờ element với danh sách locator dự phòng, trả về element đầu tiên tìm thấy"""
        if isinstance(locators, str):
            locators = [locators]

        start = time.time()
        while time.time() - start < timeout:
            for loc in locators:
                el = page.ele(loc, timeout=0)
                if el:
                    return el
            time.sleep(0.5)
        raise TimeoutError(f"Không tìm thấy {name} sau {timeout}s")

    def inject_mnemonic_js(phrase):
        """Dán mnemonic cực nhanh và trigger sự kiện React"""
        js_code = """
        const phrase = arguments[0];
        const inputs = document.querySelectorAll('input') || [];
        const input = Array.from(inputs).find(i => i.placeholder?.includes('word') || i.className?.includes('mnemonic') || true);

        if (input) {
            input.focus();
            const dataTransfer = new DataTransfer();
            dataTransfer.setData('text/plain', phrase);
            const event = new ClipboardEvent('paste', {
                clipboardData: dataTransfer,
                bubbles: true,
                cancelable: true
            });
            input.dispatchEvent(event);

            setTimeout(() => {
                if (input.value === '') {
                   input.value = phrase.split(' ')[0];
                   input.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }, 100);
            return true;
        }
        return false;
        """
        try:
            return page.run_js(js_code, phrase)
        except Exception as e:
            logger.error(f"Lỗi JS Injection: {e}")
            return False

    try:
        page = connect_with_retry(debug_address)

        # Bước 1: Điều hướng tới OKX
        if not find_okx_tab():
            target_url = "chrome-extension://mcohilncbfahbmgdjkbpemcciiolgcge/popup.html#/initialize"
            page.run_js(f"window.open('{target_url}', '_blank');")
            time.sleep(1)
            if not find_okx_tab():
                raise Exception("Không tìm thấy giao diện OKX")

        # Bước 2: Bấm Import
        try:
            import_btn = wait_for_element([
                'xpath://*[@data-testid="onboard-page-import-wallet-button"]',
                'xpath://*[text()="Import wallet" or text()="Nhập ví"]',
                'xpath://button[contains(., "Import")]'
            ], timeout=7, name="Nút Import")
            page.run_js("arguments[0].click();", import_btn)
        except Exception:
            logger.info("Có thể đã qua bước Import, tiếp tục...")

        # Bước 3: Chọn Seed Phrase
        try:
            seed_btn = wait_for_element([
                'xpath://*[@data-testid="onboard-page-import-seed-phrase-or-private-key"]',
                'xpath://*[contains(text(), "Seed phrase") or contains(text(), "Cụm từ")]'
            ], timeout=7, name="Nút Seed Phrase")
            page.run_js("arguments[0].click();", seed_btn)
        except Exception:
            logger.info("Có thể đã ở trang nhập Key, tiếp tục...")

        # Bước 4: Nhập Key (JS Injection)
        logger.info(f"[{PROJECT_NAME}] Đang nhập mnemonic...")
        time.sleep(1)
        wait_for_element('xpath://input', timeout=10, name="Các ô nhập Key")

        if inject_mnemonic_js(mnemonic_phrase):
            logger.info("Đã tiêm JS nhập Key thành công.")
        else:
            raise Exception("Không thể thực hiện JS Injection")

        # Bước 5: Xác nhận
        confirm_btn = wait_for_element([
            'xpath://*[@data-testid="import-seed-phrase-or-private-key-page-confirm-button"]',
            'xpath://button[@type="submit"]',
            'xpath://button[contains(., "Confirm") or contains(., "Xác nhận")]'
        ], name="Nút Xác nhận Key")
        page.run_js("arguments[0].click();", confirm_btn)

        # Bước 6: Password
        try:
            pass_type = wait_for_element(
                'xpath://*[contains(@class, "item") and contains(., "Password")]',
                timeout=5, name="Chọn Password"
            )
            page.run_js("arguments[0].click();", pass_type)
            next_btn = wait_for_element('xpath://button[contains(., "Next") or contains(., "Tiếp tục")]')
            page.run_js("arguments[0].click();", next_btn)
        except Exception:
            pass

        # Nhập password vào từng ô
        pass_inputs = wait_for_element('xpath://input[@type="password"]', timeout=10, name="Ô nhập mật khẩu")
        all_pass_inputs = page.eles('xpath://input[@type="password"]')
        for inp in all_pass_inputs:
            inp.input(password, clear=True)

        # Click Final
        final_btn = wait_for_element(
            'xpath://button[contains(@class, "btn-fill-highlight") or contains(., "Confirm")]',
            name="Xác nhận cuối"
        )
        page.run_js("arguments[0].click();", final_btn)

        # Bước 7: Bắt đầu
        start_btn = wait_for_element(
            'xpath://*[contains(text(), "Bắt đầu") or contains(text(), "Start")]',
            timeout=10, name="Bắt đầu hành trình"
        )
        page.run_js("arguments[0].click();", start_btn)

        logger.info(f">>> [SUCCESS] Hoàn tất cho profile: {profile_data.get('profile_id')}")

    except Exception as e:
        logger.error(f">>> [ERROR] Thất bại: {str(e)}")
        raise
    finally:
        logger.info(">>> [INFO] Tác vụ kết thúc. Trình duyệt vẫn đang mở.")


if __name__ == "__main__":
    run({"remote_debugging_address": "127.0.0.1:9222", "mnemonic": "test test test", "profile_id": "test"})
