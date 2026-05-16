import requests
from adapters.base import AntidetectAdapter

DEFAULT_PORT = 9222


class ChromeAdapter(AntidetectAdapter):
    """Chrome gốc với remote debugging port."""

    def __init__(self, debug_port: int = DEFAULT_PORT):
        self.debug_port = int(debug_port)

    def list_profiles(self) -> list[dict]:
        try:
            res = requests.get(f"http://127.0.0.1:{self.debug_port}/json", timeout=3)
            res.raise_for_status()
            return [{
                "id": str(self.debug_port),
                "name": "Chrome",
                "status": "running",
                "port": self.debug_port,
            }]
        except Exception:
            return []
