"""Time series chart widget for displaying real-time data."""

#      Copyright (c) 2025 predator. All rights reserved.

from __future__ import annotations

from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, QPointF, QMargins
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis


class TimeSeriesChart(QWidget):
    def __init__(
        self,
        title: str,
        series_names: List[str],
        max_points: int = 400,
        y_range: Optional[Tuple[float, float]] = (0.0, 100.0),
        auto_scale: bool = False,
    ) -> None:
        super().__init__()
        self.max_points = max_points
        self.auto_scale = auto_scale
        self._x: int = 0

        layout = QVBoxLayout(self)
        self.chart = QChart()
        self.chart.setTheme(QChart.ChartThemeDark)
        self.chart.setTitle(title)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)
        self.chart.setAnimationOptions(QChart.NoAnimation)
        self.chart.setBackgroundVisible(False)
        self.chart.setMargins(QMargins(8, 8, 8, 8))

        self.series: List[QLineSeries] = []
        for name in series_names:
            s = QLineSeries()
            s.setName(name)
            self.chart.addSeries(s)
            self.series.append(s)

        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Samples")
        self.axis_x.setRange(0, max_points)
        self.axis_x.setTickCount(6)
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        for s in self.series:
            s.attachAxis(self.axis_x)

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Value")
        if y_range is not None:
            self.axis_y.setRange(y_range[0], y_range[1])
        else:
            self.axis_y.setRange(0, 100)
        self.axis_y.setTickCount(6)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        for s in self.series:
            s.attachAxis(self.axis_y)

        self.view = QChartView(self.chart)
        self.view.setRenderHint(QPainter.Antialiasing, True)
        self.view.setRubberBand(QChartView.RectangleRubberBand)
        self.view.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.view)

        self._buffers: List[List[QPointF]] = [[] for _ in self.series]

        sp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(sp)

    def append(self, values: List[float]) -> None:
        n = min(len(values), len(self.series))
        self._x += 1
        x0 = max(0, self._x - self.max_points)
        for i in range(n):
            buf = self._buffers[i]
            buf.append(QPointF(float(self._x), float(values[i])))
            if len(buf) > self.max_points:
                del buf[: len(buf) - self.max_points]
            self.series[i].replace(buf)

        self.axis_x.setRange(x0, x0 + self.max_points)

        if self.auto_scale:
            current_max = 1.0
            for buf in self._buffers:
                if buf:
                    m = max(p.y() for p in buf)
                    if m > current_max:
                        current_max = m
            self.axis_y.setRange(0, current_max * 1.2)
