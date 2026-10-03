# nutriapp/services/profile_service.py
from typing import Literal

from nutriapp.models.user_profile import UserProfile


Sex = Literal["male", "female"]
ActivityLevel = Literal[
    "sedentary",      # 1.2
    "light",          # 1.375
    "moderate",       # 1.55
    "very_active",    # 1.725
    "extra_active",   # 1.9
]
Goal = Literal["maintain", "lose", "gain"]


# ---------- ALGORYTMY BMR ----------

def mifflin_st_jeor_bmr(
    sex: Sex,
    weight_kg: float,
    height_cm: float,
    age_years: int,
) -> float:
    """Zwraca BMR wg Mifflin–St Jeor (kcal/dzień)."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age_years
    if sex == "male":
        return base + 5
    else:
        return base - 161


def harris_benedict_bmr(
    sex: Sex,
    weight_kg: float,
    height_cm: float,
    age_years: int,
) -> float:
    """
    Zwraca BMR wg wzoru Harrisa-Benedicta (zrewidowanego).
    Na razie implementacja przykładowa – można doprecyzować współczynniki.
    """
    if sex == "male":
        bmr = 88.362 + 13.397 * weight_kg + 4.799 * height_cm - 5.677 * age_years
    else:
        bmr = 447.593 + 9.247 * weight_kg + 3.098 * height_cm - 4.330 * age_years
    return bmr


def compute_bmr(
    algorithm: str,
    sex: Sex,
    weight_kg: float,
    height_cm: float,
    age_years: int,
) -> float:
    """
    Wybiera algorytm BMR na podstawie nazwy.
    Dostępne: "mifflin", "harris_benedict".
    """
    if algorithm == "harris_benedict":
        return harris_benedict_bmr(sex, weight_kg, height_cm, age_years)
    # domyślnie Mifflin–St Jeor
    return mifflin_st_jeor_bmr(sex, weight_kg, height_cm, age_years)


# ---------- TDEE I CELE KALORYCZNE ----------

_ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}


def tdee_from_bmr(bmr: float, activity_level: ActivityLevel) -> float:
    """Total Daily Energy Expenditure = BMR * współczynnik aktywności."""
    factor = _ACTIVITY_FACTORS[activity_level]
    return bmr * factor


def calorie_target(tdee: float, goal: Goal, delta: int = 500) -> float:
    """
    Cel kaloryczny:
    - maintain: TDEE
    - lose: TDEE - delta (np. 500 kcal deficytu)
    - gain: TDEE + delta (np. 500 kcal surplus)
    """
    if goal == "maintain":
        return tdee
    elif goal == "lose":
        return tdee - delta
    else:  # "gain"
        return tdee + delta


# ---------- MAKRA ----------

def macros_from_per_kg(
    weight_kg: float,
    protein_g_per_kg: float | None,
    fat_g_per_kg: float | None,
    carbs_g_per_kg: float | None,
    total_calories: float | None = None,
) -> tuple[float, float, float]:
    """
    Zwraca (protein_g, fat_g, carbs_g) na podstawie g/kg.
    Jeśli carbs_g_per_kg jest None, a total_calories jest podane,
    węgle są liczone jako „reszta z kcal".
    """
    protein_g = (protein_g_per_kg or 0.0) * weight_kg
    fat_g = (fat_g_per_kg or 0.0) * weight_kg

    if carbs_g_per_kg is not None:
        carbs_g = carbs_g_per_kg * weight_kg
    elif total_calories is not None:
        # kcal = 4*P + 9*F + 4*C  => C = (kcal - 4P - 9F) / 4
        carbs_g = max((total_calories - 4 * protein_g - 9 * fat_g) / 4, 0.0)
    else:
        carbs_g = 0.0

    return protein_g, fat_g, carbs_g


# ---------- WYSOKIEGO POZIOMU: CELE UŻYTKOWNIKA ----------

def get_effective_calories(profile: UserProfile) -> float:
    """
    Zwraca efektywne dzienne kcal dla profilu,
    z uwzględnieniem trybu, algorytmu i korekty.
    """
    if profile.calorie_mode == "manual":
        # Jeśli brak ręcznych kcal, fallback na auto
        if profile.manual_calories is not None:
            return profile.manual_calories

    # Tryby "auto" i "auto_per_kg" – liczone z BMR
    bmr = compute_bmr(
        algorithm=profile.calorie_algorithm,
        sex=profile.sex,
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        age_years=profile.age_years,
    )

    tdee = tdee_from_bmr(bmr, profile.activity_level)
    base_target = calorie_target(tdee, profile.goal)

    # Korekta (deficyt/nadwyżka) – stosujemy w "auto_per_kg" i opcjonalnie w "auto"
    return base_target + (profile.calorie_adjustment or 0.0)


def get_user_targets(profile: UserProfile) -> dict:
    """
    Zwraca dict z docelowymi kcal i makroskładnikami dla profilu:
    {
        "calories": float,
        "protein_g": float,
        "fat_g": float,
        "carbs_g": float,
    }
    """
    calories = get_effective_calories(profile)

    if profile.macro_mode == "manual":
        protein_g = profile.manual_protein_g or 0.0
        fat_g = profile.manual_fat_g or 0.0
        carbs_g = profile.manual_carbs_g or 0.0
    else:
        # macro_mode == "per_kg"
        protein_g, fat_g, carbs_g = macros_from_per_kg(
            weight_kg=profile.weight_kg,
            protein_g_per_kg=profile.protein_g_per_kg,
            fat_g_per_kg=profile.fat_g_per_kg,
            carbs_g_per_kg=profile.carbs_g_per_kg,
            total_calories=calories,
        )

    return {
        "calories": calories,
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g,
    }