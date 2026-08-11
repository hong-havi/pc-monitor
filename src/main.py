"""PC Monitor Dashboard - 960x640 미니모니터용 하드웨어 대시보드"""
import sys
import os
import logging

# 로그 설정 (exe 실행 시 디버깅용)
log_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else '.', 'pcmonitor.log')
logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s %(message)s')

from core.lhm_launcher import LHMLauncher
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow


def main():
    # LHM 자동 실행 (앱보다 먼저 시작해야 WMI/HTTP 준비됨)
    lhm = LHMLauncher()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
