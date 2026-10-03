# nutriapp/screens/diet_details.py
from datetime import date

from kivy.app import App
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    StringProperty,
    NumericProperty,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from nutriapp.data.repositories.diet_repo import (
    get_session,
    get_diet_by_id,
    get_meals_for_diet_day,
    add_meal_to_diet_day,
    remove_meal_from_diet,
    update_diet_meta,
)
from nutriapp.data.repositories.product_repo import search_products_for_user
from nutriapp.data.repositories.dish_repo import search_dishes_for_user
from nutriapp.services.diets_service import (
    activate_diet,
    compute_diet_day_macros,
    deactivate_diet,
)
from nutriapp.data.repositories.daily_target_repo import ensure_daily_target_for_date
from nutriapp.data.repositories.user_repo import get_user_profile


class DietDetailsScreen(MDScreen):
    diet_name = StringProperty("")
    diet_description = StringProperty("")
    cycle_length = NumericProperty(7)
    calendar_days = NumericProperty(7)
    current_day_number = NumericProperty(1)
    is_active = BooleanProperty(False)

    day_macros_text = StringProperty("")
    average_macros_text = StringProperty("")
    target_macros_text = StringProperty("")

    # numer dnia cyklu, od którego rozpoczynamy dietę (powiązany ze start_day_field w KV)
    start_day_number = NumericProperty(1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_diet_id = None
        self.day_meals = []

        self.products = []
        self.dishes = []
        self.search_results = []
        self.selected_item = None
        self.amount_field = None

        # widgety panelu dodawania
        self.search_field = None
        self.results_list = None
        self.selected_row = None

    def on_enter(self):
        app = App.get_running_app()
        app.set_topbar(
            title="Szczegóły diety",
            visible=True,
            show_back=True,
            back_target="diets",
        )

    def load_diet(self, diet_id: int):
        app = App.get_running_app()
        session = get_session()
        try:
            diet = get_diet_by_id(session, diet_id=diet_id, user_id=app.current_user_id)
            if diet is None:
                return

            self.current_diet_id = diet_id
            self.diet_name = diet.name
            self.diet_description = diet.description or ""
            self.cycle_length = diet.cycle_length
            self.calendar_days = diet.calendar_days
            self.is_active = diet.is_active
            self.current_day_number = 1
            # wczytaj startowy dzień cyklu, jeśli istnieje
            self.start_day_number = getattr(diet, "cycle_start_day", 1) or 1
        finally:
            session.close()

        self.refresh_view()

    def refresh_view(self):
        self._update_day_label()
        self._load_day_meals()
        self._update_day_macros()
        self._update_average_macros()
        self._update_target_macros()

    def _update_day_label(self):
        if "day_label" in self.ids:
            self.ids.day_label.text = f"Dzień {self.current_day_number}"

    # ===== META =====

    def save_diet_name(self):
        app = App.get_running_app()
        name = self.ids.diet_name_field.text.strip()
        if not name:
            return

        session = get_session()
        try:
            update_diet_meta(
                session,
                diet_id=self.current_diet_id,
                user_id=app.current_user_id,
                name=name,
                description=None,
                cycle_length=None,
                calendar_days=None,
                is_active=None,
            )
        finally:
            session.close()

        self.diet_name = name

    def save_description(self):
        app = App.get_running_app()
        description = self.ids.description_field.text.strip()

        session = get_session()
        try:
            update_diet_meta(
                session,
                diet_id=self.current_diet_id,
                user_id=app.current_user_id,
                name=None,
                description=description,
                cycle_length=None,
                calendar_days=None,
                is_active=None,
            )
        finally:
            session.close()

        self.diet_description = description

    def save_cycle_length(self):
        app = App.get_running_app()
        text = self.ids.cycle_length_field.text.strip()
        try:
            new_length = int(text)
        except ValueError:
            return

        if new_length < 1:
            return

        session = get_session()
        try:
            update_diet_meta(
                session,
                diet_id=self.current_diet_id,
                user_id=app.current_user_id,
                name=None,
                description=None,
                cycle_length=new_length,
                calendar_days=None,
                is_active=None,
            )
        finally:
            session.close()

        self.cycle_length = new_length
        if self.current_day_number > self.cycle_length:
            self.current_day_number = self.cycle_length
        self.refresh_view()

    def save_calendar_days(self):
        app = App.get_running_app()
        text = self.ids.activate_days_field.text.strip()
        try:
            days = int(text)
        except ValueError:
            return

        if days < 1:
            return

        session = get_session()
        try:
            update_diet_meta(
                session,
                diet_id=self.current_diet_id,
                user_id=app.current_user_id,
                name=None,
                description=None,
                cycle_length=None,
                calendar_days=days,
                is_active=None,
            )
        finally:
            session.close()

        self.calendar_days = days

    # ===== DZIEŃ =====

    def _load_day_meals(self):
        app = App.get_running_app()
        session = get_session()
        try:
            meals = get_meals_for_diet_day(
                session,
                diet_id=self.current_diet_id,
                day_number=self.current_day_number,
                user_id=app.current_user_id,
            )
            self.day_meals = meals
        finally:
            session.close()

        self._render_day_meals()

    def _render_day_meals(self):
        container = self.ids.day_meals_container
        container.clear_widgets()

        if not self.day_meals:
            empty = MDLabel(
                text="Brak posiłków w tym dniu.",
                size_hint_y=None,
                height=dp(24),
                halign="left",
            )
            container.add_widget(empty)
            return

        for meal in self.day_meals:
            text = self._get_meal_text(meal)

            row = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(8),
                size_hint_y=None,
                height=dp(28),
            )

            label = MDLabel(
                text=text,
                halign="left",
                valign="middle",
                size_hint_x=0.8,
                size_hint_y=None,
                height=dp(28),
            )

            delete_button = MDButton(
                style="text",
                size_hint_x=0.2,
                size_hint_y=None,
                height=dp(28),
            )
            delete_button.add_widget(MDButtonText(text="Usuń"))
            delete_button.bind(
                on_release=lambda btn, meal_id=meal.id:
                self.confirm_delete_meal_direct(meal_id)
            )

            row.add_widget(label)
            row.add_widget(delete_button)
            container.add_widget(row)

    def _get_meal_text(self, meal) -> str:
        if meal.product is not None:
            name = meal.product.name or "Produkt"
            amount = meal.amount_g or 0
            return f"{name} — {amount:.0f} g"

        if meal.dish is not None:
            name = meal.dish.name or "Danie"
            servings = meal.servings or 1
            return f"{name} — {servings:.1f} porcji"

        return "Nieznany posiłek"

    # ===== MAKRO =====

    def _update_day_macros(self):
        macros = compute_diet_day_macros(self.day_meals)
        self.day_macros_text = (
            f"kcal: {macros['energy']:.0f}\n"
            f"białko: {macros['protein']:.1f} g\n"
            f"tłuszcze: {macros['fat']:.1f} g\n"
            f"węglowodany: {macros['carbs']:.1f} g"
        )

    def _update_average_macros(self):
        app = App.get_running_app()
        session = get_session()
        try:
            from nutriapp.data.repositories.diet_repo import get_all_diet_days

            days = get_all_diet_days(
                session,
                diet_id=self.current_diet_id,
                user_id=app.current_user_id,
            )
        finally:
            session.close()

        total = {
            "energy": 0.0,
            "protein": 0.0,
            "fat": 0.0,
            "carbs": 0.0,
        }
        count_days = max(self.cycle_length, 1)

        for _, meals in days.items():
            macros = compute_diet_day_macros(meals)
            total["energy"] += macros["energy"]
            total["protein"] += macros["protein"]
            total["fat"] += macros["fat"]
            total["carbs"] += macros["carbs"]

        avg = {key: value / count_days for key, value in total.items()}

        self.average_macros_text = (
            f"kcal: {avg['energy']:.0f}\n"
            f"białko: {avg['protein']:.1f} g\n"
            f"tłuszcze: {avg['fat']:.1f} g\n"
            f"węglowodany: {avg['carbs']:.1f} g"
        )

    def _update_target_macros(self):
        app = App.get_running_app()
        session = get_session()
        try:
            profile = get_user_profile(session, user_id=app.current_user_id)
            if profile:
                daily_target = ensure_daily_target_for_date(
                    session,
                    user_profile=profile,
                    day=date.today(),
                )
                self.target_macros_text = (
                    f"Cel: {daily_target.calories:.0f} kcal\n"
                    f"B: {daily_target.protein_g:.1f} g, "
                    f"T: {daily_target.fat_g:.1f} g, "
                    f"W: {daily_target.carbs_g:.1f} g"
                )
            else:
                self.target_macros_text = "Brak celu"
        finally:
            session.close()

    # ===== NAWIGACJA =====

    def previous_day(self):
        if self.current_day_number > 1:
            self.current_day_number -= 1
            self.refresh_view()

    def next_day(self):
        if self.current_day_number < self.cycle_length:
            self.current_day_number += 1
            self.refresh_view()

    # ===== PANEL DODAWANIA =====

    def open_add_meal_panel(self):
        app = App.get_running_app()
        session = get_session()
        try:
            self.products = search_products_for_user(
                session,
                user_id=app.current_user_id,
                query="",
            )
            self.dishes = search_dishes_for_user(
                session,
                user_id=app.current_user_id,
                query="",
            )
        finally:
            session.close()

        self.search_results = []
        for p in self.products:
            self.search_results.append(
                {
                    "type": "product",
                    "id": p.id,
                    "name": p.name,
                    "brand": p.brand,
                }
            )
        for d in self.dishes:
            self.search_results.append(
                {
                    "type": "dish",
                    "id": d.id,
                    "name": d.name,
                    "brand": None,
                }
            )

        self.selected_item = None
        self.amount_field = None

        container = self.ids.add_meal_panel_container
        container.clear_widgets()

        panel = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
        )
        panel.bind(minimum_height=panel.setter("height"))

        search_field = MDTextField(
            mode="outlined",
            hint_text="Szukaj produktu lub dania...",
            size_hint_y=None,
            height=dp(40),
        )
        search_field.bind(
            on_text=lambda instance, text: self._refresh_search_results(text)
        )
        panel.add_widget(search_field)
        self.search_field = search_field

        scroll = MDScrollView(
            do_scroll_x=False,
            size_hint_y=None,
            height=dp(140),
        )
        results_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None,
        )
        results_list.bind(minimum_height=results_list.setter("height"))
        scroll.add_widget(results_list)
        panel.add_widget(scroll)
        self.results_list = results_list

        selected_row = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None,
        )
        selected_row.bind(minimum_height=selected_row.setter("height"))
        panel.add_widget(selected_row)
        self.selected_row = selected_row

        buttons_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(40),
        )

        cancel_button = MDButton(
            style="text",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(40),
        )
        cancel_button.add_widget(MDButtonText(text="Anuluj"))
        cancel_button.bind(on_release=lambda btn: self.close_add_meal_panel())

        add_button = MDButton(
            style="filled",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(40),
        )
        add_button.add_widget(MDButtonText(text="Dodaj"))
        add_button.bind(on_release=lambda btn: self.save_selected_meal())

        buttons_row.add_widget(cancel_button)
        buttons_row.add_widget(add_button)
        panel.add_widget(buttons_row)

        container.add_widget(panel)

        self._refresh_search_results("")

    def close_add_meal_panel(self):
        self.ids.add_meal_panel_container.clear_widgets()
        self.selected_item = None
        self.amount_field = None

    def _refresh_search_results(self, search_text=""):
        if self.results_list is None:
            return

        container = self.results_list
        container.clear_widgets()

        search_text = (search_text or "").strip().lower()
        filtered = []

        for item in self.search_results:
            name = (item["name"] or "").lower()
            brand = (item.get("brand") or "").lower()
            if not search_text or search_text in name or search_text in brand:
                filtered.append(item)

        if not filtered:
            empty = MDButton(
                style="text",
                size_hint_y=None,
                height=dp(36),
                disabled=True,
            )
            empty.add_widget(MDButtonText(text="Nie znaleziono produktu ani dania."))
            container.add_widget(empty)
            return

        for item in filtered:
            label = item["name"] or "Bez nazwy"
            if item.get("brand"):
                label = f"{label} ({item['brand']})"
            type_label = "Produkt" if item["type"] == "product" else "Danie"
            label = f"{label} – {type_label}"

            button = MDButton(
                style="text",
                size_hint_y=None,
                height=dp(36),
            )
            button.add_widget(MDButtonText(text=label))
            button.bind(
                on_release=lambda btn, selected_item=item:
                self.select_item(selected_item)
            )
            container.add_widget(button)

    def select_item(self, item):
        self.selected_item = item
        self._render_selected_item()

    def _render_selected_item(self):
        if self.selected_row is None:
            return

        container = self.selected_row
        container.clear_widgets()

        if self.selected_item is None:
            return

        item = self.selected_item
        is_product = item["type"] == "product"

        row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            size_hint_y=None,
            height=dp(40),
        )

        label = item["name"] or "Bez nazwy"

        product_button = MDButton(
            style="outlined",
            size_hint_x=0.55,
            size_hint_y=None,
            height=dp(40),
        )
        product_button.add_widget(MDButtonText(text=label))
        product_button.bind(on_release=lambda btn: self._reopen_search())

        amount_field = MDTextField(
            mode="outlined",
            hint_text="1" if not is_product else "120",
            text="1" if not is_product else "",
            input_filter="float",
            size_hint_x=0.25,
            size_hint_y=None,
            height=dp(40),
        )

        unit_label = MDLabel(
            text="porcje" if not is_product else "g",
            halign="center",
            valign="middle",
            size_hint_x=0.12,
            size_hint_y=None,
            height=dp(40),
        )

        remove_button = MDButton(
            style="text",
            size_hint_x=0.08,
            size_hint_y=None,
            height=dp(40),
        )
        remove_button.add_widget(MDButtonText(text="×"))
        remove_button.bind(on_release=lambda btn: self._clear_selected_item())

        row.add_widget(product_button)
        row.add_widget(amount_field)
        row.add_widget(unit_label)
        row.add_widget(remove_button)

        container.add_widget(row)
        self.amount_field = amount_field

    def _reopen_search(self):
        self.selected_item = None
        self.amount_field = None
        self._render_selected_item()
        if self.search_field is not None:
            self.search_field.text = ""
        self._refresh_search_results("")

    def _clear_selected_item(self):
        self.selected_item = None
        self.amount_field = None
        self._render_selected_item()

    def _to_float(self, value):
        if not value:
            return None
        value = value.strip().replace(",", ".")
        try:
            return float(value)
        except ValueError:
            return None

    def save_selected_meal(self):
        app = App.get_running_app()

        if self.selected_item is None:
            return

        amount_text = ""
        if self.amount_field is not None:
            amount_text = self.amount_field.text.strip()

        amount_value = self._to_float(amount_text)
        if amount_value is None or amount_value <= 0:
            return

        item = self.selected_item
        is_product = item["type"] == "product"

        session = get_session()
        try:
            add_meal_to_diet_day(
                session,
                diet_id=self.current_diet_id,
                day_number=self.current_day_number,
                user_id=app.current_user_id,
                product_id=item["id"] if is_product else None,
                dish_id=item["id"] if not is_product else None,
                amount_g=amount_value if is_product else None,
                servings=amount_value if not is_product else None,
            )
        finally:
            session.close()

        self.close_add_meal_panel()
        self.refresh_view()

    # ===== USUWANIE =====

    def confirm_delete_meal_direct(self, meal_id: int):
        app = App.get_running_app()
        session = get_session()
        try:
            remove_meal_from_diet(
                session,
                diet_meal_id=meal_id,
                user_id=app.current_user_id,
            )
        finally:
            session.close()

        self.refresh_view()

    # ===== AKTYWACJA =====

    def on_activate_button_pressed(self):
        """
        Obsługa przycisku "Aktywuj dietę" (powiązana z diet_details.kv).
        Używa:
        - activate_days_field → calendar_days,
        - start_day_field → start_day_number (dzień cyklu),
        - activate_diet() → ustawia początek cyklu i generuje plan.
        """
        app = App.get_running_app()

        # liczba dni planowanych w kalendarzu
        text_days = self.ids.activate_days_field.text.strip()
        try:
            num_days = int(text_days)
        except ValueError:
            num_days = self.calendar_days

        if num_days < 1:
            return

        # zapisz calendar_days w bazie
        self.calendar_days = num_days
        self.save_calendar_days()

        # startowy dzień cyklu (np. 4 → czwartek przy cyklu 7 dni)
        text_start = self.ids.start_day_field.text.strip()
        try:
            start_day = int(text_start)
        except ValueError:
            start_day = self.start_day_number

        if start_day < 1 or start_day > self.cycle_length:
            start_day = 1

        self.start_day_number = start_day

        # aktywuj dietę od dzisiejszej daty
        activate_diet(
            user_id=app.current_user_id,
            diet_id=self.current_diet_id,
            start_day=start_day,
            start_date=date.today(),
            replace_existing=False,
        )

        self.is_active = True

    def on_deactivate_button_pressed(self):
        """
        Obsługa przycisku "Dezaktywuj dietę".
        Na razie tylko flaga is_active i brak usuwania z kalendarza.
        """
        app = App.get_running_app()
        deactivate_diet(
            user_id=app.current_user_id,
            diet_id=self.current_diet_id,
        )
        self.is_active = False