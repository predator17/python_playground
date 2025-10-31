"""Metric card widget for displaying system metrics."""

#      Copyright (c) 2025 predator. All rights reserved.

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QMargins
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QFrame,
)

from .time_series_chart import TimeSeriesChart


class MetricCard(QWidget):
    def __init__(
        self,
        title: str,
        unit: str = "",
        is_percent: bool = False,
        color: str = "#00c853",
        sparkline: bool = True,
        max_points: int = 60,
    ) -> None:
        super().__init__()
        self.is_percent = is_percent
        self.unit = unit
        self.color = color
        self._dyn_max: float = 10.0 if not is_percent else 100.0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame()
        self.frame.setObjectName("Card")
        outer.addWidget(self.frame)

        v = QVBoxLayout(self.frame)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("Title")
        self.lbl_value = QLabel(("-- " + unit).strip())
        self.lbl_value.setObjectName("Value")
        v.addWidget(self.lbl_title)
        v.addWidget(self.lbl_value)

        self.lbl_frequency = QLabel("")
        self.lbl_frequency.setStyleSheet("QLabel { color: #909090; font-size: 9pt; }")
        self.lbl_frequency.setVisible(False)
        v.addWidget(self.lbl_frequency)

        self.lbl_model = QLabel("")
        self.lbl_model.setStyleSheet(
            "QLabel { color: #808080; font-size: 8pt; font-style: italic; }"
        )
        self.lbl_model.setWordWrap(True)
        self.lbl_model.setVisible(False)
        v.addWidget(self.lbl_model)

        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setStyleSheet(
            f"QProgressBar::chunk{{background-color:{color}; border-radius:6px;}}"
        )
        v.addWidget(self.bar)

        self.sparkline: Optional[TimeSeriesChart] = None
        if sparkline:
            self.sparkline = TimeSeriesChart(
                "",
                [title],
                max_points=max_points,
                y_range=(0, 100 if is_percent else 1),
                auto_scale=(not is_percent),
            )
            self.sparkline.chart.legend().setVisible(False)
            self.sparkline.chart.setTitle("")
            self.sparkline.axis_x.setVisible(False)
            self.sparkline.axis_y.setVisible(False)
            self.sparkline.chart.setMargins(QMargins(0, 0, 0, 0))
            v.addWidget(self.sparkline)

        sp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setSizePolicy(sp)

    def set_tooltip(self, text: str) -> None:
        self.setToolTip(text)
        self.frame.setToolTip(text)
        self.lbl_value.setToolTip(text)
        self.lbl_title.setToolTip(text)

    def set_unavailable(self, message: str = "N/A") -> None:
        self.lbl_value.setText(message)
        self.bar.setValue(0)

    def set_frequency(self, freq_mhz: float) -> None:
        """Set frequency display in MHz."""
        if freq_mhz > 0:
            self.lbl_frequency.setText(f"⚡ {freq_mhz:.0f} MHz")
            self.lbl_frequency.setVisible(True)
        else:
            self.lbl_frequency.setVisible(False)

    def set_model(self, model_name: str) -> None:
        """Set model/brand name display."""
        if model_name and model_name.strip():
            self.lbl_model.setText(f"🔹 {model_name.strip()}")
            self.lbl_model.setVisible(True)
        else:
            self.lbl_model.setVisible(False)

    def update_percent(self, pct: float) -> None:
        """Update percentage value with warning colors for high usage."""
        try:
            pct_f = max(0.0, min(100.0, float(pct)))
        except Exception:
            pct_f = 0.0
        self.lbl_value.setText(f"{pct_f:.1f} %")
        self.bar.setValue(int(round(pct_f)))

        if pct_f >= 90.0:
            self.bar.setStyleSheet(
                "QProgressBar::chunk{background-color:#f44336; border-radius:6px;}"
            )
        elif pct_f >= 80.0:
            self.bar.setStyleSheet(
                "QProgressBar::chunk{background-color:#ff9800; border-radius:6px;}"
            )
        else:
            self.bar.setStyleSheet(
                f"QProgressBar::chunk{{background-color:{self.color}; border-radius:6px;}}"
            )

        if self.sparkline is not None:
            self.sparkline.append([pct_f])

    def update_value(self, value: float, ref_max: Optional[float] = None) -> None:
        try:
            v = float(value)
        except Exception:
            v = 0.0
        self.lbl_value.setText(f"{v:.2f} {self.unit}".strip())
        if self.is_percent:
            m = 100.0
        else:
            if ref_max is None:
                self._dyn_max = max(v, self._dyn_max * 0.98)
                m = max(self._dyn_max, 1e-6)
            else:
                m = max(ref_max, 1e-6)
        pct = (
            int(round(max(0.0, min(100.0, (v / m) * 100.0)))) if m > 0 else 0
        )
        self.bar.setValue(pct)
        if self.sparkline is not None:
            self.sparkline.append([v])
