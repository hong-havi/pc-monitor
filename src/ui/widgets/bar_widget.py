"""클럭/전력 위젯 - 디자인 컴프 기준 레이아웃

클럭: CPU/GPU 큰 숫자 + 수평 프로그레스 바
전력: 합계 강조 + CPU/GPU W 하단 요약
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont


class ClockBarItem(QWidget):
    """클럭 단일 항목: 라벨 + 값 + 프로그레스 바"""

    def __init__(self, label: str, max_value: float, parent=None):
        super().__init__(parent)
        self._label = label
        self._value = 0.0
        self._max_value = max_value
        self._display_text = ""
        self._unit = ""
        self.setFixedHeight(56)

    def set_value(self, value: float, display_text: str, unit: str):
        self._value = value
        self._display_text = display_text
        self._unit = unit
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 상단 행: 라벨(좌) + 값+단위(우) — baseline을 충분히 아래로
        top_y = 28

        # 라벨
        font_label = QFont("Pretendard", 12, QFont.Weight.DemiBold)
        painter.setFont(font_label)
        painter.setPen(QColor("#c0c8d2"))
        painter.drawText(4, top_y, self._label)

        # 값 (오른쪽)
        font_val = QFont("Pretendard", 20, QFont.Weight.Bold)
        painter.setFont(font_val)
        painter.setPen(QColor("#f2f4f7"))
        val_metrics = painter.fontMetrics()
        val_w = val_metrics.horizontalAdvance(self._display_text)

        # 단위
        font_unit = QFont("Pretendard", 11)
        painter.setFont(font_unit)
        unit_metrics = painter.fontMetrics()
        unit_w = unit_metrics.horizontalAdvance(self._unit)

        total_text_w = val_w + unit_w + 4
        val_x = w - total_text_w - 4

        painter.setFont(font_val)
        painter.setPen(QColor("#f2f4f7"))
        painter.drawText(int(val_x), top_y, self._display_text)

        painter.setFont(font_unit)
        painter.setPen(QColor("#b0b8c4"))
        painter.drawText(int(val_x + val_w + 4), top_y, self._unit)

        # 프로그레스 바
        bar_y = top_y + 10
        bar_h = 10
        bar_x = 4
        bar_w = w - 8

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#23272e"))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 3, 3)

        # 값 채우기
        if self._max_value > 0:
            ratio = min(self._value / self._max_value, 1.0)
        else:
            ratio = 0
        fill_w = bar_w * ratio
        painter.setBrush(QColor("#3b82f6"))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 3, 3)

        painter.end()


class ClockWidget(QWidget):
    """클럭 섹션 (CPU GHz, GPU MHz)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(6)

        title = QLabel("클럭")
        title.setFont(QFont("Pretendard", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #e4e8ed;")
        layout.addWidget(title)

        layout.addStretch()

        self.cpu_bar = ClockBarItem("CPU", max_value=6.0)
        self.gpu_bar = ClockBarItem("GPU", max_value=3000.0)

        layout.addWidget(self.cpu_bar)
        layout.addWidget(self.gpu_bar)

        layout.addStretch()

    def update_data(self, cpu_clock_ghz: float, gpu_clock_mhz: float):
        self.cpu_bar.set_value(cpu_clock_ghz, f"{cpu_clock_ghz:.2f}", "GHz")
        self.gpu_bar.set_value(gpu_clock_mhz, f"{gpu_clock_mhz:.0f}", "MHz")


class PowerWidget(QWidget):
    """전력 섹션 - 합계 강조 + CPU/GPU W + 프로그레스 바"""

    MAX_POWER = 200.0  # 최대 전력 기준 (바 표시용)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cpu_power = 0.0
        self._gpu_power = 0.0
        self._total_power = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(8)

        title = QLabel("전력")
        title.setFont(QFont("Pretendard", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #e4e8ed;")
        layout.addWidget(title)

        layout.addStretch()

        # 합계 행: "합계" + 큰 숫자W
        self._total_area = _PowerDisplay(self)
        layout.addWidget(self._total_area)

        layout.addStretch()

    def update_data(self, cpu_power: float, gpu_power: float):
        self._cpu_power = cpu_power
        self._gpu_power = gpu_power
        self._total_power = cpu_power + gpu_power
        self._total_area.set_data(self._total_power, cpu_power, gpu_power, self.MAX_POWER)


class _PowerDisplay(QWidget):
    """전력 표시 영역: 합계 + 바 + CPU/GPU 분리"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 0.0
        self._cpu = 0.0
        self._gpu = 0.0
        self._max = 200.0
        self.setMinimumHeight(80)

    def set_data(self, total, cpu, gpu, max_val):
        self._total = total
        self._cpu = cpu
        self._gpu = gpu
        self._max = max_val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        color = QColor("#f5a524")

        # 레이아웃 계산: 상단 합계행, 중간 바, 하단 CPU/GPU
        # 합계 행 baseline (충분한 여백 확보)
        row1_baseline = 36

        # 합계 라벨 (왼쪽)
        font_label = QFont("Pretendard", 12, QFont.Weight.DemiBold)
        painter.setFont(font_label)
        painter.setPen(QColor("#c0c8d2"))
        painter.drawText(4, row1_baseline, "합계")

        # 큰 숫자 (오른쪽)
        font_val = QFont("Pretendard", 28, QFont.Weight.Bold)
        painter.setFont(font_val)
        painter.setPen(color)
        val_text = f"{self._total:.0f}"
        val_metrics = painter.fontMetrics()
        val_w = val_metrics.horizontalAdvance(val_text)

        font_unit = QFont("Pretendard", 13)
        painter.setFont(font_unit)
        unit_w = painter.fontMetrics().horizontalAdvance("W")

        total_w = val_w + unit_w + 3
        val_x = w - total_w - 4

        painter.setFont(font_val)
        painter.setPen(color)
        painter.drawText(int(val_x), row1_baseline, val_text)

        painter.setFont(font_unit)
        painter.setPen(QColor(color.red(), color.green(), color.blue(), 200))
        painter.drawText(int(val_x + val_w + 3), row1_baseline, "W")

        # 프로그레스 바
        bar_y = row1_baseline + 10
        bar_h = 12
        bar_x = 4
        bar_w = w - 8

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#23272e"))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 4, 4)

        ratio = min(self._total / self._max, 1.0) if self._max > 0 else 0
        fill_w = bar_w * ratio
        painter.setBrush(color)
        painter.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 4, 4)

        # 하단 CPU/GPU 분리 표시
        bottom_y = bar_y + bar_h + 18
        font_bottom = QFont("Pretendard", 11, QFont.Weight.DemiBold)
        painter.setFont(font_bottom)
        painter.setPen(QColor("#b0b8c4"))

        cpu_text = f"CPU {self._cpu:.0f}W"
        gpu_text = f"GPU {self._gpu:.0f}W"

        painter.drawText(4, int(bottom_y), cpu_text)
        gpu_w = painter.fontMetrics().horizontalAdvance(gpu_text)
        painter.drawText(int(w - gpu_w - 4), int(bottom_y), gpu_text)

        painter.end()
