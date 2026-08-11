"""원형 게이지 위젯 - CPU/GPU 사용률, 메모리, VRAM 표시용 + 스파크라인

디자인: 반원형 아크 게이지 (270도) + 하단 영역 스파크라인
- 배경 트랙: #23272e
- 중앙에 큰 숫자 + 단위 텍스트
- 하단에 라벨(CPU/GPU/RAM/VRAM)
- 최하단에 미니 영역 차트 (스파크라인)
"""
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
        self.setFixedHeight(32)

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

        if w <= 0 or h <= 0:
            painter.end()
            return

        data = list(self._history)
        if len(data) < 2:
            painter.end()
            return

        # 포인트 계산
        points = []
        for i, val in enumerate(data):
            x = w * i / (len(data) - 1)
            ratio = min(val / self._max_value, 1.0) if self._max_value > 0 else 0
            y = h - ratio * h
            points.append(QPointF(x, y))

        # 영역 채우기
        fill_path = QPainterPath()
        fill_path.moveTo(QPointF(0, h))
        for pt in points:
            fill_path.lineTo(pt)
        fill_path.lineTo(QPointF(w, h))
        fill_path.closeSubpath()

        fill_color = QColor(self._color)
        fill_color.setAlpha(34)  # ~0x22
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill_color)
        painter.drawPath(fill_path)

        # 라인
        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for pt in points[1:]:
            line_path.lineTo(pt)

        painter.setPen(QPen(self._color, 2.2))
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
        color: str = "#4ade80",
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

        # 게이지 영역 계산 — 라벨 아래 공간 확보
        margin = 6
        label_space = 24
        available_h = h - label_space
        gauge_size = min(w - margin * 2, available_h - margin)
        if gauge_size < 40:
            gauge_size = 40

        gauge_rect = QRectF(
            (w - gauge_size) / 2,
            margin,
            gauge_size,
            gauge_size,
        )

        # 배경 호 (트랙)
        track_width = max(int(gauge_size * 0.09), 7)
        pen = QPen(QColor("#23272e"), track_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        # 270도 호: 시작 225도 → -270도 span
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
        pen.setWidth(track_width)
        painter.setPen(pen)
        painter.drawArc(gauge_rect, start_angle, value_span)

        # 중앙 텍스트 (값)
        center_x = w / 2
        center_y = gauge_rect.center().y() + gauge_size * 0.05

        if self._value >= 100:
            display_val = f"{self._value:.0f}"
        elif self._value >= 10:
            display_val = f"{self._value:.1f}"
        else:
            display_val = f"{self._value:.1f}"

        font_size = max(int(gauge_size * 0.28), 16)
        font = QFont("Pretendard", font_size, QFont.Weight.Bold)
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
        sub_font_size = max(int(gauge_size * 0.12), 10)
        font_sub = QFont("Pretendard", sub_font_size, QFont.Weight.DemiBold)
        painter.setFont(font_sub)
        painter.setPen(QColor("#8a929c"))
        metrics_sub = painter.fontMetrics()
        sub_width = metrics_sub.horizontalAdvance(sub)
        painter.drawText(
            int(center_x - sub_width / 2),
            int(center_y + metrics.ascent() / 3 + font_size * 0.55),
            sub,
        )

        # 하단 라벨 (CPU / GPU / RAM / VRAM)
        label_font_size = max(int(gauge_size * 0.16), 12)
        font_label = QFont("Pretendard", label_font_size, QFont.Weight.Bold)
        painter.setFont(font_label)
        painter.setPen(QColor("#b3bcc7"))
        label_metrics = painter.fontMetrics()
        label_width = label_metrics.horizontalAdvance(self._label)
        painter.drawText(
            int(center_x - label_width / 2),
            int(h - 4),
            self._label,
        )

        painter.end()
