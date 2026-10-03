# nutriapp/data/repositories/calendar_repo.py
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from nutriapp.data.database import SessionLocal
from nutriapp.models.dish import Dish
from nutriapp.models.meal_calendar import MealEntry
from nutriapp.models.product import Product


ALLOWED_SOURCES = {
    "manual",
    "diet",
}


def get_session() -> Session:
    return SessionLocal()


def get_entries_for_date(
    session: Session,
    *,
    user_id: int,
    entry_date: date,
) -> list[MealEntry]:
    return (
        session.query(MealEntry)
        .options(
            joinedload(MealEntry.product),
            joinedload(MealEntry.dish),
        )
        .filter(
            MealEntry.user_id == user_id,
            MealEntry.entry_date == entry_date,
        )
        .order_by(
            MealEntry.sort_order.asc(),
            MealEntry.id.asc(),
        )
        .all()
    )


def get_entries_for_range(
    session: Session,
    *,
    user_id: int,
    start_date: date,
    end_date: date,
) -> list[MealEntry]:
    return (
        session.query(MealEntry)
        .options(
            joinedload(MealEntry.product),
            joinedload(MealEntry.dish),
        )
        .filter(
            MealEntry.user_id == user_id,
            MealEntry.entry_date >= start_date,
            MealEntry.entry_date <= end_date,
        )
        .order_by(
            MealEntry.entry_date.asc(),
            MealEntry.sort_order.asc(),
            MealEntry.id.asc(),
        )
        .all()
    )


def get_entry_by_id(
    session: Session,
    *,
    entry_id: int,
    user_id: int,
) -> MealEntry | None:
    return (
        session.query(MealEntry)
        .options(
            joinedload(MealEntry.product),
            joinedload(MealEntry.dish),
        )
        .filter(
            MealEntry.id == entry_id,
            MealEntry.user_id == user_id,
        )
        .first()
    )


def _get_next_sort_order(
    session: Session,
    *,
    user_id: int,
    entry_date: date,
) -> int:
    current_max = (
        session.query(func.max(MealEntry.sort_order))
        .filter(
            MealEntry.user_id == user_id,
            MealEntry.entry_date == entry_date,
        )
        .scalar()
    )

    if current_max is None:
        return 0

    return current_max + 1


def add_product_entry(
    session: Session,
    *,
    user_id: int,
    entry_date: date,
    product_id: int,
    amount_g: float,
    is_planned: bool,
    is_eaten: bool,
    source: str = "manual",
) -> MealEntry | None:
    if amount_g <= 0:
        return None

    if source not in ALLOWED_SOURCES:
        return None

    product = (
        session.query(Product)
        .filter(
            Product.id == product_id,
            Product.user_id == user_id,
        )
        .first()
    )

    if product is None:
        return None

    entry = MealEntry(
        user_id=user_id,
        entry_date=entry_date,
        sort_order=_get_next_sort_order(
            session,
            user_id=user_id,
            entry_date=entry_date,
        ),
        product_id=product_id,
        dish_id=None,
        amount_g=amount_g,
        servings=1.0,
        is_planned=is_planned,
        is_eaten=is_eaten,
        is_diet=(source == "diet"),
        source=source,
        updated_at=datetime.utcnow(),
    )

    session.add(entry)
    session.commit()
    session.refresh(entry)

    return entry


def add_dish_entry(
    session: Session,
    *,
    user_id: int,
    entry_date: date,
    dish_id: int,
    servings: float = 1.0,
    is_planned: bool,
    is_eaten: bool,
    source: str = "manual",
) -> MealEntry | None:
    if servings <= 0:
        return None

    if source not in ALLOWED_SOURCES:
        return None

    dish = (
        session.query(Dish)
        .filter(
            Dish.id == dish_id,
            Dish.user_id == user_id,
        )
        .first()
    )

    if dish is None:
        return None

    entry = MealEntry(
        user_id=user_id,
        entry_date=entry_date,
        sort_order=_get_next_sort_order(
            session,
            user_id=user_id,
            entry_date=entry_date,
        ),
        product_id=None,
        dish_id=dish_id,
        amount_g=None,
        servings=servings,
        is_planned=is_planned,
        is_eaten=is_eaten,
        is_diet=(source == "diet"),
        source=source,
        updated_at=datetime.utcnow(),
    )

    session.add(entry)
    session.commit()
    session.refresh(entry)

    return entry


def set_entry_flags(
    session: Session,
    *,
    entry_id: int,
    user_id: int,
    is_planned: bool | None = None,
    is_eaten: bool | None = None,
) -> bool:
    entry = get_entry_by_id(
        session,
        entry_id=entry_id,
        user_id=user_id,
    )

    if entry is None:
        return False

    if is_planned is not None:
        entry.is_planned = is_planned

    if is_eaten is not None:
        entry.is_eaten = is_eaten

    entry.updated_at = datetime.utcnow()
    session.commit()
    return True


def update_entry_date(
    session: Session,
    *,
    entry_id: int,
    user_id: int,
    new_date: date,
) -> bool:
    entry = get_entry_by_id(
        session,
        entry_id=entry_id,
        user_id=user_id,
    )

    if entry is None:
        return False

    entry.entry_date = new_date
    entry.sort_order = _get_next_sort_order(
        session,
        user_id=user_id,
        entry_date=new_date,
    )
    entry.updated_at = datetime.utcnow()

    session.commit()
    return True


def update_entry_order(
    session: Session,
    *,
    entry_id: int,
    user_id: int,
    new_sort_order: int,
) -> bool:
    if new_sort_order < 0:
        return False

    entry = get_entry_by_id(
        session,
        entry_id=entry_id,
        user_id=user_id,
    )

    if entry is None:
        return False

    entry.sort_order = new_sort_order
    entry.updated_at = datetime.utcnow()

    session.commit()
    return True


def delete_entry(
    session: Session,
    *,
    entry_id: int,
    user_id: int,
) -> bool:
    entry = get_entry_by_id(
        session,
        entry_id=entry_id,
        user_id=user_id,
    )

    if entry is None:
        return False

    session.delete(entry)
    session.commit()

    return True