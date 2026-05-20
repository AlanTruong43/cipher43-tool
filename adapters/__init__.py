from adapters.gpm import GPMAdapter
from adapters.gologin import GoLoginAdapter
from adapters.genlogin import GenloginAdapter
from adapters.gpmglobal import GPMGlobalAdapter

ADAPTERS = {
    "genlogin":   GenloginAdapter,
    "gologin":    GoLoginAdapter,
    "gpm":        GPMAdapter,
    "gpmglobal":  GPMGlobalAdapter,
}

ANTIDETECT_CHOICES = [
    ("1", "genlogin",   "GenLogin"),
    ("2", "gologin",    "GoLogin"),
    ("3", "gpm",        "GPM"),
    ("4", "gpmglobal",  "GPMLogin Global"),
]

def get_adapter(browser_type: str):
    key = browser_type.lower()
    if key not in ADAPTERS:
        raise ValueError(f"Unsupported antidetect: {browser_type}. Supported: {list(ADAPTERS.keys())}")
    return ADAPTERS[key]()
