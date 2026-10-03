# nutriapp/screens/home.py
from datetime import date

from kivy.app import App
from kivymd.uix.screen import MDScreen

from nutriapp.data.repositories.user_repo import get_session
from nutriapp.services.calendar_service import (
    get_calorie_ring_data,
    compute_day_macros,
)
from nutriapp.data.repositories.calendar_repo import get_entries_for_date
from nutriapp.data.repositories.user_repo import get_user_profile
from nutriapp.data.repositories.daily_target_repo import ensure_daily_target_for_date
from nutriapp.services.profile_service import get_user_targets


class HomeScreen(MDScreen):
    def on_enter(self, *args):
        super().on_enter(*args)

        App.get_running_app().set_topbar(
            title="Strona główna",
            visible=True,
            show_back=False,
            back_target="home",
            right_actions=[],
        )

        self.update_rings_for_today()

    def update_rings_for_today(self):
        app = App.get_running_app()
        session = get_session()
        today = date.today()

        # --- KCAL ---
        kcal_data = get_calorie_ring_data(
            session,
            user_id=app.current_user_id,
            day=today,
        )

        # --- Makra (g) ---
        entries = get_entries_for_date(
            session,
            user_id=app.current_user_id,
            entry_date=today,
        )
        eaten_totals, planned_totals, _, _ = compute_day_macros(entries)

        # Cel makro z profilu (snapshotowo - jak DailyTarget)
        profile = get_user_profile(session, user_id=app.current_user_id)
        macro_targets = None
        if profile is not None:
            ensure_daily_target_for_date(session, user_profile=profile, day=today)
            macro_targets = get_user_targets(profile)

        session.close()

        # KCAL ring
        if kcal_data is not None:
            ring = self.ids.kcal_ring
            ring.target_calories = kcal_data["target_calories"]
            ring.planned_calories = kcal_data["planned_calories"]
            ring.eaten_calories = kcal_data["eaten_calories"]
            self.ids.kcal_center_label.text = ring.center_text
            self.ids.kcal_plan_label.text = f"Plan: {kcal_data['planned_calories']:.0f} kcal"
            over = kcal_data["planned_over_target"]
            self.ids.kcal_plan_over_label.text = (
                f"Planowane +{over:.0f} kcal" if over > 0 else ""
            )

        if macro_targets is None:
            return

        # Białko
        protein_target = macro_targets["protein_g"]
        protein_planned = planned_totals["protein"]
        protein_eaten = eaten_totals["protein"]
        self._update_macro_ring(
            ring=self.ids.protein_ring,
            center_label=self.ids.protein_center_label,
            plan_label=self.ids.protein_plan_label,
            over_label=self.ids.protein_plan_over_label,
            target=protein_target,
            planned=protein_planned,
            eaten=protein_eaten,
            unit="g",
        )

        # Tłuszcz
        fat_target = macro_targets["fat_g"]
        fat_planned = planned_totals["fat"]
        fat_eaten = eaten_totals["fat"]
        self._update_macro_ring(
            ring=self.ids.fat_ring,
            center_label=self.ids.fat_center_label,
            plan_label=self.ids.fat_plan_label,
            over_label=self.ids.fat_plan_over_label,
            target=fat_target,
            planned=fat_planned,
            eaten=fat_eaten,
            unit="g",
        )

        # Węgle
        carbs_target = macro_targets["carbs_g"]
        carbs_planned = planned_totals["carbs"]
        carbs_eaten = eaten_totals["carbs"]
        self._update_macro_ring(
            ring=self.ids.carbs_ring,
            center_label=self.ids.carbs_center_label,
            plan_label=self.ids.carbs_plan_label,
            over_label=self.ids.carbs_plan_over_label,
            target=carbs_target,
            planned=carbs_planned,
            eaten=carbs_eaten,
            unit="g",
        )

    def _update_macro_ring(
        self,
        ring,
        center_label,
        plan_label,
        over_label,
        target: float,
        planned: float,
        eaten: float,
        unit: str,
    ):
        if target <= 0:
            return

        ring.target_calories = target
        ring.planned_calories = planned
        ring.eaten_calories = eaten

        center_label.text = f"{eaten:.0f} / {target:.0f} {unit}"
        plan_label.text = f"Plan: {planned:.0f} {unit}"

        over = max(planned - target, 0.0)
        over_label.text = f"Plan +{over:.0f} {unit}" if over > 0 else ""