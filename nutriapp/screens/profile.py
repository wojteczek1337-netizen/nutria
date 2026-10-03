# nutriapp/screens/profile.py
from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivy.app import App

from nutriapp.data.repositories.user_repo import (
    get_session,
    get_user_profile,
    save_user_profile,
)
from nutriapp.services.profile_service import (
    mifflin_st_jeor_bmr,
    tdee_from_bmr,
    calorie_target,
    get_effective_calories,
    get_user_targets,
)


class ProfileScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sex_menu: MDDropdownMenu | None = None
        self.activity_menu: MDDropdownMenu | None = None
        self.goal_menu: MDDropdownMenu | None = None
        self.calorie_mode_menu: MDDropdownMenu | None = None
        self.calorie_algorithm_menu: MDDropdownMenu | None = None
        self.macro_mode_menu: MDDropdownMenu | None = None

    def on_enter(self):
        App.get_running_app().set_topbar(
            title="Profil użytkownika",
            visible=True,
            show_back=False,
            back_target="home",
            right_actions=[],
        )
        self._load_profile()

    def _load_profile(self):
        app = App.get_running_app()
        session = get_session()
        profile = get_user_profile(session, user_id=app.current_user_id)
        if not profile:
            return

        ids = self.ids

        # Dane podstawowe
        ids.name_field.text = profile.name or ""
        ids.sex_field.text = "Mężczyzna" if profile.sex == "male" else "Kobieta"
        ids.age_field.text = str(profile.age_years)
        ids.height_field.text = str(profile.height_cm)
        ids.weight_field.text = str(profile.weight_kg)
        ids.activity_field.text = self._activity_label(profile.activity_level)
        ids.goal_field.text = self._goal_label(profile.goal)

        # Tryb kalorii
        ids.calorie_mode_field.text = self._calorie_mode_label(profile.calorie_mode)

        # Algorytm
        ids.calorie_algorithm_field.text = self._calorie_algorithm_label(
            profile.calorie_algorithm
        )

        # Ręczne kcal i korekta
        ids.manual_calories_field.text = (
            str(int(profile.manual_calories)) if profile.manual_calories else ""
        )
        ids.calorie_adjustment_field.text = (
            str(int(profile.calorie_adjustment)) if profile.calorie_adjustment else "0"
        )

        # Tryb makro
        ids.macro_mode_field.text = self._macro_mode_label(profile.macro_mode)

        # g/kg
        ids.protein_g_per_kg_field.text = (
            str(profile.protein_g_per_kg).replace(".", ",")
            if profile.protein_g_per_kg
            else ""
        )
        ids.fat_g_per_kg_field.text = (
            str(profile.fat_g_per_kg).replace(".", ",")
            if profile.fat_g_per_kg
            else ""
        )
        ids.carbs_g_per_kg_field.text = (
            str(profile.carbs_g_per_kg).replace(".", ",")
            if profile.carbs_g_per_kg
            else ""
        )

        # Ręczne makro
        ids.manual_protein_field.text = (
            str(int(profile.manual_protein_g)) if profile.manual_protein_g else ""
        )
        ids.manual_fat_field.text = (
            str(int(profile.manual_fat_g)) if profile.manual_fat_g else ""
        )
        ids.manual_carbs_field.text = (
            str(int(profile.manual_carbs_g)) if profile.manual_carbs_g else ""
        )

        # Podsumowanie
        self._update_summary(profile)

    def save_profile(self):
        ids = self.ids
        name = ids.name_field.text.strip() or None
        sex_text = ids.sex_field.text
        sex = "male" if sex_text == "Mężczyzna" else "female"

        age_years = int(ids.age_field.text)
        height_cm = float(ids.height_field.text)
        weight_kg = float(ids.weight_field.text)

        activity_level = self._activity_value(ids.activity_field.text)
        goal = self._goal_value(ids.goal_field.text)

        # Tryb kalorii
        calorie_mode = self._calorie_mode_value(ids.calorie_mode_field.text)

        # Algorytm
        calorie_algorithm = self._calorie_algorithm_value(
            ids.calorie_algorithm_field.text
        )

        # Ręczne kcal i korekta
        manual_calories_raw = ids.manual_calories_field.text.strip()
        manual_calories = float(manual_calories_raw) if manual_calories_raw else None

        calorie_adjustment_raw = ids.calorie_adjustment_field.text.strip()
        calorie_adjustment = (
            float(calorie_adjustment_raw) if calorie_adjustment_raw else 0.0
        )

        # Tryb makro
        macro_mode = self._macro_mode_value(ids.macro_mode_field.text)

        # g/kg
        def _parse_float(text: str) -> float | None:
            t = text.strip().replace(",", ".")
            return float(t) if t else None

        protein_g_per_kg = _parse_float(ids.protein_g_per_kg_field.text)
        fat_g_per_kg = _parse_float(ids.fat_g_per_kg_field.text)
        carbs_g_per_kg = _parse_float(ids.carbs_g_per_kg_field.text)

        # Ręczne makro
        def _parse_int(text: str) -> float | None:
            t = text.strip()
            return float(t) if t else None

        manual_protein_g = _parse_int(ids.manual_protein_field.text)
        manual_fat_g = _parse_int(ids.manual_fat_field.text)
        manual_carbs_g = _parse_int(ids.manual_carbs_field.text)

        app = App.get_running_app()
        session = get_session()

        profile = save_user_profile(
            session,
            user_id=app.current_user_id,
            name=name,
            sex=sex,
            age_years=age_years,
            height_cm=height_cm,
            weight_kg=weight_kg,
            activity_level=activity_level,
            goal=goal,
            calorie_mode=calorie_mode,
            calorie_algorithm=calorie_algorithm,
            manual_calories=manual_calories,
            calorie_adjustment=calorie_adjustment,
            macro_mode=macro_mode,
            protein_g_per_kg=protein_g_per_kg,
            fat_g_per_kg=fat_g_per_kg,
            carbs_g_per_kg=carbs_g_per_kg,
            manual_protein_g=manual_protein_g,
            manual_fat_g=manual_fat_g,
            manual_carbs_g=manual_carbs_g,
        )

        self._update_summary(profile)

    def _update_summary(self, profile):
        targets = get_user_targets(profile)
        ids = self.ids
        ids.summary_label.text = (
            f"Twoje cele: {targets['calories']:.0f} kcal | "
            f"B: {targets['protein_g']:.0f} g | "
            f"T: {targets['fat_g']:.0f} g | "
            f"W: {targets['carbs_g']:.0f} g"
        )

    # ---------- LISTY ROZWIJANE ----------

    def open_sex_menu(self):
        if not self.sex_menu:
            items = [
                {"text": "Mężczyzna", "on_release": lambda text="Mężczyzna": self._set_sex(text)},
                {"text": "Kobieta", "on_release": lambda text="Kobieta": self._set_sex(text)},
            ]
            self.sex_menu = MDDropdownMenu(
                caller=self.ids.sex_field,
                items=items,
                width=dp(220),
                position="bottom",
            )
        self.sex_menu.open()

    def _set_sex(self, text: str):
        self.ids.sex_field.text = text
        if self.sex_menu:
            self.sex_menu.dismiss()

    def open_activity_menu(self):
        if not self.activity_menu:
            items = [
                {"text": "Niska", "on_release": lambda text="Niska": self._set_activity(text)},
                {"text": "Lekka", "on_release": lambda text="Lekka": self._set_activity(text)},
                {"text": "Średnia", "on_release": lambda text="Średnia": self._set_activity(text)},
                {"text": "Wysoka", "on_release": lambda text="Wysoka": self._set_activity(text)},
                {"text": "Bardzo wysoka", "on_release": lambda text="Bardzo wysoka": self._set_activity(text)},
            ]
            self.activity_menu = MDDropdownMenu(
                caller=self.ids.activity_field,
                items=items,
                width=dp(260),
                position="bottom",
            )
        self.activity_menu.open()

    def _set_activity(self, text: str):
        self.ids.activity_field.text = text
        if self.activity_menu:
            self.activity_menu.dismiss()

    def open_goal_menu(self):
        if not self.goal_menu:
            items = [
                {"text": "Utrzymanie", "on_release": lambda text="Utrzymanie": self._set_goal(text)},
                {"text": "Redukcja", "on_release": lambda text="Redukcja": self._set_goal(text)},
                {"text": "Masa", "on_release": lambda text="Masa": self._set_goal(text)},
            ]
            self.goal_menu = MDDropdownMenu(
                caller=self.ids.goal_field,
                items=items,
                width=dp(220),
                position="bottom",
            )
        self.goal_menu.open()

    def _set_goal(self, text: str):
        self.ids.goal_field.text = text
        if self.goal_menu:
            self.goal_menu.dismiss()

    # Kalorie – tryb
    def open_calorie_mode_menu(self):
        if not self.calorie_mode_menu:
            items = [
                {"text": "Automatyczne (ze wzoru)", "on_release": lambda text="Automatyczne (ze wzoru)": self._set_calorie_mode(text)},
                {"text": "Automatyczne + makro z g/kg", "on_release": lambda text="Automatyczne + makro z g/kg": self._set_calorie_mode(text)},
                {"text": "Ręczne kcal", "on_release": lambda text="Ręczne kcal": self._set_calorie_mode(text)},
            ]
            self.calorie_mode_menu = MDDropdownMenu(
                caller=self.ids.calorie_mode_field,
                items=items,
                width=dp(260),
                position="bottom",
            )
        self.calorie_mode_menu.open()

    def _set_calorie_mode(self, text: str):
        self.ids.calorie_mode_field.text = text
        if self.calorie_mode_menu:
            self.calorie_mode_menu.dismiss()

    # Algorytm
    def open_calorie_algorithm_menu(self):
        if not self.calorie_algorithm_menu:
            items = [
                {"text": "Mifflin–St Jeor", "on_release": lambda text="Mifflin–St Jeor": self._set_calorie_algorithm(text)},
                {"text": "Harris–Benedict", "on_release": lambda text="Harris–Benedict": self._set_calorie_algorithm(text)},
            ]
            self.calorie_algorithm_menu = MDDropdownMenu(
                caller=self.ids.calorie_algorithm_field,
                items=items,
                width=dp(260),
                position="bottom",
            )
        self.calorie_algorithm_menu.open()

    def _set_calorie_algorithm(self, text: str):
        self.ids.calorie_algorithm_field.text = text
        if self.calorie_algorithm_menu:
            self.calorie_algorithm_menu.dismiss()

    # Makro – tryb
    def open_macro_mode_menu(self):
        if not self.macro_mode_menu:
            items = [
                {"text": "Makro z g/kg", "on_release": lambda text="Makro z g/kg": self._set_macro_mode(text)},
                {"text": "Ręczne makro (g)", "on_release": lambda text="Ręczne makro (g)": self._set_macro_mode(text)},
            ]
            self.macro_mode_menu = MDDropdownMenu(
                caller=self.ids.macro_mode_field,
                items=items,
                width=dp(260),
                position="bottom",
            )
        self.macro_mode_menu.open()

    def _set_macro_mode(self, text: str):
        self.ids.macro_mode_field.text = text
        if self.macro_mode_menu:
            self.macro_mode_menu.dismiss()

    # ---------- MAPOWANIE WARTOŚCI ----------

    def _activity_label(self, value: str) -> str:
        mapping = {
            "sedentary": "Niska",
            "light": "Lekka",
            "moderate": "Średnia",
            "very_active": "Wysoka",
            "extra_active": "Bardzo wysoka",
        }
        return mapping.get(value, "Średnia")

    def _activity_value(self, label: str) -> str:
        mapping = {
            "Niska": "sedentary",
            "Lekka": "light",
            "Średnia": "moderate",
            "Wysoka": "very_active",
            "Bardzo wysoka": "extra_active",
        }
        return mapping.get(label, "moderate")

    def _goal_label(self, value: str) -> str:
        mapping = {
            "maintain": "Utrzymanie",
            "lose": "Redukcja",
            "gain": "Masa",
        }
        return mapping.get(value, "Utrzymanie")

    def _goal_value(self, label: str) -> str:
        mapping = {
            "Utrzymanie": "maintain",
            "Redukcja": "lose",
            "Masa": "gain",
        }
        return mapping.get(label, "maintain")

    def _calorie_mode_label(self, value: str) -> str:
        mapping = {
            "auto": "Automatyczne (ze wzoru)",
            "auto_per_kg": "Automatyczne + makro z g/kg",
            "manual": "Ręczne kcal",
        }
        return mapping.get(value, "Automatyczne (ze wzoru)")

    def _calorie_mode_value(self, label: str) -> str:
        mapping = {
            "Automatyczne (ze wzoru)": "auto",
            "Automatyczne + makro z g/kg": "auto_per_kg",
            "Ręczne kcal": "manual",
        }
        return mapping.get(label, "auto")

    def _calorie_algorithm_label(self, value: str) -> str:
        mapping = {
            "mifflin": "Mifflin–St Jeor",
            "harris_benedict": "Harris–Benedict",
        }
        return mapping.get(value, "Mifflin–St Jeor")

    def _calorie_algorithm_value(self, label: str) -> str:
        mapping = {
            "Mifflin–St Jeor": "mifflin",
            "Harris–Benedict": "harris_benedict",
        }
        return mapping.get(label, "mifflin")

    def _macro_mode_label(self, value: str) -> str:
        mapping = {
            "per_kg": "Makro z g/kg",
            "manual": "Ręczne makro (g)",
        }
        return mapping.get(value, "Makro z g/kg")

    def _macro_mode_value(self, label: str) -> str:
        mapping = {
            "Makro z g/kg": "per_kg",
            "Ręczne makro (g)": "manual",
        }
        return mapping.get(label, "per_kg")