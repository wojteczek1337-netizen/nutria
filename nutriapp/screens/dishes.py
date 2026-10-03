from kivy.app import App
from kivy.metrics import dp
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.screen import MDScreen

from nutriapp.data.repositories.dish_repo import (
    get_dishes_for_user,
    get_session,
)


class DishesScreen(MDScreen):
    def on_enter(self):
        app = App.get_running_app()

        app.set_topbar(
            title="Dania",
            visible=True,
            show_back=False,
            back_target="home",
        )

        self.refresh_dishes()

    def refresh_dishes(self):
        app = App.get_running_app()

        session = get_session()
        try:
            dishes = get_dishes_for_user(
                session,
                user_id=app.current_user_id,
            )
        finally:
            session.close()

        container = self.ids.dishes_list
        container.clear_widgets()

        if not dishes:
            empty = MDButton(
                style="text",
                size_hint_y=None,
                height=dp(44),
                disabled=True,
            )

            empty.add_widget(
                MDButtonText(
                    text="Brak dań. Dodaj pierwsze danie."
                )
            )

            container.add_widget(empty)
            return

        for dish in dishes:
            item = MDButton(
                style="text",
                size_hint_y=None,
                height=dp(52),
            )

            item.add_widget(
                MDButtonText(
                    text=dish.name,
                )
            )

            item.bind(
                on_release=lambda button, dish_id=dish.id:
                self.open_dish_details(dish_id)
            )

            container.add_widget(item)

    def open_add_dish(self):
        app = App.get_running_app()

        app.selected_dish_id = 0
        app.dish_form_mode = "create"
        app.root.screen_manager.current = "dish_form"

    def open_dish_details(self, dish_id: int):
        app = App.get_running_app()

        app.selected_dish_id = dish_id
        app.dish_form_mode = "edit"
        app.root.screen_manager.current = "dish_details"