# nutriapp/data/repositories/points_repo.py
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from nutriapp.models.daily_points import DailyPoints
from nutriapp.models.meal_calendar import MealEntry


def list_eaten_dates(session: Session, *, user_id: int) -> list[date]:
    rows = (
        session.query(MealEntry.entry_date)
        .filter(
            MealEntry.user_id == user_id,
            MealEntry.is_eaten.is_(True),
        )
        .distinct()
        .all()
    )
    return sorted(day for (day,) in rows)


def upsert_daily_points(
    session: Session,
    *,
    user_id: int,
    scored_on: date,
    calorie_points: int,
    protein_points: int,
    fat_points: int,
    updated_at: datetime,
) -> DailyPoints:
    row = (
        session.query(DailyPoints)
        .filter(
            DailyPoints.user_id == user_id,
            DailyPoints.scored_on == scored_on,
        )
        .one_or_none()
    )
    if row is None:
        row = DailyPoints(user_id=user_id, scored_on=scored_on)
        session.add(row)

    row.calorie_points = calorie_points
    row.protein_points = protein_points
    row.fat_points = fat_points
    row.updated_at = updated_at
    return row


def delete_points_outside_dates(
    session: Session,
    *,
    user_id: int,
    keep_dates: set[date],
) -> None:
    query = session.query(DailyPoints).filter(DailyPoints.user_id == user_id)
    if keep_dates:
        query = query.filter(DailyPoints.scored_on.notin_(keep_dates))
    query.delete(synchronize_session=False)


def list_daily_points(session: Session, *, user_id: int) -> list[DailyPoints]:
    return (
        session.query(DailyPoints)
        .filter(DailyPoints.user_id == user_id)
        .order_by(DailyPoints.scored_on.desc(), DailyPoints.id.desc())
        .all()
    )


def totals_by_user(session: Session) -> dict[int, int]:
    total = (
        DailyPoints.calorie_points
        + DailyPoints.protein_points
        + DailyPoints.fat_points
    )
    rows = (
        session.query(DailyPoints.user_id, func.sum(total))
        .group_by(DailyPoints.user_id)
        .all()
    )
    return {user_id: int(points or 0) for user_id, points in rows}
