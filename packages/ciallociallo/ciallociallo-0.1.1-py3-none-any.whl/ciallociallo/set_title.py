# set_title.py
import os, sys
from contextlib import contextmanager

def _safe_set_title(title: str) -> bool:
    try:
        if os.environ.get("TERM_PROGRAM") == "vscode":
            return False
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(str(title))
        else:
            sys.stdout.write(f"\033]2;{title}\007")
            sys.stdout.flush()
        return True
    except Exception:
        return False

@contextmanager
def terminal_title(title: str, reset: str | None = None):
    ok = _safe_set_title(title)
    try:
        yield
    finally:
        if reset and ok:
            _safe_set_title(reset)