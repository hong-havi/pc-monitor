"""원형 게이지 위젯 - CPU/GPU 사용률, 메모리, VRAM 표시용 + 스파크라인"""
import math
from collections import deque
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QFont, QColor, QPainterPath,
    QLinearGradient,
)


class SparklineWidget(QWidget):
    """게이지 아래 미니 스파크라인 (영역 차트)"""

    HISTORY_SIZE = 30

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._history = deque([0.0] * self.HISTORY_SIZE, maxlen=self.HISTORY_SIZE)
        self._max_value = 100.0
        self.setFixedHeight(28)

    def set_max_value(self, max_val: float):
        self._max_value = max(max_val, 1.0)

    def add_value(self, value: float):
        self._history.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin_x = 4
        draw_w = w - margin_x * 2
        draw_h = h - 4

        if draw_w <= 0 or draw_h <= 0:
            painter.end()
            return

        data = list(self._history)
        if len(data) < 2:
            painter.end()
            return

        # 포인트 계산
        points = []
        for i, val in enumerate(data):
            x = margin_x + draw_w * i / (len(data) - 1)
            ratio = min(val / self._max_value, 1.0) if self._max_value > 0 else 0
            y = (h - 2) - ratio * draw_h
            points.append(QPointF(x, y))

        # 영역 채우기
        fill_path = QPainterPath()
        fill_path.moveTo(QPointF(margin_x, h - 2))
        for pt in points:
            fill_path.lineTo(pt)
        fill_path.lineTo(QPointF(margin_x + draw_w, h - 2))
        fill_path.closeSubpath()

        fill_color = QColor(self._color)
        fill_color.setAlpha(40)
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, fill_color)
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawPath(fill_path)

        # 라인
        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for pt in points[1:]:
            line_path.lineTo(pt)

        painter.setPen(QPen(self._color, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line_path)

        painter.end()


class GaugeWidget(QWidget):
    """반원형 게이지 위젯 + 스파크라인

    270도 호(arc) 형태의 게이지.
    중앙에 큰 숫자, 아래에 라벨.
    하단에 미니 스파크라인 그래프.
    """

    def __init__(
        self,
        label: str = "",
        unit: str = "%",
        max_value: float = 100.0,
        color: str = "#4ecf72",
        parent=None,
    ):
        super().__init__(parent)
        self._value = 0.0
        self._max_value = max_value
        self._label = label
        self._unit = unit
        self._color = QColor(color)
        self._sub_text = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 게이지 그리기 영역
        self._gauge_area = _GaugeDrawArea(label, unit, max_value, color, self)
        layout.addWidget(self._gauge_area, stretch=1)

        # 스파크라인
        self._sparkline = SparklineWidget(color)
        self._sparkline.set_max_value(max_value)
        layout.addWidget(self._sparkline)

        self.setMinimumSize(120, 150)

    def set_value(self, value: float):
        self._value = min(value, self._max_value)
        self._gauge_area.set_value(self._value)
        self._sparkline.add_value(self._value)

    def set_sub_text(self, text: str):
        self._sub_text = text
        self._gauge_area.set_sub_text(text)

    @property
    def _max_value_prop(self):
        return self._max_value

    @_max_value_prop.setter
    def _max_value_prop(self, val):
        self._max_value = val
        self._gauge_area._max_value = val
        self._sparkline.set_max_value(val)


class _GaugeDrawArea(QWidget):
    """게이지 원호 그리기 전용 위젯"""

    def __init__(self, label, unit, max_value, color, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._max_value = max_value
        self._label = label
        self._unit = unit
        self._color = QColor(color)
        self._sub_text = ""

    def set_value(self, value: float):
        self._value = value
        self.update()

    def set_sub_text(self, text: str):
        self._sub_text = text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 게이지 영역 계산
        margin = 10
        gauge_size = min(w - margin * 2, h - 30)
        gauge_rect = QRectF(
            (w - gauge_size) / 2,
            margin,
            gauge_size,
            gauge_size,
        )

        # 배경 호 (어두운 트랙)
        pen = QPen(QColor("#3a3a3a"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        start_angle = 225 * 16
        span_angle = -270 * 16
        painter.drawArc(gauge_rect, start_angle, span_angle)

        # 값에 따른 호
        if self._max_value > 0:
            ratio = self._value / self._max_value
        else:
            ratio = 0
        value_span = int(-270 * 16 * ratio)

        pen.setColor(self._color)
        pen.setWidth(7)
        painter.setPen(pen)
        painter.drawArc(gauge_rect, start_angle, value_span)

        # 중앙 텍스트
        center_x = w / 2
        center_y = gauge_rect.center().y() + 5

        if self._value >= 100:
            display_val = f"{self._value:.0f}"
        elif self._value >= 10:
            display_val = f"{self._value:.1f}"
        else:
            display_val = f"{self._value:.1f}"

        font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))

        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(display_val)
        painter.drawText(
            int(center_x - text_width / 2),
            int(center_y + metrics.ascent() / 3),
            display_val,
        )

        # 단위 또는 보조 텍스트
        sub = self._sub_text if self._sub_text else self._unit
        font_sub = QFont("Segoe UI", 12)
        painter.setFont(font_sub)
        painter.setPen(QColor("#d0d0d0"))
        metrics_sub = painter.fontMetrics()
        sub_width = metrics_sub.horizontalAdvance(sub)
        painter.drawText(
            int(center_x - sub_width / 2),
            int(center_y + metrics.ascent() / 3 + 16),
            sub,
        )

        # 하단 라벨
        font_label = QFont("Malgun Gothic", 12)
        painter.setFont(font_label)
        painter.setPen(QColor("#d0d0d0"))
        label_metrics = painter.fontMetrics()
        label_width = label_metrics.horizontalAdvance(self._label)
        painter.drawText(
            int(center_x - label_width / 2),
            int(h - 3),
            self._label,
        )

        painter.end()
