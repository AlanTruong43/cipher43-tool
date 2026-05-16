import requests
from adapters.base import AntidetectAdapter

# GoLogin chạy Orbital agent local ở port 36912
BASE = "http://localhost:36912/browser"


class GoLoginAdapter(AntidetectAdapter):

    def list_profiles(self) -> list[dict]:
        res = requests.get(f"{BASE}/list", timeout=5)
        res.raise_for_status()
        profiles = res.json()
        return [
            {
                "id": str(p.get("id", "")),
                "name": p.get("name", ""),
                "status": "running" if p.get("active") else "stopped",
            }
            for p in profiles
        ]

    def get_debug_address(self, profile_name: str) -> str:
        profile = self._find_profile(profile_name)
        if not profile:
            raise ValueError(f"GoLogin: Profile '{profile_name}' không tìm thấy")

        profile_id = profile["id"]

        res = requests.post(f"{BASE}/{profile_id}/start", timeout=30)
        res.raise_for_status()
        data = res.json()

        # GoLogin trả ws: "ws://127.0.0.1:PORT/..." → parse port
        ws = data.get("wsUrl") or data.get("ws") or ""
        if ws:
            return self._parse_address_from_ws(ws)

        # Fallback: port trực tiếp
        port = data.get("debugPort") or data.get("port")
        if port:
            return f"127.0.0.1:{port}"

        raise RuntimeError(f"GoLogin: Không lấy được debug address cho '{profile_name}'")

    def _find_profile(self, name: str) -> dict | None:
        profiles = self.list_profiles()
        for p in profiles:
            if p["name"].strip().lower() == name.strip().lower():
                return p
        return None

    @staticmethod
    def _parse_address_from_ws(ws_url: str) -> str:
        # "ws://127.0.0.1:9222/devtools/..." → "127.0.0.1:9222"
        try:
            without_scheme = ws_url.replace("ws://", "").replace("wss://", "")
            host_port = without_scheme.split("/")[0]
            return host_port
        except Exception:
            raise RuntimeError(f"Không parse được address từ ws URL: {ws_url}")
