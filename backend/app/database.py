from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import os
import sys
import re
from dotenv import load_dotenv

load_dotenv()

def _normalize_database_url(raw: str) -> str:
    """
    Normalize common copy/paste mistakes when setting DATABASE_URL.

    Users sometimes paste a full CLI command like:
      psql 'postgresql://user:pass@host/db?sslmode=require'

    SQLAlchemy expects ONLY the URL:
      postgresql://user:pass@host/db?sslmode=require
    """
    if raw is None:
        return raw
    value = str(raw).strip()
    if not value:
        return value

    # Strip a leading "psql" command if present.
    if value.lower().startswith("psql"):
        value = value[4:].strip()

    # Remove one layer of wrapping quotes.
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        value = value[1:-1].strip()

    # Occasionally a pasted value includes doubled trailing quotes like: postgresql://...'' (or "")
    value = re.sub(r"(['\"]){2,}$", "", value).strip()
    return value


def _read_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _read_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./inventory_po.db")
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    image_dir: str = os.getenv("IMAGE_DIR", "./static/images")
    image_similarity_threshold: float = _read_float_env("IMAGE_SIMILARITY_THRESHOLD", 0.95)
    feature_match_ratio: float = _read_float_env("FEATURE_MATCH_RATIO", 0.55)
    feature_min_matches: int = _read_int_env("FEATURE_MIN_MATCHES", 225)

    @field_validator("database_url", mode="before")
    @classmethod
    def _validate_database_url(cls, value):
        return _normalize_database_url(value)

settings = Settings()

# Create directories if they don't exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.image_dir, exist_ok=True)

# Create database engine with error handling for SQLite compatibility issues
try:
    if settings.database_url.startswith("sqlite"):
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(settings.database_url)
except Exception as e:
    if "sqlite" in str(e).lower() or "_sqlite3" in str(e) or "sqlite3_enable_load_extension" in str(e):
        error_msg = """
╔══════════════════════════════════════════════════════════════════════════╗
║                    SQLite Compatibility Error                           ║
╚══════════════════════════════════════════════════════════════════════════╝

Your Python installation has a SQLite library compatibility issue.
This is a known issue with Python 3.8 from Homebrew on macOS.

SOLUTION OPTIONS (choose one):

1. REINSTALL PYTHON 3.8 WITH PROPER SQLITE SUPPORT:
   brew reinstall python@3.8
   
   Then recreate your virtual environment:
     cd backend
     rm -rf venv
     python3.8 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt

2. UPGRADE TO PYTHON 3.9+ (Better SQLite Support):
   brew install python@3.9
   
   Then recreate your virtual environment:
     cd backend
     rm -rf venv
     python3.9 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt

3. USE PYENV (More Control):
   brew install pyenv
   pyenv install 3.9.18
   pyenv local 3.9.18
   
   Then recreate your virtual environment with the pyenv Python.

Error details: {error}
""".format(error=str(e))
        print(error_msg)
        sys.exit(1)
    else:
        raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_updates():
    """Lightweight migrations for existing databases."""
    inspector = inspect(engine)
    if "products" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("products")}
    if "image_hash" not in existing_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE products ADD COLUMN image_hash VARCHAR(32)"))

