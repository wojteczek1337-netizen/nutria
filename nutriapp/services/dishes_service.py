from typing import Dict, Tuple

from nutriapp.models.dish import Dish


def compute_dish_macros(dish: Dish) -> Tuple[Dict[str, float], bool]:
    """
    Oblicza makro całego dania na podstawie jego składników (DishItem + Product).

    Zwraca:
    - totals: słownik z kluczami:
      'energy', 'protein', 'fat', 'saturated_fat',
      'carbs', 'sugar', 'fiber', 'salt'
    - has_nutrition_data: True, jeśli przynajmniej jeden składnik ma dane odżywcze.
    """

    totals: Dict[str, float] = {
        "energy": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "saturated_fat": 0.0,
        "carbs": 0.0,
        "sugar": 0.0,
        "fiber": 0.0,
        "salt": 0.0,
    }

    has_nutrition_data = False

    if not dish.items:
        return totals, False

    for item in dish.items:
        product = getattr(item, "product", None)

        if product is None:
            continue

        if item.amount_g is None:
            continue

        multiplier = item.amount_g / 100.0

        nutrition_values = {
            "energy": product.energy_kcal_100,
            "protein": product.protein_100,
            "fat": product.fat_100,
            "saturated_fat": product.saturated_fat_100,
            "carbs": product.carbs_100,
            "sugar": product.sugar_100,
            "fiber": product.fiber_100,
            "salt": product.salt_100,
        }

        for key, value in nutrition_values.items():
            if value is not None:
                totals[key] += value * multiplier
                has_nutrition_data = True

    return totals, has_nutrition_data