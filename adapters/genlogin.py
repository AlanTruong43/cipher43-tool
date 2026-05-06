import requests
from adapters.base import AntidetectAdapter

BASE = "http://127.0.0.1:55550"


class GenloginAdapter(AntidetectAdapter):
    def __init__(self, username: str = None, password: str = None):
        self.username = username or ""
        self.password = password or ""
        self.token = None
        if self.username and self.password:
            self._authenticate()

    def _authenticate(self):
        """Đăng nhập genlogin để lấy access token"""
        if not self.username or not self.password:
            raise ValueError("Genlogin username + password không được cấu hình")

        res = requests.post(
            f"{BASE}/backend/auth/login",
            json={"username": self.username, "password": self.password},
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()
        self.token = data.get("access_token") or data.get("data", {}).get("access_token")
        if not self.token:
            raise RuntimeError("Không lấy được access_token từ Genlogin")

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def list_profiles(self) -> list[dict]:
        res = requests.get(
            f"{BASE}/backend/profiles",
            params={"offset": 0, "limit": 100, "sort_by": "id", "order": "desc"},
            headers=self._headers(),
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()
        profiles = data.get("data", {}).get("items") or data.get("data", {}).get("profiles") or data.get("data", [])
        return [
            {
                "id": str(p.get("id", "")),
                "name": p.get("profile_data", {}).get("name") or p.get("name", ""),
                "status": "running" if p.get("status") == 2 or p.get("active") or p.get("isRunning") else "stopped",
            }
            for p in profiles
        ]

    def get_debug_address(self, profile_name: str) -> str:
        profile = self._find_profile(profile_name)
        if not profile:
            raise ValueError(f"Genlogin: Profile '{profile_name}' không tìm thấy")

        profile_id = profile["id"]

        # Start profile
        res = requests.put(
            f"{BASE}/backend/profiles/{profile_id}/start",
            headers=self._headers(),
            timeout=30,
        )
        res.raise_for_status()
        data = res.json()

        # Tìm debug port từ response — Genlogin trả về data.port (string)
        debug_data = data.get("data") if isinstance(data.get("data"), dict) else {}
        debug_port = debug_data.get("port") or debug_data.get("debugPort")
        debug_address = debug_data.get("remoteDebuggingAddress") or debug_data.get("debugAddress")

        if debug_address:
            return debug_address
        elif debug_port:
            return f"127.0.0.1:{debug_port}"

        raise RuntimeError(f"Genlogin: Không lấy được debug address cho '{profile_name}'")

    def _find_profile(self, name: str) -> dict | None:
        profiles = self.list_profiles()
        for p in profiles:
            if p["name"].strip().lower() == name.strip().lower():
                return p
        return None
