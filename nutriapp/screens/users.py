# nutriapp/screens/users.py
from kivy.app import App
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

from nutriapp.data.repositories.user_repo import get_session, list_users
from nutriapp.services.points_service import (
    format_points,
    refresh_all_points,
    user_point_totals,
)


class UsersScreen(MDScreen):
    def on_enter(self):
        App.get_running_app().set_topbar(
            title="Użytkownicy",
            visible=True,
            show_back=False,
            back_target="home",
        )
        self.refresh_users()

    def refresh_users(self):
        session = get_session()
        try:
            refresh_all_points(session)
            users = list_users(session)
            totals = user_point_totals(session)
            rows = [
                (
                    user.id,
                    (user.display_name or "").strip() or "Bez nazwy",
                    user.email,
                    totals.get(user.id, 0),
                )
                for user in users
            ]
        except Exception:
            session.rollback()
            self._show_message("Nie udało się policzyć punktów.")
            return
        finally:
            session.close()

        container = self.ids.users_list
        container.clear_widgets()

        if not rows:
            self._show_message("Brak użytkowników w bazie.")
            return

        for user_id, name, email, total in rows:
            container.add_widget(self._user_row(user_id, name, email, total))

    def open_points(self, user_id: int):
        app = App.get_running_app()
        app.selected_points_user_id = user_id
        app.root.screen_manager.current = "user_points"

    def _user_row(self, user_id: int, name: str, email: str, total: int):
        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(88),
            spacing=dp(8),
        )
        info = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2),
        )
        info.add_widget(MDLabel(text=name, adaptive_height=True))
        info.add_widget(MDLabel(text=format_points(total), adaptive_height=True))
        info.add_widget(
            MDLabel(
                text=email,
                adaptive_height=True,
                theme_text_color="Secondary",
            )
        )

        button = MDButton(
            style="outlined",
            size_hint=(None, None),
            size=(dp(120), dp(40)),
            pos_hint={"center_y": 0.5},
        )
        button.add_widget(MDButtonText(text="Szczegóły"))
        button.bind(
            on_release=lambda _button, selected_id=user_id: self.open_points(selected_id)
        )

        row.add_widget(info)
        row.add_widget(button)
        return row

    def _show_message(self, text: str):
        container = self.ids.users_list
        container.clear_widgets()
        container.add_widget(MDLabel(text=text, adaptive_height=True))
