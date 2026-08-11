# PC Monitor Dashboard

960x640 미니모니터용 하드웨어 모니터링 대시보드 (Windows)

## 기능

- **CPU/GPU 사용률** - 원형 게이지로 실시간 표시
- **메모리/VRAM** - 사용량/전체 용량 게이지
- **온도** - CPU, GPU, 메인보드, SSD 온도 바 차트
- **클럭** - CPU(GHz), GPU(MHz) 프로그레스 바
- **소비 전력** - CPU/GPU 와트 표시
- **팬 속도** - CPU, GPU, 케이스 팬 RPM
- **네트워크** - 다운/업 속도 + 실시간 그래프

## 요구사항

- Windows 10/11
- Python 3.10+
- NVIDIA GPU (GPU 모니터링용, 없어도 동작)
- [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) 실행 필요 (온도/팬/클럭/전력 데이터)

## 설치 및 실행

```bash
# 가상환경 생성
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 실행
python src/main.py
```

## EXE 빌드

```bash
# build.bat 실행 또는:
pyinstaller --onefile --windowed --name PCMonitor src/main.py
```

빌드된 파일: `dist/PCMonitor.exe`

## LibreHardwareMonitor 설정

온도, 팬 속도, 클럭, 전력 데이터를 읽으려면:

1. [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases) 다운로드
2. **관리자 권한**으로 실행
3. Options → Remote Web Server → Run 체크 (WMI 데이터 노출)

LHM 없이도 CPU 사용률, 메모리, GPU(NVIDIA), 네트워크는 정상 동작합니다.

## 프로젝트 구조

```
pc-monitor/
├── src/
│   ├── main.py              # 진입점
│   ├── core/
│   │   └── hardware_monitor.py  # 하드웨어 데이터 수집
│   └── ui/
│       ├── main_window.py   # 메인 윈도우 레이아웃
│       ├── styles.py        # 색상/스타일 정의
│       └── widgets/         # 커스텀 위젯들
│           ├── gauge_widget.py    # 원형 게이지
│           ├── temp_widget.py     # 온도 바
│           ├── bar_widget.py      # 클럭/전력 바
│           ├── fan_widget.py      # 팬 속도
│           └── network_widget.py  # 네트워크 그래프
├── requirements.txt
├── build.bat
└── build.spec
```
