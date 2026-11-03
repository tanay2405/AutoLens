from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = Path(__file__).resolve().parents[1] / "auto_intel.db"  # backend/auto_intel.db
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)