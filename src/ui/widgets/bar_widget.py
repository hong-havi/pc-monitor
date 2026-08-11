"""프로그레스 바 위젯 - 클럭, 전력 등 수평 바 표시용"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont


class HorizontalBar(QWidget):
    """라벨 + 수평 프로그레스 바 + 값 텍스트"""

    def __init__(self, label: str, color: str, max_value: float = 100.0, parent=None):
        super().__init__(parent)
        self._label = label
        self._color = QColor(color)
        self._value = 0.0
        self._max_value = max_value
        self._display_text = ""
        self.setFixedHeight(36)

    def set_value(self, value: float, display_text: str = ""):
        self._value = value
        self._display_text = display_text or f"{value:.0f}"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 라벨 (왼쪽)
        font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(5, int(h / 2 + 5), self._label)

        # 값 텍스트 (오른쪽)
        font_val = QFont("Segoe UI", 14)
        painter.setFont(font_val)
        metrics = painter.fontMetrics()
        val_w = metrics.horizontalAdvance(self._display_text)
        painter.drawText(int(w - val_w - 5), int(h / 2 + 5), self._display_text)

        # 바 영역
        bar_x = 45
        bar_w = w - 55 - val_w
        bar_y = int(h / 2 - 4)
        bar_h = 8

        if bar_w < 10:
            bar_w = 10

        # 바 배경
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#3a3a3a"))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 4, 4)

        # 바 값
        if self._max_value > 0:
            ratio = min(self._value / self._max_value, 1.0)
        else:
            ratio = 0
        fill_w = bar_w * ratio

        painter.setBrush(self._color)
        painter.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 4, 4)

        painter.end()


class ClockWidget(QWidget):
    """클럭 섹션 (CPU GHz, GPU MHz)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)

        title = QLabel("클럭")
        title.setFont(QFont("Malgun Gothic", 14))
        title.setStyleSheet("color: #d0d0d0;")
        layout.addWidget(title)

        self.cpu_bar = HorizontalBar("CPU", "#4488ff", max_value=6.0)
        self.gpu_bar = HorizontalBar("GPU", "#4ecf72", max_value=3000.0)

        layout.addWidget(self.cpu_bar)
        layout.addWidget(self.gpu_bar)
        layout.addStretch()

    def update_data(self, cpu_clock_ghz: float, gpu_clock_mhz: float):
        self.cpu_bar.set_value(cpu_clock_ghz, f"{cpu_clock_ghz:.2f} GHz")
        self.gpu_bar.set_value(gpu_clock_mhz, f"{gpu_clock_mhz:.0f} MHz")


class PowerWidget(QWidget):
    """전력 섹션 (CPU W, GPU W, 합계)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        title = QLabel("전력")
        title.setFont(QFont("Malgun Gothic", 14))
        title.setStyleSheet("color: #d0d0d0;")
        layout.addWidget(title)

        # CPU 전력
        cpu_row = QHBoxLayout()
        cpu_row.setSpacing(4)
        cpu_label = QLabel("CPU")
        cpu_label.setFont(QFont("Segoe UI", 14))
        cpu_label.setStyleSheet("color: #d0d0d0;")
        cpu_label.setFixedWidth(35)
        cpu_row.addWidget(cpu_label)
        self.cpu_value = QLabel("0W")
        self.cpu_value.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.cpu_value.setStyleSheet("color: #ffffff;")
        cpu_row.addWidget(self.cpu_value)
        cpu_row.addStretch()
        layout.addLayout(cpu_row)

        # GPU 전력
        gpu_row = QHBoxLayout()
        gpu_row.setSpacing(4)
        gpu_label = QLabel("GPU")
        gpu_label.setFont(QFont("Segoe UI", 14))
        gpu_label.setStyleSheet("color: #d0d0d0;")
        gpu_label.setFixedWidth(35)
        gpu_row.addWidget(gpu_label)
        self.gpu_value = QLabel("0W")
        self.gpu_value.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.gpu_value.setStyleSheet("color: #ffffff;")
        gpu_row.addWidget(self.gpu_value)
        gpu_row.addStretch()
        layout.addLayout(gpu_row)

        layout.addStretch()

        # 합계 라인
        total_row = QHBoxLayout()
        total_row.setSpacing(4)
        total_label = QLabel("합계")
        total_label.setFont(QFont("Malgun Gothic", 14))
        total_label.setStyleSheet("color: #d0d0d0;")
        total_label.setFixedWidth(35)
        total_row.addWidget(total_label)
        self.total_value = QLabel("0W")
        self.total_value.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.total_value.setStyleSheet("color: #f0a030;")
        total_row.addWidget(self.total_value)
        total_row.addStretch()
        layout.addLayout(total_row)

    def update_data(self, cpu_power: float, gpu_power: float):
        self.cpu_value.setText(f"{cpu_power:.0f}W")
        self.gpu_value.setText(f"{gpu_power:.0f}W")
        total = cpu_power + gpu_power
        self.total_value.setText(f"{total:.0f}W")
