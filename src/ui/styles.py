"""대시보드 스타일 정의 - 다크 테마"""

# 색상 팔레트
COLORS = {
    "bg_dark": "#1a1a1a",
    "bg_card": "#2a2a2a",
    "bg_card_border": "#3a3a3a",
    "text_primary": "#ffffff",
    "text_secondary": "#aaaaaa",
    "text_dim": "#666666",

    # 게이지 색상
    "gauge_cpu": "#7c6ef0",       # 보라색
    "gauge_gpu": "#4ecf72",       # 초록색
    "gauge_mem": "#4ecf72",       # 초록색
    "gauge_vram": "#4ecf72",      # 초록색

    # 온도 바 색상
    "temp_cpu": "#4ecf72",        # 초록
    "temp_gpu": "#f0a030",        # 주황
    "temp_board": "#555555",      # 회색
    "temp_ssd": "#2a9d8f",        # 청록

    # 프로그레스바
    "bar_cpu_clock": "#4488ff",   # 파랑
    "bar_gpu_clock": "#4ecf72",   # 초록

    # 네트워크
    "net_download": "#4ecf72",    # 초록
    "net_upload": "#4488ff",      # 파랑

    # 상태
    "status_normal": "#4ecf72",
    "status_warning": "#f0a030",
    "status_critical": "#e63946",
}

# 메인 윈도우 스타일시트
MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}
QWidget {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
}}
QLabel {{
    color: {COLORS['text_primary']};
}}
"""
