# nutriapp/screens/users.py
from kivy.app import App
from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
)
from kivymd.uix.screen import MDScreen

from nutriapp.data.repositories.user_repo import get_session, list_users


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
            users = list_users(session)
            rows = [
                (
                    user.id,
                    (user.display_name or "").strip() or "Bez nazwy",
                    user.email,
                )
                for user in users
            ]
        finally:
            session.close()

        container = self.ids.users_list
        container.clear_widgets()

        if not rows:
            container.add_widget(
                MDLabel(
                    text="Brak użytkowników w bazie.",
                    adaptive_height=True,
                )
            )
            return

        for user_id, name, email in rows:
            item = MDListItem()
            item.add_widget(MDListItemHeadlineText(text=name))
            item.add_widget(
                MDListItemSupportingText(text=f"{email}  ·  id {user_id}")
            )
            container.add_widget(item)
