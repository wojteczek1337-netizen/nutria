from sqlalchemy.orm import Session


from nutriapp.data.database import SessionLocal
from nutriapp.models.product import Product


def get_session() -> Session:
    return SessionLocal()


def get_products_for_user(session: Session, user_id: int) -> list[Product]:
    return (
        session.query(Product)
        .filter(Product.user_id == user_id)
        .order_by(Product.name.asc())
        .all()
    )


def get_product_by_id(session: Session, product_id: int, user_id: int) -> Product | None:
    return (
        session.query(Product)
        .filter(Product.id == product_id, Product.user_id == user_id)
        .first()
    )


def add_or_update_manual_product(
    session: Session,
    *,
    user_id: int,
    product_id: int | None = None,
    name: str,
    brand: str | None,
    quantity_text: str | None,
    quantity_g: float | None,
    energy_kcal_100: float | None,
    protein_100: float | None,
    fat_100: float | None,
    saturated_fat_100: float | None,
    carbs_100: float | None,
    fiber_100: float | None,
    sugar_100: float | None,
    salt_100: float | None,
) -> Product:
    if product_id is not None:
        product = get_product_by_id(session, product_id=product_id, user_id=user_id)
        if product is None:
            product = Product(user_id=user_id, source="manual")
    else:
        product = Product(user_id=user_id, source="manual")

    product.name = name
    product.brand = brand
    product.quantity_text = quantity_text
    product.quantity_g = quantity_g

    product.energy_kcal_100 = energy_kcal_100
    product.protein_100 = protein_100
    product.fat_100 = fat_100
    product.saturated_fat_100 = saturated_fat_100
    product.carbs_100 = carbs_100
    product.fiber_100 = fiber_100
    product.sugar_100 = sugar_100
    product.salt_100 = salt_100

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def delete_product(session: Session, *, product_id: int, user_id: int) -> bool:
    product = get_product_by_id(session, product_id=product_id, user_id=user_id)
    if product is None:
        return False

    session.delete(product)
    session.commit()
    return True


def search_products_for_user(
    session: Session,
    user_id: int,
    query: str,
) -> list[Product]:
    """
    Wyszukaj produkty użytkownika po nazwie (contains, case-insensitive).
    Query może być puste – wtedy zwraca wszystkie produkty.
    """
    q = session.query(Product).filter(Product.user_id == user_id)

    if query and query.strip():
        search = f"%{query.strip().lower()}%"
        q = q.filter(Product.name.ilike(search))

    return q.order_by(Product.name.asc()).all()