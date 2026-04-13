import requests
import time
from adapters.base import AntidetectAdapter

BASE = "http://127.0.0.1:19995/api/v3"


class GPMAdapter(AntidetectAdapter):

    def list_profiles(self) -> list[dict]:
        res = requests.get(f"{BASE}/profiles", params={"page": 1, "per_page": 100}, timeout=5)
        res.raise_for_status()
        data = res.json()
        profiles = data.get("data", {}).get("profiles") or data.get("data", [])
        return [
            {
                "id": str(p.get("id", p.get("profile_id", ""))),
                "name": p.get("name", p.get("profile_name", "")),
                "status": "running" if p.get("is_open") else "stopped",
            }
            for p in profiles
        ]

    def get_debug_address(self, profile_name: str) -> str:
        profile = self._find_profile(profile_name)
        if not profile:
            raise ValueError(f"GPM: Profile '{profile_name}' không tìm thấy")

        profile_id = profile["id"]

        # Nếu đang chạy thì lấy port luôn
        if profile["status"] == "running":
            return self._get_running_address(profile_id)

        # Start profile
        res = requests.get(f"{BASE}/profiles/start", params={"profile_id": profile_id}, timeout=15)
        res.raise_for_status()
        data = res.json().get("data", {})
        address = data.get("remote_debugging_address")
        if not address:
            raise RuntimeError(f"GPM: Không lấy được debug address cho '{profile_name}'")
        return address

    def _find_profile(self, name: str) -> dict | None:
        profiles = self.list_profiles()
        for p in profiles:
            if p["name"].strip().lower() == name.strip().lower():
                return p
        return None

    def _get_running_address(self, profile_id: str) -> str:
        # GPM trả debug address khi start, nếu đã chạy thì start lại để lấy address
        res = requests.get(f"{BASE}/profiles/start", params={"profile_id": profile_id}, timeout=15)
        res.raise_for_status()
        data = res.json().get("data", {})
        address = data.get("remote_debugging_address")
        if not address:
            raise RuntimeError("GPM: Không lấy được debug address từ profile đang chạy")
        return address
