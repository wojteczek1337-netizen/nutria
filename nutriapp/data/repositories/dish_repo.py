from datetime import datetime


from sqlalchemy.orm import Session, joinedload


from nutriapp.data.database import SessionLocal
from nutriapp.models.dish import Dish
from nutriapp.models.dish_item import DishItem
from nutriapp.models.product import Product


def get_session() -> Session:
    return SessionLocal()


def get_dishes_for_user(session: Session, user_id: int) -> list[Dish]:
    return (
        session.query(Dish)
        .filter(Dish.user_id == user_id)
        .order_by(Dish.name.asc())
        .all()
    )


def get_dish_by_id(
    session: Session,
    dish_id: int,
    user_id: int,
) -> Dish | None:
    return (
        session.query(Dish)
        .filter(
            Dish.id == dish_id,
            Dish.user_id == user_id,
        )
        .first()
    )


def get_dish_with_items(
    session: Session,
    dish_id: int,
    user_id: int,
) -> Dish | None:
    return (
        session.query(Dish)
        .options(
            joinedload(Dish.items).joinedload(DishItem.product)
        )
        .filter(
            Dish.id == dish_id,
            Dish.user_id == user_id,
        )
        .first()
    )


def add_or_update_dish(
    session: Session,
    *,
    user_id: int,
    dish_id: int | None = None,
    name: str,
    description: str | None = None,
    recipe_text: str | None = None,
    youtube_url: str | None = None,
) -> Dish:
    if dish_id is not None:
        dish = get_dish_by_id(
            session,
            dish_id=dish_id,
            user_id=user_id,
        )

        if dish is None:
            dish = Dish(user_id=user_id)
    else:
        dish = Dish(user_id=user_id)

    dish.name = name
    dish.description = description
    dish.recipe_text = recipe_text
    dish.youtube_url = youtube_url
    dish.updated_at = datetime.utcnow()

    session.add(dish)
    session.commit()
    session.refresh(dish)

    return dish


def delete_dish(
    session: Session,
    *,
    dish_id: int,
    user_id: int,
) -> bool:
    dish = get_dish_by_id(
        session,
        dish_id=dish_id,
        user_id=user_id,
    )

    if dish is None:
        return False

    session.delete(dish)
    session.commit()

    return True


def get_products_for_user_basic(
    session: Session,
    user_id: int,
) -> list[Product]:
    return (
        session.query(Product)
        .filter(Product.user_id == user_id)
        .order_by(Product.name.asc())
        .all()
    )


def get_dish_items(
    session: Session,
    *,
    dish_id: int,
    user_id: int,
) -> list[DishItem]:
    dish = get_dish_by_id(
        session,
        dish_id=dish_id,
        user_id=user_id,
    )

    if dish is None:
        return []

    return (
        session.query(DishItem)
        .options(joinedload(DishItem.product))
        .filter(DishItem.dish_id == dish_id)
        .order_by(DishItem.id.asc())
        .all()
    )


def add_dish_item(
    session: Session,
    *,
    dish_id: int,
    user_id: int,
    product_id: int,
    amount_g: float,
) -> DishItem | None:
    dish = get_dish_by_id(
        session,
        dish_id=dish_id,
        user_id=user_id,
    )

    if dish is None:
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

    item = DishItem(
        dish_id=dish_id,
        product_id=product_id,
        amount_g=amount_g,
        updated_at=datetime.utcnow(),
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


def replace_dish_items(
    session: Session,
    *,
    dish_id: int,
    user_id: int,
    items: list[dict],
) -> bool:
    dish = get_dish_by_id(
        session,
        dish_id=dish_id,
        user_id=user_id,
    )

    if dish is None:
        return False

    old_items = (
        session.query(DishItem)
        .filter(DishItem.dish_id == dish_id)
        .all()
    )

    for item in old_items:
        session.delete(item)

    for item_data in items:
        product_id = item_data["product_id"]
        amount_g = item_data["amount_g"]

        product = (
            session.query(Product)
            .filter(
                Product.id == product_id,
                Product.user_id == user_id,
            )
            .first()
        )

        if product is None:
            continue

        session.add(
            DishItem(
                dish_id=dish_id,
                product_id=product_id,
                amount_g=amount_g,
                updated_at=datetime.utcnow(),
            )
        )

    session.commit()
    return True


def delete_dish_item(
    session: Session,
    *,
    dish_item_id: int,
    user_id: int,
) -> bool:
    item = (
        session.query(DishItem)
        .join(Dish, DishItem.dish_id == Dish.id)
        .filter(
            DishItem.id == dish_item_id,
            Dish.user_id == user_id,
        )
        .first()
    )

    if item is None:
        return False

    session.delete(item)
    session.commit()

    return True


def search_dishes_for_user(
    session: Session,
    user_id: int,
    query: str,
) -> list[Dish]:
    """
    Wyszukaj dania użytkownika po nazwie (contains, case-insensitive).
    Query może być puste – wtedy zwraca wszystkie dania.
    """
    q = session.query(Dish).filter(Dish.user_id == user_id)

    if query and query.strip():
        search = f"%{query.strip().lower()}%"
        q = q.filter(Dish.name.ilike(search))

    return q.order_by(Dish.name.asc()).all()