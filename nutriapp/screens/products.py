from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDButton, MDButtonText
from kivy.metrics import dp
from kivy.app import App

from nutriapp.data.repositories.product_repo import get_session
from nutriapp.services.products_service import list_user_products


class ProductsScreen(MDScreen):
    def on_enter(self):
        app = App.get_running_app()
        app.topbar_title = "Produkty"
        app.topbar_visible = True

        session = get_session()
        try:
            products = list_user_products(
                session,
                user_id=app.current_user_id,
            )
        finally:
            session.close()

        container = self.ids.products_list
        container.clear_widgets()

        if not products:
            empty = MDButton(
                style="text",
                size_hint_y=None,
                height=dp(44),
                disabled=True,
            )
            empty.add_widget(
                MDButtonText(
                    text="Brak produktów. Dodaj pierwszy produkt."
                )
            )
            container.add_widget(empty)
            return

        for product in products:
            text = (
                f"{product.name} ({product.brand})"
                if product.brand
                else product.name
            )

            item = MDButton(
                style="text",
                size_hint_y=None,
                height=dp(44),
            )
            item.add_widget(MDButtonText(text=text))

            # Uwaga: używamy domknięcia z product_id jako argumentu
            item.bind(
                on_release=lambda btn, product_id=product.id:
                self.open_product_details(product_id)
            )

            container.add_widget(item)

    def open_add_product(self):
        App.get_running_app().root.screen_manager.current = "product_form"

    def open_product_details(self, product_id: int):
        app = App.get_running_app()
        app.selected_product_id = product_id
        app.root.screen_manager.current = "product_details"