# nutriapp/services/points_service.py
"""Punkty za trafienie w dzienny cel kalorii, białka i tłuszczu.

Odchylenie to |zjedzone - cel| / cel. Progi są domknięte z prawej:
3% kalorii daje jeszcze 35 pkt, a wartość powyżej 3% do 5% daje 31.
Dzień bez zjedzonych posiłków nie dostaje punktów.
"""

from collections import defaultdict
from datetime import date, datetime

from sqlalchemy.orm import Session

from nutriapp.data.repositories.calendar_repo import get_entries_for_range
from nutriapp.data.repositories.daily_target_repo import ensure_daily_target_for_date
from nutriapp.data.repositories.points_repo import (
    delete_points_outside_dates,
    list_daily_points,
    list_eaten_dates,
    totals_by_user,
    upsert_daily_points,
)
from nutriapp.data.repositories.user_repo import get_user_profile, list_users
from nutriapp.models.daily_points import DailyPoints
from nutriapp.services.calendar_service import compute_day_macros

# (górna granica odchylenia w procentach włącznie, punkty)
CALORIE_BANDS = (
    (3, 35),
    (5, 31),
    (8, 27),
    (12, 20),
    (20, 10),
)
PROTEIN_BANDS = (
    (5, 8),
    (10, 6),
    (20, 4),
    (30, 2),
)
FAT_BANDS = (
    (7, 7),
    (15, 5),
    (30, 3),
)


def deviation_percent(actual: float, target: float) -> float | None:
    """Zwraca odchylenie w procentach celu. Brak celu daje None."""
    if target <= 0:
        return None
    # Cztery miejsca po przecinku zdejmują szum float przy dokładnej granicy,
    # np. 10% liczone jako 10.00000000000001.
    return round(abs(actual - target) / target * 100.0, 4)


def points_for_deviation(percent: float | None, bands: tuple[tuple[int, int], ...]) -> int:
    if percent is None:
        return 0
    for limit, points in bands:
        if percent <= limit:
            return points
    return 0


def score_day(
    *,
    calories: float,
    calorie_target: float,
    protein: float,
    protein_target: float,
    fat: float,
    fat_target: float,
) -> tuple[int, int, int]:
    calorie_points = points_for_deviation(
        deviation_percent(calories, calorie_target),
        CALORIE_BANDS,
    )
    protein_points = points_for_deviation(
        deviation_percent(protein, protein_target),
        PROTEIN_BANDS,
    )
    fat_points = points_for_deviation(
        deviation_percent(fat, fat_target),
        FAT_BANDS,
    )
    return calorie_points, protein_points, fat_points


def format_points(value: int) -> str:
    count = abs(int(value))
    if count == 1:
        word = "punkt"
    elif 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        word = "punkty"
    else:
        word = "punktów"
    return f"{int(value)} {word}"


def refresh_all_points(session: Session, *, today: date | None = None) -> None:
    """Przelicza punkty wszystkich użytkowników do podanego dnia włącznie."""
    day = today or date.today()
    for user in list_users(session):
        _refresh_user_points(session, user_id=user.id, today=day)
    session.commit()


def refresh_user_points(
    session: Session,
    *,
    user_id: int,
    today: date | None = None,
) -> list[DailyPoints]:
    """Przelicza dni jednego użytkownika i zwraca historię od najnowszej."""
    _refresh_user_points(session, user_id=user_id, today=today or date.today())
    session.commit()
    return list_daily_points(session, user_id=user_id)


def user_point_totals(session: Session) -> dict[int, int]:
    return totals_by_user(session)


def _refresh_user_points(session: Session, *, user_id: int, today: date) -> None:
    profile = get_user_profile(session, user_id=user_id)
    eaten_dates = [
        day for day in list_eaten_dates(session, user_id=user_id) if day <= today
    ]
    if profile is None or not eaten_dates:
        delete_points_outside_dates(session, user_id=user_id, keep_dates=set())
        return

    entries = get_entries_for_range(
        session,
        user_id=user_id,
        start_date=min(eaten_dates),
        end_date=today,
    )
    entries_by_date = defaultdict(list)
    for entry in entries:
        entries_by_date[entry.entry_date].append(entry)

    kept_dates = set()
    for day in eaten_dates:
        target = ensure_daily_target_for_date(
            session,
            user_profile=profile,
            day=day,
        )
        eaten_totals, _planned, has_eaten, _has_planned = compute_day_macros(
            entries_by_date.get(day, [])
        )
        if not has_eaten:
            continue

        calorie_points, protein_points, fat_points = score_day(
            calories=eaten_totals["energy"],
            calorie_target=float(target.calories),
            protein=eaten_totals["protein"],
            protein_target=float(target.protein_g),
            fat=eaten_totals["fat"],
            fat_target=float(target.fat_g),
        )
        upsert_daily_points(
            session,
            user_id=user_id,
            scored_on=day,
            calorie_points=calorie_points,
            protein_points=protein_points,
            fat_points=fat_points,
            updated_at=datetime.utcnow(),
        )
        kept_dates.add(day)

    delete_points_outside_dates(
        session,
        user_id=user_id,
        keep_dates=kept_dates,
    )
