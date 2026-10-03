from kivy.app import App
from kivy.properties import BooleanProperty
from kivymd.uix.screen import MDScreen

from nutriapp.data.repositories.product_repo import get_session
from nutriapp.services.products_service import (
    get_user_product,
    delete_user_product,
)


def _fmt(value, suffix=""):
    if value is None:
        return "-"
    if isinstance(value, float):
        text = f"{value:.2f}".rstrip("0").rstrip(".")
    else:
        text = str(value)
    return f"{text}{suffix}"


class ProductDetailsScreen(MDScreen):
    confirm_delete_visible = BooleanProperty(False)

    def on_enter(self):
        print("DEBUG DETAILS: on_enter() z product_details.py")
        self.confirm_delete_visible = False

        app = App.get_running_app()
        app.set_topbar(
            title="Szczegóły produktu",
            visible=True,
            show_back=True,
            back_target="products",
        )

        product_id = app.selected_product_id
        if not product_id:
            self._clear_fields()
            return

        session = get_session()
        try:
            product = get_user_product(
                session,
                user_id=app.current_user_id,
                product_id=product_id,
            )
        finally:
            session.close()

        if product is None:
            self._clear_fields()
            self.ids.name_value.text = "Nie znaleziono produktu"
            return

        self.ids.name_value.text = product.name or "-"
        self.ids.brand_value.text = product.brand or "-"
        self.ids.quantity_text_value.text = product.quantity_text or "-"
        self.ids.quantity_g_value.text = _fmt(product.quantity_g, " g")

        self.ids.energy_value.text = _fmt(product.energy_kcal_100, " kcal")
        self.ids.protein_value.text = _fmt(product.protein_100, " g")
        self.ids.fat_value.text = _fmt(product.fat_100, " g")
        self.ids.saturated_fat_value.text = _fmt(
            product.saturated_fat_100, " g"
        )
        self.ids.carbs_value.text = _fmt(product.carbs_100, " g")
        self.ids.sugar_value.text = _fmt(product.sugar_100, " g")
        self.ids.fiber_value.text = _fmt(product.fiber_100, " g")
        self.ids.salt_value.text = _fmt(product.salt_100, " g")

        self.ids.ingredients_value.text = product.ingredients_text or "-"
        self.ids.allergens_value.text = product.allergens or "-"
        self.ids.tags_value.text = "Wkrótce"

    def open_edit_product(self):
        print("DEBUG DETAILS: open_edit_product()")
        app = App.get_running_app()
        app.product_form_mode = "edit"
        app.root.screen_manager.current = "product_form"

    def show_delete_confirmation(self):
        print("DEBUG DETAILS: show_delete_confirmation()")
        self.confirm_delete_visible = True

    def hide_delete_confirmation(self):
        print("DEBUG DETAILS: hide_delete_confirmation()")
        self.confirm_delete_visible = False

    def confirm_delete_product(self):
        print("DEBUG DETAILS: confirm_delete_product()")
        app = App.get_running_app()
        product_id = app.selected_product_id
        if not product_id:
            return

        session = get_session()
        try:
            delete_user_product(
                session,
                user_id=app.current_user_id,
                product_id=product_id,
            )
        finally:
            session.close()

        self.confirm_delete_visible = False
        app.selected_product_id = 0
        app.product_form_mode = "create"
        app.root.screen_manager.current = "products"

    def _clear_fields(self):
        ids = self.ids
        ids.name_value.text = "-"
        ids.brand_value.text = "-"
        ids.quantity_text_value.text = "-"
        ids.quantity_g_value.text = "-"
        ids.energy_value.text = "-"
        ids.protein_value.text = "-"
        ids.fat_value.text = "-"
        ids.saturated_fat_value.text = "-"
        ids.carbs_value.text = "-"
        ids.sugar_value.text = "-"
        ids.fiber_value.text = "-"
        ids.salt_value.text = "-"
        ids.ingredients_value.text = "-"
        ids.allergens_value.text = "-"
        ids.tags_value.text = "-"