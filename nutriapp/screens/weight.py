# nutriapp/screens/weight.py
from datetime import date, datetime

from kivy.properties import StringProperty
from kivymd.uix.button import MDIconButton
from kivymd.uix.list import (
    MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
    MDListItemTertiaryText,
)
from kivymd.uix.pickers import MDModalDatePicker
from kivymd.uix.screen import MDScreen

from nutriapp.data.database import SessionLocal
from nutriapp.services.weight_service import (
    create_weight_measurement,
    get_weight_history,
    remove_weight_measurement,
)
from nutriapp.widgets.weight_chart import WeightChart


class WeightHistoryItem(MDListItem):
    weight_id = None

    def __init__(self, *, record, is_latest=False, on_delete=None, **kwargs):
        super().__init__(**kwargs)
        self.weight_id = record.id
        self.add_widget(
            MDListItemHeadlineText(text=f"{record.weight_kg:.1f} kg")
        )
        self.add_widget(
            MDListItemSupportingText(
                text=f"Pomiar: {record.measured_on.isoformat()}"
            )
        )
        if is_latest:
            self.add_widget(
                MDListItemTertiaryText(text="Najnowszy pomiar")
            )

        delete_button = MDIconButton(icon="delete-outline")
        if on_delete is not None:
            delete_button.bind(on_release=on_delete)
        self.add_widget(delete_button)


class WeightScreen(MDScreen):
    selected_date = StringProperty("")

    def on_pre_enter(self, *args):
        self.selected_date = date.today().isoformat()
        self.ids.date_field.text = self.selected_date
        self.refresh_screen()

    def on_kv_post(self, base_widget):
        self.chart = WeightChart()
        self.ids.chart_container.add_widget(self.chart)

    def open_date_picker(self):
        today = date.today()
        picker = MDModalDatePicker(
            year=today.year,
            month=today.month,
            day=today.day,
        )
        picker.bind(on_ok=self._date_picker_ok)
        picker.open()

    def _date_picker_ok(self, picker, *args):
        selected = picker.get_date()
        if isinstance(selected, (list, tuple)):
            if not selected:
                picker.dismiss()
                return
            selected = selected[0]
        if hasattr(selected, "date"):
            selected = selected.date()
        if not isinstance(selected, date):
            picker.dismiss()
            return
        self.selected_date = selected.isoformat()
        self.ids.date_field.text = self.selected_date
        picker.dismiss()

    def save_measurement(self):
        try:
            measured_on = datetime.strptime(
                self.ids.date_field.text, "%Y-%m-%d"
            ).date()
            weight_kg = float(
                self.ids.weight_field.text.strip().replace(",", ".")
            )
        except (TypeError, ValueError):
            self.ids.profile_label.text = "Podaj poprawną wagę i datę."
            return

        session = SessionLocal()
        try:
            create_weight_measurement(
                session,
                user_id=self._user_id(),
                measured_on=measured_on,
                weight_kg=weight_kg,
            )
            session.commit()
        except ValueError as exc:
            session.rollback()
            self.ids.profile_label.text = str(exc)
        except Exception:
            session.rollback()
            self.ids.profile_label.text = "Nie udało się zapisać pomiaru."
        finally:
            session.close()

        self.ids.weight_field.text = ""
        self.refresh_screen()

    def refresh_screen(self):
        session = SessionLocal()
        try:
            history = get_weight_history(
                session,
                user_id=self._user_id(),
            )
        finally:
            session.close()

        if hasattr(self, "chart"):
            self.chart.set_points(history)

        self.ids.history_list.clear_widgets()
        if not history:
            self.ids.profile_label.text = "Profil: brak pomiaru"
            return

        latest = history[0]
        self.ids.profile_label.text = (
            f"Profil: {latest.weight_kg:.1f} kg "
            f"({latest.measured_on.isoformat()})"
        )

        for record in history:
            item_id = record.id
            item = WeightHistoryItem(
                record=record,
                is_latest=item_id == latest.id,
                on_delete=lambda widget, weight_id=item_id:
                    self.delete_measurement(weight_id),
            )
            self.ids.history_list.add_widget(item)

    def delete_measurement(self, weight_id: int):
        session = SessionLocal()
        try:
            deleted = remove_weight_measurement(
                session,
                user_id=self._user_id(),
                weight_id=weight_id,
            )
            if not deleted:
                session.rollback()
                self.ids.profile_label.text = (
                    "Nie znaleziono pomiaru do usunięcia."
                )
                return
            session.commit()
        except Exception:
            session.rollback()
            self.ids.profile_label.text = "Nie udało się usunąć pomiaru."
        finally:
            session.close()

        self.refresh_screen()

    @staticmethod
    def _user_id() -> int:
        from kivy.app import App
        return int(App.get_running_app().current_user_id)