"""메인 윈도우 - 리사이즈 가능 + 전체화면 대시보드 레이아웃

Layout:
- Header: 타이틀 + 상태 + 가동시간 (좌) | 전체화면 버튼 + 날짜/시간 (우)
- Row 1: 4개 아크 게이지 + 스파크라인 (CPU, GPU, RAM, VRAM)
- Row 2: 온도 | 클럭 | 전력
- Row 3: 네트워크 | 디스크
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QShortcut, QKeySequence

from ui.styles import MAIN_STYLESHEET, COLORS
from ui.widgets import GaugeWidget, TempWidget, NetworkWidget, ClockWidget, PowerWidget, DiskWidget
from core.hardware_monitor import HardwareMonitor


class CardFrame(QFrame):
    """둥근 모서리 카드 프레임"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['bg_card_border']};
                border-radius: 10px;
            }}
        """)
        self.setFrameShape(QFrame.Shape.StyledPanel)


class MainWindow(QMainWindow):
    """리사이즈 가능 PC 모니터 대시보드"""

    UPDATE_INTERVAL_MS = 1000

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC MONITOR")
        self.resize(960, 640)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(MAIN_STYLESHEET)

        # 하드웨어 모니터
        self._monitor = HardwareMonitor()

        # UI 구성
        self._setup_ui()

        # 단축키: F11 전체화면 토글, Esc 전체화면 해제
        QShortcut(QKeySequence("F11"), self, self._toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self, self._exit_fullscreen)

        # 업데이트 타이머
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_data)
        self._timer.start(self.UPDATE_INTERVAL_MS)

        # 초기 데이터 수집
        self._update_data()

    def _toggle_fullscreen(self):
        """전체화면 토글"""
        if self.isFullScreen():
            self.showNormal()
            self._fs_btn.setText("⛶")
        else:
            self.showFullScreen()
            self._fs_btn.setText("⮌")

    def _exit_fullscreen(self):
        """전체화면 해제"""
        if self.isFullScreen():
            self.showNormal()
            self._fs_btn.setText("⛶")

    def _setup_ui(self):
        """전체 UI 레이아웃 구성"""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(14, 10, 14, 10)
        main_layout.setSpacing(10)

        # === 헤더 ===
        header = self._create_header()
        main_layout.addLayout(header)

        # === Row 1: 4개 게이지 ===
        top_row = self._create_gauge_row()
        main_layout.addLayout(top_row)

        # === Row 2: 온도 | 클럭 | 전력 ===
        mid_row = self._create_middle_row()
        main_layout.addLayout(mid_row)

        # === Row 3: 네트워크 | 디스크 ===
        bottom_row = self._create_bottom_row()
        main_layout.addLayout(bottom_row)

    def _create_header(self) -> QHBoxLayout:
        """헤더"""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        # 좌측: 타이틀 + 상태 + 가동시간
        self._header_left = QLabel("PC MONITOR · 정상  가동 0일 00:00")
        self._header_left.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._header_left.setStyleSheet("color: #ffffff;")
        layout.addWidget(self._header_left)

        layout.addStretch()

        # 전체화면 버튼
        self._fs_btn = QPushButton("⛶")
        self._fs_btn.setFont(QFont("Segoe UI", 16))
        self._fs_btn.setFixedSize(36, 36)
        self._fs_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #d0d0d0;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                color: #ffffff;
            }
        """)
        self._fs_btn.clicked.connect(self._toggle_fullscreen)
        layout.addWidget(self._fs_btn)

        # 우측: 날짜/시간
        self._header_right = QLabel("2026-01-01 (월) 00:00")
        self._header_right.setFont(QFont("Segoe UI", 14))
        self._header_right.setStyleSheet("color: #d0d0d0;")
        layout.addWidget(self._header_right)

        return layout

    def _create_gauge_row(self) -> QHBoxLayout:
        """상단 4개 원형 게이지 + 스파크라인"""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        card1 = CardFrame()
        card1_layout = QVBoxLayout(card1)
        card1_layout.setContentsMargins(4, 4, 4, 4)
        self._gauge_cpu = GaugeWidget("CPU", "%", 100.0, COLORS["gauge_cpu"])
        card1_layout.addWidget(self._gauge_cpu)
        layout.addWidget(card1)

        card2 = CardFrame()
        card2_layout = QVBoxLayout(card2)
        card2_layout.setContentsMargins(4, 4, 4, 4)
        self._gauge_gpu = GaugeWidget("GPU", "%", 100.0, COLORS["gauge_gpu"])
        card2_layout.addWidget(self._gauge_gpu)
        layout.addWidget(card2)

        card3 = CardFrame()
        card3_layout = QVBoxLayout(card3)
        card3_layout.setContentsMargins(4, 4, 4, 4)
        self._gauge_mem = GaugeWidget("RAM", "", 32.0, COLORS["gauge_mem"])
        card3_layout.addWidget(self._gauge_mem)
        layout.addWidget(card3)

        card4 = CardFrame()
        card4_layout = QVBoxLayout(card4)
        card4_layout.setContentsMargins(4, 4, 4, 4)
        self._gauge_vram = GaugeWidget("VRAM", "", 12.0, COLORS["gauge_vram"])
        card4_layout.addWidget(self._gauge_vram)
        layout.addWidget(card4)

        return layout

    def _create_middle_row(self) -> QHBoxLayout:
        """중단: 온도 | 클럭 | 전력"""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        temp_card = CardFrame()
        temp_layout = QVBoxLayout(temp_card)
        temp_layout.setContentsMargins(4, 4, 4, 4)
        self._temp_widget = TempWidget()
        temp_layout.addWidget(self._temp_widget)
        layout.addWidget(temp_card, stretch=3)

        clock_card = CardFrame()
        clock_layout = QVBoxLayout(clock_card)
        clock_layout.setContentsMargins(4, 4, 4, 4)
        self._clock_widget = ClockWidget()
        clock_layout.addWidget(self._clock_widget)
        layout.addWidget(clock_card, stretch=3)

        power_card = CardFrame()
        power_layout = QVBoxLayout(power_card)
        power_layout.setContentsMargins(4, 4, 4, 4)
        self._power_widget = PowerWidget()
        power_layout.addWidget(self._power_widget)
        layout.addWidget(power_card, stretch=2)

        return layout

    def _create_bottom_row(self) -> QHBoxLayout:
        """하단: 네트워크 | 디스크"""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        net_card = CardFrame()
        net_layout = QVBoxLayout(net_card)
        net_layout.setContentsMargins(4, 4, 4, 4)
        self._net_widget = NetworkWidget()
        net_layout.addWidget(self._net_widget)
        layout.addWidget(net_card, stretch=3)

        disk_card = CardFrame()
        disk_layout = QVBoxLayout(disk_card)
        disk_layout.setContentsMargins(4, 4, 4, 4)
        self._disk_widget = DiskWidget()
        disk_layout.addWidget(self._disk_widget)
        layout.addWidget(disk_card, stretch=3)

        return layout

    def _format_uptime(self, seconds: int) -> str:
        days = seconds // 86400
        remaining = seconds % 86400
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        return f"{days}일 {hours:02d}:{minutes:02d}"

    def _update_data(self):
        """주기적 데이터 업데이트"""
        data = self._monitor.collect()

        # 헤더
        uptime_str = self._format_uptime(data.uptime_seconds)
        self._header_left.setText(
            f"PC MONITOR · {data.status}  가동 {uptime_str}"
        )

        now = datetime.now()
        day_names = ["월", "화", "수", "목", "금", "토", "일"]
        day_name = day_names[now.weekday()]
        self._header_right.setText(now.strftime(f"%Y-%m-%d ({day_name}) %H:%M"))

        # 게이지
        self._gauge_cpu.set_value(data.cpu_usage)
        self._gauge_gpu.set_value(data.gpu_usage)

        self._gauge_mem.set_value(data.mem_used)
        self._gauge_mem.set_sub_text(f"{data.mem_used:.1f}/{data.mem_total:.0f} GB")
        self._gauge_mem._gauge_area._max_value = data.mem_total
        self._gauge_mem._sparkline.set_max_value(data.mem_total)

        self._gauge_vram.set_value(data.gpu_vram_used)
        self._gauge_vram.set_sub_text(f"{data.gpu_vram_used:.1f}/{data.gpu_vram_total:.0f} GB")
        vram_max = max(data.gpu_vram_total, 1.0)
        self._gauge_vram._gauge_area._max_value = vram_max
        self._gauge_vram._sparkline.set_max_value(vram_max)

        # 온도
        self._temp_widget.update_data(
            data.cpu_temp, data.gpu_temp, data.board_temp, data.ssd_temp,
            cpu_temp_max=data.cpu_temp_max,
            gpu_temp_max=data.gpu_temp_max,
        )

        # 클럭
        self._clock_widget.update_data(data.cpu_clock, data.gpu_clock)

        # 전력
        self._power_widget.update_data(data.cpu_power, data.gpu_power)

        # 네트워크
        self._net_widget.update_data(data.net_download, data.net_upload)

        # 디스크
        self._disk_widget.update_data(
            data.disk_read_speed, data.disk_write_speed, data.disks
        )

    def closeEvent(self, event):
        self._timer.stop()
        self._monitor.cleanup()
        event.accept()
