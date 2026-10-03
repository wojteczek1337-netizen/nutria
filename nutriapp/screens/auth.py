# nutriapp/screens/auth.py
from kivymd.uix.screen import MDScreen
from kivy.app import App

from nutriapp.data.repositories.user_repo import (
    get_session,
    create_user,
    verify_user_credentials,
)


class AuthScreen(MDScreen):
    """Ekran logowania / rejestracji."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mode = "login"  # "login" albo "register"

    def on_enter(self, *args):
        App.get_running_app().set_topbar(
            title="",
            visible=False,
            show_back=False,
            right_actions=[],
        )
        
    def _notify(self, message: str):
        """Pokazuje komunikat w labelu statusu na dole ekranu."""
        self.ids.status_label.text = message

    def switch_mode(self):
        """Przełącza między trybem logowania a rejestracji."""
        ids = self.ids
        if self.mode == "login":
            self.mode = "register"
            ids.mode_label.text = "Rejestracja"
            ids.submit_button_text.text = "Zarejestruj się"
        else:
            self.mode = "login"
            ids.mode_label.text = "Logowanie"
            ids.submit_button_text.text = "Zaloguj"

    def submit(self):
        """Obsługuje kliknięcie głównego przycisku (login / register)."""
        ids = self.ids
        email = ids.email_field.text.strip()
        password = ids.password_field.text.strip()
        display_name = ids.name_field.text.strip() or None

        if not email or not password:
            self._notify("Podaj email i hasło")
            return

        session = get_session()

        if self.mode == "register":
            user = create_user(
                session,
                email=email,
                raw_password=password,
                display_name=display_name,
            )
            self._notify("Utworzono użytkownika")
        else:
            user = verify_user_credentials(
                session,
                email=email,
                raw_password=password,
            )
            if user is None:
                self._notify("Niepoprawny email lub hasło")
                return
            self._notify("Zalogowano")

        # ustawiamy aktywnego użytkownika w aplikacji
        app = App.get_running_app()
        app.current_user_id = user.id

        # przejście do Home
        app.root.screen_manager.current = "home"