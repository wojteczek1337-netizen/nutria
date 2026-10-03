from kivy.app import App
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from nutriapp.data.repositories.dish_repo import (
    add_or_update_dish,
    get_dish_by_id,
    get_dish_items,
    get_products_for_user_basic,
    get_session,
    replace_dish_items,
)


class DishFormScreen(MDScreen):
    product_picker_visible = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.products = []
        self.ingredient_rows = []
        self.active_ingredient_row = None

    def on_enter(self):
        app = App.get_running_app()
        is_edit = app.dish_form_mode == "edit"

        app.set_topbar(
            title="Edytuj danie" if is_edit else "Nowe danie",
            visible=True,
            show_back=True,
            back_target="dishes",
        )

        self._clear_form()
        self._load_products()

        if is_edit and app.selected_dish_id:
            self._load_dish_data()
        else:
            self._add_empty_ingredient_row()

    def _load_dish_data(self):
        app = App.get_running_app()
        dish_id = app.selected_dish_id

        session = get_session()
        try:
            dish = get_dish_by_id(
                session,
                dish_id=dish_id,
                user_id=app.current_user_id,
            )

            items = get_dish_items(
                session,
                dish_id=dish_id,
                user_id=app.current_user_id,
            )
        finally:
            session.close()

        if dish is None:
            self._add_empty_ingredient_row()
            return

        self.ids.name_field.text = dish.name or ""
        self.ids.description_field.text = dish.description or ""
        self.ids.recipe_field.text = dish.recipe_text or ""
        self.ids.youtube_field.text = dish.youtube_url or ""

        for item in items:
            if item.product is None:
                continue

            self._add_selected_ingredient_row(
                product_id=item.product.id,
                product_name=item.product.name,
                brand=item.product.brand,
                amount_g=item.amount_g,
            )

        self._add_empty_ingredient_row()

    def _load_products(self):
        app = App.get_running_app()

        session = get_session()
        try:
            self.products = get_products_for_user_basic(
                session,
                user_id=app.current_user_id,
            )
        finally:
            session.close()

    def open_product_picker(self, ingredient_row):
        self.active_ingredient_row = ingredient_row
        self.product_picker_visible = True
        self.ids.product_search_field.text = ""
        self._refresh_product_search_results()

    def close_product_picker(self):
        self.product_picker_visible = False
        self.active_ingredient_row = None

    def filter_products(self, search_text):
        self._refresh_product_search_results(search_text)

    def _refresh_product_search_results(self, search_text=""):
        container = self.ids.product_search_list
        container.clear_widgets()

        search_text = search_text.strip().lower()
        filtered_products = []

        for product in self.products:
            product_name = (product.name or "").lower()
            brand = (product.brand or "").lower()

            if (
                not search_text
                or search_text in product_name
                or search_text in brand
            ):
                filtered_products.append(product)

        if not filtered_products:
            empty = MDButton(
                style="text",
                size_hint_y=None,
                height=dp(44),
                disabled=True,
            )

            empty.add_widget(
                MDButtonText(
                    text="Nie znaleziono produktu."
                )
            )

            container.add_widget(empty)
            return

        for product in filtered_products:
            label = product.name or "Bez nazwy"

            if product.brand:
                label = f"{label} ({product.brand})"

            button = MDButton(
                style="text",
                size_hint_y=None,
                height=dp(48),
            )

            button.add_widget(
                MDButtonText(text=label)
            )

            button.bind(
                on_release=lambda btn, selected_product=product:
                self.select_product(selected_product)
            )

            container.add_widget(button)

    def select_product(self, product):
        ingredient_row = self.active_ingredient_row

        if ingredient_row is None:
            return

        ingredient_row["product_id"] = product.id
        ingredient_row["product_name"] = product.name
        ingredient_row["brand"] = product.brand

        self._render_selected_row(ingredient_row)
        self.close_product_picker()

        self._remove_extra_empty_rows()
        self._add_empty_ingredient_row()

    def _add_empty_ingredient_row(self):
        row_data = {
            "product_id": None,
            "product_name": None,
            "brand": None,
            "row": None,
            "amount_field": None,
        }

        self.ingredient_rows.append(row_data)
        self._render_empty_row(row_data)

    def _add_selected_ingredient_row(
        self,
        *,
        product_id,
        product_name,
        brand,
        amount_g,
    ):
        row_data = {
            "product_id": product_id,
            "product_name": product_name,
            "brand": brand,
            "row": None,
            "amount_field": None,
        }

        self.ingredient_rows.append(row_data)

        self._render_selected_row(
            row_data,
            self._format_number(amount_g),
        )

    def _render_empty_row(self, row_data):
        row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(52),
        )

        button = MDButton(
            style="outlined",
            size_hint_x=0.72,
            size_hint_y=None,
            height=dp(48),
        )

        button.add_widget(
            MDButtonText(
                text="Dodaj produkt       +"
            )
        )

        button.bind(
            on_release=lambda btn, current_row=row_data:
            self.open_product_picker(current_row)
        )

        row.add_widget(button)

        row_data["row"] = row
        self.ids.ingredients_list.add_widget(row)

    def _render_selected_row(self, row_data, amount_text=""):
        old_row = row_data.get("row")

        if old_row is not None:
            self.ids.ingredients_list.remove_widget(old_row)

        row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            size_hint_y=None,
            height=dp(52),
        )

        product_label = row_data["product_name"] or "Produkt"

        if row_data.get("brand"):
            product_label = (
                f"{product_label} ({row_data['brand']})"
            )

        product_button = MDButton(
            style="outlined",
            size_hint_x=0.45,
            size_hint_y=None,
            height=dp(48),
        )

        product_button.add_widget(
            MDButtonText(text=product_label)
        )

        product_button.bind(
            on_release=lambda btn, current_row=row_data:
            self.open_product_picker(current_row)
        )

        amount_field = MDTextField(
            mode="outlined",
            hint_text="120",
            text=amount_text,
            input_filter="float",
            size_hint_x=0.30,
            size_hint_y=None,
            height=dp(48),
        )

        unit_label = MDLabel(
            text="g",
            halign="center",
            valign="middle",
            size_hint_x=0.08,
            size_hint_y=None,
            height=dp(48),
        )

        remove_button = MDButton(
            style="text",
            size_hint_x=0.12,
            size_hint_y=None,
            height=dp(48),
        )

        remove_button.add_widget(
            MDButtonText(text="×")
        )

        remove_button.bind(
            on_release=lambda btn, current_row=row_data:
            self.remove_ingredient_row(current_row)
        )

        row.add_widget(product_button)
        row.add_widget(amount_field)
        row.add_widget(unit_label)
        row.add_widget(remove_button)

        row_data["row"] = row
        row_data["amount_field"] = amount_field

        self.ids.ingredients_list.add_widget(row)

    def remove_ingredient_row(self, row_data):
        if row_data in self.ingredient_rows:
            self.ingredient_rows.remove(row_data)

        row = row_data.get("row")

        if row is not None:
            self.ids.ingredients_list.remove_widget(row)

        self._remove_extra_empty_rows()

        if not self._has_empty_row():
            self._add_empty_ingredient_row()

    def _remove_extra_empty_rows(self):
        empty_rows = [
            row
            for row in self.ingredient_rows
            if row["product_id"] is None
        ]

        for row_data in empty_rows[1:]:
            self.ingredient_rows.remove(row_data)

            row = row_data.get("row")

            if row is not None:
                self.ids.ingredients_list.remove_widget(row)

    def _has_empty_row(self):
        return any(
            row["product_id"] is None
            for row in self.ingredient_rows
        )

    def save_dish(self, go_to_list=True):
        app = App.get_running_app()

        name = self.ids.name_field.text.strip()

        if not name:
            return False

        description = (
            self.ids.description_field.text.strip() or None
        )

        recipe_text = (
            self.ids.recipe_field.text.strip() or None
        )

        youtube_url = (
            self.ids.youtube_field.text.strip() or None
        )

        dish_id = (
            app.selected_dish_id
            if app.dish_form_mode == "edit"
            else None
        )

        ingredient_items = []

        for row_data in self.ingredient_rows:
            if row_data["product_id"] is None:
                continue

            amount_field = row_data.get("amount_field")

            if amount_field is None:
                continue

            amount_g = self._to_float(amount_field.text)

            if amount_g is None or amount_g <= 0:
                continue

            ingredient_items.append(
                {
                    "product_id": row_data["product_id"],
                    "amount_g": amount_g,
                }
            )

        session = get_session()
        saved_dish_id = None

        try:
            saved_dish = add_or_update_dish(
                session,
                user_id=app.current_user_id,
                dish_id=dish_id,
                name=name,
                description=description,
                recipe_text=recipe_text,
                youtube_url=youtube_url,
            )

            saved_dish_id = saved_dish.id

            replace_dish_items(
                session,
                dish_id=saved_dish_id,
                user_id=app.current_user_id,
                items=ingredient_items,
            )
        finally:
            session.close()

        if saved_dish_id is None:
            return False

        app.selected_dish_id = saved_dish_id
        app.dish_form_mode = "edit"

        if go_to_list:
            app.root.screen_manager.current = "dishes"

        return True

    def open_details(self):
        app = App.get_running_app()

        saved = self.save_dish(go_to_list=False)

        if saved and app.selected_dish_id:
            app.root.screen_manager.current = "dish_details"

    def cancel(self):
        app = App.get_running_app()

        app.dish_form_mode = "create"
        app.selected_dish_id = 0
        app.root.screen_manager.current = "dishes"

    def _clear_form(self):
        self.product_picker_visible = False
        self.active_ingredient_row = None
        self.products = []
        self.ingredient_rows = []

        self.ids.name_field.text = ""
        self.ids.description_field.text = ""
        self.ids.recipe_field.text = ""
        self.ids.youtube_field.text = ""

        self.ids.ingredients_list.clear_widgets()
        self.ids.product_search_list.clear_widgets()

    def _to_float(self, value):
        value = value.strip().replace(",", ".")

        if not value:
            return None

        try:
            return float(value)
        except ValueError:
            return None

    def _format_number(self, value):
        if value is None:
            return ""

        return f"{value:.2f}".rstrip("0").rstrip(".")