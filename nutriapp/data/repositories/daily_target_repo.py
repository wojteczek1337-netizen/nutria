# nutriapp/data/repositories/daily_target_repo.py
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from nutriapp.models.daily_target import DailyTarget
from nutriapp.models.user_profile import UserProfile
from nutriapp.services.profile_service import get_user_targets

def get_daily_target_for_date(
    session: Session,
    *,
    user_profile: UserProfile,
    day: date,
) -> DailyTarget | None:
    """Pobiera istniejący snapshot celu. Nie przelicza go ponownie."""
    statement = select(DailyTarget).where(
        DailyTarget.user_profile_id == user_profile.id,
        DailyTarget.date == day,
    )
    return session.execute(statement).scalar_one_or_none()


def ensure_daily_target_for_date(
    session: Session,
    *,
    user_profile: UserProfile,
    day: date,
) -> DailyTarget:
    """Zwraca istniejący cel albo tworzy go tylko przy pierwszym użyciu daty."""
    existing = get_daily_target_for_date(
        session,
        user_profile=user_profile,
        day=day,
    )
    if existing is not None:
        return existing

    targets = get_user_targets(user_profile)
    target = DailyTarget(
        user_profile_id=user_profile.id,
        date=day,
        calories=float(targets["calories"]),
        protein_g=float(targets["protein_g"]),
        fat_g=float(targets["fat_g"]),
        carbs_g=float(targets["carbs_g"]),
    )
    session.add(target)
    session.flush()
    return target