"""D3DKMT API를 이용한 GPU 사용률 읽기 (초고속)

Windows 작업 관리자와 동일한 방식.
gdi32.dll D3DKMTQueryStatistics로 노드별 RunningTime을 읽어 사용률 계산.
WMI GPUEngine(50초+)과 달리 < 1ms로 즉시 반환.
"""
import ctypes
import time
from ctypes import Structure, byref, sizeof, c_uint32, c_uint64, c_void_p, c_byte
import ctypes.wintypes as wintypes
from typing import Optional

gdi32 = ctypes.windll.gdi32


class LUID(Structure):
    _fields_ = [('LowPart', wintypes.DWORD), ('HighPart', wintypes.LONG)]


# D3DKMT_QUERYSTATISTICS_TYPE
QUERYSTATISTICS_ADAPTER = 0
QUERYSTATISTICS_NODE = 5


class D3DKMTGpuMonitor:
    """D3DKMT 기반 초고속 GPU 사용률 모니터

    collect_usage()를 1초 간격으로 호출하면 GPU 사용률(%)을 반환.
    호출당 소요 시간: <1ms.
    """

    def __init__(self, luid_low: int = 0, luid_high: int = 0):
        """
        Args:
            luid_low: GPU의 LUID LowPart (0이면 자동 감지 시도)
            luid_high: GPU의 LUID HighPart
        """
        self._luid = LUID(luid_low, luid_high)
        self._num_nodes = 0
        self._prev_running_time: int = 0
        self._prev_time: float = 0.0
        self._last_usage: float = 0.0
        self._initialized = False

        if luid_low > 0:
            self._query_adapter_info()

    def initialize_with_luid(self, luid_low: int, luid_high: int = 0):
        """LUID로 초기화 (나중에 설정 가능)"""
        self._luid = LUID(luid_low, luid_high)
        self._query_adapter_info()

    def _query_adapter_info(self):
        """어댑터 노드 수 확인"""
        buf = (c_byte * 1024)()
        ctypes.memmove(buf, byref(c_uint32(QUERYSTATISTICS_ADAPTER)), 4)
        ctypes.memmove(ctypes.byref(buf, 4), byref(self._luid), 8)

        status = gdi32.D3DKMTQueryStatistics(buf)
        if status == 0:
            self._num_nodes = c_uint32.from_buffer_copy(buf, 24).value
            self._initialized = True

    def _query_node_running_time(self, node_id: int) -> Optional[int]:
        """특정 노드의 RunningTime (100ns 단위) 반환"""
        buf = (c_byte * 1024)()
        ctypes.memmove(buf, byref(c_uint32(QUERYSTATISTICS_NODE)), 4)
        ctypes.memmove(ctypes.byref(buf, 4), byref(self._luid), 8)
        ctypes.memmove(ctypes.byref(buf, 24), byref(c_uint32(node_id)), 4)

        status = gdi32.D3DKMTQueryStatistics(buf)
        if status != 0:
            return None

        # RunningTime은 결과의 offset 24 (uint64)
        return c_uint64.from_buffer_copy(buf, 24).value

    def collect_usage(self) -> float:
        """GPU 사용률 계산 (0~100%)

        이전 호출과의 RunningTime 차이로 계산.
        최소 2회 호출 필요 (첫 호출은 baseline).
        """
        if not self._initialized or self._num_nodes == 0:
            return 0.0

        current_time = time.perf_counter()

        # 노드 0 (보통 3D 엔진)의 RunningTime
        # 모든 노드가 동일한 값을 반환하는 경우가 있으므로 노드 0만 사용
        running_time = self._query_node_running_time(0)
        if running_time is None:
            return self._last_usage

        if self._prev_time > 0 and self._prev_running_time > 0:
            dt = current_time - self._prev_time
            if dt > 0:
                dt_100ns = dt * 10_000_000  # 초 → 100나노초
                delta = running_time - self._prev_running_time
                usage = (delta / dt_100ns) * 100.0
                self._last_usage = min(max(usage, 0.0), 100.0)

        self._prev_running_time = running_time
        self._prev_time = current_time
        return self._last_usage

    @property
    def is_available(self) -> bool:
        return self._initialized

    def cleanup(self):
        pass
