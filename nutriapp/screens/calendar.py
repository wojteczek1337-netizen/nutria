# nutriapp/screens/calendar.py
from datetime import date, timedelta

from kivy.app import App
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.pickers import MDModalDatePicker
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView

from nutriapp.data.repositories.calendar_repo import (
    add_dish_entry,
    add_product_entry,
    delete_entry as repo_delete_entry,
    get_entries_for_date,
    get_session,
    set_entry_flags,
)
from nutriapp.data.repositories.dish_repo import search_dishes_for_user
from nutriapp.data.repositories.product_repo import search_products_for_user
from nutriapp.services.calendar_service import compute_day_macros
from nutriapp.services.diets_service import ensure_active_diet_plan


class CalendarScreen(MDScreen):
    selected_date = ObjectProperty(None, allownone=True)
    confirm_delete_visible = BooleanProperty(False)
    pending_delete_entry_id = ObjectProperty(None, allownone=True)
    day_macros_text = StringProperty("Brak danych odżywczych dla tego dnia.")
    add_mode = StringProperty("eaten")

    month_names = [
        "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
        "lipca", "sierpnia", "września", "października", "listopada",
        "grudnia",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.products = []
        self.dishes = []
        self.search_results = []
        self.selected_item = None
        self.amount_field = None
        self.add_panel_widget = None
        self.add_search_field = None
        self.add_search_list = None
        self.add_selected_row = None

    def on_enter(self, *args):
        super().on_enter(*args)
        app = App.get_running_app()
        app.set_topbar(title="Kalendarz", visible=True, show_back=False, back_target="home")
        if self.selected_date is None:
            self.selected_date = date.today()
        ensure_active_diet_plan(user_id=app.current_user_id, today=date.today())
        self.confirm_delete_visible = False
        self.pending_delete_entry_id = None
        self.refresh_calendar()

    def refresh_calendar(self):
        self._update_date_label()
        entries = self._load_entries()
        self._update_day_macros(entries)

    def _update_date_label(self):
        if self.selected_date is not None:
            self.ids.date_button_text.text = (
                f"{self.selected_date.day} "
                f"{self.month_names[self.selected_date.month - 1]} "
                f"{self.selected_date.year}"
            )

    def previous_day(self):
        self.selected_date = (self.selected_date or date.today()) - timedelta(days=1)
        self.confirm_delete_visible = False
        self.pending_delete_entry_id = None
        self.refresh_calendar()

    def next_day(self):
        self.selected_date = (self.selected_date or date.today()) + timedelta(days=1)
        self.confirm_delete_visible = False
        self.pending_delete_entry_id = None
        self.refresh_calendar()

    def go_to_today(self):
        self.selected_date = date.today()
        self.confirm_delete_visible = False
        self.pending_delete_entry_id = None
        self.refresh_calendar()

    def open_date_picker(self):
        self.selected_date = self.selected_date or date.today()
        picker = MDModalDatePicker(
            year=self.selected_date.year,
            month=self.selected_date.month,
            day=self.selected_date.day,
        )
        picker.bind(on_ok=self._on_date_picker_ok)
        picker.open()

    def _on_date_picker_ok(self, picker):
        selected_dates = picker.get_date()
        picker.dismiss()
        if selected_dates:
            self.selected_date = selected_dates[0]
            self.confirm_delete_visible = False
            self.pending_delete_entry_id = None
            self.refresh_calendar()

    def _load_entries(self):
        app = App.get_running_app()
        container = self.ids.entries_list
        container.clear_widgets()

        session = get_session()
        try:
            entries = get_entries_for_date(
                session,
                user_id=app.current_user_id,
                entry_date=self.selected_date,
            )
        finally:
            session.close()

        if not entries:
            empty = MDButton(style="text", size_hint_y=None, height=dp(48), disabled=True)
            empty.add_widget(MDButtonText(text="Brak posiłków w tym dniu."))
            container.add_widget(empty)
            return []

        for entry in entries:
            entry_id = int(entry.id)
            item_text = self._get_entry_text(entry)
            is_planned = bool(getattr(entry, "is_planned", False))
            is_eaten = bool(getattr(entry, "is_eaten", False))
            can_mark_eaten = is_planned and not is_eaten

            row = MDBoxLayout(
                orientation="vertical",
                spacing=dp(4),
                size_hint_y=None,
                padding=(0, dp(4), 0, dp(4)),
            )
            row.bind(minimum_height=row.setter("height"))

            top_row = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(6),
                size_hint_y=None,
                height=dp(48),
            )

            main_button = MDButton(
                style="outlined",
                size_hint_x=1,
                size_hint_y=None,
                height=dp(48),
            )
            main_button.add_widget(MDButtonText(text=item_text))
            top_row.add_widget(main_button)
            row.add_widget(top_row)

            actions_row = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(8),
                size_hint_y=None,
                height=dp(40),
            )

            mark_button = MDButton(
                style="text",
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(40),
                disabled=not can_mark_eaten,
            )
            mark_button.add_widget(
                MDButtonText(text="Zjedzone" if can_mark_eaten else "-")
            )
            if can_mark_eaten:
                mark_button.bind(
                    on_release=self._make_mark_eaten_callback(entry_id)
                )

            delete_button = MDButton(
                style="text",
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(40),
            )
            delete_button.add_widget(MDButtonText(text="Usuń"))
            delete_button.bind(
                on_release=self._make_delete_callback(entry_id)
            )

            actions_row.add_widget(mark_button)
            actions_row.add_widget(delete_button)
            row.add_widget(actions_row)
            container.add_widget(row)

        return entries

    def _make_mark_eaten_callback(self, entry_id: int):
        def callback(*_args):
            self.mark_entry_as_eaten(entry_id)
        return callback

    def _make_delete_callback(self, entry_id: int):
        def callback(*_args):
            self.ask_delete_entry(entry_id)
        return callback

    def _update_day_macros(self, entries):
        eaten, planned, has_eaten, has_planned = compute_day_macros(entries)
        parts = []

        if has_eaten:
            parts.append(
                "Zjedzone:\n"
                f"Kalorie: {self._format_number(eaten['energy'])} kcal\n"
                f"Białko: {self._format_number(eaten['protein'])} g\n"
                f"Tłuszcz: {self._format_number(eaten['fat'])} g\n"
                f"Tłuszcze nasycone: {self._format_number(eaten['saturated_fat'])} g\n"
                f"Węglowodany: {self._format_number(eaten['carbs'])} g\n"
                f"Cukry: {self._format_number(eaten['sugar'])} g\n"
                f"Błonnik: {self._format_number(eaten['fiber'])} g\n"
                f"Sól: {self._format_number(eaten['salt'])} g"
            )

        if has_planned:
            parts.append(
                "Zaplanowane:\n"
                f"Kalorie: {self._format_number(planned['energy'])} kcal\n"
                f"Białko: {self._format_number(planned['protein'])} g\n"
                f"Tłuszcz: {self._format_number(planned['fat'])} g\n"
                f"Tłuszcze nasycone: {self._format_number(planned['saturated_fat'])} g\n"
                f"Węglowodany: {self._format_number(planned['carbs'])} g\n"
                f"Cukry: {self._format_number(planned['sugar'])} g\n"
                f"Błonnik: {self._format_number(planned['fiber'])} g\n"
                f"Sól: {self._format_number(planned['salt'])} g"
            )

        self.day_macros_text = (
            "\n\n".join(parts)
            if parts
            else "Brak danych odżywczych dla tego dnia."
        )

    def ask_delete_entry(self, entry_id: int):
        self.pending_delete_entry_id = entry_id
        self.confirm_delete_visible = True

    def cancel_delete_entry(self):
        self.pending_delete_entry_id = None
        self.confirm_delete_visible = False

    def confirm_delete_entry(self):
        if self.pending_delete_entry_id is None:
            return
        self.delete_entry(self.pending_delete_entry_id)
        self.pending_delete_entry_id = None
        self.confirm_delete_visible = False

    def delete_entry(self, entry_id: int):
        app = App.get_running_app()
        session = get_session()
        try:
            repo_delete_entry(session, entry_id=entry_id, user_id=app.current_user_id)
        finally:
            session.close()
        self.refresh_calendar()

    def mark_entry_as_eaten(self, entry_id: int):
        app = App.get_running_app()
        session = get_session()
        try:
            set_entry_flags(
                session,
                entry_id=entry_id,
                user_id=app.current_user_id,
                is_eaten=True,
            )
        finally:
            session.close()
        self.refresh_calendar()

    def _get_entry_text(self, entry):
        prefix_parts = []
        if getattr(entry, "is_planned", False):
            prefix_parts.append("PLAN")
        if getattr(entry, "is_eaten", False):
            prefix_parts.append("EAT")
        prefix = f"[{'+'.join(prefix_parts)}] " if prefix_parts else ""

        if entry.product is not None:
            return (
                f"{prefix}{entry.product.name or 'Produkt'} — "
                f"{self._format_number(entry.amount_g or 0)} g"
            )
        if entry.dish is not None:
            return (
                f"{prefix}{entry.dish.name or 'Danie'} — "
                f"{self._format_number(entry.servings or 1)} porcji"
            )
        return f"{prefix}Nieznany wpis"

    def _format_number(self, value):
        return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")

    def open_add_eaten_entry(self):
        self.add_mode = "eaten"
        self._open_add_panel()

    def open_add_planned_entry(self):
        self.add_mode = "planned"
        self._open_add_panel()

    def open_add_entry(self):
        self.open_add_eaten_entry()

    def _open_add_panel(self):
        app = App.get_running_app()
        session = get_session()
        try:
            self.products = search_products_for_user(session, user_id=app.current_user_id, query="")
            self.dishes = search_dishes_for_user(session, user_id=app.current_user_id, query="")
        finally:
            session.close()

        self.search_results = [
            {"type": "product", "id": p.id, "name": p.name, "brand": p.brand}
            for p in self.products
        ] + [
            {"type": "dish", "id": d.id, "name": d.name, "brand": None}
            for d in self.dishes
        ]
        self.selected_item = None
        self.amount_field = None

        container = self.ids.add_panel_container
        container.clear_widgets()
        panel = MDBoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        panel.bind(minimum_height=panel.setter("height"))

        search_field = MDTextField(
            mode="outlined",
            hint_text="Szukaj produktu lub dania...",
            size_hint_y=None,
            height=dp(48),
        )
        search_field.bind(on_text=lambda _instance, text: self.filter_search_results(text))
        panel.add_widget(search_field)
        self.add_search_field = search_field

        scroll = MDScrollView(do_scroll_x=False, size_hint_y=None, height=dp(180))
        results_list = MDBoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        results_list.bind(minimum_height=results_list.setter("height"))
        scroll.add_widget(results_list)
        panel.add_widget(scroll)
        self.add_search_list = results_list

        selected_row = MDBoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        selected_row.bind(minimum_height=selected_row.setter("height"))
        panel.add_widget(selected_row)
        self.add_selected_row = selected_row

        buttons_row = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(44))
        cancel_button = MDButton(style="text", size_hint_x=0.5, size_hint_y=None, height=dp(44))
        cancel_button.add_widget(MDButtonText(text="Anuluj"))
        cancel_button.bind(on_release=lambda *_: self.close_add_panel())
        add_button = MDButton(style="filled", size_hint_x=0.5, size_hint_y=None, height=dp(44))
        add_button.add_widget(MDButtonText(text="Dodaj"))
        add_button.bind(on_release=lambda *_: self.save_selected_entry())
        buttons_row.add_widget(cancel_button)
        buttons_row.add_widget(add_button)
        panel.add_widget(buttons_row)
        container.add_widget(panel)

        self._refresh_search_results("")
        self._render_selected_item_none()

    def close_add_panel(self):
        self.ids.add_panel_container.clear_widgets()
        self.add_panel_widget = None
        self.add_search_field = None
        self.add_search_list = None
        self.add_selected_row = None
        self.selected_item = None
        self.amount_field = None

    def filter_search_results(self, search_text):
        self._refresh_search_results(search_text)

    def _refresh_search_results(self, search_text=""):
        if self.add_search_list is None:
            return
        container = self.add_search_list
        container.clear_widgets()
        search_text = (search_text or "").strip().lower()
        filtered = [
            item for item in self.search_results
            if not search_text
            or search_text in (item["name"] or "").lower()
            or search_text in (item.get("brand") or "").lower()
        ]

        if not filtered:
            empty = MDButton(style="text", size_hint_y=None, height=dp(44), disabled=True)
            empty.add_widget(MDButtonText(text="Nie znaleziono produktu ani dania."))
            container.add_widget(empty)
            return

        for item in filtered:
            label = item["name"] or "Bez nazwy"
            if item.get("brand"):
                label = f"{label} ({item['brand']})"
            label = f"{label} – {'Produkt' if item['type'] == 'product' else 'Danie'}"
            button = MDButton(style="text", size_hint_y=None, height=dp(48))
            button.add_widget(MDButtonText(text=label))
            button.bind(on_release=self._make_select_item_callback(item))
            container.add_widget(button)

    def _make_select_item_callback(self, item):
        def callback(*_args):
            self.select_item(item)
        return callback

    def select_item(self, item):
        self.selected_item = item
        self._render_selected_item()

    def _render_selected_item_none(self):
        if self.add_selected_row is not None:
            self.add_selected_row.clear_widgets()

    def _render_selected_item(self):
        if self.add_selected_row is None:
            return
        container = self.add_selected_row
        container.clear_widgets()
        if self.selected_item is None:
            return

        item = self.selected_item
        is_product = item["type"] == "product"
        row = MDBoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(52))

        product_button = MDButton(style="outlined", size_hint_x=0.55, size_hint_y=None, height=dp(48))
        product_button.add_widget(MDButtonText(text=item["name"] or "Bez nazwy"))
        product_button.bind(on_release=lambda *_: self._reopen_search())

        amount_field = MDTextField(
            mode="outlined",
            hint_text="1" if not is_product else "120",
            text="1" if not is_product else "",
            input_filter="float",
            size_hint_x=0.25,
            size_hint_y=None,
            height=dp(48),
        )
        unit_label = MDLabel(
            text="porcje" if not is_product else "g",
            halign="center",
            valign="middle",
            size_hint_x=0.12,
            size_hint_y=None,
            height=dp(48),
        )
        remove_button = MDButton(style="text", size_hint_x=0.08, size_hint_y=None, height=dp(48))
        remove_button.add_widget(MDButtonText(text="×"))
        remove_button.bind(on_release=lambda *_: self._clear_selected_item())

        row.add_widget(product_button)
        row.add_widget(amount_field)
        row.add_widget(unit_label)
        row.add_widget(remove_button)
        container.add_widget(row)
        self.amount_field = amount_field

    def _reopen_search(self):
        self.selected_item = None
        self.amount_field = None
        self._render_selected_item_none()
        if self.add_search_field is not None:
            self.add_search_field.text = ""
        self._refresh_search_results("")

    def _clear_selected_item(self):
        self.selected_item = None
        self.amount_field = None
        self._render_selected_item_none()

    def save_selected_entry(self):
        app = App.get_running_app()
        if self.selected_item is None:
            return
        amount_value = self._to_float(self.amount_field.text if self.amount_field else "")
        if amount_value is None or amount_value <= 0:
            return

        item = self.selected_item
        is_product = item["type"] == "product"
        is_eaten = self.add_mode == "eaten"
        is_planned = not is_eaten
        session = get_session()
        try:
            if is_product:
                entry = add_product_entry(
                    session,
                    user_id=app.current_user_id,
                    entry_date=self.selected_date,
                    product_id=item["id"],
                    amount_g=amount_value,
                    is_planned=is_planned,
                    is_eaten=is_eaten,
                    source="manual",
                )
            else:
                entry = add_dish_entry(
                    session,
                    user_id=app.current_user_id,
                    entry_date=self.selected_date,
                    dish_id=item["id"],
                    servings=amount_value,
                    is_planned=is_planned,
                    is_eaten=is_eaten,
                    source="manual",
                )
            if entry is not None:
                self.refresh_calendar()
                self.close_add_panel()
        finally:
            session.close()

    @staticmethod
    def _to_float(value):
        if not value:
            return None
        try:
            return float(value.strip().replace(",", "."))
        except ValueError:
            return None