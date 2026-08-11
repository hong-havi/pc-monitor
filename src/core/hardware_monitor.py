"""하드웨어 모니터링 데이터 수집 모듈 (최종 최적화 버전)

성능 요구사항: collect()가 UI 스레드에서 <50ms 안에 반환되어야 함.

전략:
- CPU/메모리/네트워크: psutil (즉시, <5ms)
- GPU 사용률: D3DKMT API (즉시, <1ms)
- GPU VRAM: WMI GPUAdapterMemory (백그라운드, ~200ms)
- 온도/팬/클럭/전력: LibreHardwareMonitorLib.dll (pythonnet, 백그라운드)
- 디스크: psutil (즉시)
- Uptime: psutil.boot_time (즉시)
"""
import time
import threading
from dataclasses import dataclass, field

import psutil

try:
    import wmi
    import pythoncom
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False

from core.gpu_d3dkmt import D3DKMTGpuMonitor
from core.lhm_reader import LHMReader


@dataclass
class HardwareData:
    """하드웨어 모니터링 데이터 컨테이너"""
    cpu_usage: float = 0.0
    cpu_temp: float = 0.0
    cpu_clock: float = 0.0
    cpu_power: float = 0.0
    cpu_fan: int = 0

    gpu_usage: float = 0.0
    gpu_temp: float = 0.0
    gpu_clock: float = 0.0
    gpu_power: float = 0.0
    gpu_fan: int = 0
    gpu_vram_used: float = 0.0
    gpu_vram_total: float = 0.0

    mem_used: float = 0.0
    mem_total: float = 0.0

    board_temp: float = 0.0
    ssd_temp: float = 0.0
    case_fan: int = 0

    net_download: float = 0.0
    net_upload: float = 0.0

    # 새로 추가된 필드
    uptime_seconds: int = 0
    cpu_temp_max: float = 0.0
    gpu_temp_max: float = 0.0
    disk_read_speed: float = 0.0   # MB/s
    disk_write_speed: float = 0.0  # MB/s
    disks: list = field(default_factory=list)  # [{drive, total_gb, used_gb, free_gb}, ...]

    status: str = "정상"
    timestamp: float = 0.0


