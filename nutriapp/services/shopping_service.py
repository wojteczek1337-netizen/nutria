# nutriapp/services/shopping_service.py
from collections import OrderedDict
from datetime import date

from sqlalchemy.orm import joinedload

from nutriapp.data.repositories.shopping_repo import (
    add_item,
    create_list,
    delete_old_lists,
    get_list_by_id,
)
from nutriapp.models.dish import Dish
from nutriapp.models.dish_item import DishItem
from nutriapp.models.meal_calendar import MealEntry


def _product_key(product_id: int | None, name: str) -> tuple:
    """
    Produkty z product_id łączymy po ID.
    Pozycje bez ID — po nazwie.
    """
    if product_id is not None:
        return ("product", product_id)

    return ("name", name.casefold().strip())


def collect_products_from_calendar(
    session,
    *,
    user_id: int,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Pobiera planowane wpisy kalendarza z zakresu inclusive:
    start_date <= entry_date <= end_date.

    Obsługuje:
    - wpisy bezpośrednio wskazujące produkt,
    - wpisy wskazujące danie,
    - rozbijanie dań na składniki,
    - sumowanie tych samych produktów.
    """
    if end_date < start_date:
        raise ValueError(
            "Data końcowa nie może być wcześniejsza od początkowej."
        )

    entries = (
        session.query(MealEntry)
        .options(
            joinedload(MealEntry.product),
            joinedload(MealEntry.dish)
            .joinedload(Dish.items)
            .joinedload(DishItem.product),
        )
        .filter(
            MealEntry.user_id == user_id,
            MealEntry.entry_date >= start_date,
            MealEntry.entry_date <= end_date,
            MealEntry.is_planned.is_(True),
        )
        .order_by(
            MealEntry.entry_date.asc(),
            MealEntry.sort_order.asc(),
            MealEntry.id.asc(),
        )
        .all()
    )

    aggregated: OrderedDict[tuple, dict] = OrderedDict()

    def add_product(product, quantity: float, source: str):
        if product is None or quantity <= 0:
            return

        product_name = product.name or "Produkt"
        key = _product_key(product.id, product_name)

        if key not in aggregated:
            aggregated[key] = {
                "product_id": product.id,
                "name": product_name,
                "quantity": 0.0,
                "unit": "g",
                "source": source,
            }

        aggregated[key]["quantity"] += quantity

    for entry in entries:
        # Bezpośredni wpis produktu.
        if entry.product is not None and entry.amount_g is not None:
            add_product(
                entry.product,
                float(entry.amount_g),
                "calendar",
            )
            continue

        # Wpis dania rozbijamy na jego składniki.
        if entry.dish is not None:
            servings = float(entry.servings or 1.0)

            if servings <= 0:
                continue

            for dish_item in entry.dish.items:
                if dish_item.product is None:
                    continue

                if dish_item.amount_g is None:
                    continue

                quantity = float(dish_item.amount_g) * servings

                add_product(
                    dish_item.product,
                    quantity,
                    "calendar_dish",
                )

    return list(aggregated.values())


def generate_shopping_list(
    session,
    *,
    user_id: int,
    start_date: date,
    end_date: date,
    name: str | None = None,
) -> int:
    """
    Tworzy i zapisuje listę zakupów z planowanych wpisów kalendarza.

    Zakres dat jest obustronnie domknięty:
    - start_date jest uwzględniona,
    - end_date jest uwzględniona.
    """
    if end_date < start_date:
        raise ValueError(
            "Data końcowa nie może być wcześniejsza od początkowej."
        )

    items = collect_products_from_calendar(
        session,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    if name is None:
        name = (
            f"Zakupy {start_date.strftime('%d.%m')}–"
            f"{end_date.strftime('%d.%m')}"
        )

    shopping_list = create_list(
        session,
        user_id=user_id,
        name=name,
        start_date=start_date,
        end_date=end_date,
    )

    for item in items:
        add_item(
            session,
            shopping_list_id=shopping_list.id,
            name=item["name"],
            quantity=item["quantity"],
            unit=item["unit"],
            product_id=item["product_id"],
            source=item["source"],
        )

    session.commit()
    session.refresh(shopping_list)

    return shopping_list.id


def add_manual_item(
    session,
    *,
    user_id: int,
    shopping_list_id: int,
    name: str,
    quantity: float,
    unit: str = "szt.",
) -> bool:
    shopping_list = get_list_by_id(
        session,
        shopping_list_id=shopping_list_id,
        user_id=user_id,
    )

    if shopping_list is None:
        return False

    clean_name = name.strip()
    clean_unit = unit.strip() or "szt."

    if not clean_name or quantity <= 0:
        return False

    add_item(
        session,
        shopping_list_id=shopping_list_id,
        name=clean_name,
        quantity=quantity,
        unit=clean_unit,
        source="manual",
    )

    session.commit()
    return True


def cleanup_old_shopping_lists(
    session,
    *,
    user_id: int,
    older_than_days: int = 90,
) -> int:
    return delete_old_lists(
        session,
        user_id=user_id,
        older_than_days=older_than_days,
    )