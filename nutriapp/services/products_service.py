# nutriapp/services/products_service.py

from sqlalchemy.orm import Session

from nutriapp.data.repositories.product_repo import (
    get_products_for_user,
    get_product_by_id,
    add_or_update_manual_product,
    delete_product,
)
from nutriapp.models.product import Product


def list_user_products(session: Session, user_id: int) -> list[Product]:
    """
    Zwraca listę produktów użytkownika, posortowaną po nazwie.
    Prosta nakładka na repozytorium – miejsce na przyszłe reguły biznesowe.
    """
    return get_products_for_user(session, user_id=user_id)


def get_user_product(
    session: Session,
    user_id: int,
    product_id: int,
) -> Product | None:
    """
    Pobierz pojedynczy produkt użytkownika.
    """
    return get_product_by_id(session, product_id=product_id, user_id=user_id)


def save_manual_product(
    session: Session,
    *,
    user_id: int,
    product_id: int | None,
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
    """
    Utwórz lub zaktualizuj ręcznie dodany produkt użytkownika.

    Na razie deleguje do repozytorium; tu można dodać walidacje/normalizacje.
    """
    name = (name or "").strip()
    if not name:
        raise ValueError("Nazwa produktu nie może być pusta.")

    return add_or_update_manual_product(
        session,
        user_id=user_id,
        product_id=product_id,
        name=name,
        brand=(brand or None),
        quantity_text=(quantity_text or None),
        quantity_g=quantity_g,
        energy_kcal_100=energy_kcal_100,
        protein_100=protein_100,
        fat_100=fat_100,
        saturated_fat_100=saturated_fat_100,
        carbs_100=carbs_100,
        fiber_100=fiber_100,
        sugar_100=sugar_100,
        salt_100=salt_100,
    )


def delete_user_product(
    session: Session,
    *,
    user_id: int,
    product_id: int,
) -> bool:
    """
    Usuń produkt użytkownika (jeśli istnieje).
    """
    return delete_product(
        session,
        product_id=product_id,
        user_id=user_id,
    )