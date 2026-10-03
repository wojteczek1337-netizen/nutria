from kivy.app import App
from kivy.properties import BooleanProperty
from kivymd.uix.screen import MDScreen


from nutriapp.data.repositories.dish_repo import (
    delete_dish,
    get_dish_with_items,
    get_session,
)
from nutriapp.services.dishes_service import compute_dish_macros



class DishDetailsScreen(MDScreen):
    confirm_delete_visible = BooleanProperty(False)


    def on_enter(self):
        self.confirm_delete_visible = False

        app = App.get_running_app()

        app.set_topbar(
            title="Szczegóły dania",
            visible=True,
            show_back=True,
            back_target="dishes",
        )

        dish_id = app.selected_dish_id

        if not dish_id:
            self._clear_fields()
            return

        session = get_session()

        try:
            dish = get_dish_with_items(
                session,
                dish_id=dish_id,
                user_id=app.current_user_id,
            )
        finally:
            session.close()

        if dish is None:
            self._clear_fields()
            self.ids.name_value.text = "Nie znaleziono dania"
            return

        self.ids.name_value.text = dish.name or "-"
        self.ids.description_value.text = dish.description or "-"
        self.ids.recipe_value.text = dish.recipe_text or "-"
        self.ids.youtube_value.text = dish.youtube_url or "-"

        ingredients_text = self._build_ingredients_text(dish)
        macros_text = self._build_macros_text(dish)

        self.ids.ingredients_value.text = ingredients_text
        self.ids.macros_value.text = macros_text


    def _build_ingredients_text(self, dish):
        if not dish.items:
            return "Brak składników"

        lines = []

        for item in dish.items:
            if item.product is None:
                continue

            product_name = item.product.name or "Nieznany produkt"
            amount_text = self._fmt(item.amount_g)

            if item.product.brand:
                product_name = (
                    f"{product_name} ({item.product.brand})"
                )

            lines.append(
                f"- {product_name}: {amount_text} g"
            )

        if not lines:
            return "Brak składników"

        return "\n".join(lines)


    def _build_macros_text(self, dish):
        totals, has_nutrition_data = compute_dish_macros(dish)

        if not has_nutrition_data:
            return "Brak danych odżywczych dla składników"

        return (
            f"Kalorie: {self._fmt(totals['energy'])} kcal\n"
            f"Białko: {self._fmt(totals['protein'])} g\n"
            f"Tłuszcz: {self._fmt(totals['fat'])} g\n"
            f"Tłuszcze nasycone: "
            f"{self._fmt(totals['saturated_fat'])} g\n"
            f"Węglowodany: {self._fmt(totals['carbs'])} g\n"
            f"Cukry: {self._fmt(totals['sugar'])} g\n"
            f"Błonnik: {self._fmt(totals['fiber'])} g\n"
            f"Sól: {self._fmt(totals['salt'])} g"
        )


    def open_edit_dish(self):
        app = App.get_running_app()

        app.dish_form_mode = "edit"
        app.root.screen_manager.current = "dish_form"


    def show_delete_confirmation(self):
        self.confirm_delete_visible = True


    def hide_delete_confirmation(self):
        self.confirm_delete_visible = False


    def confirm_delete_dish(self):
        app = App.get_running_app()
        dish_id = app.selected_dish_id

        if not dish_id:
            return

        session = get_session()

        try:
            delete_dish(
                session,
                dish_id=dish_id,
                user_id=app.current_user_id,
            )
        finally:
            session.close()

        self.confirm_delete_visible = False
        app.selected_dish_id = 0
        app.dish_form_mode = "create"
        app.root.screen_manager.current = "dishes"


    def _clear_fields(self):
        ids = self.ids

        ids.name_value.text = "-"
        ids.description_value.text = "-"
        ids.recipe_value.text = "-"
        ids.youtube_value.text = "-"
        ids.ingredients_value.text = "-"
        ids.macros_value.text = "-"


    def _fmt(self, value):
        if value is None:
            return "0"

        return f"{value:.2f}".rstrip("0").rstrip(".")