class HardwareMonitor:
    """하드웨어 정보 수집기"""

    def __init__(self):
        self._last_net_io = None
        self._last_net_time = None
        self._last_disk_io = None
        self._last_disk_time = None

        # 최고 온도 추적
        self._cpu_temp_max: float = 0.0
        self._gpu_temp_max: float = 0.0

        # GPU 모니터 (D3DKMT - 즉시 반환)
        self._gpu_monitor = D3DKMTGpuMonitor()

        # GPU VRAM 정보
        self._gpu_vram_total: float = 0.0
        self._gpu_vram_used: float = 0.0
        self._gpu_luid_low: int = 0
        self._gpu_luid: str = ""
        self._gpu_name = ""

        # LHM 센서 (온도/팬/클럭/전력) - 자체 백그라운드 스레드
        self._lhm = LHMReader()

        # GPU 정보 초기 감지
        self._detect_gpu()

        # VRAM 업데이트용 백그라운드 스레드
        self._cache_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._bg_worker, daemon=True)
        self._worker.start()

    def _detect_gpu(self):
        """GPU 기본 정보 감지"""
        if not WMI_AVAILABLE:
            return
        try:
            w = wmi.WMI()
            for vc in w.Win32_VideoController():
                name = vc.Name or ""
                if "Mirage" in name or "Microsoft" in name or "Remote" in name:
                    continue
                self._gpu_name = name
                ram = int(vc.AdapterRAM or 0)
                if ram < 0:
                    ram += 2**32
                elif ram == 0:
                    ram = 4 * 1024**3
                self._gpu_vram_total = ram / (1024**3)
                break
        except Exception:
            pass

        # GPU LUID 감지
        try:
            w = wmi.WMI(namespace=r"root\cimv2")
            mem_counters = w.Win32_PerfFormattedData_GPUPerformanceCounters_GPUAdapterMemory()
            max_dedicated = 0
            best_name = ""
            for m in mem_counters:
                d = int(m.DedicatedUsage or 0)
                if d > max_dedicated:
                    max_dedicated = d
                    best_name = (m.Name or "").strip()

            if best_name:
                parts = best_name.split("_")
                if len(parts) >= 3:
                    self._gpu_luid = f"{parts[1]}_{parts[2]}"
                    try:
                        self._gpu_luid_low = int(parts[2], 16)
                    except ValueError:
                        pass

            self._gpu_vram_used = max_dedicated / (1024**3)
        except Exception:
            pass

        # D3DKMT 초기화
        if self._gpu_luid_low > 0:
            self._gpu_monitor.initialize_with_luid(self._gpu_luid_low)

    def _bg_worker(self):
        """백그라운드 스레드: VRAM 사용량 업데이트"""
        if not WMI_AVAILABLE:
            return

        pythoncom.CoInitialize()
        try:
            wmi_cimv2 = wmi.WMI(namespace=r"root\cimv2")
            while not self._stop_event.is_set():
                self._update_vram(wmi_cimv2)
                self._stop_event.wait(2.0)
        finally:
            pythoncom.CoUninitialize()

    def _update_vram(self, wmi_conn):
        """VRAM 사용량 업데이트"""
        try:
            mem_counters = wmi_conn.Win32_PerfFormattedData_GPUPerformanceCounters_GPUAdapterMemory()
            for m in mem_counters:
                name = (m.Name or "").strip()
                if self._gpu_luid and self._gpu_luid in name:
                    with self._cache_lock:
                        self._gpu_vram_used = int(m.DedicatedUsage or 0) / (1024**3)
                    return
            # fallback
            max_d = max((int(m.DedicatedUsage or 0) for m in mem_counters), default=0)
            with self._cache_lock:
                self._gpu_vram_used = max_d / (1024**3)
        except Exception:
            pass

    def _collect_disk_info(self) -> list:
        """디스크 파티션별 사용량 수집"""
        disks = []
        try:
            partitions = psutil.disk_partitions(all=False)
            for p in partitions:
                # 고정 디스크만 (CD-ROM 등 제외)
                if 'fixed' not in p.opts and 'rw' not in p.opts:
                    # Windows에서는 opts에 'fixed'가 없을 수 있으므로 fstype 체크
                    if p.fstype == '' or p.fstype == 'cdfs':
                        continue
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    drive_letter = p.mountpoint.rstrip('\\')
                    disks.append({
                        'drive': drive_letter,
                        'total_gb': usage.total / (1024**3),
                        'used_gb': usage.used / (1024**3),
                        'free_gb': usage.free / (1024**3),
                    })
                except (PermissionError, OSError):
                    continue
        except Exception:
            pass
        return disks

    def _collect_disk_speed(self) -> tuple:
        """디스크 읽기/쓰기 속도 (MB/s)"""
        try:
            current_io = psutil.disk_io_counters()
            current_time = time.time()

            if self._last_disk_io and self._last_disk_time:
                dt = current_time - self._last_disk_time
                if dt > 0:
                    read_speed = (current_io.read_bytes - self._last_disk_io.read_bytes) / dt / (1024 * 1024)
                    write_speed = (current_io.write_bytes - self._last_disk_io.write_bytes) / dt / (1024 * 1024)
                    self._last_disk_io = current_io
                    self._last_disk_time = current_time
                    return (max(read_speed, 0.0), max(write_speed, 0.0))

            self._last_disk_io = current_io
            self._last_disk_time = current_time
        except Exception:
            pass
        return (0.0, 0.0)

    def collect(self) -> HardwareData:
        """데이터 수집 - UI 스레드에서 호출 (<50ms 보장)"""
        data = HardwareData(timestamp=time.time())

        # === 즉시 수집 (psutil) ===
        data.cpu_usage = psutil.cpu_percent(interval=None)

        mem = psutil.virtual_memory()
        data.mem_used = mem.used / (1024**3)
        data.mem_total = mem.total / (1024**3)

        # 네트워크 속도
        current_io = psutil.net_io_counters()
        current_time = time.time()
        if self._last_net_io and self._last_net_time:
            dt = current_time - self._last_net_time
            if dt > 0:
                data.net_download = (
                    (current_io.bytes_recv - self._last_net_io.bytes_recv) / dt / (1024 * 1024)
                )
                data.net_upload = (
                    (current_io.bytes_sent - self._last_net_io.bytes_sent) / dt / (1024 * 1024)
                )
        self._last_net_io = current_io
        self._last_net_time = current_time

        # === GPU 사용률 (D3DKMT, <1ms) ===
        data.gpu_usage = self._gpu_monitor.collect_usage()

        # === VRAM (캐시) ===
        with self._cache_lock:
            data.gpu_vram_used = self._gpu_vram_used
        data.gpu_vram_total = self._gpu_vram_total

        # === LHM 센서 데이터 (온도/팬/클럭/전력) ===
        sensor = self._lhm.get_data()
        data.cpu_temp = sensor.cpu_temp
        data.cpu_clock = sensor.cpu_clock
        data.cpu_power = sensor.cpu_power
        data.cpu_fan = sensor.cpu_fan
        data.gpu_temp = sensor.gpu_temp
        data.gpu_clock = sensor.gpu_clock
        data.gpu_power = sensor.gpu_power
        data.gpu_fan = sensor.gpu_fan
        data.board_temp = sensor.board_temp
        data.ssd_temp = sensor.ssd_temp
        data.case_fan = sensor.case_fan

        # === 최고 온도 추적 ===
        if data.cpu_temp > self._cpu_temp_max:
            self._cpu_temp_max = data.cpu_temp
        if data.gpu_temp > self._gpu_temp_max:
            self._gpu_temp_max = data.gpu_temp
        data.cpu_temp_max = self._cpu_temp_max
        data.gpu_temp_max = self._gpu_temp_max

        # === Uptime ===
        try:
            boot_time = psutil.boot_time()
            data.uptime_seconds = int(time.time() - boot_time)
        except Exception:
            data.uptime_seconds = 0

        # === 디스크 ===
        data.disks = self._collect_disk_info()
        disk_read, disk_write = self._collect_disk_speed()
        data.disk_read_speed = disk_read
        data.disk_write_speed = disk_write

        # 상태 판단
        if data.cpu_temp > 90 or data.gpu_temp > 90:
            data.status = "경고"
        elif data.cpu_usage > 95 or data.gpu_usage > 95:
            data.status = "높음"
        else:
            data.status = "정상"

        return data

    def cleanup(self):
        """리소스 해제"""
        self._stop_event.set()
        self._worker.join(timeout=3)
        self._gpu_monitor.cleanup()
        self._lhm.cleanup()
