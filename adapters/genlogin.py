import requests
from adapters.base import AntidetectAdapter

BASE = "http://localhost:55550"


class GenloginAdapter(AntidetectAdapter):
    """Adapter cho Genlogin antidetect browser"""

    def __init__(self, username: str = "", password: str = ""):
        self.username = username or ""
        self.password = password or ""
        self.access_token = None

    def _login(self) -> str:
        """Lấy access token từ Genlogin API"""
        if self.access_token:
            return self.access_token

        if not self.username or not self.password:
            raise ValueError("Genlogin: Cần cung cấp username và password")

        res = requests.post(
            f"{BASE}/backend/auth/login",
            json={"username": self.username, "password": self.password},
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()

        token = data.get("access_token")
        if not token:
            raise RuntimeError("Genlogin: Không lấy được access token")

        self.access_token = token
        return token

    def _get_headers(self) -> dict:
        """Trả về headers với token"""
        token = self._login()
        return {"Authorization": f"Bearer {token}"}

    def list_profiles(self) -> list[dict]:
        """Liệt kê tất cả profiles"""
        res = requests.get(
            f"{BASE}/backend/profiles",
            params={"offset": 0, "limit": 1000, "sort_by": "id", "order": "desc"},
            headers=self._get_headers(),
            timeout=10,
        )
        res.raise_for_status()
        data = res.json().get("data", [])

        return [
            {
                "id": str(p.get("id", "")),
                "name": p.get("name", ""),
                "status": "running" if p.get("is_open") else "stopped",
            }
            for p in data
        ]

    def get_debug_address(self, profile_name: str) -> str:
        """Lấy debug port của profile"""
        profile = self._find_profile(profile_name)
        if not profile:
            raise ValueError(f"Genlogin: Profile '{profile_name}' không tìm thấy")

        profile_id = profile["id"]

        # Start profile
        res = requests.post(
            f"{BASE}/backend/profiles/{profile_id}/start",
            headers=self._get_headers(),
            timeout=30,
        )
        res.raise_for_status()
        data = res.json().get("data", {})

        # Genlogin trả về ws URL hoặc debug port trực tiếp
        ws_url = data.get("ws") or data.get("wsUrl") or ""
        if ws_url:
            return self._parse_address_from_ws(ws_url)

        # Hoặc port trực tiếp
        port = data.get("debug_port") or data.get("debugPort") or data.get("port")
        if port:
            return f"127.0.0.1:{port}"

        raise RuntimeError(f"Genlogin: Không lấy được debug address cho '{profile_name}'")

    def _find_profile(self, name: str) -> dict | None:
        """Tìm profile theo tên (case-insensitive)"""
        profiles = self.list_profiles()
        name_lower = name.strip().lower()
        for p in profiles:
            if p["name"].strip().lower() == name_lower:
                return p
        return None

    @staticmethod
    def _parse_address_from_ws(ws_url: str) -> str:
        """Parse debug address từ WebSocket URL"""
        # Ví dụ: "ws://127.0.0.1:9222/devtools/..." → "127.0.0.1:9222"
        try:
            without_scheme = ws_url.replace("ws://", "").replace("wss://", "")
            host_port = without_scheme.split("/")[0]
            return host_port
        except Exception:
            raise RuntimeError(f"Genlogin: Không parse được address từ ws URL: {ws_url}")
