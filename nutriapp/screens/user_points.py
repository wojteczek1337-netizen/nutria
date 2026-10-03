# nutriapp/screens/user_points.py
from kivy.app import App
from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
)
from kivymd.uix.screen import MDScreen

from nutriapp.data.repositories.user_repo import get_session, get_user_by_id
from nutriapp.services.points_service import format_points, refresh_user_points


class UserPointsScreen(MDScreen):
    def on_enter(self):
        app = App.get_running_app()
        app.set_topbar(
            title="Punkty",
            visible=True,
            show_back=True,
            back_target="users",
        )
        self.refresh_points()

    def refresh_points(self):
        app = App.get_running_app()
        user_id = int(app.selected_points_user_id or 0)
        summary = self.ids.summary_label
        hint = self.ids.hint_label
        container = self.ids.days_list
        container.clear_widgets()

        if not user_id:
            summary.text = "Nie wybrano użytkownika."
            hint.text = ""
            return

        session = get_session()
        try:
            user = get_user_by_id(session, user_id=user_id)
            if user is None:
                name = None
                day_rows = []
            else:
                days = refresh_user_points(session, user_id=user_id)
                name = (user.display_name or "").strip() or user.email
                day_rows = [
                    (
                        day.scored_on,
                        day.total_points,
                        day.calorie_points,
                        day.protein_points,
                        day.fat_points,
                    )
                    for day in days
                ]
        except Exception:
            session.rollback()
            summary.text = "Nie udało się wczytać punktów."
            hint.text = ""
            return
        finally:
            session.close()

        if name is None:
            summary.text = "Nie znaleziono użytkownika."
            hint.text = ""
            return

        app.topbar_title = name
        total = sum(points for _day, points, _calories, _protein, _fat in day_rows)
        summary.text = f"Suma: {format_points(total)}"
        hint.text = "Punkty z każdego dnia, od najnowszego."

        if not day_rows:
            container.add_widget(
                MDLabel(
                    text="Brak punktów. Pojawią się po zapisaniu zjedzonych posiłków.",
                    adaptive_height=True,
                )
            )
            return

        for scored_on, points, calorie_points, protein_points, fat_points in day_rows:
            item = MDListItem()
            item.add_widget(
                MDListItemHeadlineText(
                    text=f"{scored_on.strftime('%d.%m.%Y')} — {format_points(points)}"
                )
            )
            item.add_widget(
                MDListItemSupportingText(
                    text=(
                        f"Kalorie {calorie_points} pkt"
                        f" · Białko {protein_points} pkt"
                        f" · Tłuszcze {fat_points} pkt"
                    )
                )
            )
            container.add_widget(item)
