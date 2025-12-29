# python/phaeton/__init__.py


try:
    from ._phaeton import __version__ as _rust_version
except ImportError:
    _rust_version = "0.0.0-dev"

from . import text, io, guard

# --- ROOT FUNCTIONS & CONFIG ---

_CONFIG = {
    "threads": 4,
    "strict": True
}

def configure(threads: int = 4, strict: bool = True):
    """Global configuration settings for Phaeton engine."""
    global _CONFIG
    _CONFIG["threads"] = threads
    _CONFIG["strict"] = strict
    print(f"DEBUG: Config updated -> {_CONFIG}")

def version() -> str:
    """Check library and engine version."""
    return f"Phaeton v0.1.0 (Engine: Rust v{_rust_version})"

def sanitize(text: str) -> str:
    """
    [DUMMY] Otomatis mendeteksi PII umum dan menggantinya dengan ***.
    """
    if not text: return ""
    return text.replace("@", "***").replace("08", "**")