import argparse
import importlib
import importlib.util
import sys
from pathlib import Path

# from rustpy.bootstrap import auto_setup
from rustpy.generator import generate_project
# from rustpy.migrations.makemigrations import makemigrations
# from rustpy.migrations.migrate import migrate
from rustpy.setup import setup_from_config


# 🔥 DJANGO-MANAGE.PY ANALOG
PROJECT_ROOT = Path.cwd()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_config():
    path = PROJECT_ROOT / "config.py"

    if not path.exists():
        raise RuntimeError(
            f"config.py topilmadi: {path.resolve()}"
        )

    spec = importlib.util.spec_from_file_location("config", path)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config



def main():
    parser = argparse.ArgumentParser("rustpy")
    sub = parser.add_subparsers(dest="cmd", required=True)

    start = sub.add_parser("startproject")
    start.add_argument("path")

    # sub.add_parser("makemigrations")
    # sub.add_parser("migrate")
    sub.add_parser("smigrate")

    args = parser.parse_args()   # ✅ AVVAL SHU

    # print("🟢 CLI STARTED")
    # print("ARGS:", args.cmd)

    if args.cmd == "startproject":
        generate_project(args.path)

    # elif args.cmd == "makemigrations":
    #     config = load_config()
    #     setup_from_config(config)

    #     print("🟠 INSTALLED_APPS:", getattr(config, "INSTALLED_APPS", None))

    #     for app in getattr(config, "INSTALLED_APPS", []):
    #         print("🔵 importing app:", app)
    #         importlib.import_module(app)
        
    #     makemigrations(
    #         installed_apps=config.INSTALLED_APPS
    #     )

    # elif args.cmd == "migrate":
    #     config = load_config()
    #     setup_from_config(config)
    #     migrate()

    elif args.cmd == "smigrate":
        config = load_config()
        setup_from_config(config)

        # 🔥 MODELLARNI RO‘YXATGA OLAMIZ
        for app in getattr(config, "INSTALLED_APPS", []):
            __import__(app)

        from rustpy.db import get_backend
        from rustpy.migrations.safe_migrate import safe_migrate

        db = get_backend()
        safe_migrate(db)


