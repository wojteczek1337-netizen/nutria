# nutriapp/data/repositories/weight_repo.py
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from nutriapp.models.weight import Weight


def get_weight_for_date(
    session: Session,
    *,
    user_id: int,
    measured_on: date,
) -> Weight | None:
    statement = (
        select(Weight)
        .where(
            Weight.user_id == user_id,
            Weight.measured_on == measured_on,
        )
        .order_by(Weight.id.desc())
    )
    return session.execute(statement).scalars().first()


def list_weights(session: Session, *, user_id: int) -> list[Weight]:
    statement = (
        select(Weight)
        .where(Weight.user_id == user_id)
        .order_by(Weight.measured_on.desc(), Weight.id.desc())
    )
    return list(session.execute(statement).scalars().all())


def get_latest_weight(session: Session, *, user_id: int) -> Weight | None:
    statement = (
        select(Weight)
        .where(Weight.user_id == user_id)
        .order_by(Weight.measured_on.desc(), Weight.id.desc())
        .limit(1)
    )
    return session.execute(statement).scalars().first()


def add_weight(
    session: Session,
    *,
    user_id: int,
    measured_on: date,
    weight_kg: float,
) -> Weight:
    record = Weight(
        user_id=user_id,
        measured_on=measured_on,
        weight_kg=weight_kg,
    )
    session.add(record)
    session.flush()
    return record


def delete_weight(
    session: Session,
    *,
    weight_id: int,
    user_id: int,
) -> bool:
    record = session.get(Weight, int(weight_id))
    if record is None:
        return False
    if int(record.user_id) != int(user_id):
        return False

    session.delete(record)
    session.flush()
    return True