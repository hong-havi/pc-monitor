"""온도 위젯 - CPU/GPU/보드/SSD 온도를 수평 바 형태로 표시

색상 규칙:
- 초록(#4ecf72): temp < 60°C
- 주황(#f0a030): 60 <= temp < 80°C
- 빨강(#e63946): temp >= 80°C
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen


def _temp_color(value: float) -> QColor:
    """온도 값에 따른 색상 반환"""
    if value >= 80:
        return QColor("#e63946")
    elif value >= 60:
        return QColor("#f0a030")
    else:
        return QColor("#4ecf72")


class TempBar(QWidget):
    """단일 온도 수평 바 위젯 (라벨 + 바 + 값)"""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._label = label
        self.setFixedHeight(30)

    def set_value(self, value: float):
        self._value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 라벨 (왼쪽)
        font = QFont("Malgun Gothic", 14)
        painter.setFont(font)
        painter.setPen(QColor("#d0d0d0"))
        painter.drawText(4, int(h / 2 + 5), self._label)

        # 값 텍스트 (오른쪽)
        font_val = QFont("Segoe UI", 14, QFont.Weight.Bold)
        painter.setFont(font_val)

        if self._value > 0:
            color = _temp_color(self._value)
            painter.setPen(color)
            val_text = f"{self._value:.0f}°C"
        else:
            painter.setPen(QColor("#555555"))
            val_text = "—"

        metrics = painter.fontMetrics()
        val_w = metrics.horizontalAdvance(val_text)
        painter.drawText(int(w - val_w - 4), int(h / 2 + 5), val_text)

        # 바 영역
        bar_x = 40
        bar_w = w - 50 - val_w
        bar_y = int(h / 2 - 4)
        bar_h = 8

        if bar_w < 10:
            bar_w = 10

        # 바 배경
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#3a3a3a"))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 3, 3)

        # 바 채우기 (온도 기준 색상)
        if self._value > 0:
            ratio = min(self._value / 100.0, 1.0)
            fill_w = bar_w * ratio
            color = _temp_color(self._value)
            painter.setBrush(color)
            painter.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 3, 3)

        painter.end()


class TempWidget(QWidget):
    """온도 섹션 전체 위젯 (CPU, GPU, 보드, SSD)

    헤더에 최고 온도 표시: "최고 CPU XX° · GPU XX°"
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # 타이틀 + 최고온도
        self._title = QLabel("온도")
        self._title.setFont(QFont("Malgun Gothic", 14))
        self._title.setStyleSheet("color: #d0d0d0;")
        layout.addWidget(self._title)

        self._max_label = QLabel("최고 CPU —° · GPU —°")
        self._max_label.setFont(QFont("Malgun Gothic", 12))
        self._max_label.setStyleSheet("color: #999999;")
        layout.addWidget(self._max_label)

        # 바 영역
        self.cpu_bar = TempBar("CPU")
        self.gpu_bar = TempBar("GPU")
        self.board_bar = TempBar("보드")

        layout.addWidget(self.cpu_bar)
        layout.addWidget(self.gpu_bar)
        layout.addWidget(self.board_bar)
        layout.addStretch()

    def update_data(self, cpu_temp, gpu_temp, board_temp, ssd_temp=0.0,
                    cpu_temp_max=0.0, gpu_temp_max=0.0):
        self.cpu_bar.set_value(cpu_temp)
        self.gpu_bar.set_value(gpu_temp)
        self.board_bar.set_value(board_temp)

        # 최고 온도 헤더
        cpu_max_str = f"{cpu_temp_max:.0f}" if cpu_temp_max > 0 else "—"
        gpu_max_str = f"{gpu_temp_max:.0f}" if gpu_temp_max > 0 else "—"
        self._max_label.setText(f"최고 CPU {cpu_max_str}° · GPU {gpu_max_str}°")
