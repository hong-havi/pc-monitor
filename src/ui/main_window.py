"""메인 윈도우 - 디자인 컴프(PC Monitor Mini.dc.html) 기준 레이아웃

Layout (grid: auto 178px 1fr 1fr):
- Header: "PC MONITOR" + 상태 배지 + 가동시간 (좌) | 날짜/시간 + 전체화면 버튼 (우)
- Row 1: 4개 아크 게이지 + 스파크라인 (CPU, GPU, RAM, VRAM)
- Row 2: 온도(1.15fr) | 클럭(1fr) | 전력(0.9fr)
- Row 3: 네트워크(1fr) | 디스크(1.35fr)
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QShortcut, QKeySequence, QColor

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
                border-radius: 12px;
            }}
        """)
        self.setFrameShape(QFrame.Shape.StyledPanel)


class MainWindow(QMainWindow):
    """PC 모니터 대시보드 (디자인 컴프 반영)"""

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
        else:
            self.showFullScreen()

    def _exit_fullscreen(self):
        """전체화면 해제"""
        if self.isFullScreen():
            self.showNormal()

    def _setup_ui(self):
        """전체 UI 레이아웃 구성"""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(9)

        # === 헤더 ===
        header = self._create_header()
        main_layout.addLayout(header)

        # === Row 1: 4개 게이지 (고정 높이 비율) ===
        top_row = self._create_gauge_row()
        main_layout.addLayout(top_row)

        # === Row 2: 온도 | 클럭 | 전력 ===
        mid_row = self._create_middle_row()
        main_layout.addLayout(mid_row)

        # === Row 3: 네트워크 | 디스크 ===
        bottom_row = self._create_bottom_row()
        main_layout.addLayout(bottom_row)

        # === 하단 크레딧 ===
        credit = QLabel("By. Havi.hong")
        credit.setFont(QFont("Pretendard", 9))
        credit.setStyleSheet(f"color: {COLORS['text_dim']};")
        credit.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(credit)

    def _create_header(self) -> QHBoxLayout:
        """헤더 - 디자인 컴프 스타일"""
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(2, 0, 2, 0)

        # 좌측: 타이틀
        title = QLabel("PC MONITOR")
        title.setFont(QFont("Pretendard", 15, QFont.Weight.ExtraBold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; letter-spacing: 1px;")
        layout.addWidget(title)

        # 상태 배지
        self._status_label = QLabel("● 정상")
        self._status_label.setFont(QFont("Pretendard", 12, QFont.Weight.Bold))
        self._status_label.setStyleSheet(f"""
            color: {COLORS['status_normal']};
            background: rgba(74,222,128,0.14);
            border-radius: 10px;
            padding: 3px 10px;
        """)
        layout.addWidget(self._status_label)

        # 가동시간
        self._uptime_label = QLabel("가동 0일 00:00")
        self._uptime_label.setFont(QFont("Pretendard", 12, QFont.Weight.DemiBold))
        self._uptime_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self._uptime_label)

        layout.addStretch()

        # 우측: 날짜/시간
        self._datetime_label = QLabel("2026-08-11 (화) 09:06")
        self._datetime_label.setFont(QFont("Pretendard", 13, QFont.Weight.DemiBold))
        self._datetime_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self._datetime_label)

        # 전체화면 버튼
        self._fs_btn = QPushButton("⛶")
        self._fs_btn.setFont(QFont("Segoe UI", 12))
        self._fs_btn.setFixedSize(30, 30)
        self._fs_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_label']};
                border: 1px solid {COLORS['bg_card_border']};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_border']};
                color: {COLORS['text_primary']};
            }}
        """)
        self._fs_btn.clicked.connect(self._toggle_fullscreen)
        layout.addWidget(self._fs_btn)

        return layout

    def _create_gauge_row(self) -> QHBoxLayout:
        """상단 4개 원형 게이지 + 스파크라인"""
        layout = QHBoxLayout()
        layout.setSpacing(9)

        card1 = CardFrame()
        card1_layout = QVBoxLayout(card1)
        card1_layout.setContentsMargins(4, 4, 4, 0)
        self._gauge_cpu = GaugeWidget("CPU", "%", 100.0, COLORS["gauge_cpu"], threshold_mode="cpu")
        card1_layout.addWidget(self._gauge_cpu)
        layout.addWidget(card1)

        card2 = CardFrame()
        card2_layout = QVBoxLayout(card2)
        card2_layout.setContentsMargins(4, 4, 4, 0)
        self._gauge_gpu = GaugeWidget("GPU", "%", 100.0, COLORS["gauge_gpu"], threshold_mode=None)
        card2_layout.addWidget(self._gauge_gpu)
        layout.addWidget(card2)

        card3 = CardFrame()
        card3_layout = QVBoxLayout(card3)
        card3_layout.setContentsMargins(4, 4, 4, 0)
        self._gauge_mem = GaugeWidget("RAM", "", 32.0, COLORS["gauge_mem"], threshold_mode="ram")
        card3_layout.addWidget(self._gauge_mem)
        layout.addWidget(card3)

        card4 = CardFrame()
        card4_layout = QVBoxLayout(card4)
        card4_layout.setContentsMargins(4, 4, 4, 0)
        self._gauge_vram = GaugeWidget("VRAM", "", 12.0, COLORS["gauge_vram"], threshold_mode="ram")
        card4_layout.addWidget(self._gauge_vram)
        layout.addWidget(card4)

        return layout

    def _create_middle_row(self) -> QHBoxLayout:
        """중단: 온도(1.15) | 클럭(1) | 전력(0.9)"""
        layout = QHBoxLayout()
        layout.setSpacing(9)

        temp_card = CardFrame()
        temp_layout = QVBoxLayout(temp_card)
        temp_layout.setContentsMargins(0, 0, 0, 0)
        self._temp_widget = TempWidget()
        temp_layout.addWidget(self._temp_widget)
        layout.addWidget(temp_card, stretch=115)

        clock_card = CardFrame()
        clock_layout = QVBoxLayout(clock_card)
        clock_layout.setContentsMargins(0, 0, 0, 0)
        self._clock_widget = ClockWidget()
        clock_layout.addWidget(self._clock_widget)
        layout.addWidget(clock_card, stretch=100)

        power_card = CardFrame()
        power_layout = QVBoxLayout(power_card)
        power_layout.setContentsMargins(0, 0, 0, 0)
        self._power_widget = PowerWidget()
        power_layout.addWidget(self._power_widget)
        layout.addWidget(power_card, stretch=90)

        return layout

    def _create_bottom_row(self) -> QHBoxLayout:
        """하단: 네트워크(1) | 디스크(1.35)"""
        layout = QHBoxLayout()
        layout.setSpacing(9)

        net_card = CardFrame()
        net_layout = QVBoxLayout(net_card)
        net_layout.setContentsMargins(0, 0, 0, 0)
        self._net_widget = NetworkWidget()
        net_layout.addWidget(self._net_widget)
        layout.addWidget(net_card, stretch=100)

        disk_card = CardFrame()
        disk_layout = QVBoxLayout(disk_card)
        disk_layout.setContentsMargins(0, 0, 0, 0)
        self._disk_widget = DiskWidget()
        disk_layout.addWidget(self._disk_widget)
        layout.addWidget(disk_card, stretch=135)

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

        # 헤더 업데이트
        uptime_str = self._format_uptime(data.uptime_seconds)
        self._uptime_label.setText(f"가동 {uptime_str}")

        # 상태 배지
        if data.status == "정상":
            self._status_label.setText("● 정상")
            self._status_label.setStyleSheet(f"""
                color: {COLORS['status_normal']};
                background: rgba(74,222,128,0.14);
                border-radius: 10px;
                padding: 3px 10px;
            """)
        elif data.status == "높음":
            self._status_label.setText("● 높음")
            self._status_label.setStyleSheet(f"""
                color: {COLORS['status_warning']};
                background: rgba(245,165,36,0.14);
                border-radius: 10px;
                padding: 3px 10px;
            """)
        else:
            self._status_label.setText("● 경고")
            self._status_label.setStyleSheet(f"""
                color: {COLORS['status_critical']};
                background: rgba(239,68,68,0.14);
                border-radius: 10px;
                padding: 3px 10px;
            """)

        # 날짜/시간
        now = datetime.now()
        day_names = ["월", "화", "수", "목", "금", "토", "일"]
        day_name = day_names[now.weekday()]
        self._datetime_label.setText(now.strftime(f"%Y-%m-%d ({day_name}) %H:%M"))

        # 게이지
        self._gauge_cpu.set_value(data.cpu_usage)
        self._gauge_gpu.set_value(data.gpu_usage)

        self._gauge_mem.set_value(data.mem_used)
        self._gauge_mem.set_sub_text(f"/ {data.mem_total:.0f} GB")
        self._gauge_mem._gauge_area._max_value = data.mem_total
        self._gauge_mem._sparkline.set_max_value(data.mem_total)

        self._gauge_vram.set_value(data.gpu_vram_used)
        self._gauge_vram.set_sub_text(f"/ {data.gpu_vram_total:.0f} GB")
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
