# nutriapp/data/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Plik bazy będzie leżał obok main.py (w katalogu projektu)
DATABASE_URL = "sqlite:///nutriapp.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,         # możesz dać True, żeby widzieć SQL w konsoli
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()