# -*- coding: utf-8 -*-
import json
import random
import urllib.request
import urllib.error


class AIProvider:
    def __init__(self, config=None):
        cfg = config or {}
        self.api_key = cfg.get("api_key", "")
        self.model = cfg.get("model", "")
        self.system_prompt = cfg.get("comment_prompt", "Write a short, natural comment for this tweet.")
        self.max_tokens = cfg.get("max_tokens", 100)

    def generate_comment(self, tweet_data, profile_tag=""):
        raise NotImplementedError

    def _build_tweet_description(self, tweet_data):
        parts = []
        if tweet_data.get("text"):
            parts.append(f'Tweet content: "{tweet_data["text"]}"')
        if tweet_data.get("has_image"):
            alt = tweet_data.get("image_alt", "")
            parts.append(f"[Has image{': ' + alt if alt else ''}]")
        if tweet_data.get("has_video"):
            parts.append("[Has video]")
        if tweet_data.get("author_name"):
            parts.append(f'Author: {tweet_data["author_name"]}')
        return "\n".join(parts) if parts else "A short tweet on the timeline."

    def _fallback_comment(self):
        fallbacks = ["🔥", "💯", "Nice!", "Interesting", "👏", "Great post!", "Love this", "💪", "Facts", "🙌"]
        return random.choice(fallbacks)


class DemoClient(AIProvider):
    def __init__(self, config=None):
        super().__init__(config)
        self.model = self.model or "gpt-4.1-nano"

    def generate_comment(self, tweet_data, profile_tag=""):
        description = self._build_tweet_description(tweet_data)
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": description},
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.9,
        }
        try:
            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(
                "https://ezaiapi.com/v1/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "cipher43-tool/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            comment = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not comment:
                return self._fallback_comment()
            return comment.strip('"\'')
        except Exception as e:
            print(f"[{profile_tag}] DEMO error: {e}")
            return self._fallback_comment()


class GeminiClient(AIProvider):
    def __init__(self, config=None):
        super().__init__(config)
        self.model = self.model or "gemini-2.0-flash"

    def generate_comment(self, tweet_data, profile_tag=""):
        description = self._build_tweet_description(tweet_data)
        body = {
            "contents": [{"parts": [{"text": f"{self.system_prompt}\n\n{description}"}]}],
            "generationConfig": {
                "maxOutputTokens": self.max_tokens,
                "temperature": 0.9,
                "topP": 0.95,
            },
        }
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            comment = (
                result.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                .strip()
            )
            if not comment:
                return self._fallback_comment()
            return comment.strip('"\'')
        except Exception as e:
            print(f"[{profile_tag}] Gemini error: {e}")
            return self._fallback_comment()


def create_ai_provider(config):
    ap = config.get("ai_provider", {})
    provider_type = ap.get("type", "gemini").lower()
    if provider_type == "demo":
        return DemoClient(ap)
    return GeminiClient(ap)
