import argparse
import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

DEFAULT_SQLITE_URL = "sqlite:///./inventory_po.db"


def _load_dotenv():
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path, override=False)


def _set_mode(use_dev: bool):
    """
    Configure environment variables for dev/prod mode **before** FastAPI loads.
    """
    if use_dev:
        os.environ["APP_MODE"] = "dev"
        sqlite_url = os.getenv("SQLITE_DATABASE_URL") or DEFAULT_SQLITE_URL
        os.environ["DATABASE_URL"] = sqlite_url
        os.environ["FORCE_LOCAL_IMAGE_STORAGE"] = "1"
        os.environ.setdefault("IMAGE_DIR", "./static/images")
    else:
        os.environ["APP_MODE"] = "prod"
        os.environ.pop("FORCE_LOCAL_IMAGE_STORAGE", None)


def main():
    parser = argparse.ArgumentParser(description="Run Inventory PO backend")
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Use SQLite + local image storage (overrides DATABASE_URL/R2 settings)",
    )
    args = parser.parse_args()

    _load_dotenv()
    _set_mode(args.dev)

    mode_label = "development" if args.dev else "production"
    print(f"[run.py] Starting backend in {mode_label} mode at http://0.0.0.0:8000")

    # Hot-reload is convenient during dev, but it can restart the server when
    # images/files are written (e.g. during uploads or the integration tests).
    # Enable it explicitly via: UVICORN_RELOAD=1 python run.py [--dev]
    reload_enabled = os.getenv("UVICORN_RELOAD", "").strip().lower() in {"1", "true", "yes", "y"}
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=reload_enabled)


if __name__ == "__main__":
    main()

