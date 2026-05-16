from adapters.gpm import GPMAdapter
from adapters.gologin import GoLoginAdapter
from adapters.genlogin import GenloginAdapter

ADAPTERS = {
    "genlogin": GenloginAdapter,
    "gologin": GoLoginAdapter,
    "gpm": GPMAdapter,
}

ANTIDETECT_CHOICES = [
    ("1", "genlogin",  "GenLogin"),
    ("2", "gologin",   "GoLogin"),
    ("3", "gpm",       "GPM"),
]

def get_adapter(browser_type: str):
    key = browser_type.lower()
    if key not in ADAPTERS:
        raise ValueError(f"Unsupported antidetect: {browser_type}. Supported: {list(ADAPTERS.keys())}")
    return ADAPTERS[key]()
