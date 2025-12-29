import os
import importlib
from rustpy.setup import setup_from_config
from rustpy.db import is_configured


_BOOTSTRAPPED = False

def auto_setup():
    # print("🚀 auto_setup chaqirildi")
    global _BOOTSTRAPPED

    if _BOOTSTRAPPED or is_configured():
        return

    # Default: config.py
    module_name = os.environ.get("RUSTPY_SETTINGS", "config")

    try:
        config = importlib.import_module(module_name)
    except ModuleNotFoundError:
        raise RuntimeError(
            f"Config module '{module_name}' topilmadi"
        )

    setup_from_config(config)
    _BOOTSTRAPPED = True
