# 📷 Lightroom Macro Panel

Adobe Lightroom Classic을 터치 패널로 제어하는 Windows용 GUI 매크로 프로그램입니다.

## 🎯 주요 기능

| 버튼 | 기능 | 설명 |
|------|------|------|
| **1번** | 📷 촬영 시작 | Lightroom 실행 → 테더링 촬영 모드 시작 |
| **2번** | 💾 전체 내보내기 | 모든 사진을 바탕화면 폴더로 내보내기 |
| **3번** | 🖨️ 인화하기 | 선택한 사진을 즉시 인화 |

## 🖥️ 시스템 요구사항

- **OS**: Windows 10/11
- **Python**: 3.9 이상
- **모니터**: 듀얼 모니터 권장 (서브 모니터 = 터치 모니터)
- **소프트웨어**: Adobe Lightroom Classic

---

## 🚀 빠른 설치 가이드

### 1단계: Python 설치

Python이 설치되어 있지 않다면:

1. [Python 공식 사이트](https://www.python.org/downloads/)에서 Python 3.11+ 다운로드
2. 설치 시 **"Add Python to PATH"** 체크 필수!
3. 설치 완료 후 명령 프롬프트에서 확인:
   ```cmd
   python --version
   ```

### 2단계: 프로젝트 다운로드

프로젝트 폴더를 원하는 위치에 저장합니다.
예: `C:\Users\사용자\Documents\lightroom_macro_panel`

### 3단계: 필요 패키지 설치

명령 프롬프트(관리자 권한)를 열고 프로젝트 폴더로 이동 후 실행:

```cmd
cd C:\Users\사용자\Documents\lightroom_macro_panel
pip install -r requirements.txt
```

또는 직접 설치:

```cmd
pip install PySide6 pywin32 keyboard psutil
```

### 4단계: 프로그램 실행

```cmd
python lightroom_macro_panel.py
```

---

## 📁 파일 구조

```
lightroom_macro_panel/
├── lightroom_macro_panel.py   # 메인 프로그램
├── config.json                # 설정 파일 (자동 생성됨)
├── requirements.txt           # Python 패키지 목록
├── README.md                  # 이 문서
└── logs/
    └── macro_log.txt          # 작업 로그 (자동 생성됨)
```

---

## ⚙️ 설정 파일 (config.json)

프로그램 첫 실행 시 `config.json`이 자동 생성됩니다.
필요에 따라 수정하세요.

### 주요 설정 항목

```json
{
    "lightroom_path": "C:\\Program Files\\Adobe\\Adobe Lightroom Classic\\Lightroom.exe",
    "lightroom_process_name": "Lightroom.exe",
    "lightroom_window_title_contains": "Lightroom",
    
    "export_target_folder": "Desktop\\STUDIO_EXPORT",
    "log_path": "logs\\macro_log.txt",
    
    "gui_settings": {
        "monitor_index": 1,      // 0 = 메인 모니터, 1 = 서브 모니터
        "fullscreen": true,
        "always_on_top": true
    }
}
```

### 설정 항목 상세 설명

| 항목 | 설명 | 기본값 |
|------|------|--------|
| `lightroom_path` | Lightroom 실행 파일 경로 | Adobe 기본 설치 경로 |
| `monitor_index` | 패널을 표시할 모니터 (0부터 시작) | 1 (서브 모니터) |
| `fullscreen` | 전체 화면 모드 | true |
| `always_on_top` | 항상 위에 표시 | true |
| `export_target_folder` | 내보내기 대상 폴더 | Desktop\STUDIO_EXPORT |

### 단축키 시퀀스 커스터마이징

단축키 시퀀스는 아래 형식으로 수정할 수 있습니다:

```json
"export_all_sequence": [
    {"action": "key", "value": "ctrl+a", "delay_after_ms": 300},
    {"action": "key", "value": "ctrl+alt+shift+e", "delay_after_ms": 100}
]
```

- `action`: `key` (단축키) 또는 `write` (텍스트 입력) 또는 `sleep` (대기)
- `value`: 키 조합 (예: `ctrl+a`, `alt+f`, `enter`)
- `delay_after_ms`: 해당 키 입력 후 대기 시간 (밀리초)

---

## 🎨 GUI 설정

### 색상 커스터마이징

`config.json`의 `gui_settings`에서 색상을 변경할 수 있습니다:

```json
"gui_settings": {
    "background_color": "#1a1a2e",      // 배경색
    "button_color": "#16213e",          // 버튼 기본색
    "button_hover_color": "#0f3460",    // 마우스 오버 시
    "button_pressed_color": "#e94560",  // 클릭 시
    "text_color": "#ffffff",            // 텍스트 색상
    "subtext_color": "#a0a0a0"          // 서브텍스트 색상
}
```

### 모니터 선택

듀얼 모니터 환경에서 프로그램 실행 시 콘솔에 모니터 정보가 표시됩니다:

```
[모니터 정보]
  [0] \\.\DISPLAY1: 1920x1080 @ (0, 0)
  [1] \\.\DISPLAY2: 1920x1080 @ (1920, 0)
```

`monitor_index`를 원하는 모니터 번호로 설정하세요.

---

## 📋 Lightroom 사전 설정

### 1. Export Preset 설정 (필수)

전체 내보내기 기능을 사용하려면 Lightroom에서 Export Preset을 미리 설정해야 합니다.

1. Lightroom에서 `File` → `Export...` 클릭
2. 내보내기 설정:
   - **Export Location**: 
     - Export To: `Specific Folder`
     - Folder: `C:\Users\사용자\Desktop\STUDIO_EXPORT`
     - Put in Subfolder: 원하는 경우 체크
   - **File Settings**: JPEG, 품질 등 설정
   - **Image Sizing**: 원하는 크기 설정
3. 좌측 하단 `Add` 버튼을 눌러 프리셋 저장
4. **중요**: 이후 `Export with Previous` (Ctrl+Alt+Shift+E) 기능 사용

### 2. Print Preset 설정 (인화 사용 시)

1. Lightroom에서 `Print` 모듈로 이동
2. 프린터, 용지 크기, 레이아웃 설정
3. 좌측 `Template Browser`에서 템플릿 저장
4. 기본 프린터와 설정이 저장된 상태로 두기

### 3. 테더링 촬영 설정

1. 카메라를 USB로 연결
2. `File` → `Tethered Capture` → `Start Tethered Capture...`
3. 세션 이름, 저장 위치 등 설정
4. 이후에는 동일한 설정으로 바로 시작됨

---

## 🔧 문제 해결

### "pywin32 설치 오류"

관리자 권한으로 명령 프롬프트를 실행한 후:
```cmd
pip install --upgrade pywin32
python -c "import win32api"
```

### "keyboard 모듈 권한 오류"

`keyboard` 라이브러리는 관리자 권한이 필요할 수 있습니다.
명령 프롬프트를 **관리자 권한**으로 실행하세요.

### "Lightroom 윈도우를 찾을 수 없습니다"

1. Lightroom이 실행 중인지 확인
2. `config.json`의 `lightroom_window_title_contains` 값 확인
3. Lightroom 창 제목에 "Lightroom" 문자열이 포함되어 있어야 함

### "모니터 인덱스가 없습니다"

- 듀얼 모니터가 연결되어 있는지 확인
- `monitor_index`를 0으로 변경 (메인 모니터 사용)

### "단축키가 작동하지 않습니다"

1. Lightroom이 포커스를 받았는지 확인
2. `config.json`의 단축키 시퀀스가 올바른지 확인
3. `delay_after_ms` 값을 늘려보세요 (예: 500ms)

---

## 📊 로그 파일

모든 작업은 `logs/macro_log.txt`에 기록됩니다.

### 로그 형식 예시

```
2025-12-05 13:22:45 | APP_START | version=1.0.0
2025-12-05 13:23:10 | TETHER_START | status=success
2025-12-05 13:25:30 | EXPORT_ALL | target=C:\Users\...\Desktop\STUDIO_EXPORT
2025-12-05 13:28:45 | PRINT | note=print_selected_photos
```

---

## 🔌 확장 가능성

### Evoto 연동 준비

`config.json`에서 Evoto를 활성화할 수 있습니다:

```json
"extra_programs": [
    {
        "name": "Evoto",
        "path": "C:\\Program Files\\Evoto\\Evoto.exe",
        "enabled": true
    }
]
```

`enabled`를 `true`로 설정하면 촬영 시작 버튼 클릭 시 Evoto도 함께 실행됩니다.

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 제공됩니다.

---

## 🆘 지원

문제가 발생하면:
1. 로그 파일 (`logs/macro_log.txt`) 확인
2. `config.json` 설정 확인
3. Lightroom이 최신 버전인지 확인

---

## 📌 버전 정보

- **v1.0.0** (2025-12-05): 최초 릴리즈
  - 촬영 시작, 전체 내보내기, 인화하기 기능
  - 서브 모니터 전체화면 지원
  - 외부 설정 파일 지원
  - 작업 로그 기능
