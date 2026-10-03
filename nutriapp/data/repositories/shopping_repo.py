# nutriapp/data/repositories/shopping_repo.py
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from nutriapp.data.database import SessionLocal
from nutriapp.models.shopping_list import ShoppingItem, ShoppingList


RETENTION_DAYS = 90


def get_session() -> Session:
    return SessionLocal()


def get_list_by_id(
    session: Session,
    *,
    shopping_list_id: int,
    user_id: int,
) -> ShoppingList | None:
    return (
        session.query(ShoppingList)
        .options(
            joinedload(ShoppingList.items).joinedload(ShoppingItem.product),
        )
        .filter(
            ShoppingList.id == shopping_list_id,
            ShoppingList.user_id == user_id,
        )
        .first()
    )


def list_for_user(
    session: Session,
    *,
    user_id: int,
) -> list[ShoppingList]:
    return (
        session.query(ShoppingList)
        .filter(ShoppingList.user_id == user_id)
        .order_by(ShoppingList.created_at.desc())
        .all()
    )


def create_list(
    session: Session,
    *,
    user_id: int,
    name: str,
    start_date: date,
    end_date: date,
) -> ShoppingList:
    shopping_list = ShoppingList(
        user_id=user_id,
        name=name,
        start_date=start_date,
        end_date=end_date,
    )
    session.add(shopping_list)
    session.flush()
    return shopping_list


def add_item(
    session: Session,
    *,
    shopping_list_id: int,
    name: str,
    quantity: float,
    unit: str = "g",
    product_id: int | None = None,
    source: str = "manual",
) -> ShoppingItem:
    item = ShoppingItem(
        shopping_list_id=shopping_list_id,
        product_id=product_id,
        name=name,
        quantity=quantity,
        unit=unit,
        source=source,
    )
    session.add(item)
    session.flush()
    return item


def set_item_bought(
    session: Session,
    *,
    item_id: int,
    shopping_list_id: int,
    user_id: int,
    is_bought: bool,
) -> bool:
    item = (
        session.query(ShoppingItem)
        .join(ShoppingList)
        .filter(
            ShoppingItem.id == item_id,
            ShoppingItem.shopping_list_id == shopping_list_id,
            ShoppingList.user_id == user_id,
        )
        .first()
    )
    if item is None:
        return False

    item.is_bought = is_bought
    item.updated_at = datetime.utcnow()
    session.commit()
    return True


def delete_item(
    session: Session,
    *,
    item_id: int,
    shopping_list_id: int,
    user_id: int,
) -> bool:
    item = (
        session.query(ShoppingItem)
        .join(ShoppingList)
        .filter(
            ShoppingItem.id == item_id,
            ShoppingItem.shopping_list_id == shopping_list_id,
            ShoppingList.user_id == user_id,
        )
        .first()
    )
    if item is None:
        return False

    session.delete(item)
    session.commit()
    return True


def delete_list(
    session: Session,
    *,
    shopping_list_id: int,
    user_id: int,
) -> bool:
    shopping_list = (
        session.query(ShoppingList)
        .filter(
            ShoppingList.id == shopping_list_id,
            ShoppingList.user_id == user_id,
        )
        .first()
    )
    if shopping_list is None:
        return False

    session.delete(shopping_list)
    session.commit()
    return True


def delete_old_lists(
    session: Session,
    *,
    user_id: int,
    older_than_days: int = RETENTION_DAYS,
) -> int:
    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    deleted = (
        session.query(ShoppingList)
        .filter(
            ShoppingList.user_id == user_id,
            ShoppingList.created_at < cutoff,
        )
        .delete(synchronize_session=False)
    )
    session.commit()
    return deleted