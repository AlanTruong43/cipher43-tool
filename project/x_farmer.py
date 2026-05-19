# -*- coding: utf-8 -*-
import random
import time
import threading
from datetime import datetime, timezone, timedelta
from x_ai import create_ai_provider

# ── CSS Selectors (mirrors X-Only/utils/selectors.js) ─────────────────────────
SEL_TWEET_ARTICLE = 'css:article[data-testid="tweet"]'
SEL_LIKE_BTN      = 'css:button[data-testid="like"]'
SEL_REPLY_BTN     = 'css:button[data-testid="reply"]'
SEL_TEXTAREA      = 'css:div[data-testid="tweetTextarea_0"]'
SEL_SUBMIT_BTN    = 'css:button[data-testid="tweetButton"]'
SEL_DISCARD_BTN   = 'css:button[data-testid="confirmationSheetConfirm"]'
SEL_SEARCH_INPUT  = 'css:input[data-testid="SearchBox_Search_Input"]'
SEL_LATEST_TAB    = 'css:a[href*="f=live"]'


def _random_delay(min_ms, max_ms):
    time.sleep(random.randint(min_ms, max_ms) / 1000.0)


class XFarmer:
    def __init__(self, tab, config, profile_tag="", log_callback=None):
        self.tab = tab
        self.config = config
        self.profile_tag = profile_tag
        self.ai = create_ai_provider(config)
        self._log_callback = log_callback

        farming = config.get("farming", {})
        self.mode               = farming.get("mode", "newsfeed")
        self.hashtags           = farming.get("hashtags", ["#AI"])
        self.loop_count         = farming.get("loop_count", 2)
        self.scroll_duration    = farming.get("scroll_duration_seconds", 15)
        self.like_prob          = farming.get("like_probability", 0.4)
        self.comment_prob       = farming.get("comment_probability", 0.2)
        self.max_tweets         = farming.get("max_tweets_per_loop", 10)
        self.min_action_delay   = farming.get("min_delay_between_actions_ms", 3000)
        self.max_action_delay   = farming.get("max_delay_between_actions_ms", 8000)

        self._processed_ids = set()

    def _log(self, msg):
        formatted = f"[{self.profile_tag}] {msg}"
        print(formatted)
        if self._log_callback:
            self._log_callback(msg)

    def _safe_navigate(self, url: str):
        try:
            self.tab.handle_alert(accept=True)
        except Exception:
            pass
        try:
            self.tab.set.alert.auto_handle(on_off=True, accept=True)
        except Exception:
            pass
        self.tab.get(url)

    # ── Kiểm tra bài viết mới nhất có #cipher43lab không ─────────────────────
    def _check_cipher43lab_post(self):
        """
        Vào trang cá nhân, tìm bài viết mới nhất (không tính bài ghim).
        Trả về True nếu bài đó chứa #cipher43lab VÀ không quá 4 ngày tuổi.
        """
        try:
            self._safe_navigate("https://x.com/home")
            time.sleep(2)
            profile_link = self.tab.ele('css:a[data-testid="AppTabBar_Profile_Link"]', timeout=5)
            if not profile_link:
                self._log("Không tìm thấy link profile, bỏ qua kiểm tra")
                return True
            profile_url = profile_link.attr("href")
            if not profile_url:
                self._log("Không lấy được profile URL, bỏ qua kiểm tra")
                return True

            self._log(f"Kiểm tra profile: {profile_url}")
            # profile_url có thể là path (/user) hoặc full URL
            if profile_url.startswith("http"):
                self._safe_navigate(profile_url)
            else:
                self._safe_navigate(f"https://x.com{profile_url}")
            _random_delay(3000, 4000)

            tweets = self.tab.eles(SEL_TWEET_ARTICLE)
            if not tweets:
                self._log("Không tìm thấy bài viết nào trên profile")
                return False

            for tweet in tweets:
                # Bỏ qua bài ghim
                is_pinned = tweet.run_js(
                    "return !!this.querySelector('[data-testid=\"socialContext\"]')"
                )
                if is_pinned:
                    self._log("Bỏ qua bài ghim")
                    continue

                # Lấy text và datetime của bài mới nhất
                result = tweet.run_js("""
                    var textEl = this.querySelector('div[data-testid="tweetText"]');
                    var timeEl = this.querySelector('time[datetime]');
                    return {
                        text: textEl ? textEl.innerText : '',
                        datetime: timeEl ? timeEl.getAttribute('datetime') : ''
                    };
                """)

                text = (result or {}).get("text", "") if isinstance(result, dict) else ""
                dt_str = (result or {}).get("datetime", "") if isinstance(result, dict) else ""

                # Kiểm tra hashtag
                has_tag = "#cipher43lab" in (text or "").lower()

                # Kiểm tra ngày — không quá 4 ngày
                within_days = True
                if dt_str:
                    try:
                        post_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                        age = datetime.now(timezone.utc) - post_dt
                        within_days = age <= timedelta(days=4)
                        self._log(
                            f"Bài mới nhất: {age.days}d {age.seconds//3600}h tuổi "
                            f"({'✅ trong 4 ngày' if within_days else '❌ quá 4 ngày'})"
                        )
                    except Exception:
                        pass

                self._log(
                    f"Nội dung: \"{(text or '')[:80]}\" "
                    f"→ {'✅' if has_tag else '❌'} #cipher43lab"
                )

                if not within_days:
                    self._log("❌ Bài mới nhất đã quá 4 ngày → dừng farming")
                    return False
                if not has_tag:
                    self._log("❌ Bài mới nhất không có #cipher43lab → dừng farming")
                    return False

                self._log("✅ Điều kiện hợp lệ — tiến hành farming")
                return True

            self._log("Không tìm thấy bài viết không ghim")
            return False

        except Exception as e:
            self._log(f"Lỗi kiểm tra profile: {e} — bỏ qua kiểm tra")
            return True

    # ── Entry point ────────────────────────────────────────────────────────────
    def farm(self):
        total_stats = {"processed": 0, "liked": 0, "commented": 0}

        # Kiểm tra điều kiện #cipher43lab trước khi farming
        if not self._check_cipher43lab_post():
            self._log("⛔ Không đủ điều kiện — dừng farming")
            return total_stats

        for loop in range(self.loop_count):
            self._log(f"Loop {loop + 1}/{self.loop_count} — mode: {self.mode}")
            self._processed_ids.clear()

            if self.mode == "hashtag":
                hashtag = self.hashtags[loop % len(self.hashtags)]
                stats = self.farm_hashtag(hashtag)
            else:
                stats = self.farm_newsfeed()

            total_stats["processed"]  += stats["processed"]
            total_stats["liked"]      += stats["liked"]
            total_stats["commented"]  += stats["commented"]

            if loop < self.loop_count - 1:
                wait = random.randint(60, 120)
                self._log(f"Nghỉ {wait}s trước loop tiếp theo...")
                elapsed = 0
                while elapsed < wait:
                    chunk = min(10, wait - elapsed)
                    time.sleep(chunk)
                    elapsed += chunk
                    if elapsed < wait:
                        self._log(f"  còn {wait - elapsed}s...")

        self._log(
            f"Hoàn thành: {total_stats['processed']} tweets | "
            f"{total_stats['liked']} liked | {total_stats['commented']} commented"
        )
        return total_stats

    # ── Mode 1: Newsfeed ───────────────────────────────────────────────────────
    def farm_newsfeed(self):
        self._log("🌾 NEWSFEED — lướt feed, like & comment")
        self._safe_navigate("https://x.com/home")
        self._scroll_feed(self.scroll_duration)
        return self._process_tweets_on_page()

    # ── Mode 2: Hashtag ────────────────────────────────────────────────────────
    def farm_hashtag(self, hashtag):
        self._log(f"🔍 HASHTAG — tìm kiếm: {hashtag}")
        self._safe_navigate("https://x.com/explore")
        _random_delay(2000, 4000)

        search_input = self.tab.ele(SEL_SEARCH_INPUT, timeout=10)
        if search_input:
            search_input.click()
            time.sleep(0.5)
            search_input.input(hashtag)
            time.sleep(0.8)
            self.tab.actions.key("Enter")
            _random_delay(3000, 5000)
            latest_tab = self.tab.ele(SEL_LATEST_TAB, timeout=5)
            if latest_tab:
                latest_tab.click()
                _random_delay(2000, 3000)
        else:
            encoded = hashtag.replace("#", "%23")
            self._safe_navigate(f"https://x.com/search?q={encoded}&src=typed_query&f=live")
            _random_delay(3000, 5000)

        self._log(f"Warm-up scroll {self.scroll_duration}s...")
        self._scroll_feed(self.scroll_duration)
        return self._process_tweets_on_page()

    # ── Core: xử lý tweets trên page ──────────────────────────────────────────
    def _process_tweets_on_page(self):
        processed = liked = commented = 0
        self.tab.run_js("window.scrollTo(0, 0)")
        time.sleep(1)

        for _ in range(self.max_tweets + 5):
            if processed >= self.max_tweets:
                break

            tweets = self.tab.eles(SEL_TWEET_ARTICLE)
            if not tweets:
                self._log("Không tìm thấy tweet, scroll thêm...")
                self._scroll_page(3)
                _random_delay(2000, 4000)
                continue

            for tweet in tweets:
                if processed >= self.max_tweets:
                    break
                try:
                    # Bỏ qua tweet không visible
                    if not tweet.states.is_in_viewport:
                        continue

                    # Unique ID để tránh xử lý lại
                    tweet_id = tweet.run_js(
                        "return (this.querySelector('a[href*=\"/status/\"]') || {}).getAttribute('href')"
                    )
                    if tweet_id and tweet_id in self._processed_ids:
                        continue
                    if tweet_id:
                        self._processed_ids.add(tweet_id)

                    tweet_data = self._extract_tweet_data(tweet)
                    if not tweet_data:
                        continue

                    processed += 1
                    text_preview = (tweet_data.get("text") or "")[:60]
                    self._log(f"Tweet {processed}: \"{text_preview}...\"")

                    should_like    = random.random() < self.like_prob
                    should_comment = random.random() < self.comment_prob

                    # Pre-fetch AI comment song song với like (threading)
                    comment_result = [None]
                    ai_thread = None
                    if should_comment:
                        def fetch_comment():
                            try:
                                comment_result[0] = self.ai.generate_comment(tweet_data, self.profile_tag)
                            except Exception:
                                comment_result[0] = None
                        ai_thread = threading.Thread(target=fetch_comment, daemon=True)
                        ai_thread.start()

                    if should_like:
                        if self._like_tweet(tweet):
                            liked += 1
                            _random_delay(self.min_action_delay, self.max_action_delay)

                    if ai_thread:
                        ai_thread.join(timeout=35)
                        if comment_result[0]:
                            if self._submit_comment(tweet, comment_result[0]):
                                commented += 1
                                _random_delay(self.min_action_delay, self.max_action_delay)

                except Exception as e:
                    self._log(f"Bỏ qua tweet: {e}")

            self._scroll_page(2)
            _random_delay(1500, 3000)

        self._log(f"Kết quả: {processed} xử lý | {liked} liked | {commented} commented")
        return {"processed": processed, "liked": liked, "commented": commented}

    # ── Extract tweet data ─────────────────────────────────────────────────────
    def _extract_tweet_data(self, tweet_ele):
        try:
            data = tweet_ele.run_js("""
                var textEl = this.querySelector('div[data-testid="tweetText"]');
                var authorEl = this.querySelector('div[data-testid="User-Name"]');
                var imgEl = this.querySelector('div[data-testid="tweetPhoto"] img');
                var videoEl = this.querySelector('div[data-testid="videoPlayer"]');
                var unlikeBtn = this.querySelector('button[data-testid="unlike"]');
                return {
                    text: textEl ? textEl.innerText : '',
                    author_name: authorEl ? authorEl.innerText.split('\\n')[0] : '',
                    has_image: !!imgEl,
                    image_alt: imgEl ? (imgEl.getAttribute('alt') || '') : '',
                    has_video: !!videoEl,
                    already_liked: !!unlikeBtn
                };
            """)
            return data
        except Exception:
            return None

    # ── Like tweet ─────────────────────────────────────────────────────────────
    def _like_tweet(self, tweet_ele):
        try:
            like_btn = tweet_ele.ele(SEL_LIKE_BTN, timeout=0)
            if not like_btn:
                return False
            like_btn.click()
            self._log("❤️  Liked")
            return True
        except Exception as e:
            self._log(f"Like lỗi: {e}")
            return False

    # ── Submit comment ─────────────────────────────────────────────────────────
    def _submit_comment(self, tweet_ele, comment_text):
        try:
            reply_btn = tweet_ele.ele(SEL_REPLY_BTN, timeout=0)
            if not reply_btn:
                self._log("Không tìm thấy nút reply")
                return False

            reply_btn.click()
            _random_delay(1500, 3000)

            textarea = self.tab.ele(SEL_TEXTAREA, timeout=8)
            if not textarea:
                self._log("Không tìm thấy textarea")
                self._dismiss_dialog()
                return False

            textarea.click()
            time.sleep(0.5)
            # Gõ từng ký tự như người thật
            for char in comment_text:
                self.tab.actions.type(char)
                time.sleep(random.uniform(0.03, 0.12))
            _random_delay(1000, 2000)

            submit_btn = self.tab.ele(SEL_SUBMIT_BTN, timeout=5)
            if not submit_btn:
                self._log("Không tìm thấy nút submit")
                self._dismiss_dialog()
                return False

            submit_btn.click()

            # Đợi dialog đóng
            if self._wait_for_dialog_close(6000):
                time.sleep(1)
                self._log(f"💬 Commented: \"{comment_text[:50]}...\"")
                return True

            self._log("Reply timeout, đóng dialog")
            self._dismiss_dialog()
            return False

        except Exception as e:
            self._log(f"Submit comment lỗi: {e}")
            self._dismiss_dialog()
            return False

    # ── Đợi reply dialog đóng ─────────────────────────────────────────────────
    def _wait_for_dialog_close(self, timeout_ms=5000):
        deadline = time.time() + timeout_ms / 1000.0
        while time.time() < deadline:
            textarea = self.tab.ele(SEL_TEXTAREA, timeout=0)
            if not textarea:
                return True
            try:
                if not textarea.states.is_in_viewport:
                    return True
            except Exception:
                return True
            time.sleep(0.5)
        return False

    # ── Dismiss dialog ─────────────────────────────────────────────────────────
    def _dismiss_dialog(self):
        try:
            self.tab.actions.key("Escape")
            time.sleep(1)
            discard_btn = self.tab.ele(SEL_DISCARD_BTN, timeout=2)
            if discard_btn:
                discard_btn.click()
                time.sleep(0.8)
                return
            self.tab.actions.key("Escape")
            time.sleep(0.5)
        except Exception:
            pass

    # ── Scroll feed warm-up ────────────────────────────────────────────────────
    def _scroll_feed(self, duration_seconds):
        end_time = time.time() + duration_seconds
        while time.time() < end_time:
            distance = random.randint(200, 600)
            self.tab.run_js(f"window.scrollBy(0, {distance})")
            if random.random() < 0.3:
                time.sleep(random.uniform(3, 6))
            else:
                time.sleep(random.uniform(0.8, 2))
            if random.random() < 0.1:
                back = random.randint(50, 150)
                self.tab.run_js(f"window.scrollBy(0, -{back})")
                time.sleep(random.uniform(0.5, 1.5))

    def _scroll_page(self, scrolls=2):
        for _ in range(scrolls):
            distance = random.randint(200, 600)
            self.tab.run_js(f"window.scrollBy(0, {distance})")
            time.sleep(random.uniform(0.8, 2.5))
