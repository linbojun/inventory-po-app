import uvicorn
import os

if __name__ == "__main__":
    # Hot-reload is convenient during dev, but it can restart the server when
    # images/files are written (e.g. during uploads or the integration tests).
    # Enable it explicitly via: UVICORN_RELOAD=1 python run.py
    reload = os.getenv("UVICORN_RELOAD", "").strip().lower() in {"1", "true", "yes", "y"}
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=reload)

