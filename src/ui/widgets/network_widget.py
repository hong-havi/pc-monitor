"""네트워크 속도 위젯 - 다운로드/업로드 속도 + 실시간 듀얼 라인 그래프

디자인:
- 헤더: "네트워크" + In/Out 범례
- 속도 표시: ↓ X.X MB/s  ↑ X.X MB/s
- 듀얼 라인 그래프 (In=초록, Out=파랑)
"""
from collections import deque
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QPainterPath,
    QLinearGradient,
)


class NetworkGraph(QWidget):
    """네트워크 속도 실시간 듀얼 라인 그래프"""

    HISTORY_SIZE = 60  # 60초간 데이터

    def __init__(self, parent=None):
        super().__init__(parent)
        self._download_history = deque([0.0] * self.HISTORY_SIZE, maxlen=self.HISTORY_SIZE)
        self._upload_history = deque([0.0] * self.HISTORY_SIZE, maxlen=self.HISTORY_SIZE)
        self._max_value = 1.0  # 자동 스케일
        self.setMinimumHeight(40)

    def add_data(self, download: float, upload: float):
        self._download_history.append(download)
        self._upload_history.append(upload)

        # 자동 스케일링
        all_values = list(self._download_history) + list(self._upload_history)
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

        # 배경 그리드 (수평선)
        painter.setPen(QPen(QColor("#1d2128"), 1))
        for i in range(1, 4):
            y = h * i / 4
            painter.drawLine(0, int(y), w, int(y))

        # 다운로드 영역 + 라인 (초록)
        self._draw_area_line(
            painter, self._download_history, QColor("#4ade80"), w, h
        )

        # 업로드 라인 (파랑, 영역 없음)
        self._draw_line_only(
            painter, self._upload_history, QColor("#3b82f6"), w, h
        )

        painter.end()

    def _draw_area_line(self, painter, data, line_color, w, h):
        """영역 채우기 + 라인"""
        if len(data) < 2:
            return

        points = []
        for i, val in enumerate(data):
            x = w * i / (len(data) - 1)
            y = h - (val / self._max_value) * h
            y = max(2, min(h - 2, y))
            points.append(QPointF(x, y))

        # 채우기 영역
        fill_path = QPainterPath()
        fill_path.moveTo(QPointF(0, h))
        for pt in points:
            fill_path.lineTo(pt)
        fill_path.lineTo(QPointF(w, h))
        fill_path.closeSubpath()

        fill_color = QColor(line_color)
        fill_color.setAlpha(24)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill_color)
        painter.drawPath(fill_path)

        # 라인
        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for pt in points[1:]:
            line_path.lineTo(pt)

        painter.setPen(QPen(line_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line_path)

    def _draw_line_only(self, painter, data, line_color, w, h):
        """라인만 (영역 없음)"""
        if len(data) < 2:
            return

        points = []
        for i, val in enumerate(data):
            x = w * i / (len(data) - 1)
            y = h - (val / self._max_value) * h
            y = max(2, min(h - 2, y))
            points.append(QPointF(x, y))

        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for pt in points[1:]:
            line_path.lineTo(pt)

        painter.setPen(QPen(line_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line_path)


class NetworkWidget(QWidget):
    """네트워크 속도 섹션"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(6)

        # 헤더: 타이틀 + 범례
        header = QHBoxLayout()
        header.setSpacing(10)

        title = QLabel("네트워크")
        title.setFont(QFont("Pretendard", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #e4e8ed;")
        header.addWidget(title)

        header.addStretch()

        # 범례
        legend = QLabel("● In  ● Out")
        legend.setFont(QFont("Pretendard", 10, QFont.Weight.DemiBold))
        legend.setStyleSheet("color: #b0b8c4;")
        header.addWidget(legend)

        layout.addLayout(header)

        # 속도 표시 행
        speed_row = QHBoxLayout()
        speed_row.setSpacing(20)

        # 다운로드
        self._dl_label = QLabel("↓ 0.0 MB/s")
        self._dl_label.setFont(QFont("Pretendard", 14, QFont.Weight.Bold))
        self._dl_label.setStyleSheet("color: #4ade80;")
        speed_row.addWidget(self._dl_label)

        # 업로드
        self._ul_label = QLabel("↑ 0.0 MB/s")
        self._ul_label.setFont(QFont("Pretendard", 14, QFont.Weight.Bold))
        self._ul_label.setStyleSheet("color: #3b82f6;")
        speed_row.addWidget(self._ul_label)

        speed_row.addStretch()
        layout.addLayout(speed_row)

        # 그래프
        self.graph = NetworkGraph()
        layout.addWidget(self.graph, stretch=1)

    def update_data(self, download_mbps: float, upload_mbps: float):
        self._dl_label.setText(f"↓ {download_mbps:.1f} MB/s")
        self._ul_label.setText(f"↑ {upload_mbps:.1f} MB/s")
        self.graph.add_data(download_mbps, upload_mbps)
