"""간단한 라이트룸 테더링 테스트 스크립트"""
import time
import os

try:
    import win32gui
    import win32con
    import keyboard
    import psutil
    print("✅ 필요한 모듈 로드 성공")
except ImportError as e:
    print(f"❌ 모듈 로드 실패: {e}")
    input("Enter를 눌러 종료...")
    exit(1)

def find_lightroom_window():
    """라이트룸 창 찾기"""
    result = []
    def enum_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if 'lightroom' in title.lower():
                result.append((hwnd, title))
        return True
    win32gui.EnumWindows(enum_callback, None)
    return result

def is_lightroom_running():
    """라이트룸 프로세스 확인"""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and 'lightroom' in proc.info['name'].lower():
                return True
        except:
            pass
    return False

print("\n=== 라이트룸 테더링 디버그 ===\n")

# 1. 프로세스 확인
print("1. 라이트룸 프로세스 확인...")
if is_lightroom_running():
    print("   ✅ 라이트룸 프로세스 실행 중")
else:
    print("   ❌ 라이트룸 프로세스가 실행되지 않음")
    print("   → 라이트룸을 먼저 실행하세요")
    input("\nEnter를 눌러 종료...")
    exit(1)

# 2. 창 찾기
print("\n2. 라이트룸 창 찾기...")
windows = find_lightroom_window()
if windows:
    for hwnd, title in windows:
        print(f"   ✅ 발견: [{hwnd}] {title}")
else:
    print("   ❌ 라이트룸 창을 찾을 수 없음")
    input("\nEnter를 눌러 종료...")
    exit(1)

# 3. 창 활성화
print("\n3. 라이트룸 창 활성화 시도...")
try:
    hwnd = windows[0][0]
    if win32gui.IsIconic(hwnd):
        print("   → 최소화된 상태, 복원 중...")
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.5)
    
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    
    # 활성화 확인
    fg_hwnd = win32gui.GetForegroundWindow()
    fg_title = win32gui.GetWindowText(fg_hwnd)
    if 'lightroom' in fg_title.lower():
        print(f"   ✅ 활성화 성공: {fg_title}")
    else:
        print(f"   ⚠️ 활성화 실패? 현재 포그라운드: {fg_title}")
except Exception as e:
    print(f"   ❌ 활성화 오류: {e}")
    input("\nEnter를 눌러 종료...")
    exit(1)

# 4. 키 입력 테스트
print("\n4. 테더링 키 시퀀스 테스트 (5초 후 시작)...")
print("   → Alt+F (파일 메뉴) → 아래 8번 → 오른쪽 → Enter")
print("   → 라이트룸을 보시면서 확인하세요!")
time.sleep(5)

try:
    print("   → Alt+F 전송...")
    keyboard.send('alt+f')
    time.sleep(0.4)
    
    for i in range(8):
        print(f"   → Down {i+1}/8...")
        keyboard.send('down')
        time.sleep(0.1)
    
    print("   → Right...")
    keyboard.send('right')
    time.sleep(0.3)
    
    print("   → Enter...")
    keyboard.send('enter')
    time.sleep(0.5)
    
    print("\n✅ 키 시퀀스 전송 완료!")
    print("→ 라이트룸에서 테더링 다이얼로그가 열렸는지 확인하세요.")
except Exception as e:
    print(f"   ❌ 키 입력 오류: {e}")

input("\nEnter를 눌러 종료...")
