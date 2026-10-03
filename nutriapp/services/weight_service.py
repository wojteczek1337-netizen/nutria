# nutriapp/services/weight_service.py
from datetime import date

from sqlalchemy.orm import Session

from nutriapp.data.repositories.user_repo import get_user_profile
from nutriapp.data.repositories.weight_repo import (
    add_weight,
    delete_weight,
    get_latest_weight,
    list_weights,
)


def _validate_weight(weight_kg: float) -> float:
    try:
        value = float(weight_kg)
    except (TypeError, ValueError) as exc:
        raise ValueError("Waga musi być liczbą.") from exc

    if value <= 0 or value > 500:
        raise ValueError("Podaj wagę większą od 0 i nie większą niż 500 kg.")
    return value


def _validate_date(measured_on: date) -> date:
    if not isinstance(measured_on, date):
        raise ValueError("Data pomiaru jest nieprawidłowa.")
    return measured_on


def sync_profile_with_latest_weight(
    session: Session,
    *,
    user_id: int,
):
    profile = get_user_profile(session, user_id=user_id)
    if profile is None:
        return None

    latest = get_latest_weight(session, user_id=user_id)
    if latest is not None:
        profile.weight_kg = latest.weight_kg

    session.flush()
    return profile


def create_weight_measurement(
    session: Session,
    *,
    user_id: int,
    measured_on: date,
    weight_kg: float,
):
    record = add_weight(
        session,
        user_id=user_id,
        measured_on=_validate_date(measured_on),
        weight_kg=_validate_weight(weight_kg),
    )
    profile = sync_profile_with_latest_weight(session, user_id=user_id)
    return record, profile


def remove_weight_measurement(
    session: Session,
    *,
    user_id: int,
    weight_id: int,
) -> bool:
    deleted = delete_weight(
        session,
        weight_id=int(weight_id),
        user_id=int(user_id),
    )
    if not deleted:
        return False

    sync_profile_with_latest_weight(session, user_id=user_id)
    return True


def get_weight_history(
    session: Session,
    *,
    user_id: int,
):
    return list_weights(session, user_id=user_id)