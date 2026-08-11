"""온도 위젯 - CPU/GPU/보드 온도를 수직 바 차트로 표시

디자인 컴프 기준:
- 수직 컬럼 바 차트 형태
- 상단에 온도 값 (색상 코딩)
- 중앙에 세로 바 (높이 = 온도%)
- 하단에 라벨 (CPU / GPU / 보드)

색상 규칙:
- 초록(#4ade80): temp < 60°C
- 주황(#f5a524): 60 <= temp < 80°C
- 빨강(#ef4444): temp >= 80°C
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen


def _temp_color(value: float) -> QColor:
    """온도 값에 따른 색상 반환"""
    if value >= 80:
        return QColor("#ef4444")
    elif value >= 60:
        return QColor("#f5a524")
    else:
        return QColor("#4ade80")


class TempColumnChart(QWidget):
    """수직 바 차트 (온도 표시용)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # [(label, value), ...]
        self.setMinimumHeight(60)

    def set_data(self, data: list):
        """data: [(label, value), ...]"""
        self._data = data
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        n = len(self._data)
        gap = 16
        bar_area_w = (w - gap * (n + 1)) / n
        if bar_area_w < 20:
            bar_area_w = 20

        # 영역 분할: 상단 온도값(22px) + 바 영역 + 하단 라벨(20px)
        top_text_h = 26
        bottom_label_h = 22
        bar_h = h - top_text_h - bottom_label_h - 10

        for i, (label, value) in enumerate(self._data):
            cx = gap + i * (bar_area_w + gap) + bar_area_w / 2
            bar_x = cx - bar_area_w / 2

            color = _temp_color(value)

            # 상단 온도값
            font_val = QFont("Pretendard", 14, QFont.Weight.Bold)
            painter.setFont(font_val)
            painter.setPen(color)
            val_text = f"{value:.0f}°" if value > 0 else "—"
            metrics = painter.fontMetrics()
            tw = metrics.horizontalAdvance(val_text)
            painter.drawText(int(cx - tw / 2), top_text_h - 4, val_text)

            # 바 (높이 비율: value / 100)
            ratio = min(value / 100.0, 1.0) if value > 0 else 0
            actual_bar_h = bar_h * ratio
            bar_y = top_text_h + bar_h - actual_bar_h

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(
                QRectF(bar_x + 4, bar_y, bar_area_w - 8, actual_bar_h),
                4, 4
            )

            # 하단 라벨
            font_label = QFont("Pretendard", 11, QFont.Weight.DemiBold)
            painter.setFont(font_label)
            painter.setPen(QColor("#9aa3ae"))
            metrics_l = painter.fontMetrics()
            lw = metrics_l.horizontalAdvance(label)
            painter.drawText(int(cx - lw / 2), int(h - 4), label)

        painter.end()


class TempWidget(QWidget):
    """온도 섹션 전체 위젯 (수직 컬럼 바 차트)"""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(6)

        # 타이틀
        self._title = QLabel("온도")
        self._title.setFont(QFont("Pretendard", 13, QFont.Weight.Bold))
        self._title.setStyleSheet("color: #cfd6de;")
        layout.addWidget(self._title)

        # 차트 영역
        self._chart = TempColumnChart()
        layout.addWidget(self._chart, stretch=1)

    def update_data(self, cpu_temp, gpu_temp, board_temp, ssd_temp=0.0,
                    cpu_temp_max=0.0, gpu_temp_max=0.0):
        data = [
            ("CPU", cpu_temp),
            ("GPU", gpu_temp),
            ("보드", board_temp),
        ]
        self._chart.set_data(data)
