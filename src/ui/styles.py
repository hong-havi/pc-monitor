"""대시보드 스타일 정의 - 다크 테마 (디자인 컴프 반영)"""

# 색상 팔레트 (PC Monitor Mini.dc.html 기준)
COLORS = {
    "bg_dark": "#0b0d10",
    "bg_card": "#14171b",
    "bg_card_border": "#22262c",
    "bg_bar_track": "#23272e",
    "text_primary": "#f2f4f7",
    "text_secondary": "#d9dee4",
    "text_dim": "#b0b8c4",
    "text_muted": "#a0a8b4",
    "text_label": "#c0c8d2",
    "text_heading": "#e4e8ed",
    "text_value": "#dce1e8",

    # 게이지 색상
    "gauge_cpu": "#8b7cf6",       # 보라색
    "gauge_gpu": "#22d3ee",       # 시안
    "gauge_mem": "#3b82f6",       # 파랑
    "gauge_vram": "#f59e0b",      # 앰버

    # 온도 바 색상
    "temp_hot": "#f5a524",        # 주황 (>=60)
    "temp_normal": "#4ade80",     # 초록 (<60)

    # 클럭/전력
    "bar_clock": "#3b82f6",       # 파랑
    "power_color": "#f5a524",     # 앰버

    # 네트워크
    "net_download": "#4ade80",    # 초록
    "net_upload": "#3b82f6",      # 파랑

    # 디스크
    "disk_warn": "#f5a524",       # 주황 (>=70%)
    "disk_ok": "#4ade80",         # 초록 (<70%)
    "disk_read": "#4ade80",
    "disk_write": "#3b82f6",

    # 상태
    "status_normal": "#4ade80",
    "status_warning": "#f5a524",
    "status_critical": "#ef4444",
}

# 메인 윈도우 스타일시트
MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}
QWidget {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    font-family: 'Pretendard', 'Segoe UI', 'Malgun Gothic', sans-serif;
}}
QLabel {{
    color: {COLORS['text_primary']};
}}
"""
