# nutriapp/screens/shopping.py
from kivy.app import App
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.uix.button import MDButton, MDButtonIcon, MDButtonText
from kivymd.uix.pickers import MDModalDatePicker
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel

from nutriapp.data.repositories.shopping_repo import (
    delete_item,
    delete_list,
    get_list_by_id,
    get_session,
    list_for_user,
    set_item_bought,
)
from nutriapp.services.shopping_service import (
    add_manual_item,
    cleanup_old_shopping_lists,
    generate_shopping_list,
)


class ShoppingScreen(MDScreen):
    selected_list_id = NumericProperty(0)
    selected_range_text = StringProperty("Nie wybrano zakresu")
    empty_text = StringProperty("Brak zapisanych list zakupów.")
    has_selected_list = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_date = None
        self.end_date = None

    def on_enter(self):
        app = App.get_running_app()
        app.set_topbar(
            title="Lista zakupów",
            visible=True,
            show_back=False,
            back_target="home",
        )
        self.refresh_lists()

    def refresh_lists(self):
        app = App.get_running_app()
        session = get_session()
        try:
            cleanup_old_shopping_lists(session, user_id=app.current_user_id)
            lists = list_for_user(session, user_id=app.current_user_id)
        finally:
            session.close()

        if not lists:
            self.selected_list_id = 0
            self.has_selected_list = False
            self._render_lists([])
            self._render_items([])
            return

        list_ids = {shopping_list.id for shopping_list in lists}
        if self.selected_list_id not in list_ids:
            self.selected_list_id = lists[0].id

        self.has_selected_list = True
        self._render_lists(lists)
        self.refresh_selected_list()

    def _render_lists(self, lists):
        container = self.ids.lists_container
        container.clear_widgets()

        if not lists:
            container.add_widget(
                MDLabel(
                    text=self.empty_text,
                    size_hint_y=None,
                    height=dp(32),
                )
            )
            return

        for shopping_list in lists:
            button = MDButton(
                style=(
                    "outlined"
                    if shopping_list.id == self.selected_list_id
                    else "text"
                ),
                size_hint_y=None,
                height=dp(48),
            )
            button.add_widget(MDButtonText(text=shopping_list.name))
            button.bind(
                on_release=self._make_list_callback(shopping_list.id)
            )
            container.add_widget(button)

    def _make_list_callback(self, list_id: int):
        def callback(*_args):
            self.select_list(list_id)

        return callback

    def select_list(self, shopping_list_id: int):
        self.selected_list_id = shopping_list_id
        self.has_selected_list = True
        self.refresh_lists()

    def refresh_selected_list(self):
        if not self.selected_list_id:
            self._render_items([])
            return

        app = App.get_running_app()
        session = get_session()
        try:
            shopping_list = get_list_by_id(
                session,
                shopping_list_id=self.selected_list_id,
                user_id=app.current_user_id,
            )
        finally:
            session.close()

        if shopping_list is None:
            self.selected_list_id = 0
            self.has_selected_list = False
            self._render_items([])
            return

        self._render_items(shopping_list.items)

    def _render_items(self, items):
        container = self.ids.items_container
        container.clear_widgets()

        if not items:
            container.add_widget(
                MDLabel(
                    text="Lista nie zawiera jeszcze pozycji.",
                    size_hint_y=None,
                    height=dp(32),
                )
            )
            return

        # Stabilna lista rekordów przed tworzeniem widgetów.
        items = sorted(
            list(items),
            key=lambda item: (
                bool(item.is_bought),
                (item.name or "").casefold(),
                item.id,
            ),
        )

        for item in items:
            item_id = int(item.id)
            current_bought = bool(item.is_bought)

            row = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(6),
                size_hint_y=None,
                height=dp(48),
            )

            state_icon = (
                "checkbox-marked"
                if current_bought
                else "checkbox-blank-outline"
            )
            toggle_button = MDButton(
                style="text",
                size_hint_x=None,
                width=dp(48),
                size_hint_y=None,
                height=dp(44),
            )
            toggle_button.add_widget(MDButtonIcon(icon=state_icon))
            toggle_button.bind(
                on_release=self._make_toggle_callback(
                    item_id,
                    current_bought,
                )
            )

            item_name = item.name or "Pozycja"
            quantity = self._format_number(item.quantity)
            item_text = f"{item_name} — {quantity} {item.unit}"
            if current_bought:
                item_text = f"[s]{item_text}[/s]"

            label = MDLabel(
                text=item_text,
                markup=True,
                size_hint_x=0.75,
                valign="middle",
            )

            delete_button = MDButton(
                style="text",
                size_hint_x=0.2,
                size_hint_y=None,
                height=dp(44),
            )
            delete_button.add_widget(MDButtonText(text="Usuń"))
            delete_button.bind(
                on_release=self._make_delete_callback(item_id)
            )

            row.add_widget(toggle_button)
            row.add_widget(label)
            row.add_widget(delete_button)
            container.add_widget(row)

    def _make_toggle_callback(self, item_id: int, current_bought: bool):
        def callback(*_args):
            self.toggle_item(item_id, not current_bought)

        return callback

    def _make_delete_callback(self, item_id: int):
        def callback(*_args):
            self.remove_item(item_id)

        return callback

    def open_range_picker(self):
        picker = MDModalDatePicker(mode="range")
        picker.bind(on_ok=self._on_range_picker_ok)
        picker.open()

    def _on_range_picker_ok(self, picker):
        selected_dates = picker.get_date()
        picker.dismiss()

        if not selected_dates:
            return

        self.start_date = min(selected_dates)
        self.end_date = max(selected_dates)
        self.selected_range_text = (
            f"{self.start_date.strftime('%d.%m.%Y')} – "
            f"{self.end_date.strftime('%d.%m.%Y')}"
        )

    def generate_list_from_calendar(self):
        if self.start_date is None or self.end_date is None:
            return

        app = App.get_running_app()
        session = get_session()
        try:
            list_id = generate_shopping_list(
                session,
                user_id=app.current_user_id,
                start_date=self.start_date,
                end_date=self.end_date,
            )
        finally:
            session.close()

        self.selected_list_id = list_id
        self.has_selected_list = True
        self.refresh_lists()

    def open_manual_item_panel(self):
        container = self.ids.manual_item_container
        container.clear_widgets()

        container.add_widget(
            MDLabel(
                text="Dodaj własną pozycję do listy",
                bold=True,
                size_hint_y=None,
                height=dp(28),
            )
        )
        container.add_widget(
            MDLabel(
                text="Nazwa produktu lub rzeczy:",
                size_hint_y=None,
                height=dp(22),
            )
        )

        name_field = MDTextField(
            mode="outlined",
            hint_text="np. papier kuchenny",
            size_hint_y=None,
            height=dp(48),
        )
        container.add_widget(name_field)

        container.add_widget(
            MDLabel(
                text="Ilość:",
                size_hint_y=None,
                height=dp(22),
            )
        )
        quantity_field = MDTextField(
            mode="outlined",
            hint_text="np. 2",
            input_filter="float",
            size_hint_y=None,
            height=dp(48),
        )
        container.add_widget(quantity_field)

        container.add_widget(
            MDLabel(
                text="Jednostka:",
                size_hint_y=None,
                height=dp(22),
            )
        )
        unit_field = MDTextField(
            mode="outlined",
            hint_text="np. szt., opak., kg",
            text="szt.",
            size_hint_y=None,
            height=dp(48),
        )
        container.add_widget(unit_field)

        buttons = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(44),
        )

        cancel = MDButton(
            style="text",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(44),
        )
        cancel.add_widget(MDButtonText(text="Anuluj"))
        cancel.bind(on_release=lambda *_: container.clear_widgets())

        save = MDButton(
            style="filled",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(44),
        )
        save.add_widget(MDButtonText(text="Dodaj"))
        save.bind(
            on_release=lambda *_: self.save_manual_item(
                name_field,
                quantity_field,
                unit_field,
            )
        )

        buttons.add_widget(cancel)
        buttons.add_widget(save)
        container.add_widget(buttons)

    def save_manual_item(
        self,
        name_field,
        quantity_field,
        unit_field,
    ):
        if not self.selected_list_id:
            return

        name = name_field.text.strip()
        quantity = self._to_float(quantity_field.text)
        unit = unit_field.text.strip() or "szt."

        if not name or quantity is None or quantity <= 0:
            return

        app = App.get_running_app()
        session = get_session()
        try:
            success = add_manual_item(
                session,
                user_id=app.current_user_id,
                shopping_list_id=self.selected_list_id,
                name=name,
                quantity=quantity,
                unit=unit,
            )
        finally:
            session.close()

        if success:
            self.ids.manual_item_container.clear_widgets()
            self.refresh_selected_list()

    def toggle_item(self, item_id: int, is_bought: bool):
        app = App.get_running_app()
        session = get_session()
        try:
            set_item_bought(
                session,
                item_id=item_id,
                shopping_list_id=self.selected_list_id,
                user_id=app.current_user_id,
                is_bought=is_bought,
            )
        finally:
            session.close()
        self.refresh_selected_list()

    def remove_item(self, item_id: int):
        app = App.get_running_app()
        session = get_session()
        try:
            delete_item(
                session,
                item_id=item_id,
                shopping_list_id=self.selected_list_id,
                user_id=app.current_user_id,
            )
        finally:
            session.close()
        self.refresh_selected_list()

    def remove_selected_list(self):
        if not self.selected_list_id:
            return

        app = App.get_running_app()
        session = get_session()
        try:
            delete_list(
                session,
                shopping_list_id=self.selected_list_id,
                user_id=app.current_user_id,
            )
        finally:
            session.close()

        self.selected_list_id = 0
        self.has_selected_list = False
        self.refresh_lists()

    @staticmethod
    def _to_float(value: str) -> float | None:
        try:
            return float(value.strip().replace(",", "."))
        except (AttributeError, ValueError):
            return None

    @staticmethod
    def _format_number(value: float) -> str:
        text = f"{value:.2f}".rstrip("0").rstrip(".")
        return text.replace(".", ",")