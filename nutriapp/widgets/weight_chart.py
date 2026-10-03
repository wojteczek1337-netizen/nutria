# nutriapp/widgets/weight_chart.py
from datetime import date

from kivy.graphics import Color, Line, Ellipse
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class WeightChart(Widget):
    """Wykres wagi z opisanymi osiami, wartościami i datami."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []
        self.labels = []
        self.bind(pos=self._redraw, size=self._redraw)

    def set_points(self, records):
        ordered = sorted(
            records,
            key=lambda record: (record.measured_on, record.id),
        )
        self.points = [
            (record.measured_on, float(record.weight_kg))
            for record in ordered
        ]
        self._redraw()

    def _clear_labels(self):
        for label in self.labels:
            self.remove_widget(label)
        self.labels.clear()

    def _add_label(self, text, *, x, y, font_size=10, color=(0.25, 0.25, 0.3, 1)):
        label = Label(
            text=str(text),
            font_size=font_size,
            color=color,
            size_hint=(None, None),
            size=(dp(60), dp(20)),
            halign="center",
            valign="middle",
        )
        label.text_size = label.size
        label.pos = (x, y)
        self.add_widget(label)
        self.labels.append(label)

    def _redraw(self, *args):
        self.canvas.clear()
        self._clear_labels()

        with self.canvas:
            Color(0.92, 0.92, 0.94, 1)
            Line(rectangle=(*self.pos, *self.size), width=1)

        if not self.points:
            self._add_label(
                "Brak pomiarów",
                x=self.x + self.width / 2 - dp(30),
                y=self.y + self.height / 2 - dp(10),
            )
            return

        values = [value for _, value in self.points]
        minimum = min(values)
        maximum = max(values)
        if minimum == maximum:
            minimum -= 1
            maximum += 1
        else:
            padding = max((maximum - minimum) * 0.15, 0.5)
            minimum -= padding
            maximum += padding

        left = self.x + dp(48)
        right = self.right - dp(18)
        bottom = self.y + dp(32)
        top = self.top - dp(24)
        width = max(right - left, 1)
        height = max(top - bottom, 1)
        count = len(self.points)

        with self.canvas:
            Color(0.75, 0.75, 0.8, 1)
            Line(points=[left, bottom, left, top], width=1)
            Line(points=[left, bottom, right, bottom], width=1)

            for fraction in (0, 0.25, 0.5, 0.75, 1):
                y = bottom + height * fraction
                Color(0.88, 0.88, 0.91, 1)
                Line(points=[left, y, right, y], width=1)

        for fraction in (0, 0.25, 0.5, 0.75, 1):
            value = minimum + (maximum - minimum) * fraction
            y = bottom + height * fraction - dp(10)
            self._add_label(
                f"{value:.1f}",
                x=self.x,
                y=y,
            )

        coordinates = []
        for index, (measured_on, value) in enumerate(self.points):
            x = left if count == 1 else left + width * index / (count - 1)
            y = bottom + height * (value - minimum) / (maximum - minimum)
            coordinates.extend((x, y))

            self._add_label(
                f"{value:.1f}",
                x=x - dp(30),
                y=y + dp(5),
                color=(0.35, 0.34, 0.58, 1),
            )
            self._add_label(
                measured_on.strftime("%d.%m"),
                x=x - dp(30),
                y=self.y + dp(4),
            )

        with self.canvas:
            Color(0.35, 0.34, 0.58, 1)
            Line(points=coordinates, width=2)
            for index in range(0, len(coordinates), 2):
                x = coordinates[index]
                y = coordinates[index + 1]
                Ellipse(pos=(x - dp(4), y - dp(4)), size=(dp(8), dp(8)))

        self._add_label(
            "Data pomiaru",
            x=left + width / 2 - dp(30),
            y=self.y - dp(10),
            font_size=10,
        )
        self._add_label(
            "kg",
            x=self.x + dp(2),
            y=top + dp(2),
            font_size=10,
        )