from kivymd.uix.screen import MDScreen
from kivy.app import App

from nutriapp.data.repositories.product_repo import get_session
from nutriapp.services.products_service import (
    get_user_product,
    save_manual_product,
)


def _to_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


class ProductFormScreen(MDScreen):
    def on_enter(self):
        app = App.get_running_app()
        is_edit = app.product_form_mode == "edit"

        app.set_topbar(
            title="Edytuj produkt" if is_edit else "Nowy produkt",
            visible=True,
            show_back=True,
            back_target="products",
        )

        self._clear_form()

        if not is_edit:
            return

        product_id = app.selected_product_id
        if not product_id:
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
            return

        self.ids.name_field.text = product.name or ""
        self.ids.brand_field.text = product.brand or ""
        self.ids.quantity_text_field.text = product.quantity_text or ""
        self.ids.quantity_g_field.text = _to_text(product.quantity_g)
        self.ids.energy_field.text = _to_text(product.energy_kcal_100)
        self.ids.protein_field.text = _to_text(product.protein_100)
        self.ids.fat_field.text = _to_text(product.fat_100)
        self.ids.saturated_fat_field.text = _to_text(
            product.saturated_fat_100
        )
        self.ids.carbs_field.text = _to_text(product.carbs_100)
        self.ids.sugar_field.text = _to_text(product.sugar_100)
        self.ids.fiber_field.text = _to_text(product.fiber_100)
        self.ids.salt_field.text = _to_text(product.salt_100)

    def save_product(self):
        app = App.get_running_app()

        name = self.ids.name_field.text.strip()
        if not name:
            return

        brand = self.ids.brand_field.text.strip() or None
        quantity_text = self.ids.quantity_text_field.text.strip() or None
        quantity_g = self._to_float(self.ids.quantity_g_field.text)
        energy_kcal_100 = self._to_float(self.ids.energy_field.text)
        protein_100 = self._to_float(self.ids.protein_field.text)
        fat_100 = self._to_float(self.ids.fat_field.text)
        saturated_fat_100 = self._to_float(
            self.ids.saturated_fat_field.text
        )
        carbs_100 = self._to_float(self.ids.carbs_field.text)
        sugar_100 = self._to_float(self.ids.sugar_field.text)
        fiber_100 = self._to_float(self.ids.fiber_field.text)
        salt_100 = self._to_float(self.ids.salt_field.text)

        product_id = (
            app.selected_product_id
            if app.product_form_mode == "edit"
            else None
        )

        session = get_session()
        try:
            saved_product = save_manual_product(
                session,
                user_id=app.current_user_id,
                product_id=product_id,
                name=name,
                brand=brand,
                quantity_text=quantity_text,
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
        finally:
            session.close()

        app.selected_product_id = saved_product.id
        app.product_form_mode = "create"
        app.root.screen_manager.current = "product_details"

    def cancel(self):
        app = App.get_running_app()
        app.product_form_mode = "create"
        app.root.screen_manager.current = "products"

    def _clear_form(self):
        self.ids.name_field.text = ""
        self.ids.brand_field.text = ""
        self.ids.quantity_text_field.text = ""
        self.ids.quantity_g_field.text = ""
        self.ids.energy_field.text = ""
        self.ids.protein_field.text = ""
        self.ids.fat_field.text = ""
        self.ids.saturated_fat_field.text = ""
        self.ids.carbs_field.text = ""
        self.ids.sugar_field.text = ""
        self.ids.fiber_field.text = ""
        self.ids.salt_field.text = ""

    def _to_float(self, value: str):
        value = value.strip().replace(",", ".")
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None