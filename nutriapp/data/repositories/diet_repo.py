# nutriapp/data/repositories/diet_repo.py
from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy.orm import Session, joinedload

from nutriapp.data.database import SessionLocal
from nutriapp.models.diet_plan import DietPlan, DietDay, DietMeal
from nutriapp.models.meal_calendar import MealEntry
from nutriapp.models.dish import Dish
from nutriapp.models.dish_item import DishItem
from nutriapp.models.product import Product

from nutriapp.data.repositories.calendar_repo import _get_next_sort_order


def get_session() -> Session:
    return SessionLocal()


def create_diet(
    session: Session,
    *,
    user_id: int,
    name: str,
    cycle_length: int = 7,
    calendar_days: int = 7,
) -> DietPlan:
    diet = DietPlan(
        user_id=user_id,
        name=name,
        description="",
        cycle_length=cycle_length,
        calendar_days=calendar_days,
        is_active=False,
        cycle_start_date=None,
        cycle_start_day=1,
    )
    session.add(diet)
    session.commit()
    session.refresh(diet)
    return diet


def get_diet_by_id(
    session: Session,
    *,
    diet_id: int,
    user_id: int,
) -> Optional[DietPlan]:
    return (
        session.query(DietPlan)
        .options(
            joinedload(DietPlan.days)
            .joinedload(DietDay.meals)
            .joinedload(DietMeal.product),
            joinedload(DietPlan.days)
            .joinedload(DietDay.meals)
            .joinedload(DietMeal.dish)
            .joinedload(Dish.items)
            .joinedload(DishItem.product),
        )
        .filter(
            DietPlan.id == diet_id,
            DietPlan.user_id == user_id,
        )
        .first()
    )


def list_diets_for_user(
    session: Session,
    *,
    user_id: int,
) -> List[DietPlan]:
    return (
        session.query(DietPlan)
        .filter(DietPlan.user_id == user_id)
        .order_by(DietPlan.created_at.desc())
        .all()
    )


def get_active_diet_for_user(
    session: Session,
    *,
    user_id: int,
) -> Optional[DietPlan]:
    return (
        session.query(DietPlan)
        .filter(
            DietPlan.user_id == user_id,
            DietPlan.is_active == True,  # noqa: E712
        )
        .order_by(DietPlan.id.asc())
        .first()
    )


def update_diet_meta(
    session: Session,
    *,
    diet_id: int,
    user_id: int,
    name: str | None = None,
    description: str | None = None,
    cycle_length: int | None = None,
    calendar_days: int | None = None,
    is_active: bool | None = None,
    cycle_start_date=None,
    cycle_start_day: int | None = None,
) -> bool:
    diet = (
        session.query(DietPlan)
        .filter(
            DietPlan.id == diet_id,
            DietPlan.user_id == user_id,
        )
        .first()
    )
    if diet is None:
        return False

    if name is not None:
        diet.name = name

    if description is not None:
        diet.description = description

    if cycle_length is not None:
        diet.cycle_length = cycle_length

    if calendar_days is not None:
        diet.calendar_days = calendar_days

    if is_active is not None:
        diet.is_active = is_active

    if cycle_start_date is not None:
        diet.cycle_start_date = cycle_start_date

    if cycle_start_day is not None:
        diet.cycle_start_day = cycle_start_day

    diet.updated_at = datetime.utcnow()
    session.commit()
    return True


def set_active_diet(
    session: Session,
    *,
    user_id: int,
    diet_id: Optional[int],
) -> None:
    """
    Ustawia jedną dietę jako aktywną (lub żadną, gdy diet_id=None).
    """
    # dezaktywuj wszystkie
    session.query(DietPlan).filter(DietPlan.user_id == user_id).update(
        {"is_active": False}, synchronize_session=False
    )
    if diet_id is not None:
        session.query(DietPlan).filter(
            DietPlan.user_id == user_id,
            DietPlan.id == diet_id,
        ).update({"is_active": True}, synchronize_session=False)
    session.commit()


def add_meal_to_diet_day(
    session: Session,
    *,
    diet_id: int,
    day_number: int,
    user_id: int,
    product_id: Optional[int] = None,
    dish_id: Optional[int] = None,
    amount_g: Optional[float] = None,
    servings: Optional[float] = None,
) -> Optional[DietMeal]:
    # walidacja źródła – dokładnie jeden z product_id/dish_id
    if (product_id is None and dish_id is None) or (
        product_id is not None and dish_id is not None
    ):
        return None

    diet_day = (
        session.query(DietDay)
        .join(DietPlan)
        .filter(
            DietPlan.id == diet_id,
            DietPlan.user_id == user_id,
            DietDay.day_number == day_number,
        )
        .first()
    )

    if diet_day is None:
        diet_day = DietDay(
            diet_id=diet_id,
            day_number=day_number,
        )
        session.add(diet_day)
        session.flush()

    meal = DietMeal(
        diet_day_id=diet_day.id,
        product_id=product_id,
        dish_id=dish_id,
        amount_g=amount_g,
        servings=servings,
    )
    session.add(meal)
    session.commit()
    session.refresh(meal)
    return meal


