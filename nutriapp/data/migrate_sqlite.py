# nutriapp/data/migrate_sqlite.py
"""Jednorazowe przeniesienie danych z lokalnego nutriapp.db do PostgreSQL."""

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from nutriapp.data.database import PROJECT_ROOT, engine
from nutriapp.models.daily_target import DailyTarget
from nutriapp.models.diet_plan import DietDay, DietMeal, DietPlan
from nutriapp.models.dish import Dish
from nutriapp.models.dish_item import DishItem
from nutriapp.models.meal_calendar import MealEntry
from nutriapp.models.product import Product
from nutriapp.models.shopping_list import ShoppingItem, ShoppingList
from nutriapp.models.user import User
from nutriapp.models.user_profile import UserProfile
from nutriapp.models.weight import Weight

SQLITE_PATH = PROJECT_ROOT / "nutriapp.db"

# Kolejność zgodna z kluczami obcymi.
_MODEL_ORDER = (
    User,
    UserProfile,
    Product,
    Dish,
    DishItem,
    DailyTarget,
    MealEntry,
    DietPlan,
    DietDay,
    DietMeal,
    ShoppingList,
    ShoppingItem,
    Weight,
)


def migrate_sqlite_if_empty() -> int:
    """Kopiuje wiersze z SQLite, gdy baza PostgreSQL nie ma jeszcze danych.

    Zwraca liczbę skopiowanych wierszy. Gdy plik SQLite nie istnieje albo
    PostgreSQL ma już dane, nic nie zmienia.
    """
    if not SQLITE_PATH.exists():
        return 0

    if not _postgres_is_empty():
        return 0

    sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH.as_posix()}", future=True)
    SqliteSession = sessionmaker(bind=sqlite_engine, autoflush=False, autocommit=False)
    copied = 0

    try:
        with SqliteSession() as source, engine.begin() as connection:
            for model in _MODEL_ORDER:
                rows = source.execute(select(model)).scalars().all()
                payload = [
                    {column.key: getattr(row, column.key) for column in model.__table__.columns}
                    for row in rows
                ]
                if not payload:
                    continue
                connection.execute(model.__table__.insert(), payload)
                copied += len(payload)

            if copied:
                _sync_id_sequences(connection)
    finally:
        sqlite_engine.dispose()

    if copied:
        print(f"DEBUG DB: przeniesiono {copied} wierszy z nutriapp.db do PostgreSQL")
    return copied


def _postgres_is_empty() -> bool:
    with engine.connect() as connection:
        for model in _MODEL_ORDER:
            count = connection.execute(
                text(f"SELECT COUNT(*) FROM {model.__tablename__}")
            ).scalar_one()
            if count:
                return False
    return True


def _sync_id_sequences(connection) -> None:
    for model in _MODEL_ORDER:
        max_id = connection.execute(
            text(f"SELECT MAX(id) FROM {model.__tablename__}")
        ).scalar()
        if not max_id:
            continue
        connection.execute(
            text("SELECT setval(pg_get_serial_sequence(:table_name, 'id'), :max_id, true)"),
            {"table_name": model.__tablename__, "max_id": max_id},
        )
