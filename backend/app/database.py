from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings
import os
import sys
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./inventory_po.db")
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    image_dir: str = os.getenv("IMAGE_DIR", "./static/images")
    image_similarity_threshold: float = 0.95
    feature_match_ratio: float = 0.75
    feature_min_matches: int = 15
    
    class Config:
        env_file = ".env"

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

