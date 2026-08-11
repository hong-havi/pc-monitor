"""센서 데이터 읽기 (다중 소스 지원)

우선순위:
1. LHM HTTP 웹서버 (http://localhost:8085/data.json) - LHM GUI 실행 + 웹서버 활성화 시
2. LHM WMI (root\\LibreHardwareMonitor) - LHM GUI 실행 시
3. LibreHardwareMonitorLib.dll 직접 로드 (pythonnet) - DLL 번들 시

CPU 온도를 정확히 읽으려면 LHM 최신 버전(0.9.6+)을 관리자 권한으로 실행하고
Options > HTTP Server 를 활성화해야 함.
"""
import json
import os
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass
from typing import Optional

try:
    import clr
    CLR_AVAILABLE = True
except ImportError:
    CLR_AVAILABLE = False

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False


@dataclass
class SensorData:
    """센서 데이터"""
    cpu_temp: float = 0.0
    cpu_clock: float = 0.0
    cpu_power: float = 0.0
    cpu_fan: int = 0
    gpu_temp: float = 0.0
    gpu_clock: float = 0.0
    gpu_power: float = 0.0
    gpu_fan: int = 0
    board_temp: float = 0.0
    ssd_temp: float = 0.0
    case_fan: int = 0


class LHMReader:
    """센서 읽기 (HTTP > WMI > DLL 직접 로드 순으로 시도)"""

    LHM_HTTP_URL = "http://localhost:8085/data.json"

    def __init__(self, lib_dir: Optional[str] = None):
        self._lock = threading.Lock()
        self._data = SensorData()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._source = "none"  # 현재 데이터 소스

        # DLL 관련
        self._computer = None
        self._dll_initialized = False

        if lib_dir is None:
            if getattr(sys, '_MEIPASS', None):
                lib_dir = os.path.join(sys._MEIPASS, 'lib')
            else:
                base = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(base))
                lib_dir = os.path.join(project_root, 'lib', 'lhm', 'lib', 'net472')

        self._lib_dir = lib_dir
        self._hidsharp_dir = lib_dir  # 기본값

        if not getattr(sys, '_MEIPASS', None):
            base = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(base))
            self._hidsharp_dir = os.path.join(project_root, 'lib', 'hidsharp', 'lib', 'net35')

        # DLL 초기화 (메인 스레드에서 해야 함)
        self._init_dll()

        # 백그라운드 스레드 시작
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def _update_loop(self):
        """백그라운드 업데이트 루프 - 사용 가능한 소스를 자동 감지"""
        while not self._stop_event.is_set():
            # 1순위: HTTP 웹서버
            if self._try_http():
                self._source = "http"
            # 2순위: WMI
            elif self._try_wmi():
                self._source = "wmi"
            # 3순위: DLL 직접
            elif self._dll_initialized:
                self._try_dll()
                self._source = "dll"

            self._stop_event.wait(2.0)

    def _try_http(self) -> bool:
        """LHM HTTP 웹서버에서 JSON 데이터 읽기"""
        try:
            resp = urllib.request.urlopen(self.LHM_HTTP_URL, timeout=1)
            raw = json.loads(resp.read())
            self._parse_lhm_json(raw)
            return True
        except Exception:
            return False

    def _parse_lhm_json(self, data: dict):
        """LHM JSON 트리 구조 파싱 (재귀)"""
        result = SensorData()
        self._walk_json_node(data, result)
        with self._lock:
            self._data = result

    def _walk_json_node(self, node: dict, data: SensorData):
        """JSON 트리를 재귀 탐색하며 센서 값 추출"""
        # node 구조: { "id", "Text", "Min", "Max", "Value", "Children": [...] }
        text = node.get("Text", "")
        value_str = node.get("Value", "")
        children = node.get("Children", [])

        # 센서 값 파싱
        if value_str and value_str != "-":
            try:
                # "45.0 °C", "3800 MHz", "65.2 W", "1200 RPM" 형태
                val = float(value_str.split()[0].replace(",", "."))
                self._classify_sensor(text, val, node, data)
            except (ValueError, IndexError):
                pass

        # 자식 노드 재귀 탐색
        for child in children:
            self._walk_json_node(child, data)

    def _classify_sensor(self, name: str, value: float, node: dict, data: SensorData):
        """센서 이름과 값으로 분류"""
        name_lower = name.lower()
        # 상위 노드의 ImageURL이나 id로 하드웨어 타입 판별이 어려우므로
        # 이름 기반으로 분류
        
        # 온도
        if "°C" in node.get("Value", "") or "°c" in node.get("Value", ""):
            if value <= 0:
                return
            if "tctl" in name_lower or "tdie" in name_lower or ("core" in name_lower and "gpu" not in name_lower):
                data.cpu_temp = max(data.cpu_temp, value)
            elif "gpu" in name_lower:
                data.gpu_temp = max(data.gpu_temp, value)
            elif "board" in name_lower or "system" in name_lower or "motherboard" in name_lower:
                data.board_temp = max(data.board_temp, value)

        # 클럭 (MHz/GHz)
        elif "MHz" in node.get("Value", "") or "GHz" in node.get("Value", ""):
            if "core" in name_lower and "gpu" not in name_lower:
                if "GHz" in node.get("Value", ""):
                    data.cpu_clock = max(data.cpu_clock, value)
                else:
                    data.cpu_clock = max(data.cpu_clock, value / 1000.0)
            elif "gpu" in name_lower and "core" in name_lower:
                data.gpu_clock = max(data.gpu_clock, value)

        # 전력 (W)
        elif "W" in node.get("Value", ""):
            if "package" in name_lower or ("cpu" in name_lower and "gpu" not in name_lower):
                data.cpu_power = max(data.cpu_power, value)
            elif "gpu" in name_lower:
                data.gpu_power = max(data.gpu_power, value)

        # 팬 (RPM)
        elif "RPM" in node.get("Value", ""):
            if value <= 0:
                return
            if "cpu" in name_lower:
                data.cpu_fan = max(data.cpu_fan, int(value))
            elif "gpu" in name_lower:
                data.gpu_fan = max(data.gpu_fan, int(value))
            else:
                data.case_fan = max(data.case_fan, int(value))

    def _try_wmi(self) -> bool:
        """LHM WMI namespace에서 센서 읽기"""
        if not WMI_AVAILABLE:
            return False
        try:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                w = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
                sensors = w.Sensor()
                if not sensors:
                    return False

                result = SensorData()
                for s in sensors:
                    self._parse_wmi_sensor(s, result)

                with self._lock:
                    self._data = result
                return True
            finally:
                pythoncom.CoUninitialize()
        except Exception:
            return False

    def _parse_wmi_sensor(self, sensor, data: SensorData):
        """WMI 센서 파싱"""
        name = sensor.Name or ""
        stype = sensor.SensorType or ""
        parent = sensor.Parent or ""
        value = sensor.Value
        if value is None or value <= 0:
            return

        pl = parent.lower()
        nl = name.lower()

        if stype == "Temperature":
            if "cpu" in pl:
                data.cpu_temp = max(data.cpu_temp, value)
            elif "gpu" in pl:
                data.gpu_temp = max(data.gpu_temp, value)
            elif "motherboard" in pl:
                data.board_temp = max(data.board_temp, value)
            elif "nvme" in pl or "ssd" in pl or "drive" in pl or "hdd" in pl:
                data.ssd_temp = max(data.ssd_temp, value)
        elif stype == "Clock":
            if "cpu" in pl and "core" in nl:
                data.cpu_clock = max(data.cpu_clock, value / 1000.0)
            elif "gpu" in pl:
                data.gpu_clock = max(data.gpu_clock, value)
        elif stype == "Power":
            if "cpu" in pl:
                data.cpu_power = max(data.cpu_power, value)
            elif "gpu" in pl:
                data.gpu_power = max(data.gpu_power, value)
        elif stype == "Fan":
            if "cpu" in nl:
                data.cpu_fan = max(data.cpu_fan, int(value))
            elif "gpu" in pl:
                data.gpu_fan = max(data.gpu_fan, int(value))
            else:
                data.case_fan = max(data.case_fan, int(value))

    def _init_dll(self):
        """LHM DLL 직접 로드"""
        if not CLR_AVAILABLE:
            import logging
            logging.warning("[LHMReader] pythonnet(clr) not available")
            return
        try:
            dll_path = os.path.join(self._lib_dir, 'LibreHardwareMonitorLib.dll')
            import logging
            logging.info(f"[LHMReader] lib_dir={self._lib_dir}, dll exists={os.path.exists(dll_path)}")
            if not os.path.exists(dll_path):
                return

            sys.path.append(self._lib_dir)
            clr.AddReference(dll_path)

            hidsharp_dll = os.path.join(self._hidsharp_dir, 'HidSharp.dll')
            if os.path.exists(hidsharp_dll):
                sys.path.append(self._hidsharp_dir)
                clr.AddReference(hidsharp_dll)

            from LibreHardwareMonitor.Hardware import Computer
            self._computer = Computer()
            self._computer.IsCpuEnabled = True
            self._computer.IsGpuEnabled = True
            self._computer.IsMotherboardEnabled = True
            self._computer.IsStorageEnabled = True
            self._computer.Open()
            self._dll_initialized = True
            logging.info("[LHMReader] DLL init SUCCESS")
        except Exception as e:
            self._dll_initialized = False
            import logging
            logging.warning(f"[LHMReader] DLL init failed: {e}")

    def _try_dll(self):
        """DLL로 직접 센서 읽기"""
        if not self._dll_initialized or not self._computer:
            return

        from LibreHardwareMonitor.Hardware import SensorType, HardwareType

        result = SensorData()
        try:
            for hw in self._computer.Hardware:
                hw.Update()
                self._process_hw(hw, result, SensorType, HardwareType)
                for sub in hw.SubHardware:
                    sub.Update()
                    self._process_hw(sub, result, SensorType, HardwareType)

            with self._lock:
                self._data = result
        except Exception:
            pass

    def _process_hw(self, hw, data: SensorData, SensorType, HardwareType):
        """DLL 하드웨어 센서 처리"""
        hw_type = hw.HardwareType
        is_cpu = hw_type == HardwareType.Cpu
        is_gpu = hw_type in (HardwareType.GpuAmd, HardwareType.GpuNvidia, HardwareType.GpuIntel)
        is_mobo = hw_type == HardwareType.Motherboard
        is_storage = hw_type == HardwareType.Storage

        for sensor in hw.Sensors:
            value = sensor.Value
            if value is None or value <= 0:
                continue
            # nan 체크
            if value != value:
                continue

            name_lower = (sensor.Name or "").lower()
            stype = sensor.SensorType

            if stype == SensorType.Temperature:
                if is_cpu:
                    data.cpu_temp = max(data.cpu_temp, value)
                elif is_gpu:
                    data.gpu_temp = max(data.gpu_temp, value)
                elif is_mobo:
                    data.board_temp = max(data.board_temp, value)
                elif is_storage:
                    data.ssd_temp = max(data.ssd_temp, value)
            elif stype == SensorType.Clock:
                if is_cpu and "core" in name_lower:
                    data.cpu_clock = max(data.cpu_clock, value / 1000.0)
                elif is_gpu and ("core" in name_lower or "shader" in name_lower):
                    data.gpu_clock = max(data.gpu_clock, value)
            elif stype == SensorType.Power:
                if is_cpu:
                    data.cpu_power = max(data.cpu_power, value)
                elif is_gpu:
                    data.gpu_power = max(data.gpu_power, value)
            elif stype == SensorType.Fan:
                if is_cpu or "cpu" in name_lower:
                    data.cpu_fan = max(data.cpu_fan, int(value))
                elif is_gpu or "gpu" in name_lower:
                    data.gpu_fan = max(data.gpu_fan, int(value))
                else:
                    data.case_fan = max(data.case_fan, int(value))

    def get_data(self) -> SensorData:
        """현재 센서 데이터 반환 (스레드 안전)"""
        with self._lock:
            return SensorData(
                cpu_temp=self._data.cpu_temp,
                cpu_clock=self._data.cpu_clock,
                cpu_power=self._data.cpu_power,
                cpu_fan=self._data.cpu_fan,
                gpu_temp=self._data.gpu_temp,
                gpu_clock=self._data.gpu_clock,
                gpu_power=self._data.gpu_power,
                gpu_fan=self._data.gpu_fan,
                board_temp=self._data.board_temp,
                ssd_temp=self._data.ssd_temp,
                case_fan=self._data.case_fan,
            )

    @property
    def source(self) -> str:
        return self._source

    @property
    def is_available(self) -> bool:
        return self._source != "none"

    def cleanup(self):
        """리소스 해제"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)
        if self._computer:
            try:
                self._computer.Close()
            except Exception:
                pass
