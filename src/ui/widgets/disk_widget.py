"""디스크 위젯 - 드라이브별 사용량 바 + 잔여 공간 표시"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont


class DiskDriveBar(QWidget):
    """단일 드라이브 사용량 바"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drive = ""
        self._total_gb = 0.0
        self._used_gb = 0.0
        self._free_gb = 0.0
        self.setFixedHeight(32)

    def set_data(self, drive: str, total_gb: float, used_gb: float, free_gb: float):
        self._drive = drive
        self._total_gb = total_gb
        self._used_gb = used_gb
        self._free_gb = free_gb
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 드라이브 레이블 (왼쪽)
        font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(4, int(h / 2 + 5), self._drive)

        # 잔여 공간 텍스트 (오른쪽)
        font_val = QFont("Segoe UI", 12)
        painter.setFont(font_val)
        painter.setPen(QColor("#d0d0d0"))
        free_text = f"{self._free_gb:.0f}GB 남음"
        metrics = painter.fontMetrics()
        val_w = metrics.horizontalAdvance(free_text)
        painter.drawText(int(w - val_w - 4), int(h / 2 + 4), free_text)

        # 바 영역
        bar_x = 35
        bar_w = w - 45 - val_w
        bar_y = int(h / 2 - 4)
        bar_h = 8

        if bar_w < 10:
            bar_w = 10

        # 바 배경
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#3a3a3a"))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 3, 3)

        # 바 채우기
        if self._total_gb > 0:
            ratio = min(self._used_gb / self._total_gb, 1.0)
            fill_w = bar_w * ratio

            # 사용량에 따른 색상
            if ratio >= 0.9:
                color = QColor("#e63946")  # 빨강
            elif ratio >= 0.7:
                color = QColor("#f0a030")  # 주황
            else:
                color = QColor("#4ecf72")  # 초록

            painter.setBrush(color)
            painter.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 3, 3)

        painter.end()


class DiskWidget(QWidget):
    """디스크 섹션 - Read/Write 속도 + 드라이브별 사용량"""

    MAX_DRIVES = 4  # 최대 표시 드라이브 수

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # 타이틀
        title = QLabel("디스크")
        title.setFont(QFont("Malgun Gothic", 14))
        title.setStyleSheet("color: #d0d0d0;")
        layout.addWidget(title)

        # Read/Write 속도 헤더
        speed_row = QHBoxLayout()
        speed_row.setSpacing(12)

        # Read
        read_col = QVBoxLayout()
        read_col.setSpacing(0)
        read_label = QLabel("Read")
        read_label.setFont(QFont("Segoe UI", 12))
        read_label.setStyleSheet("color: #d0d0d0;")
        read_col.addWidget(read_label)
        self._read_value = QLabel("0.0 MB/s")
        self._read_value.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._read_value.setStyleSheet("color: #4ecf72;")
        read_col.addWidget(self._read_value)
        speed_row.addLayout(read_col)

        # Write
        write_col = QVBoxLayout()
        write_col.setSpacing(0)
        write_label = QLabel("Write")
        write_label.setFont(QFont("Segoe UI", 12))
        write_label.setStyleSheet("color: #d0d0d0;")
        write_col.addWidget(write_label)
        self._write_value = QLabel("0.0 MB/s")
        self._write_value.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._write_value.setStyleSheet("color: #4488ff;")
        write_col.addWidget(self._write_value)
        speed_row.addLayout(write_col)

        speed_row.addStretch()
        layout.addLayout(speed_row)

        # 드라이브 바들
        self._drive_bars: list[DiskDriveBar] = []
        for _ in range(self.MAX_DRIVES):
            bar = DiskDriveBar()
            bar.setVisible(False)
            self._drive_bars.append(bar)
            layout.addWidget(bar)

        layout.addStretch()

    def update_data(self, read_speed: float, write_speed: float, disks: list):
        """데이터 업데이트

        Args:
            read_speed: 읽기 속도 MB/s
            write_speed: 쓰기 속도 MB/s
            disks: [{drive, total_gb, used_gb, free_gb}, ...]
        """
        self._read_value.setText(f"{read_speed:.1f} MB/s")
        self._write_value.setText(f"{write_speed:.1f} MB/s")

        # 드라이브 바 업데이트
        for i, bar in enumerate(self._drive_bars):
            if i < len(disks):
                d = disks[i]
                bar.set_data(d['drive'], d['total_gb'], d['used_gb'], d['free_gb'])
                bar.setVisible(True)
            else:
                bar.setVisible(False)
