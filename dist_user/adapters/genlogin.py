import requests
from adapters.base import AntidetectAdapter

BASE = "http://127.0.0.1:55550"


class GenloginAdapter(AntidetectAdapter):
    def list_profiles(self) -> list[dict]:
        try:
            res = requests.get(f"{BASE}/backend/profiles/running", timeout=5)
            res.raise_for_status()
            data = res.json()
            profiles = data.get("data", [])
            if not isinstance(profiles, list):
                profiles = []
            result = []
            for p in profiles:
                name = p.get("profile_data", {}).get("name") or p.get("name", "")
                port = p.get("port") or p.get("debug_port") or p.get("debugPort")
                result.append({
                    "id": str(p.get("id", "")),
                    "name": name,
                    "status": "running",
                    "port": int(port) if port else None,
                })
            return result
        except Exception:
            return []
