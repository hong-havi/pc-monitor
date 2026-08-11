"""LibreHardwareMonitor 자동 실행/종료 관리

PCMonitor 시작 시 LHM을 백그라운드로 자동 실행하고,
PCMonitor 종료 시 같이 종료한다.

LHM이 이미 실행 중이면 중복 실행하지 않는다.
"""
import os
import sys
import time
import subprocess
import atexit
from typing import Optional


class LHMLauncher:
    """LHM 프로세스 자동 관리"""

    PROCESS_NAME = "LibreHardwareMonitor"

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._lhm_dir: Optional[str] = None
        self._we_started_it = False

        self._find_lhm_dir()

        if self._lhm_dir:
            self._start_if_not_running()

        # 프로그램 종료 시 LHM도 종료
        atexit.register(self.cleanup)

    def _find_lhm_dir(self):
        """LHM exe 경로 찾기"""
        # PyInstaller 번들 시
        if getattr(sys, '_MEIPASS', None):
            candidate = os.path.join(sys._MEIPASS, 'lhm')
            if os.path.exists(os.path.join(candidate, 'LibreHardwareMonitor.exe')):
                self._lhm_dir = candidate
                return

        # 소스 실행 시
        base = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(base))
        candidate = os.path.join(project_root, 'lib', 'lhm-096')
        if os.path.exists(os.path.join(candidate, 'LibreHardwareMonitor.exe')):
            self._lhm_dir = candidate
            return

        # 0.9.4 fallback
        candidate = os.path.join(project_root, 'lib', 'lhm-app')
        if os.path.exists(os.path.join(candidate, 'LibreHardwareMonitor.exe')):
            self._lhm_dir = candidate

    def _is_lhm_running(self) -> bool:
        """LHM이 이미 실행 중인지 확인"""
        try:
            result = subprocess.run(
                ['tasklist', '/fi', f'imagename eq {self.PROCESS_NAME}.exe', '/fo', 'csv', '/nh'],
                capture_output=True, text=True, timeout=5
            )
            return self.PROCESS_NAME in result.stdout
        except Exception:
            return False

    def _start_if_not_running(self):
        """LHM이 실행 중이 아니면 시작"""
        if self._is_lhm_running():
            return  # 이미 실행 중

        if not self._lhm_dir:
            return

        exe_path = os.path.join(self._lhm_dir, 'LibreHardwareMonitor.exe')
        try:
            # 숨김 상태로 백그라운드 실행
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE

            self._process = subprocess.Popen(
                [exe_path],
                cwd=self._lhm_dir,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._we_started_it = True

            # LHM 초기화 대기 후 창 숨기기
            time.sleep(2)
            self._hide_lhm_window()

        except Exception:
            self._process = None

    def cleanup(self):
        """우리가 시작한 LHM만 종료"""
        if self._we_started_it and self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass

    def _hide_lhm_window(self):
        """LHM 창을 숨기기 (Win32 API)"""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            SW_HIDE = 0

            def enum_callback(hwnd, _):
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if self._process and pid.value == self._process.pid:
                    user32.ShowWindow(hwnd, SW_HIDE)
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(
                ctypes.c_bool, wintypes.HWND, wintypes.LPARAM
            )
            user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
        except Exception:
            pass

    @property
    def is_running(self) -> bool:
        return self._is_lhm_running()
