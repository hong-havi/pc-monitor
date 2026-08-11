"""네트워크 속도 위젯 - 다운로드/업로드 속도 + 실시간 그래프"""
from collections import deque
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QPainterPath,
    QLinearGradient,
)


class NetworkGraph(QWidget):
    """네트워크 속도 실시간 라인 그래프"""

    HISTORY_SIZE = 60  # 60초간 데이터

    def __init__(self, parent=None):
        super().__init__(parent)
        self._download_history = deque([0.0] * self.HISTORY_SIZE, maxlen=self.HISTORY_SIZE)
        self._upload_history = deque([0.0] * self.HISTORY_SIZE, maxlen=self.HISTORY_SIZE)
        self._max_value = 1.0  # 자동 스케일
        self.setMinimumHeight(50)

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

        # 배경 그리드 라인
        painter.setPen(QPen(QColor("#333333"), 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            y = h * i / 4
            painter.drawLine(0, int(y), w, int(y))

        # 다운로드 라인 (초록)
        self._draw_line(
            painter, self._download_history, QColor("#4ecf72"), QColor(78, 207, 114, 30), w, h
        )

        # 업로드 라인 (파랑)
        self._draw_line(
            painter, self._upload_history, QColor("#4488ff"), QColor(68, 136, 255, 30), w, h
        )

        painter.end()

    def _draw_line(self, painter, data, line_color, fill_color, w, h):
        """라인 + 그라디언트 영역 그리기"""
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

        painter.setPen(QPen(line_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line_path)


class NetworkWidget(QWidget):
    """네트워크 속도 섹션"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # 타이틀
        title = QLabel("네트워크")
        title.setFont(QFont("Malgun Gothic", 14))
        title.setStyleSheet("color: #d0d0d0;")
        layout.addWidget(title)

        # 헤더: 다운/업 속도 표시
        header = QHBoxLayout()
        header.setSpacing(15)

        # 다운로드
        dl_layout = QVBoxLayout()
        dl_layout.setSpacing(0)
        dl_title = QLabel("↓ 다운")
        dl_title.setFont(QFont("Malgun Gothic", 12))
        dl_title.setStyleSheet("color: #d0d0d0;")
        dl_layout.addWidget(dl_title)

        self.dl_value = QLabel("0.0")
        self.dl_value.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.dl_value.setStyleSheet("color: #4ecf72;")
        dl_layout.addWidget(self.dl_value)

        self.dl_unit = QLabel("MB/s")
        self.dl_unit.setFont(QFont("Segoe UI", 12))
        self.dl_unit.setStyleSheet("color: #d0d0d0;")
        dl_layout.addWidget(self.dl_unit)

        header.addLayout(dl_layout)

        # 업로드
        ul_layout = QVBoxLayout()
        ul_layout.setSpacing(0)
        ul_title = QLabel("↑ 업")
        ul_title.setFont(QFont("Malgun Gothic", 12))
        ul_title.setStyleSheet("color: #d0d0d0;")
        ul_layout.addWidget(ul_title)

        self.ul_value = QLabel("0.0")
        self.ul_value.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.ul_value.setStyleSheet("color: #4488ff;")
        ul_layout.addWidget(self.ul_value)

        self.ul_unit = QLabel("MB/s")
        self.ul_unit.setFont(QFont("Segoe UI", 12))
        self.ul_unit.setStyleSheet("color: #d0d0d0;")
        ul_layout.addWidget(self.ul_unit)

        header.addLayout(ul_layout)
        header.addStretch()
        layout.addLayout(header)

        # 그래프
        self.graph = NetworkGraph()
        layout.addWidget(self.graph)

    def update_data(self, download_mbps: float, upload_mbps: float):
        self.dl_value.setText(f"{download_mbps:.1f}")
        self.ul_value.setText(f"{upload_mbps:.1f}")
        self.graph.add_data(download_mbps, upload_mbps)
