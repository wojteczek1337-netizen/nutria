# nutriapp/services/calendar_service.py
from datetime import date
from typing import Dict, Tuple, Sequence

from sqlalchemy.orm import Session

from nutriapp.services.dishes_service import compute_dish_macros
from nutriapp.data.repositories.dish_repo import (
    get_dish_with_items,
    get_session as get_dish_session,
)
from nutriapp.data.repositories.user_repo import get_user_profile
from nutriapp.data.repositories.daily_target_repo import ensure_daily_target_for_date
from nutriapp.data.repositories.calendar_repo import get_entries_for_date


def _empty_totals() -> Dict[str, float]:
    return {
        "energy": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "saturated_fat": 0.0,
        "carbs": 0.0,
        "sugar": 0.0,
        "fiber": 0.0,
        "salt": 0.0,
    }


def compute_entry_macros(entry) -> Tuple[Dict[str, float], bool]:
    totals = _empty_totals()
    has_data = False

    # Produkt
    if getattr(entry, "product", None) is not None and entry.amount_g:
        product = entry.product
        multiplier = entry.amount_g / 100.0

        nutrition_values = {
            "energy": product.energy_kcal_100,
            "protein": product.protein_100,
            "fat": product.fat_100,
            "saturated_fat": product.saturated_fat_100,
            "carbs": product.carbs_100,
            "sugar": product.sugar_100,
            "fiber": product.fiber_100,
            "salt": product.salt_100,
        }

        for key, value in nutrition_values.items():
            if value is not None:
                totals[key] += value * multiplier
                has_data = True

        return totals, has_data

    # Danie
    if getattr(entry, "dish_id", None) is not None and entry.servings:
        session = get_dish_session()
        try:
            dish = get_dish_with_items(
                session,
                dish_id=entry.dish_id,
                user_id=entry.user_id,
            )
        finally:
            session.close()

        if dish is None:
            return totals, False

        dish_totals, dish_has_data = compute_dish_macros(dish)

        if not dish_has_data:
            return totals, False

        multiplier = entry.servings

        for key in totals.keys():
            totals[key] += dish_totals.get(key, 0.0) * multiplier

        return totals, True

    return totals, False


def compute_day_macros(entries: Sequence):
    """
    Zwraca:
    - eaten_totals: sumy dla wpisów z is_eaten == True
    - planned_totals: sumy dla wpisów z is_planned == True
    - has_eaten, has_planned: czy w ogóle były dane w tych kategoriach
    """
    eaten_totals = _empty_totals()
    planned_totals = _empty_totals()
    has_eaten = False
    has_planned = False

    for entry in entries:
        entry_totals, has_data = compute_entry_macros(entry)
        if not has_data:
            continue

        is_eaten = bool(getattr(entry, "is_eaten", False))
        is_planned = bool(getattr(entry, "is_planned", False))

        if is_eaten:
            has_eaten = True
            for key in eaten_totals.keys():
                eaten_totals[key] += entry_totals.get(key, 0.0)

        if is_planned:
            has_planned = True
            for key in planned_totals.keys():
                planned_totals[key] += entry_totals.get(key, 0.0)

    return eaten_totals, planned_totals, has_eaten, has_planned


def get_calorie_ring_data(
    session: Session,
    *,
    user_id: int,
    day: date,
) -> dict | None:
    """
    Zwraca dane pod wykres pierścieniowy kcal dla danego dnia:
    {
        "target_calories": float,
        "planned_calories": float,
        "eaten_calories": float,
        "planned_over_target": float,
    }
    """
    profile = get_user_profile(session, user_id=user_id)
    if profile is None:
        return None

    # snapshot celów na dzień
    daily_target = ensure_daily_target_for_date(
        session,
        user_profile=profile,
        day=day,
    )

    entries = get_entries_for_date(
        session,
        user_id=user_id,
        entry_date=day,
    )

    eaten_totals, planned_totals, _, _ = compute_day_macros(entries)

    planned_kcal = planned_totals["energy"]
    eaten_kcal = eaten_totals["energy"]
    target = daily_target.calories

    planned_over_target = max(planned_kcal - target, 0.0)

    return {
        "target_calories": target,
        "planned_calories": planned_kcal,
        "eaten_calories": eaten_kcal,
        "planned_over_target": planned_over_target,
    }