# nutriapp/widgets/charts.py
from kivy.graphics import Color, Ellipse
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout


class CalorieRingChart(Widget):
    """
    Pierścień:
    - tło = 100% celu (pierścień),
    - planned: zielony z niższym alpha,
    - eaten: zielony pełny,
    - overflow: żółty / czerwony przy przekroczeniu 100% / 120%.
    Start z góry (0°), w prawo.
    """

    target_calories = NumericProperty(0.0)
    planned_calories = NumericProperty(0.0)
    eaten_calories = NumericProperty(0.0)

    background_color = ListProperty([0.9, 0.9, 0.9, 1.0])
    planned_color_base = ListProperty([0.2, 0.8, 0.2, 0.4])
    eaten_color_base = ListProperty([0.2, 0.8, 0.2, 1.0])

    overflow_yellow = ListProperty([1.0, 0.85, 0.0, 0.6])
    overflow_red = ListProperty([1.0, 0.2, 0.2, 0.6])

    ring_thickness_ratio = NumericProperty(0.09)
    center_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            target_calories=self._on_values_change,
            planned_calories=self._on_values_change,
            eaten_calories=self._on_values_change,
            ring_thickness_ratio=self._redraw,
        )

    def _on_values_change(self, *args):
        if self.target_calories > 0:
            self.center_text = f"{self.eaten_calories:.0f} / {self.target_calories:.0f}"
        else:
            self.center_text = ""
        self._redraw()

    def _redraw(self, *args):
        self.canvas.after.clear()

        if self.target_calories <= 0:
            return

        size = min(self.width, self.height)
        thickness = size * self.ring_thickness_ratio
        outer_size = size
        inner_size = size - 2 * thickness

        x = self.x + (self.width - outer_size) / 2.0
        y = self.y + (self.height - outer_size) / 2.0

        with self.canvas.after:
            # TŁO: szary pierścień
            Color(*self.background_color)
            Ellipse(
                pos=(x, y),
                size=(outer_size, outer_size),
                angle_start=0,
                angle_end=360,
            )

            # wycięcie środka
            Color(1, 1, 1, 1)
            Ellipse(
                pos=(x + thickness, y + thickness),
                size=(inner_size, inner_size),
                angle_start=0,
                angle_end=360,
            )

            def draw_ring_segment(ratio: float, color_rgba):
                if ratio <= 0:
                    return
                sweep = ratio * 360.0
                angle_start = 0.0  # góra
                angle_end = angle_start + sweep  # w prawo

                # segment
                Color(*color_rgba)
                Ellipse(
                    pos=(x, y),
                    size=(outer_size, outer_size),
                    angle_start=angle_start,
                    angle_end=angle_end,
                )

                # wycięcie środka dla tego segmentu
                Color(1, 1, 1, 1)
                Ellipse(
                    pos=(x + thickness, y + thickness),
                    size=(inner_size, inner_size),
                    angle_start=angle_start,
                    angle_end=angle_end,
                )

            def choose_overflow_color(ratio: float):
                return self.overflow_yellow if ratio <= 1.2 else self.overflow_red

            planned_ratio = self.planned_calories / self.target_calories if self.target_calories > 0 else 0.0
            eaten_ratio = self.eaten_calories / self.target_calories if self.target_calories > 0 else 0.0

            base_planned = min(planned_ratio, 1.0)
            overflow_planned = max(planned_ratio - 1.0, 0.0)

            base_eaten = min(eaten_ratio, 1.0)
            overflow_eaten = max(eaten_ratio - 1.0, 0.0)

            # planned pod spodem
            if base_planned > 0:
                draw_ring_segment(base_planned, self.planned_color_base)

            if overflow_planned > 0:
                draw_ring_segment(min(overflow_planned, 1.0), choose_overflow_color(planned_ratio))

            # eaten na wierzchu
            if base_eaten > 0:
                draw_ring_segment(base_eaten, self.eaten_color_base)

            if overflow_eaten > 0:
                draw_ring_segment(min(overflow_eaten, 1.0), choose_overflow_color(eaten_ratio))


class MacroRingCard(MDBoxLayout):
    """
    Ogólna karta z ringiem:
    - tytuł,
    - ring,
    - center text,
    - plan i nadwyżka.
    """

    title = StringProperty("")
    unit = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "4dp"
        self.padding = [0, 0, 0, 0]