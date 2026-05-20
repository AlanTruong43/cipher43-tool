import requests
from adapters.base import AntidetectAdapter

BASE = "http://127.0.0.1:9495"


class GPMGlobalAdapter(AntidetectAdapter):

    def list_profiles(self) -> list[dict]:
        try:
            res = requests.get(
                f"{BASE}/api/v1/profiles",
                params={"page": 1, "per_page": 200},
                timeout=5,
            )
            res.raise_for_status()
            data = res.json()
            profiles = (
                data.get("data", {}).get("profiles")
                or data.get("data", [])
            )
            if not isinstance(profiles, list):
                profiles = []
            return [
                {
                    "id": str(p.get("id", "")),
                    "name": p.get("name", ""),
                    "status": "stopped",
                    "port": None,
                }
                for p in profiles
            ]
        except Exception:
            return []

    def start_profile(self, profile_id: str) -> str:
        """Start profile và trả về debug address '127.0.0.1:PORT'."""
        res = requests.get(
            f"{BASE}/api/v1/profiles/start/{profile_id}",
            timeout=30,
        )
        res.raise_for_status()
        data = res.json().get("data", {})
        port = data.get("remote_debugging_port")
        if not port:
            raise RuntimeError(f"GPMGlobal: Không lấy được remote_debugging_port cho profile '{profile_id}'")
        return f"127.0.0.1:{port}"
