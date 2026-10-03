# nutriapp/services/diets_service.py
from datetime import date, timedelta
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from nutriapp.data.repositories.diet_repo import (
    get_session,
    get_diet_by_id,
    get_meals_for_diet_day,
    get_active_diet_for_user,
    day_has_diet_entries,
    delete_diet_entries_for_dates,
    add_diet_meals_to_calendar,
    set_active_diet,
)
from nutriapp.models.diet_plan import DietMeal
from nutriapp.services.dishes_service import compute_dish_macros


def compute_diet_day_macros(
    diet_meals: List[DietMeal],
) -> Dict[str, float]:
    """
    Oblicza makro dla jednego dnia szablonu diety.
    Uwzględnia:
    - produkty (amount_g),
    - dania (servings * makro dania).
    """
    totals = {
        "energy": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "saturated_fat": 0.0,
        "carbs": 0.0,
        "sugar": 0.0,
        "fiber": 0.0,
        "salt": 0.0,
    }

    for dm in diet_meals:
        # produkt w diecie
        if dm.product is not None and dm.amount_g:
            p = dm.product
            multiplier = dm.amount_g / 100.0

            nutrition_values = {
                "energy": p.energy_kcal_100,
                "protein": p.protein_100,
                "fat": p.fat_100,
                "saturated_fat": p.saturated_fat_100,
                "carbs": p.carbs_100,
                "sugar": p.sugar_100,
                "fiber": p.fiber_100,
                "salt": p.salt_100,
            }

            for key, value in nutrition_values.items():
                if value is not None:
                    totals[key] += value * multiplier

        # danie w diecie
        elif dm.dish is not None and dm.servings:
            dish_totals, has_data = compute_dish_macros(dm.dish)
            if not has_data:
                continue

            multiplier = dm.servings
            for key in totals.keys():
                totals[key] += dish_totals.get(key, 0.0) * multiplier

    return totals


def activate_diet(
    user_id: int,
    diet_id: int,
    start_day: int,
    start_date: Optional[date] = None,
    replace_existing: bool = False,
) -> None:
    """
    Aktywuje dietę:
    - ustawia ją jako aktywną (is_active=True, inne is_active=False),
    - zapisuje cycle_start_date i cycle_start_day,
    - opcjonalnie usuwa przyszłe wpisy z tej diety (replace_existing),
    - generuje plan w kalendarzu, korzystając z ensure_active_diet_plan().
    """
    if start_date is None:
        start_date = date.today()

    session = get_session()
    try:
        diet = get_diet_by_id(session, diet_id=diet_id, user_id=user_id)
        if diet is None:
            raise ValueError("Dieta nie istnieje")

        cycle_length = diet.cycle_length
        if cycle_length <= 0:
            raise ValueError("cycle_length musi być >= 1")

        if start_day < 1 or start_day > cycle_length:
            raise ValueError("start_day musi być w zakresie 1..cycle_length")

        # ustaw tę dietę jako aktywną (dezaktywując inne)
        set_active_diet(session, user_id=user_id, diet_id=diet_id)

        # zapisz początek cyklu
        diet.cycle_start_date = start_date
        diet.cycle_start_day = start_day
        diet.updated_at = date.today()
        session.commit()

        # opcjonalne wyczyszczenie przyszłych wpisów z diety
        if replace_existing:
            cal_days = max(diet.calendar_days, 1)
            dates = [start_date + timedelta(days=i) for i in range(cal_days)]
            delete_diet_entries_for_dates(
                session,
                user_id=user_id,
                dates=dates,
            )

        # wygeneruj plan od start_date w przód
        ensure_active_diet_plan(user_id=user_id, today=start_date)
    finally:
        session.close()


def ensure_active_diet_plan(
    user_id: int,
    today: Optional[date] = None,
) -> None:
    """
    Utrzymuje rolling plan dla aktywnej diety użytkownika.

    Dla aktywnej diety:
    - bierze diet.calendar_days,
    - zakres [today .. today + calendar_days - 1],
    - dla każdego dnia bez wpisów z diety:
        - wylicza numer dnia cyklu (modulo cycle_length),
        - pobiera DietMeal,
        - dodaje wpisy MealEntry (is_planned=True, is_diet=True, source="diet").
    """
    if today is None:
        today = date.today()

    session = get_session()
    try:
        diet = get_active_diet_for_user(session, user_id=user_id)
        if diet is None or not diet.is_active:
            return

        cal_days = max(diet.calendar_days, 1)
        cycle_length = max(diet.cycle_length, 1)

        # jeśli brak zainicjalizowanej daty startu, przyjmij today i dzień 1
        if diet.cycle_start_date is None:
            diet.cycle_start_date = today
            diet.cycle_start_day = 1
            diet.updated_at = today
            session.commit()

        start_date = today
        end_date = today + timedelta(days=cal_days - 1)

        current_date = start_date
        while current_date <= end_date:
            # nie duplikuj wpisów z diety dla danego dnia
            if day_has_diet_entries(
                session,
                user_id=user_id,
                entry_date=current_date,
            ):
                current_date += timedelta(days=1)
                continue

            # offset względem początku cyklu
            offset = (current_date - diet.cycle_start_date).days
            # zabezpieczenie – jeśli offset ujemny, nie generujemy
            if offset < 0:
                current_date += timedelta(days=1)
                continue

            day_number = ((diet.cycle_start_day - 1 + offset) % cycle_length) + 1

            diet_meals = get_meals_for_diet_day(
                session,
                diet_id=diet.id,
                day_number=day_number,
                user_id=user_id,
            )

            if diet_meals:
                add_diet_meals_to_calendar(
                    session,
                    user_id=user_id,
                    entry_date=current_date,
                    diet_meals=diet_meals,
                )

            current_date += timedelta(days=1)

        # wszystkie nowe wpisy są już commitowane w add_diet_meals_to_calendar
    finally:
        session.close()


def deactivate_diet(
    user_id: int,
    diet_id: int,
) -> None:
    """
    Dezaktywuje dietę (is_active=False).
    Na razie nie usuwa wpisów z kalendarza.
    """
    session = get_session()
    try:
        set_active_diet(session, user_id=user_id, diet_id=None)
    finally:
        session.close()