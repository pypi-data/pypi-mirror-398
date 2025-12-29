import os
import json
import threading
import requests
from packaging import version
from pathlib import Path
from pkg_resources import get_distribution

# Optional: colored printing for console and notebook
try:
    from IPython.display import display, Markdown
    IN_NOTEBOOK = True
except ImportError:
    IN_NOTEBOOK = False

CHECK_INTERVAL_DAYS = 7

def _should_check(cache_file: Path) -> bool:
    if not cache_file.exists():
        return True
    try:
        with open(cache_file, "r") as f:
            data = json.load(f)
            last_check = data.get("last_check", 0)
    except Exception:
        return True

    import time
    days_since = (time.time() - last_check) / (60 * 60 * 24)
    return days_since >= CHECK_INTERVAL_DAYS


def _write_check_timestamp(cache_file: Path):
    try:
        with open(cache_file, "w") as f:
            json.dump({"last_check": __import__("time").time()}, f)
    except Exception:
        pass

def _print_update_message(pkg_name, installed, latest):
    message = (
        f"📈 A new version of '{pkg_name}' is available!\n"
        f"Installed version: {installed}\n"
        f"Latest version:    {latest}\n"
        f"Update with:\n"
        f"    pip install --upgrade {pkg_name}\n\n"
        f"✨ What's New?\n"
        f"Check out the latest features, improvements, and fixes here:\n"
        f"https://pypi.org/project/qdesc/#description\n"
    )
    if IN_NOTEBOOK:
        # Display nicely in Jupyter Notebook
        display(Markdown(f"**{message}**"))
    else:
        # Regular console print
        print(message)

def _check_now(package_name: str):
    cache_file = Path.home() / f".{package_name}_update_check.json"
    if not _should_check(cache_file):
        return
    _write_check_timestamp(cache_file)
    if os.getenv("PYLIB_DISABLE_UPDATE_CHECK") == "1":
        return
    try:
        installed_version = get_distribution(package_name).version
    except Exception:
        return
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=3)
        latest_version = response.json()["info"]["version"]
    except Exception:
        return

    if version.parse(latest_version) > version.parse(installed_version):
        _print_update_message(package_name, installed_version, latest_version)

def check_for_update(package_name: str):
    # Run in background thread
    thread = threading.Thread(target=_check_now, args=(package_name,), daemon=True)
    thread.start()
