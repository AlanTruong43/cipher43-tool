import requests
from adapters.base import AntidetectAdapter

BASE = "http://127.0.0.1:9495"


class GPMGlobalAdapter(AntidetectAdapter):

    def list_profiles(self) -> list[dict]:
        """
        GPMLogin Global không trả running status trong list endpoint.
        Fallback callback sẽ không hoạt động — chỉ dùng khi callback gửi port trực tiếp.
        """
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
