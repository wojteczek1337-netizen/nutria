# nutriapp/data/database.py
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

_raw_url = os.getenv("DATABASE_URL", "").strip()
if not _raw_url:
    raise RuntimeError(
        "Brak DATABASE_URL. Skopiuj .env.example do .env i wstaw hasło bazy Supabase."
    )

database_url = make_url(_raw_url)
password_override = os.getenv("DB_PASSWORD", "").strip()
if password_override:
    database_url = database_url.set(password=password_override)

if database_url.password in {None, "", "YOUR-PASSWORD", "YOUR_PASSWORD"}:
    raise RuntimeError(
        "W pliku .env zastąp YOUR-PASSWORD prawdziwym hasłem bazy "
        "(Supabase: Project Settings, Database). Nie zostawiaj nawiasów "
        "kwadratowych wokół hasła."
    )

if (
    len(database_url.password) >= 2
    and database_url.password.startswith("[")
    and database_url.password.endswith("]")
):
    raise RuntimeError(
        "Hasło w DATABASE_URL jest w nawiasach kwadratowych. "
        "W szablonie Supabase [YOUR-PASSWORD] nawiasy są tylko znacznikiem — usuń je."
    )

if database_url.drivername in {"postgresql", "postgres"}:
    database_url = database_url.set(drivername="postgresql+psycopg")

if database_url.drivername.startswith("postgresql"):
    query = dict(database_url.query)
    query.setdefault("sslmode", "require")
    query.setdefault("connect_timeout", "10")
    database_url = database_url.set(query=query)

# public.users w Supabase to konta Auth (uuid). Tabele Nutrii mają własne
# users.id typu integer, więc siedzą w osobnym schemacie.
NUTRIA_SCHEMA = "nutria"

engine = create_engine(
    database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
    execution_options={"schema_translate_map": {None: NUTRIA_SCHEMA}},
)


@event.listens_for(engine, "connect")
def _set_search_path(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute(f"SET search_path TO {NUTRIA_SCHEMA}, public")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def prepare_database() -> None:
    with engine.begin() as connection:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {NUTRIA_SCHEMA}"))
    Base.metadata.create_all(bind=engine)
