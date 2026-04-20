from adapters.gpm import GPMAdapter
from adapters.gologin import GoLoginAdapter
from adapters.genlogin import GenloginAdapter

ADAPTERS = {
    "gpm": GPMAdapter,
    "gologin": GoLoginAdapter,
    "genlogin": GenloginAdapter,
}

def get_adapter(browser_type: str, config: dict = None):
    """Get adapter instance. Config needed for adapters requiring credentials (e.g., Genlogin)"""
    cls = ADAPTERS.get(browser_type.lower())
    if not cls:
        raise ValueError(f"Unsupported browser: {browser_type}. Supported: {list(ADAPTERS.keys())}")

    # Pass credentials if available (for Genlogin)
    if browser_type.lower() == "genlogin" and config:
        return cls(
            username=config.get("genlogin_username", ""),
            password=config.get("genlogin_password", "")
        )
    return cls()
