"""디스크 위젯 - 드라이브별 사용량 바 + Read/Write 스파크라인 그래프

디자인 컴프:
- 헤더: "디스크" + R/W 속도 + 기간
- 드라이브별: 드라이브명 + 퍼센트 + "X / Y GB · ZGB 남음" + 프로그레스 바
- 하단: R/W 듀얼 라인 스파크라인
"""
from collections import deque
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QPainterPath


class DiskSparkline(QWidget):
    """디스크 R/W 스파크라인 그래프"""

    HISTORY_SIZE = 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self._read_history = deque([0.0] * self.HISTORY_SIZE, maxlen=self.HISTORY_SIZE)
        self._write_history = deque([0.0] * self.HISTORY_SIZE, maxlen=self.HISTORY_SIZE)
        self._max_value = 1.0
        self.setFixedHeight(34)

    def add_data(self, read_speed: float, write_speed: float):
        self._read_history.append(read_speed)
        self._write_history.append(write_speed)

        all_values = list(self._read_history) + list(self._write_history)
        max_val = max(all_values) if all_values else 1.0
        self._max_value = max(max_val * 1.2, 1.0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        if w <= 0 or h <= 0:
            painter.end()
            return

        # 그리드
        painter.setPen(QPen(QColor("#1d2128"), 1))
        for i in range(1, 3):
            y = h * i / 3
            painter.drawLine(0, int(y), w, int(y))

        # Read (초록) - 영역 + 라인
        self._draw_area_line(painter, self._read_history, QColor("#4ade80"), w, h)
        # Write (파랑) - 라인만
        self._draw_line(painter, self._write_history, QColor("#3b82f6"), w, h)

        painter.end()

    def _draw_area_line(self, painter, data, color, w, h):
        if len(data) < 2:
            return
        points = []
        for i, val in enumerate(data):
            x = w * i / (len(data) - 1)
            y = h - (val / self._max_value) * h
            y = max(1, min(h - 1, y))
            points.append(QPointF(x, y))

        fill_path = QPainterPath()
        fill_path.moveTo(QPointF(0, h))
        for pt in points:
            fill_path.lineTo(pt)
        fill_path.lineTo(QPointF(w, h))
        fill_path.closeSubpath()

        fill_color = QColor(color)
        fill_color.setAlpha(24)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill_color)
        painter.drawPath(fill_path)

        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for pt in points[1:]:
            line_path.lineTo(pt)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line_path)

    def _draw_line(self, painter, data, color, w, h):
        if len(data) < 2:
            return
        points = []
        for i, val in enumerate(data):
            x = w * i / (len(data) - 1)
            y = h - (val / self._max_value) * h
            y = max(1, min(h - 1, y))
            points.append(QPointF(x, y))

        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for pt in points[1:]:
            line_path.lineTo(pt)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line_path)


class DiskDriveItem(QWidget):
    """단일 드라이브 표시: 드라이브명 + % + 상세 + 프로그레스 바"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drive = ""
        self._total_gb = 0.0
        self._used_gb = 0.0
        self._free_gb = 0.0
        self._percent = 0.0
        self.setFixedHeight(44)

    def set_data(self, drive: str, total_gb: float, used_gb: float, free_gb: float):
        self._drive = drive
        self._total_gb = total_gb
        self._used_gb = used_gb
        self._free_gb = free_gb
        self._percent = (used_gb / total_gb * 100) if total_gb > 0 else 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 색상 결정: 70% 미만 초록, 70~90% 주황, 90%+ 빨강
        if self._percent >= 90:
            color = QColor("#ef4444")
        elif self._percent >= 70:
            color = QColor("#f5a524")
        else:
            color = QColor("#4ade80")

        # 상단 행: 드라이브명 + % + 상세
        top_y = 16

        # 드라이브명
        font_drive = QFont("Pretendard", 13, QFont.Weight.Bold)
        painter.setFont(font_drive)
        painter.setPen(QColor("#dce1e8"))
        painter.drawText(4, top_y, self._drive)

        drive_w = painter.fontMetrics().horizontalAdvance(self._drive)

        # 퍼센트
        font_pct = QFont("Pretendard", 12, QFont.Weight.DemiBold)
        painter.setFont(font_pct)
        painter.setPen(color)
        pct_text = f"{self._percent:.0f}%"
        painter.drawText(int(4 + drive_w + 10), top_y, pct_text)

        # 상세 정보 (오른쪽)
        font_detail = QFont("Pretendard", 11, QFont.Weight.DemiBold)
        painter.setFont(font_detail)
        painter.setPen(QColor("#b0b8c4"))
        detail_text = f"{self._used_gb:.0f} / {self._total_gb:.0f} GB · {self._free_gb:.0f}GB 남음"
        detail_w = painter.fontMetrics().horizontalAdvance(detail_text)
        painter.drawText(int(w - detail_w - 4), top_y, detail_text)

        # 프로그레스 바
        bar_y = top_y + 8
        bar_h = 14
        bar_x = 4
        bar_w = w - 8

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#23272e"))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 4, 4)

        ratio = min(self._percent / 100.0, 1.0)
        fill_w = bar_w * ratio
        painter.setBrush(color)
        painter.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 4, 4)

        painter.end()


class DiskWidget(QWidget):
    """디스크 섹션 - R/W 속도 헤더 + 드라이브 바 + 스파크라인"""

    MAX_DRIVES = 4

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(6)

        # 헤더: 타이틀 + R/W 속도
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("디스크")
        title.setFont(QFont("Pretendard", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #e4e8ed;")
        header.addWidget(title)

        header.addStretch()

        # R/W 속도 표시
        self._speed_label = QLabel("R 0.0  W 0.0 MB/s · 60초")
        self._speed_label.setFont(QFont("Pretendard", 10, QFont.Weight.DemiBold))
        self._speed_label.setStyleSheet("color: #b0b8c4;")
        header.addWidget(self._speed_label)

        layout.addLayout(header)

        # 드라이브 항목들
        self._drive_items: list[DiskDriveItem] = []
        for _ in range(self.MAX_DRIVES):
            item = DiskDriveItem()
            item.setVisible(False)
            self._drive_items.append(item)
            layout.addWidget(item)

        layout.addStretch()

        # 하단 스파크라인
        self._sparkline = DiskSparkline()
        layout.addWidget(self._sparkline)

    def update_data(self, read_speed: float, write_speed: float, disks: list):
        """데이터 업데이트"""
        # 속도 헤더 업데이트
        self._speed_label.setText(
            f"R {read_speed:.1f}  W {write_speed:.1f} MB/s · 60초"
        )

        # 드라이브 바 업데이트
        for i, item in enumerate(self._drive_items):
            if i < len(disks):
                d = disks[i]
                item.set_data(d['drive'], d['total_gb'], d['used_gb'], d['free_gb'])
                item.setVisible(True)
            else:
                item.setVisible(False)

        # 스파크라인 데이터
        self._sparkline.add_data(read_speed, write_speed)
