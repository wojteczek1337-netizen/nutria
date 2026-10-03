# nutriapp/screens/diets.py
from kivy.app import App
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout

from nutriapp.data.repositories.diet_repo import (
    get_session,
    create_diet,
    list_diets_for_user,
)


class DietListScreen(MDScreen):
    diets_list_text = StringProperty("")

    def on_enter(self):
        app = App.get_running_app()
        app.set_topbar(
            title="Diety",
            visible=True,
            show_back=False,
            back_target="home",
        )
        self.refresh_diets_list()

    def refresh_diets_list(self):
        app = App.get_running_app()
        session = get_session()
        try:
            diets = list_diets_for_user(session, user_id=app.current_user_id)
        finally:
            session.close()

        self._render_diets_list(diets)

    def _render_diets_list(self, diets: list):
        container = self.ids.diets_list_container
        container.clear_widgets()

        if not diets:
            empty = MDButton(
                style="text",
                size_hint_y=None,
                height=dp(48),
                disabled=True,
            )
            empty.add_widget(MDButtonText(text="Brak diet. Utwórz pierwszą dietę."))
            container.add_widget(empty)
            return

        for diet in diets:
            row = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(8),
                size_hint_y=None,
                height=dp(56),
            )

            label = diet.name
            if diet.is_active:
                label = f"{label} (aktywna)"

            info_button = MDButton(
                style="outlined",
                size_hint_x=0.7,
                size_hint_y=None,
                height=dp(56),
            )
            info_button.add_widget(
                MDButtonText(text=f"{label} ({diet.cycle_length} dni)")
            )
            info_button.bind(
                on_release=lambda btn, diet_id=diet.id:
                self.open_diet_details(diet_id)
            )

            delete_button = MDButton(
                style="text",
                size_hint_x=0.3,
                size_hint_y=None,
                height=dp(56),
            )
            delete_button.add_widget(MDButtonText(text="Usuń"))
            # TODO: usuwanie diety

            row.add_widget(info_button)
            row.add_widget(delete_button)
            container.add_widget(row)

    def open_diet_details(self, diet_id: int):
        app = App.get_running_app()
        app.root.screen_manager.current = "diet_details"
        diet_details_screen = app.root.screen_manager.get_screen("diet_details")
        diet_details_screen.load_diet(diet_id)

    def create_new_diet(self):
        app = App.get_running_app()
        session = get_session()
        try:
            diets = list_diets_for_user(session, user_id=app.current_user_id)
            next_num = len(diets) + 1
            diet_name = f"Dieta {next_num}"

            diet = create_diet(
                session,
                user_id=app.current_user_id,
                name=diet_name,
                cycle_length=7,
                calendar_days=7,
            )
        finally:
            session.close()

        self.refresh_diets_list()
        self.open_diet_details(diet.id)