# nutriapp/screens/users.py
from kivy.app import App
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.image import AsyncImage
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

from nutriapp.data.repositories.user_repo import get_session, list_users
from nutriapp.services.avatar_service import (
    avatar_url_for_points,
    load_avatar_catalog,
)
from nutriapp.services.points_service import (
    format_points,
    refresh_all_points,
    user_point_totals,
)


class UserAvatar(Widget):
    """Kwadrat awatara rysowany w miejscu widgetu, bez osobnej warstwy obrazka."""

    def __init__(self, *, url: str | None, letter: str, **kwargs):
        super().__init__(
            size_hint=(None, None),
            size=(dp(56), dp(56)),
            pos_hint={"center_y": 0.5},
            **kwargs,
        )
        self._photo = None
        self._texture = None
        self._loader = None

        with self.canvas.before:
            Color(0.82, 0.84, 0.88, 1)
            self._background = Rectangle(pos=self.pos, size=self.size)

        self._letter = CoreLabel(
            text=letter,
            font_size=dp(20),
            color=(0.25, 0.28, 0.32, 1),
        )
        self._letter.refresh()
        with self.canvas.after:
            Color(1, 1, 1, 1)
            self._letter_rect = Rectangle(
                texture=self._letter.texture,
                size=self._letter.texture.size,
                pos=self._letter_pos(),
            )

        self.bind(pos=self._sync, size=self._sync)

        if url:
            self._loader = AsyncImage(source=url)
            self._loader.bind(on_load=self._show_photo)

    def _letter_pos(self):
        width, height = self._letter.texture.size
        return (
            self.x + (self.width - width) / 2,
            self.y + (self.height - height) / 2,
        )

    def _sync(self, *_args):
        self._background.pos = self.pos
        self._background.size = self.size
        self._letter_rect.pos = self._letter_pos()
        if self._photo is not None and self._texture is not None:
            self._photo.pos = self.pos
            self._photo.size = self.size
            self._photo.tex_coords = self._cover_coords(self._texture)

    def _cover_coords(self, texture):
        coords = list(texture.tex_coords)
        texture_w, texture_h = texture.size
        if (
            texture_w <= 0
            or texture_h <= 0
            or self.width <= 0
            or self.height <= 0
        ):
            return coords

        image_ratio = texture_w / texture_h
        box_ratio = self.width / self.height
        if image_ratio > box_ratio:
            inset_u = (1 - box_ratio / image_ratio) / 2
            inset_v = 0.0
        else:
            inset_u = 0.0
            inset_v = (1 - image_ratio / box_ratio) / 2

        u0, v0, u1, v1, u2, v2, u3, v3 = coords

        def mix(start, end, amount):
            return start + (end - start) * amount

        return (
            mix(u0, u1, inset_u),
            mix(v0, v3, inset_v),
            mix(u0, u1, 1 - inset_u),
            mix(v1, v2, inset_v),
            mix(u3, u2, 1 - inset_u),
            mix(v1, v2, 1 - inset_v),
            mix(u3, u2, inset_u),
            mix(v0, v3, 1 - inset_v),
        )

    def _show_photo(self, loader):
        texture = loader.texture
        if texture is None:
            return
        self._texture = texture
        self._letter_rect.size = (0, 0)
        with self.canvas:
            Color(1, 1, 1, 1)
            self._photo = Rectangle(
                texture=texture,
                pos=self.pos,
                size=self.size,
                tex_coords=self._cover_coords(texture),
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
            try:
                catalog = load_avatar_catalog(session)
            except Exception:
                catalog = {}
            rows = []
            for user in users:
                total = totals.get(user.id, 0)
                rows.append(
                    (
                        user.id,
                        (user.display_name or "").strip() or "Bez nazwy",
                        user.email,
                        total,
                        avatar_url_for_points(total, catalog),
                    )
                )
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

        for user_id, name, email, total, avatar_url in rows:
            container.add_widget(
                self._user_row(user_id, name, email, total, avatar_url)
            )

    def open_points(self, user_id: int):
        app = App.get_running_app()
        app.selected_points_user_id = user_id
        app.root.screen_manager.current = "user_points"

    def _user_row(
        self,
        user_id: int,
        name: str,
        email: str,
        total: int,
        avatar_url: str | None,
    ):
        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(88),
            spacing=dp(12),
        )
        row.add_widget(
            UserAvatar(
                url=avatar_url,
                letter=(name[:1] or "?").upper(),
            )
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