def remove_meal_from_diet(
    session: Session,
    *,
    diet_meal_id: int,
    user_id: int,
) -> bool:
    meal = (
        session.query(DietMeal)
        .join(DietDay)
        .join(DietPlan)
        .filter(
            DietMeal.id == diet_meal_id,
            DietPlan.user_id == user_id,
        )
        .first()
    )

    if meal is None:
        return False

    session.delete(meal)
    session.commit()
    return True


def get_meals_for_diet_day(
    session: Session,
    *,
    diet_id: int,
    day_number: int,
    user_id: int,
) -> List[DietMeal]:
    return (
        session.query(DietMeal)
        .join(DietDay)
        .join(DietPlan)
        .options(
            joinedload(DietMeal.product),
            joinedload(DietMeal.dish)
            .joinedload(Dish.items)
            .joinedload(DishItem.product),
        )
        .filter(
            DietPlan.id == diet_id,
            DietPlan.user_id == user_id,
            DietDay.day_number == day_number,
        )
        .order_by(DietMeal.id)
        .all()
    )


def get_all_diet_days(
    session: Session,
    *,
    diet_id: int,
    user_id: int,
) -> Dict[int, List[DietMeal]]:
    from collections import defaultdict

    days = (
        session.query(DietDay)
        .join(DietPlan)
        .options(
            joinedload(DietDay.meals)
            .joinedload(DietMeal.product),
            joinedload(DietDay.meals)
            .joinedload(DietMeal.dish)
            .joinedload(Dish.items)
            .joinedload(DishItem.product),
        )
        .filter(
            DietPlan.id == diet_id,
            DietPlan.user_id == user_id,
        )
        .all()
    )

    result: Dict[int, List[DietMeal]] = defaultdict(list)
    for day in days:
        result[day.day_number].extend(day.meals)

    return result


def day_has_planned_meals(
    session: Session,
    *,
    user_id: int,
    entry_date,
) -> bool:
    exists = (
        session.query(MealEntry.id)
        .filter(
            MealEntry.user_id == user_id,
            MealEntry.entry_date == entry_date,
            MealEntry.is_planned == True,  # noqa: E712
        )
        .first()
    )
    return exists is not None


def day_has_diet_entries(
    session: Session,
    *,
    user_id: int,
    entry_date,
) -> bool:
    """
    Czy dany dzień kalendarza ma już wpisy z diety (is_diet=True)?
    """
    exists = (
        session.query(MealEntry.id)
        .filter(
            MealEntry.user_id == user_id,
            MealEntry.entry_date == entry_date,
            MealEntry.is_diet == True,  # noqa: E712
        )
        .first()
    )
    return exists is not None


def delete_diet_entries_for_dates(
    session: Session,
    *,
    user_id: int,
    dates: List,
) -> int:
    count = 0
    for d in dates:
        deleted = (
            session.query(MealEntry)
            .filter(
                MealEntry.user_id == user_id,
                MealEntry.entry_date == d,
                MealEntry.is_diet == True,  # tylko wpisy z diety
            )
            .delete(synchronize_session=False)
        )
        count += deleted

    session.commit()
    return count


def add_diet_meals_to_calendar(
    session: Session,
    *,
    user_id: int,
    entry_date,
    diet_meals: List[DietMeal],
) -> int:
    """
    Dodaje konkretne posiłki z DietMeal do kalendarza na dany dzień.
    Wpisy są oznaczane jako:
    - is_planned=True
    - is_eaten=False
    - is_diet=True
    - source="diet"
    """
    from datetime import datetime

    count = 0
    for dm in diet_meals:
        sort_order = _get_next_sort_order(
            session,
            user_id=user_id,
            entry_date=entry_date,
        )

        entry = MealEntry(
            user_id=user_id,
            entry_date=entry_date,
            sort_order=sort_order,
            product_id=dm.product_id,
            dish_id=dm.dish_id,
            amount_g=dm.amount_g,
            servings=dm.servings,
            is_planned=True,
            is_eaten=False,
            is_diet=True,
            source="diet",
            updated_at=datetime.utcnow(),
        )
        session.add(entry)
        count += 1

    # commit całości po dodaniu wszystkich wpisów
    session.commit()
    return count