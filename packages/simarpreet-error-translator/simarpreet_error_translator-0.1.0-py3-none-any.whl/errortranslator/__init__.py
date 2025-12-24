import sys
import json
import requests

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

_ERRORS_URL = "https://simarpreetsingh.org/ErrorTranslator/errors.json"
_errors = None


def _load_errors():
    global _errors
    if _errors is not None:
        return

    try:
        r = requests.get(_ERRORS_URL, timeout=5)
        r.raise_for_status()
        _errors = json.loads(r.text)
    except Exception:
        _errors = {}


def _get_error_line(tb):
    while tb.tb_next is not None:
        tb = tb.tb_next
    frame = tb.tb_frame
    return frame.f_code.co_filename, tb.tb_lineno


def _read_line(filename, lineno):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.readlines()[lineno - 1].rstrip()
    except Exception:
        return "<could not read code line>"


def excepthook(etype, evalue, etraceback):
    _load_errors()

    filename, lineno = _get_error_line(etraceback)
    code_line = _read_line(filename, lineno)

    explanation = _errors.get(
        etype.__name__,
        [{"explanation": "No explanation available"}],
    )[0]["explanation"]

    print(f"{RED}There was an error: {etype.__name__}{RESET}")
    print(f"{YELLOW}{explanation}{RESET}")
    print(f"{CYAN}Python says: {evalue}{RESET}")
    print(f"\n{MAGENTA}File: {filename}, line {lineno}{RESET}")
    print(f">>> {BLUE}{code_line}{RESET}\n")


def install():
    """Activate the error translator."""
    sys.excepthook = excepthook
