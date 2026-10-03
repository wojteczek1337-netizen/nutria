# nutriapp/app.py
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu

from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty

from nutriapp.navigation import create_root_widget
from nutriapp.data.database import prepare_database
from nutriapp.data.migrate_sqlite import migrate_sqlite_if_empty

# MODELE – wszystkie muszą być zaimportowane przed create_all()
import nutriapp.models.user
import nutriapp.models.user_profile
import nutriapp.models.product
import nutriapp.models.dish
import nutriapp.models.dish_item
import nutriapp.models.meal_calendar
import nutriapp.models.daily_target
import nutriapp.models.diet_plan
import nutriapp.models.shopping_list
import nutriapp.models.weight
import nutriapp.models.daily_points


class NutriApp(MDApp):
    topbar_title = StringProperty("")
    topbar_visible = BooleanProperty(False)
    topbar_right_action_items = ListProperty([])
    show_topbar_back = BooleanProperty(False)
    selected_product_id = NumericProperty(0)
    selected_dish_id = NumericProperty(0)
    selected_points_user_id = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "NutriApp"

        # TODO: w przyszłości ustawiać po zalogowaniu.
        self.current_user_id = 1

        self._back_target = "home"
        self.topbar_menu = None
        self.product_form_mode = "create"
        self.dish_form_mode = "create"

        self.screen_titles = {
            "auth": "Logowanie",
            "home": "Strona główna",
            "profile": "Profil",
            "products": "Produkty",
            "product_form": "Nowy produkt",
            "product_details": "Szczegóły produktu",
            "dishes": "Dania",
            "dish_form": "Nowe danie",
            "dish_details": "Szczegóły dania",
            "calendar": "Kalendarz",
            "diets": "Diety",
            "diet_details": "Szczegóły diety",
            "shopping": "Lista zakupów",
            "weight": "Pomiary wagi",
            "users": "Użytkownicy",
            "user_points": "Punkty",
        }

        self.topbar_destinations = [
            ("home", "Strona główna"),
            ("profile", "Profil"),
            ("products", "Produkty"),
            ("dishes", "Dania"),
            ("calendar", "Kalendarz"),
            ("diets", "Diety"),
            ("shopping", "Lista zakupów"),
            ("weight", "Pomiary wagi"),
            ("users", "Użytkownicy"),
        ]

    def build(self):
        print("DEBUG APP: build() start")
        print("DEBUG APP: loading nutriapp/kv/screens/auth.kv")
        Builder.load_file("nutriapp/kv/screens/auth.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/home.kv")
        Builder.load_file("nutriapp/kv/screens/home.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/profile.kv")
        Builder.load_file("nutriapp/kv/screens/profile.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/products.kv")
        Builder.load_file("nutriapp/kv/screens/products.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/product_form.kv")
        Builder.load_file("nutriapp/kv/screens/product_form.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/product_details.kv")
        Builder.load_file("nutriapp/kv/screens/product_details.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/dishes.kv")
        Builder.load_file("nutriapp/kv/screens/dishes.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/dish_form.kv")
        Builder.load_file("nutriapp/kv/screens/dish_form.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/dish_details.kv")
        Builder.load_file("nutriapp/kv/screens/dish_details.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/calendar.kv")
        Builder.load_file("nutriapp/kv/screens/calendar.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/diets.kv")
        Builder.load_file("nutriapp/kv/screens/diets.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/diet_details.kv")
        Builder.load_file("nutriapp/kv/screens/diet_details.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/shopping.kv")
        Builder.load_file("nutriapp/kv/screens/shopping.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/weight.kv")
        Builder.load_file("nutriapp/kv/screens/weight.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/users.kv")
        Builder.load_file("nutriapp/kv/screens/users.kv")

        print("DEBUG APP: loading nutriapp/kv/screens/user_points.kv")
        Builder.load_file("nutriapp/kv/screens/user_points.kv")

        print("DEBUG APP: creating screen manager")
        screen_manager = create_root_widget()

        print("DEBUG APP: loading nutriapp/kv/root.kv")
        root = Builder.load_file("nutriapp/kv/root.kv")

        root.ids.screen_container.add_widget(screen_manager)
        root.screen_manager = screen_manager

        screen_manager.bind(current=self.on_current_screen_changed)
        self.on_current_screen_changed(screen_manager, screen_manager.current)

        print("DEBUG APP: build() end")
        return root

    def on_start(self):
        print("DEBUG APP: on_start()")
        prepare_database()
        migrate_sqlite_if_empty()

    def set_topbar(
        self,
        title="",
        visible=True,
        show_back=False,
        back_target="home",
        right_actions=None,
    ):
        self.topbar_title = title
        self.topbar_visible = visible
        self.show_topbar_back = show_back
        self._back_target = back_target
        self.topbar_right_action_items = right_actions or []

    def go_back(self):
        if self.root and hasattr(self.root, "screen_manager"):
            self.root.screen_manager.current = self._back_target

    def on_current_screen_changed(self, screen_manager, screen_name):
        print(f"DEBUG APP: current screen changed -> {screen_name}")
        self.topbar_title = self.screen_titles.get(screen_name, "NutriApp")
        self.topbar_visible = screen_name != "auth"
        self.show_topbar_back = False
        self._back_target = "home"

        if self.topbar_menu:
            self.topbar_menu.dismiss()

    def open_topbar_menu(self, caller):
        if not self.root or not hasattr(self.root, "screen_manager"):
            return

        current_screen = self.root.screen_manager.current

        menu_items = [
            {
                "text": label,
                "leading_icon": "check" if screen_name == current_screen else "circle-outline",
                "on_release": lambda target=screen_name: self.switch_from_topbar_menu(target),
            }
            for screen_name, label in self.topbar_destinations
        ]

        if self.topbar_menu:
            self.topbar_menu.dismiss()

        self.topbar_menu = MDDropdownMenu(
            caller=caller,
            items=menu_items,
        )
        self.topbar_menu.open()

    def switch_from_topbar_menu(self, screen_name):
        if self.topbar_menu:
            self.topbar_menu.dismiss()

        if self.root and hasattr(self.root, "screen_manager"):
            if self.root.screen_manager.current != screen_name:
                self.root.screen_manager.current = screen_name