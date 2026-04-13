from adapters.gpm import GPMAdapter
from adapters.gologin import GoLoginAdapter

ADAPTERS = {
    "gpm": GPMAdapter,
    "gologin": GoLoginAdapter,
}

def get_adapter(browser_type: str):
    cls = ADAPTERS.get(browser_type.lower())
    if not cls:
        raise ValueError(f"Unsupported browser: {browser_type}. Supported: {list(ADAPTERS.keys())}")
    return cls()
