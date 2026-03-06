#!/usr/bin/env pythonw
# -*- coding: utf-8 -*-
"""
=============================================================================
Studio Birthday - Lightroom Macro Panel
=============================================================================

버전: 4.0.0 - Kiosk Edition
- 상태 기반 UI 전환 (IDLE → SHOOTING → EXPORT_READY)
- 미사용 코드 제거 (경량화)
- 버그 수정 (glass_border_hover, StatusWidget 중복)

=============================================================================
"""

import sys
import os
import json
import time
import threading
import subprocess
import logging
import shutil
import zipfile
import ctypes
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

# Windows 전용 모듈
try:
    import win32gui
    import win32con
    import win32process
    import win32api
    import keyboard
    import psutil
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

# PySide6 GUI 모듈
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QFrame, QMessageBox, QSizePolicy,
        QGraphicsDropShadowEffect, QDialog, QGridLayout, QStackedWidget
    )
    from PySide6.QtCore import (
        Qt, QTimer, Signal, QThread, QPropertyAnimation,
        QEasingCurve, Property, QRect, QUrl, QByteArray, QPoint
    )
    from PySide6.QtGui import (
        QFont, QScreen, QColor, QPalette, QCursor, QPainter,
        QPainterPath, QLinearGradient, QBrush, QPen, QFontDatabase,
        QPixmap, QDesktopServices, QIcon, QRadialGradient
    )
    from PySide6.QtSvg import QSvgRenderer
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    sys.exit(1)


APP_NAME = "Studio Birthday"
APP_VERSION = "4.0.0"
CONFIG_FILE = "config.json"

# === 상태 상수 ===
STATE_IDLE = "IDLE"
STATE_CONFIRM = "CONFIRM"
STATE_SHOOTING = "SHOOTING"
STATE_EXPORT_READY = "EXPORT_READY"

# 🍎 iPad Pro Dark Style Theme
IPAD_DARK_THEME = {
    "bg_base": "#1C1C1E",
    "bg_alt": "#2C2C2E",

    # Text
    "text_main": "#FFFFFF",
    "text_sub": "#AEAEB2",
    "text_accent": "#0A84FF",

    # Dialogs
    "dialog_bg": "#2C2C2E",
    "dialog_border": "#3A3A3C",
    "glass_border": "#3A3A3C",
    "glass_border_hover": "#48484A",  # 버그 수정: 누락 키 추가
    "glass_bg": "#2C2C2E",
    "glass_hover": "#3A3A3C",
    "glass_pressed": "#48484A",

    # Standard Buttons (in Dialogs)
    "button_bg": "#3A3A3C",
    "button_hover_color": "#48484A",
    "button_pressed_color": "#636366",

    # Special Colors
    "accent_glow": "rgba(10, 132, 255, 0.3)",
    "danger_glow": "rgba(255, 69, 58, 0.3)",
    "danger_color": "#FF453A",
    "danger_hover": "#FF6961",
    "danger_pressed": "#D70015",
    "share_color": "#FF9F0A",
    "special_color": "#FFD60A",

    # Compatibility Keys
    "background_gradient": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #000000, stop:1 #1C1C1E)",
    "header_color": "#FFFFFF",
    "subtext_color": "#8E8E93",
    "text_color": "#FFFFFF",
    "accent_color": "#0A84FF",
    "button_color": "#2C2C2E",
    "tip_background": "#2C2C2E",
    "tip_border": "#3A3A3C",
    "close_button_color": "#FF453A",
    "close_button_hover": "#FF3B30"
}

CURRENT_THEME = IPAD_DARK_THEME

DEFAULT_CONFIG = {
    "studio_name": "Studio Birthday",
    "studio_slogan": "프라이빗하고 합리적인 무인 스튜디오",

    "presets": [
        {"name": "만삭사진", "favorite_index": 1},
        {"name": "흑백", "favorite_index": 2},
        {"name": "가족사진", "favorite_index": 3}
    ],

    "lightroom_path": "C:\\Program Files\\Adobe\\Adobe Lightroom Classic\\Lightroom.exe",
    "lightroom_process_name": "Lightroom.exe",
    "lightroom_window_title_contains": "Lightroom",

    "extra_programs": [
        {"name": "Evoto", "path": "", "enabled": False}
    ],

    "tether_start_sequence": [
        {"action": "key", "value": "g", "delay_after_ms": 500, "comment": "Library Grid View로 이동"},
        {"action": "key", "value": "alt+f", "delay_after_ms": 500, "comment": "파일(F) 메뉴 열기"},
        {"action": "key", "value": "down", "delay_after_ms": 100, "comment": "아래 1"},
        {"action": "key", "value": "down", "delay_after_ms": 100, "comment": "아래 2"},
        {"action": "key", "value": "down", "delay_after_ms": 100, "comment": "아래 3"},
        {"action": "key", "value": "down", "delay_after_ms": 100, "comment": "아래 4"},
        {"action": "key", "value": "down", "delay_after_ms": 100, "comment": "아래 5"},
        {"action": "key", "value": "down", "delay_after_ms": 100, "comment": "아래 6"},
        {"action": "key", "value": "down", "delay_after_ms": 100, "comment": "아래 7"},
        {"action": "key", "value": "down", "delay_after_ms": 100, "comment": "아래 8 - 연결전송된 촬영"},
        {"action": "key", "value": "right", "delay_after_ms": 300, "comment": "하위메뉴 열기"},
        {"action": "key", "value": "enter", "delay_after_ms": 500, "comment": "연결전송된 촬영 시작 선택"}
    ],

    "export_all_sequence": [
        {"action": "key", "value": "ctrl+a", "delay_after_ms": 300},
        {"action": "key", "value": "ctrl+alt+shift+e", "delay_after_ms": 100}
    ],

    "print_sequence": [
        {"action": "key", "value": "ctrl+alt+p", "delay_after_ms": 1000, "comment": "Print One Copy"}
    ],

    "export_target_folder": "Desktop\\내보내기",
    "log_path": "logs\\macro_log.txt",

    "gui_settings": {
        "monitor_index": 1,
        "fullscreen": True,
        "always_on_top": True,
        "theme": "sage_garden"
    },

    "delays": {
        "app_launch_wait_ms": 8000,
        "window_activation_wait_ms": 500,
        "between_key_default_ms": 100
    }
}


# =============================================================================
# SVG 아이콘
# =============================================================================
class IconSVG:
    """SVG 아이콘 모음 (사용되는 것만 유지)"""

    CAMERA_LOGO = '''
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
        <circle cx="12" cy="13" r="4"/>
    </svg>
    '''

    PLAY = '''
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="5 3 19 12 5 21 5 3"/>
    </svg>
    '''

    FOLDER_EXPORT = '''
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        <polyline points="12 11 15 14 12 17"/>
        <line x1="9" y1="14" x2="15" y2="14"/>
    </svg>
    '''

    SHARE = '''<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>'''

    TRASH = '''<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>'''

    WARNING = '''
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
    '''


# =============================================================================
# 설정 관리
# =============================================================================
class ConfigManager:
    def __init__(self, config_path: str = CONFIG_FILE):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except json.JSONDecodeError:
                self.config = DEFAULT_CONFIG.copy()
                self.save_config()
        else:
            self.config = DEFAULT_CONFIG.copy()
            self.save_config()
        return self.config

    def save_config(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


# =============================================================================
# 로그 관리
# =============================================================================
class LogManager:
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger('MacroPanel')
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        file_handler = logging.FileHandler(self.log_path, encoding='utf-8', mode='a')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        )
        self.logger.addHandler(file_handler)

    def log_action(self, action_type: str, **kwargs):
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"{action_type} | {extra_info}" if extra_info else action_type)

    def log_error(self, message: str):
        self.logger.error(f"ERROR | {message}")

    def log_warning(self, message: str):
        self.logger.warning(f"WARNING | {message}")


# =============================================================================
# Windows 컨트롤러
# =============================================================================
class WindowsController:
    def __init__(self, config: ConfigManager, log_manager: LogManager):
        self.config = config
        self.log = log_manager

    def is_process_running(self, process_name: str) -> bool:
        if not WINDOWS_AVAILABLE:
            return False
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    def launch_program(self, exe_path: str, wait_ms: int = 5000) -> bool:
        if not os.path.exists(exe_path):
            return False
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            subprocess.Popen([exe_path], startupinfo=startupinfo)
            time.sleep(wait_ms / 1000.0)
            return True
        except:
            return False

    def find_window_by_title(self, title_contains: str) -> Optional[int]:
        if not WINDOWS_AVAILABLE:
            return None
        result = []
        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title_contains.lower() in title.lower():
                    result.append(hwnd)
            return True
        win32gui.EnumWindows(enum_callback, None)
        return result[0] if result else None

    def activate_window(self, hwnd: int) -> bool:
        if not WINDOWS_AVAILABLE or hwnd is None:
            return False
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(self.config.get('delays.window_activation_wait_ms', 500) / 1000.0)
            return True
        except:
            return False

    def send_key_sequence(self, sequence: List[Dict]) -> bool:
        if not WINDOWS_AVAILABLE:
            return True
        try:
            for step in sequence:
                action = step.get('action', 'key')
                value = step.get('value', '')
                delay_ms = step.get('delay_after_ms', 100)

                if action == 'key':
                    keyboard.send(value)
                elif action == 'write':
                    keyboard.write(value)
                elif action == 'sleep':
                    time.sleep(int(value) / 1000.0)

                time.sleep(delay_ms / 1000.0)
            return True
        except:
            return False

    def ensure_lightroom_running(self) -> bool:
        """라이트룸이 실행 중인지 확인하고, 아니면 시작"""
        process_name = self.config.get('lightroom_process_name', 'Lightroom.exe')

        if self.is_process_running(process_name):
            self.log.log_action("LIGHTROOM_CHECK", status="already_running")
            return True

        lr_path = self.config.get('lightroom_path')
        if not lr_path or not os.path.exists(lr_path):
            self.log.log_error(f"Lightroom path not found: {lr_path}")
            return False

        self.log.log_action("LIGHTROOM_LAUNCH", status="starting", path=lr_path)

        if not self.launch_program(lr_path, 3000):
            self.log.log_error("Failed to launch Lightroom")
            return False

        self.log.log_action("LIGHTROOM_LAUNCH", status="waiting_for_window")
        title_contains = self.config.get('lightroom_window_title_contains', 'Lightroom')

        for i in range(20):
            time.sleep(1.5)
            hwnd = self.find_window_by_title(title_contains)
            if hwnd:
                self.log.log_action("LIGHTROOM_LAUNCH", status="window_found", attempt=i+1)
                time.sleep(5)
                break
        else:
            self.log.log_error("Lightroom window did not appear within timeout")
            return False

        self.log.log_action("LIGHTROOM_LAUNCH", status="success")
        return True

    def minimize_window(self, hwnd: int) -> bool:
        if not WINDOWS_AVAILABLE or hwnd is None:
            return False
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        except:
            return False

    def minimize_lightroom(self) -> bool:
        title_contains = self.config.get('lightroom_window_title_contains', 'Lightroom')
        hwnd = self.find_window_by_title(title_contains)
        if hwnd:
            return self.minimize_window(hwnd)
        return False

    def activate_lightroom(self) -> bool:
        title_contains = self.config.get('lightroom_window_title_contains', 'Lightroom')
        hwnd = self.find_window_by_title(title_contains)
        if hwnd:
            return self.activate_window(hwnd)
        return False

    def is_lightroom_foreground(self) -> bool:
        if not WINDOWS_AVAILABLE:
            return True
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            title_contains = self.config.get('lightroom_window_title_contains', 'Lightroom')
            return title_contains.lower() in window_title.lower()
        except:
            return False

    def is_window_responding(self, hwnd: int, timeout_ms: int = 3000) -> bool:
        """윈도우가 응답하는지 확인 (프리징 감지)

        SendMessageTimeout으로 WM_NULL을 보내 응답 여부 확인.
        프리징 상태면 타임아웃되어 False 반환.
        """
        if not WINDOWS_AVAILABLE or hwnd is None:
            return False
        try:
            SMTO_ABORTIFHUNG = 0x0002
            result = ctypes.windll.user32.SendMessageTimeoutW(
                hwnd, 0x0000,  # WM_NULL
                0, 0,
                SMTO_ABORTIFHUNG,
                timeout_ms,
                ctypes.byref(ctypes.c_ulong(0))
            )
            return result != 0
        except Exception:
            return False

    def wait_for_lightroom_responsive(self, max_wait_seconds: int = 120) -> bool:
        """Lightroom이 프리징에서 풀리고 응답할 때까지 대기

        단순 delay 대신 실제 응답 상태를 확인하므로,
        저사양 PC에서도 정확한 타이밍에 키 입력 가능.
        """
        if not WINDOWS_AVAILABLE:
            return True

        title_contains = self.config.get('lightroom_window_title_contains', 'Lightroom')
        start_time = time.time()

        while (time.time() - start_time) < max_wait_seconds:
            hwnd = self.find_window_by_title(title_contains)
            if not hwnd:
                self.log.log_warning("Lightroom window not found, waiting...")
                time.sleep(2)
                continue

            if self.is_window_responding(hwnd, timeout_ms=3000):
                elapsed = round(time.time() - start_time, 1)
                self.log.log_action("LIGHTROOM_RESPONSIVE",
                                  status="ready", elapsed_sec=elapsed)
                return True

            self.log.log_warning("Lightroom not responding (freezing), waiting...")
            time.sleep(2)

        self.log.log_error(f"Lightroom not responsive after {max_wait_seconds}s")
        return False

    def wait_for_lightroom_focus(self, max_retries: int = 10) -> bool:
        if not WINDOWS_AVAILABLE:
            return True

        for attempt in range(max_retries):
            title_contains = self.config.get('lightroom_window_title_contains', 'Lightroom')
            hwnd = self.find_window_by_title(title_contains)

            if not hwnd:
                self.log.log_warning(f"Lightroom window not found yet, waiting... (attempt {attempt + 1}/{max_retries})")
                time.sleep(1.5)
                continue

            if self.is_lightroom_foreground():
                self.log.log_action("LIGHTROOM_FOCUS", status="success", attempt=attempt + 1)
                return True

            self.activate_lightroom()
            time.sleep(0.8)

            if self.is_lightroom_foreground():
                self.log.log_action("LIGHTROOM_FOCUS", status="success", attempt=attempt + 1)
                return True

            self.log.log_warning(f"Lightroom focus attempt {attempt + 1}/{max_retries} failed")

        self.log.log_error("Failed to focus Lightroom after multiple attempts")
        return False


# =============================================================================
# 매크로 액션
# =============================================================================
class MacroActions:
    def __init__(self, config: ConfigManager, log_manager: LogManager,
                 win_controller: WindowsController):
        self.config = config
        self.log = log_manager
        self.win = win_controller

    def action_start_tethering(self) -> bool:
        """테더링 촬영 시작 - 완전 자동화 (프리징 대응)"""
        if not self.win.ensure_lightroom_running():
            return False

        # 1단계: Lightroom이 프리징에서 풀릴 때까지 대기
        self.log.log_action("TETHER_PREP", status="waiting_for_responsive")
        if not self.win.wait_for_lightroom_responsive(max_wait_seconds=120):
            self.log.log_error("Cannot start tethering: Lightroom not responsive")
            return False

        # 2단계: 포커스 확보
        if not self.win.wait_for_lightroom_focus():
            self.log.log_error("Cannot start tethering: Lightroom is not in foreground")
            return False

        # 3단계: 한 번 더 응답 확인 후 키 입력 시작
        time.sleep(1)
        self.win.activate_lightroom()
        time.sleep(0.5)

        # 응답 재확인 (activate 직후 프리징 가능)
        if not self.win.wait_for_lightroom_responsive(max_wait_seconds=30):
            self.log.log_error("Lightroom froze again after activation")
            return False

        # 파일 메뉴에서 테더링 다이얼로그 열기
        keyboard.send('alt+f')
        time.sleep(1.0)  # 메뉴 열림 대기 (저사양 대응)

        for _ in range(8):
            keyboard.send('down')
            time.sleep(0.15)

        keyboard.send('right')
        time.sleep(0.5)
        keyboard.send('enter')
        time.sleep(1.0)  # 다이얼로그 열림 대기

        # 세션 정보 입력
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M")
        keyboard.write(session_name)

        time.sleep(0.3)
        keyboard.send('tab')
        time.sleep(0.2)
        keyboard.send('tab')
        time.sleep(0.2)
        keyboard.send('tab')
        time.sleep(0.2)
        keyboard.send('tab')
        time.sleep(0.2)
        keyboard.write('1')

        time.sleep(0.3)
        keyboard.send('enter')
        time.sleep(2)

        # Library 확대경 뷰로 이동
        keyboard.send('ctrl+alt+1')
        time.sleep(0.5)
        keyboard.send('e')
        time.sleep(0.5)

        self.log.log_action("TETHER_START", status="success", session=session_name)
        return True

    def action_export_all(self) -> bool:
        """전체 내보내기"""
        if not self.win.wait_for_lightroom_focus():
            self.log.log_error("Cannot export: Lightroom is not in foreground")
            return False

        sequence = self.config.get('export_all_sequence', [
            {'action': 'key', 'value': 'ctrl+a', 'delay_after_ms': 300},
            {'action': 'key', 'value': 'ctrl+alt+shift+e', 'delay_after_ms': 100}
        ])

        if not self.win.send_key_sequence(sequence):
            return False

        self.log.log_action("EXPORT_ALL", status="success")
        return True

    def action_end_session(self) -> bool:
        """촬영 종료 - 내보내기 폴더 비우기 + 압축파일 삭제 + 라이트룸 종료"""
        import glob

        export_folder = self.config.get('export_target_folder', 'Desktop\\보정사진')
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        full_export_path = os.path.join(desktop_path,
                                        export_folder.replace('Desktop\\', '').replace('Desktop/', ''))

        try:
            # 1. 내보내기 폴더 비우기
            if os.path.exists(full_export_path) and os.listdir(full_export_path):
                for item in os.listdir(full_export_path):
                    item_path = os.path.join(full_export_path, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)

            # 2. 바탕화면의 사진_*.zip 파일 삭제
            zip_pattern = os.path.join(desktop_path, "사진_*.zip")
            zip_files = glob.glob(zip_pattern)
            for zip_file in zip_files:
                os.remove(zip_file)

            # 3. 라이트룸 종료
            lightroom_closed = False
            if WINDOWS_AVAILABLE:
                process_name = self.config.get('lightroom_process_name', 'Lightroom.exe')
                for proc in psutil.process_iter(['name', 'pid']):
                    try:
                        if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                            proc.terminate()
                            proc.wait(timeout=5)
                            lightroom_closed = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        pass

            self.log.log_action("SESSION_END", status="success",
                              folder_cleared=full_export_path,
                              zip_deleted=len(zip_files),
                              lightroom_closed=lightroom_closed)
            return True
        except Exception as e:
            self.log.log_error(f"Session end failed: {e}")
            return False

    def get_export_folder_path(self) -> str:
        export_folder = self.config.get('export_target_folder', 'Desktop\\보정사진')
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        return os.path.join(desktop_path, export_folder.replace('Desktop\\', '').replace('Desktop/', ''))

    def create_share_zip(self) -> Optional[str]:
        """내보내기 폴더 전체를 압축"""
        export_path = self.get_export_folder_path()

        if not os.path.exists(export_path) or not os.listdir(export_path):
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"사진_{timestamp}.zip"
        zip_path = os.path.join(os.path.expanduser('~'), 'Desktop', zip_filename)

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(export_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, export_path)
                        zipf.write(file_path, arcname)

            self.log.log_action("ZIP_CREATED", path=zip_path)
            return zip_path
        except Exception as e:
            self.log.log_error(f"ZIP creation failed: {e}")
            return None


# =============================================================================
# 스레드 워커
# =============================================================================
class ActionWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, action_func, action_name: str):
        super().__init__()
        self.action_func = action_func
        self.action_name = action_name

    def run(self):
        try:
            result = self.action_func()
            if result:
                self.finished.emit(True, f"{self.action_name} 완료")
            else:
                self.finished.emit(False, f"{self.action_name} 실패")
        except Exception as e:
            self.finished.emit(False, f"오류: {str(e)}")


# =============================================================================
# 사운드 재생
# =============================================================================
class SoundPlayer:
    """MP3 사운드 파일 재생 클래스 (pygame 사용)"""

    SOUND_FILES = {
        'start': 'Start_shoot.mp3',
        'end_15min': 'end_15min.mp3',
        'end_5min': 'end_5min.mp3',
        'end': 'The_end.mp3'
    }

    _initialized = False

    @classmethod
    def get_sounds_dir(cls):
        return os.path.join(os.getcwd(), 'Sounds')

    @classmethod
    def _init_mixer(cls):
        if not cls._initialized:
            try:
                import pygame
                pygame.mixer.init()
                cls._initialized = True
            except Exception as e:
                print(f"pygame mixer init failed: {e}")

    @classmethod
    def play(cls, sound_type: str):
        sound_file = cls.SOUND_FILES.get(sound_type)
        if not sound_file:
            return

        sound_path = os.path.join(cls.get_sounds_dir(), sound_file)
        if not os.path.exists(sound_path):
            return

        def _play_thread():
            try:
                import pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(sound_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except Exception as e:
                print(f"Sound playback error: {e}")

        import threading
        thread = threading.Thread(target=_play_thread, daemon=True)
        thread.start()


# =============================================================================
# 세션 타이머
# =============================================================================
class SessionTimer(QThread):
    """촬영 세션 타이머 - 사운드 알림 기능"""
    reminder_signal = Signal(str)
    timer_tick = Signal(int)  # 남은 초
    session_ended = Signal()

    def __init__(self, duration_minutes: int = 35):
        super().__init__()
        self.duration_minutes = duration_minutes
        self.total_seconds = duration_minutes * 60
        self.remaining_seconds = self.total_seconds
        self.is_running = False

        self.reminder_points = {
            15: "15분 남았습니다.",
            5: "5분 남았습니다.",
            0: "촬영이 종료되었습니다."
        }
        self.reminded = set()

    def run(self):
        self.is_running = True
        self.reminded.clear()

        SoundPlayer.play('start')
        self.reminder_signal.emit(f"촬영 시작! ({self.duration_minutes}분)")

        while self.remaining_seconds > 0 and self.is_running:
            time.sleep(1)
            self.remaining_seconds -= 1
            self.timer_tick.emit(self.remaining_seconds)

            if self.remaining_seconds == 15 * 60 and 15 not in self.reminded:
                self.reminded.add(15)
                SoundPlayer.play('end_15min')
                self.reminder_signal.emit(self.reminder_points[15])

            elif self.remaining_seconds == 5 * 60 and 5 not in self.reminded:
                self.reminded.add(5)
                SoundPlayer.play('end_5min')
                self.reminder_signal.emit(self.reminder_points[5])

        if self.is_running:
            SoundPlayer.play('end')
            self.reminder_signal.emit(self.reminder_points[0])
            self.session_ended.emit()

        self.is_running = False

    def stop(self):
        self.is_running = False


# =============================================================================
# 다이얼로그
# =============================================================================
class PackageSelectDialog(QDialog):
    """패키지 선택 다이얼로그"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_minutes = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("패키지 선택")
        self.setFixedSize(900, 560)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        theme = CURRENT_THEME

        container = QFrame(self)
        container.setGeometry(0, 0, 900, 560)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme['dialog_bg']};
                border-radius: 40px;
                border: 4px solid {theme['glass_border']};
            }}
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(40)

        title = QLabel("촬영 패키지를 선택해주세요")
        title.setStyleSheet(f"color: {theme['text_main']}; font-size: 40px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(20)

        btn_basic = QPushButton("30분 촬영 - 베이직")
        btn_basic.setFixedHeight(120)
        btn_basic.setCursor(Qt.PointingHandCursor)
        btn_basic.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['glass_bg']};
                border: 4px solid {theme['glass_border']};
                border-radius: 30px;
                color: {theme['text_main']};
                font-size: 36px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme['glass_hover']};
                border-color: {theme['text_accent']};
            }}
        """)
        btn_basic.clicked.connect(lambda: self._select_package(30))
        layout.addWidget(btn_basic)

        btn_premium = QPushButton("⭐ 55분 촬영 - 프리미엄 ⭐")
        btn_premium.setFixedHeight(120)
        btn_premium.setCursor(Qt.PointingHandCursor)
        btn_premium.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(218, 165, 32, 0.3), stop:1 rgba(184, 134, 11, 0.3));
                border: 4px solid rgba(218, 165, 32, 0.8);
                border-radius: 30px;
                color: #FFD700;
                font-size: 36px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(218, 165, 32, 0.5), stop:1 rgba(184, 134, 11, 0.5));
                border-color: #DAA520;
            }}
        """)
        btn_premium.clicked.connect(lambda: self._select_package(55))
        layout.addWidget(btn_premium)

    def _select_package(self, minutes):
        self.selected_minutes = minutes
        self.accept()

    def get_selected_minutes(self):
        return self.selected_minutes


class ConfirmDialog(QDialog):
    """확인/취소 다이얼로그"""
    def __init__(self, title: str, message: str, sub_message: str = "",
                 icon_svg: str = None, parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setFixedSize(750, 500)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._setup_ui(title, message, sub_message, icon_svg)

    def _setup_ui(self, title: str, message: str, sub_message: str, icon_svg: str):
        theme = CURRENT_THEME

        main_widget = QFrame(self)
        main_widget.setGeometry(0, 0, 750, 500)
        main_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {theme['dialog_bg']};
                border-radius: 20px;
                border: 1px solid {theme['glass_border']};
            }}
        """)

        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        if icon_svg:
            icon_label = QLabel()
            icon_label.setFixedSize(100, 100)
            icon_label.setAlignment(Qt.AlignCenter)

            colored_svg = icon_svg.replace('currentColor', "#F43F5E")
            renderer = QSvgRenderer(colored_svg.encode())
            pixmap = QPixmap(100, 100)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            icon_label.setPixmap(pixmap)

            icon_layout = QHBoxLayout()
            icon_layout.addStretch()
            icon_layout.addWidget(icon_label)
            icon_layout.addStretch()
            layout.addLayout(icon_layout)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {theme['text_main']}; font-size: 32px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"color: {theme['text_sub']}; font-size: 24px;")
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        if sub_message:
            sub_label = QLabel(sub_message)
            sub_label.setStyleSheet(f"""
                color: {theme['text_accent']}; font-size: 13px;
                padding: 8px; background-color: rgba(255,255,255,0.05); border-radius: 8px;
            """)
            sub_label.setAlignment(Qt.AlignCenter)
            sub_label.setWordWrap(True)
            layout.addWidget(sub_label)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        cancel_btn = QPushButton("취소")
        cancel_btn.setFixedSize(130, 45)
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255,255,255,0.1); color: {theme['text_sub']};
                border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; font-size: 14px; font-weight: bold; }}
            QPushButton:hover {{ background-color: rgba(255,255,255,0.2); color: white; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("확인")
        confirm_btn.setFixedSize(130, 45)
        confirm_btn.setCursor(QCursor(Qt.PointingHandCursor))
        confirm_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(244, 63, 94, 0.8); color: white;
                border: none; border-radius: 12px; font-size: 14px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #E11D48; }}
        """)
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)


# =============================================================================
# AppIcon (iPad 스타일 앱 아이콘)
# =============================================================================
class AppIcon(QWidget):
    """iPad Home Screen Style App Icon"""
    def __init__(self, title, svg_xml, bg_color, action_callback=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 220)
        self.action_callback = action_callback
        self._current_bg_color = bg_color
        self._current_svg = svg_xml

        self.bg = QFrame(self)
        self.bg.setGeometry(20, 10, 140, 140)
        self.bg.setStyleSheet(f"background-color: {bg_color}; border-radius: 35px;")

        self.icon_lbl = QLabel(self.bg)
        self.icon_lbl.setGeometry(35, 35, 70, 70)
        self.icon_lbl.setAlignment(Qt.AlignCenter)

        self._render_svg(svg_xml)

        self.text_lbl = QLabel(title, self)
        self.text_lbl.setGeometry(0, 160, 180, 40)
        self.text_lbl.setAlignment(Qt.AlignCenter)
        self.text_lbl.setStyleSheet("color: #FFFFFF; font-family: 'Segoe UI', 'Malgun Gothic'; font-size: 20px; font-weight: 600;")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.bg.setGraphicsEffect(shadow)

        self.setCursor(Qt.PointingHandCursor)

    def _render_svg(self, svg_xml):
        if svg_xml:
            pm = QPixmap(70, 70)
            pm.fill(Qt.transparent)
            painter = QPainter(pm)
            renderer = QSvgRenderer(QByteArray(svg_xml.encode()))
            renderer.render(painter)
            painter.end()
            self.icon_lbl.setPixmap(pm)

    def enterEvent(self, e):
        self.bg.setGeometry(15, 5, 150, 150)
        self.icon_lbl.setGeometry(37, 37, 76, 76)

    def leaveEvent(self, e):
        self.bg.setGeometry(20, 10, 140, 140)
        self.icon_lbl.setGeometry(35, 35, 70, 70)

    def mousePressEvent(self, e):
        self.bg.setGeometry(25, 15, 130, 130)
        self.icon_lbl.setGeometry(32, 32, 66, 66)

    def mouseReleaseEvent(self, e):
        self.bg.setGeometry(15, 5, 150, 150)
        self.icon_lbl.setGeometry(37, 37, 76, 76)
        if self.action_callback:
            self.action_callback()


# =============================================================================
# 프리미엄 UI 위젯 (Apple Style)
# =============================================================================
class StartShootingButton(QPushButton):
    """촬영 시작 버튼 - Apple 스타일 대형 터치 버튼

    QPainter로 직접 렌더링하여 SVG 의존성 없이 확실하게 표시.
    은은한 pulse 애니메이션 + 카메라 아이콘 + "촬영 시작" 텍스트 통합.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pulse_opacity = 0.0

        # Pulse 애니메이션 (테두리 밝기 호흡)
        self.anim = QPropertyAnimation(self, b"pulseOpacity")
        self.anim.setDuration(3000)
        self.anim.setStartValue(0.0)
        self.anim.setKeyValueAt(0.5, 1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1)
        self.anim.start()

    def get_pulse_opacity(self):
        return self._pulse_opacity

    def set_pulse_opacity(self, val):
        self._pulse_opacity = val
        self.update()

    pulseOpacity = Property(float, get_pulse_opacity, set_pulse_opacity)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        # ── 1. 외곽 글로우 (pulse) ──
        if self._pulse_opacity > 0:
            glow_r = min(w, h) / 2 + 20
            grad = QRadialGradient(cx, cy, glow_r)
            alpha = int(25 * self._pulse_opacity)
            grad.setColorAt(0.6, QColor(255, 255, 255, alpha))
            grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.NoPen)
            p.drawEllipse(int(cx - glow_r), int(cy - glow_r),
                          int(glow_r * 2), int(glow_r * 2))

        # ── 2. 메인 원형 배경 ──
        btn_r = min(w, h) / 2 - 25
        border_alpha = int(40 + 30 * self._pulse_opacity)

        # 배경 (반투명 다크)
        p.setBrush(QBrush(QColor(255, 255, 255, 12)))
        p.setPen(QPen(QColor(255, 255, 255, border_alpha), 2.0))
        p.drawEllipse(int(cx - btn_r), int(cy - btn_r),
                      int(btn_r * 2), int(btn_r * 2))

        # ── 3. 카메라 아이콘 (QPainter로 직접 그리기) ──
        icon_color = QColor(255, 255, 255, 210)
        p.setPen(QPen(icon_color, 3.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)

        # 카메라 본체 비율 계산 (중앙 위쪽에 배치)
        icon_w = 80
        icon_h = 56
        ix = cx - icon_w / 2
        iy = cy - 50  # 중앙보다 위

        # 카메라 본체 (둥근 사각형)
        body_path = QPainterPath()
        body_path.addRoundedRect(ix, iy + 14, icon_w, icon_h - 14, 10, 10)
        p.drawPath(body_path)

        # 카메라 상단 돌출부 (렌즈 하우징)
        top_path = QPainterPath()
        top_path.moveTo(ix + 22, iy + 14)
        top_path.lineTo(ix + 28, iy + 4)
        top_path.lineTo(ix + 52, iy + 4)
        top_path.lineTo(ix + 58, iy + 14)
        p.drawPath(top_path)

        # 렌즈 (원)
        lens_cx = cx
        lens_cy = iy + 36
        p.drawEllipse(int(lens_cx - 14), int(lens_cy - 14), 28, 28)

        # 렌즈 내부 점
        p.setBrush(QBrush(icon_color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(int(lens_cx - 5), int(lens_cy - 5), 10, 10)

        # ── 4. "촬영 시작" 텍스트 ──
        p.setPen(QColor(255, 255, 255, 200))

        main_font = QFont('Apple SD Gothic Neo', 22)
        main_font.setStyleStrategy(QFont.PreferAntialias)
        if not QFontDatabase.hasFamily('Apple SD Gothic Neo'):
            main_font = QFont('Malgun Gothic', 22)
        main_font.setWeight(QFont.DemiBold)
        main_font.setLetterSpacing(QFont.AbsoluteSpacing, 6)
        p.setFont(main_font)

        text_y = cy + 30
        text_rect = QRect(0, int(text_y), w, 40)
        p.drawText(text_rect, Qt.AlignCenter, "촬영 시작")

        # ── 5. 안내 문구 ──
        p.setPen(QColor(255, 255, 255, 60))
        sub_font = QFont('Malgun Gothic', 11)
        sub_font.setWeight(QFont.Normal)
        p.setFont(sub_font)

        sub_rect = QRect(0, int(text_y + 44), w, 30)
        p.drawText(sub_rect, Qt.AlignCenter, "터치하여 촬영을 시작합니다")

        p.end()


class ExportButton(QPushButton):
    """내보내기 버튼 - QPainter로 폴더+화살표 아이콘 + 텍스트 직접 렌더링"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pulse_opacity = 0.0

        self.anim = QPropertyAnimation(self, b"pulseOpacity")
        self.anim.setDuration(3000)
        self.anim.setStartValue(0.0)
        self.anim.setKeyValueAt(0.5, 1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1)
        self.anim.start()

    def get_pulse_opacity(self):
        return self._pulse_opacity

    def set_pulse_opacity(self, val):
        self._pulse_opacity = val
        self.update()

    pulseOpacity = Property(float, get_pulse_opacity, set_pulse_opacity)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        # ── 1. 외곽 글로우 (pulse) ──
        if self._pulse_opacity > 0:
            glow_r = min(w, h) / 2 + 20
            grad = QRadialGradient(cx, cy, glow_r)
            alpha = int(20 * self._pulse_opacity)
            grad.setColorAt(0.6, QColor(10, 132, 255, alpha))
            grad.setColorAt(1.0, QColor(10, 132, 255, 0))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.NoPen)
            p.drawEllipse(int(cx - glow_r), int(cy - glow_r),
                          int(glow_r * 2), int(glow_r * 2))

        # ── 2. 메인 원형 배경 ──
        btn_r = min(w, h) / 2 - 25
        border_alpha = int(40 + 30 * self._pulse_opacity)

        p.setBrush(QBrush(QColor(10, 132, 255, 15)))
        p.setPen(QPen(QColor(10, 132, 255, border_alpha), 2.0))
        p.drawEllipse(int(cx - btn_r), int(cy - btn_r),
                      int(btn_r * 2), int(btn_r * 2))

        # ── 3. 내보내기 아이콘 (폴더 + 위쪽 화살표) ──
        icon_color = QColor(10, 132, 255, 210)
        p.setPen(QPen(icon_color, 3.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)

        # 아이콘 기준점 (중앙 위쪽)
        ix = cx - 40
        iy = cy - 55

        # 폴더 본체
        folder = QPainterPath()
        folder.moveTo(ix, iy + 18)
        folder.lineTo(ix, iy + 60)
        folder.lineTo(ix + 80, iy + 60)
        folder.lineTo(ix + 80, iy + 18)
        folder.lineTo(ix + 50, iy + 18)
        folder.lineTo(ix + 44, iy + 8)
        folder.lineTo(ix + 16, iy + 8)
        folder.lineTo(ix + 10, iy + 18)
        folder.closeSubpath()
        p.drawPath(folder)

        # 위쪽 화살표 (내보내기 상징)
        arrow_cx = cx
        arrow_top = iy + 24
        arrow_bot = iy + 50

        # 화살표 줄기
        p.drawLine(int(arrow_cx), int(arrow_top), int(arrow_cx), int(arrow_bot))

        # 화살표 머리
        arrow_head = QPainterPath()
        arrow_head.moveTo(arrow_cx - 10, arrow_top + 10)
        arrow_head.lineTo(arrow_cx, arrow_top)
        arrow_head.lineTo(arrow_cx + 10, arrow_top + 10)
        p.drawPath(arrow_head)

        # ── 4. "내보내기" 텍스트 ──
        p.setPen(QColor(10, 132, 255, 200))

        main_font = QFont('Apple SD Gothic Neo', 22)
        main_font.setStyleStrategy(QFont.PreferAntialias)
        if not QFontDatabase.hasFamily('Apple SD Gothic Neo'):
            main_font = QFont('Malgun Gothic', 22)
        main_font.setWeight(QFont.DemiBold)
        main_font.setLetterSpacing(QFont.AbsoluteSpacing, 6)
        p.setFont(main_font)

        text_y = cy + 30
        text_rect = QRect(0, int(text_y), w, 40)
        p.drawText(text_rect, Qt.AlignCenter, "내보내기")

        # ── 5. 안내 문구 ──
        p.setPen(QColor(255, 255, 255, 60))
        sub_font = QFont('Malgun Gothic', 11)
        sub_font.setWeight(QFont.Normal)
        p.setFont(sub_font)

        sub_rect = QRect(0, int(text_y + 44), w, 30)
        p.drawText(sub_rect, Qt.AlignCenter, "사진을 바탕화면으로 내보냅니다")

        p.end()


# =============================================================================
# 상태 표시 위젯
# =============================================================================
class StatusWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        theme = CURRENT_THEME
        self.setStyleSheet(f"color: {theme['text_sub']}; font-size: 24px; padding: 10px;")
        self.setAlignment(Qt.AlignCenter)

    def update_status(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.setText(f"[{timestamp}] {message}")


# =============================================================================
# Home Assistant 연동
# =============================================================================
class HomeAssistantController:
    """Home Assistant REST API를 통한 스마트 스위치 제어

    config.json의 home_assistant 섹션에서 설정을 읽어옵니다:
      {
        "home_assistant": {
          "url": "http://homeassistant.local:8123",
          "token": "YOUR_LONG_LIVED_ACCESS_TOKEN",
          "light_entity": "switch.studio_light",
          "camera_entity": "switch.studio_camera"
        }
      }
    """

    def __init__(self, config: 'ConfigManager', log_manager: 'LogManager' = None):
        self.log = log_manager
        ha_config = config.get('home_assistant', {})
        self._url = ha_config.get('url', '').rstrip('/')
        self._token = ha_config.get('token', '')
        self._light_entity = ha_config.get('light_entity', '')
        self._camera_entity = ha_config.get('camera_entity', '')
        self._available = bool(self._url and self._token)

        if not self._available and self.log:
            self.log.log_warning("Home Assistant 설정 없음 (config.json → home_assistant)")

    def _call_service(self, domain: str, service: str, entity_id: str) -> bool:
        """Home Assistant 서비스 호출 (REST API)"""
        if not self._available or not entity_id:
            return False

        import urllib.request
        import urllib.error

        url = f"{self._url}/api/services/{domain}/{service}"
        data = json.dumps({"entity_id": entity_id}).encode('utf-8')

        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Authorization', f'Bearer {self._token}')
        req.add_header('Content-Type', 'application/json')

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if self.log:
                    self.log.log_action("HA_SERVICE_CALL",
                                        service=f"{domain}.{service}",
                                        entity=entity_id,
                                        status=resp.status)
                return resp.status == 200
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            if self.log:
                self.log.log_error(f"Home Assistant 호출 실패: {domain}.{service} → {e}")
            return False

    def turn_on_studio(self) -> dict:
        """조명 + 카메라 전원 ON"""
        results = {}
        results['light'] = self._call_service('switch', 'turn_on', self._light_entity)
        results['camera'] = self._call_service('switch', 'turn_on', self._camera_entity)
        if self.log:
            self.log.log_action("HA_STUDIO_ON", **results)
        return results

    def turn_off_studio(self) -> dict:
        """조명 + 카메라 전원 OFF"""
        results = {}
        results['light'] = self._call_service('switch', 'turn_off', self._light_entity)
        results['camera'] = self._call_service('switch', 'turn_off', self._camera_entity)
        if self.log:
            self.log.log_action("HA_STUDIO_OFF", **results)
        return results

    @property
    def is_available(self) -> bool:
        return self._available


# =============================================================================
# Google Calendar 연동
# =============================================================================
class CalendarSync:
    """Google Calendar API를 통한 예약 조회 및 패키지 자동 감지

    캘린더 이벤트 제목에 키워드를 포함하여 패키지를 구분합니다:
      - "프리미엄" 또는 "premium" → 프리미엄 (50분)
      - 그 외 → 베이직 (35분)

    사용법:
      1. Google Cloud Console에서 Calendar API 활성화
      2. OAuth 2.0 데스크탑 앱 사용자 인증 정보 다운로드 → credentials.json
      3. 최초 실행 시 브라우저 인증 → token.json 자동 생성
    """

    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    TOKEN_PATH = 'token.json'
    CREDENTIALS_PATH = 'credentials.json'

    # 패키지 설정
    PACKAGE_CONFIG = {
        'basic':   {'minutes': 35, 'keywords': []},           # 기본값 (키워드 매칭 실패 시)
        'premium': {'minutes': 50, 'keywords': ['프리미엄', 'premium']},
    }

    def __init__(self, log_manager: LogManager = None):
        self.log = log_manager
        self._service = None
        self._auth_failed = False

    def _get_service(self):
        """Google Calendar API 서비스 객체 (lazy init + 캐싱)"""
        if self._service is not None:
            return self._service

        if self._auth_failed:
            return None

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            if self.log:
                self.log.log_warning("Google Calendar 패키지 미설치 (pip install google-api-python-client google-auth-oauthlib)")
            self._auth_failed = True
            return None

        creds = None

        # 저장된 토큰 로드
        if os.path.exists(self.TOKEN_PATH):
            try:
                creds = Credentials.from_authorized_user_file(self.TOKEN_PATH, self.SCOPES)
            except Exception:
                creds = None

        # 토큰 갱신 또는 새로 인증
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None

            if not creds:
                if not os.path.exists(self.CREDENTIALS_PATH):
                    if self.log:
                        self.log.log_warning(f"Google Calendar 인증 파일 없음: {self.CREDENTIALS_PATH}")
                    self._auth_failed = True
                    return None
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.CREDENTIALS_PATH, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    if self.log:
                        self.log.log_error(f"Google Calendar 인증 실패: {e}")
                    self._auth_failed = True
                    return None

            # 토큰 저장
            try:
                with open(self.TOKEN_PATH, 'w') as f:
                    f.write(creds.to_json())
            except Exception:
                pass

        try:
            self._service = build('calendar', 'v3', credentials=creds)
            if self.log:
                self.log.log_action("CALENDAR_INIT", status="success")
            return self._service
        except Exception as e:
            if self.log:
                self.log.log_error(f"Google Calendar 서비스 생성 실패: {e}")
            self._auth_failed = True
            return None

    def get_current_event(self) -> Optional[Dict]:
        """현재 시간에 진행 중인 캘린더 이벤트 조회"""
        service = self._get_service()
        if not service:
            return None

        try:
            now = datetime.now(timezone.utc)
            time_min = now.strftime('%Y-%m-%dT%H:%M:%SZ')
            time_max = (now + timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ')

            result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=5,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = result.get('items', [])

            # 현재 시간에 걸쳐 있는 이벤트 찾기 (시작 <= now <= 종료)
            for event in events:
                start = event.get('start', {})
                end = event.get('end', {})

                # 종일 이벤트 → dateTime이 없고 date만 있음
                start_str = start.get('dateTime', start.get('date', ''))
                end_str = end.get('dateTime', end.get('date', ''))

                if start_str and end_str:
                    if self.log:
                        self.log.log_action("CALENDAR_EVENT_FOUND",
                                          summary=event.get('summary', ''),
                                          start=start_str)
                    return event

            # 현재 진행 중인 이벤트가 없으면, 가장 가까운 예약 조회
            time_max_extended = (now + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
            result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max_extended,
                maxResults=1,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = result.get('items', [])
            if events:
                event = events[0]
                if self.log:
                    self.log.log_action("CALENDAR_NEXT_EVENT",
                                      summary=event.get('summary', ''),
                                      start=event.get('start', {}).get('dateTime', ''))
                return event

            return None

        except Exception as e:
            if self.log:
                self.log.log_error(f"캘린더 이벤트 조회 실패: {e}")
            return None

    def detect_package_from_event(self, event: Dict) -> tuple:
        """이벤트 제목/설명에서 패키지 타입 감지 → (package_type, minutes)"""
        if not event:
            return ('basic', self.PACKAGE_CONFIG['basic']['minutes'])

        summary = (event.get('summary', '') or '').lower()
        description = (event.get('description', '') or '').lower()
        search_text = f"{summary} {description}"

        # 프리미엄 키워드 검색
        for keyword in self.PACKAGE_CONFIG['premium']['keywords']:
            if keyword.lower() in search_text:
                return ('premium', self.PACKAGE_CONFIG['premium']['minutes'])

        # 기본값: 베이직
        return ('basic', self.PACKAGE_CONFIG['basic']['minutes'])

    def get_current_session_info(self) -> dict:
        """현재 예약의 세션 정보 반환

        Returns:
            {
                'package': 'basic' | 'premium',
                'total_minutes': 35 | 50,
                'remaining_minutes': int,  # 지금부터 종료까지 남은 분
                'hard_end_time': datetime | None,  # 캘린더 기준 고정 종료 시각
                'event_summary': str,
            }

        캘린더 연동 실패 시 remaining_minutes = total_minutes (풀타임 제공)
        """
        event = self.get_current_event()
        package_type, total_minutes = self.detect_package_from_event(event)

        result = {
            'package': package_type,
            'total_minutes': total_minutes,
            'remaining_minutes': total_minutes,
            'hard_end_time': None,
            'event_summary': '',
        }

        if event:
            result['event_summary'] = event.get('summary', '')

            # 캘린더 이벤트의 시작 시각에서 패키지 시간을 더한 값이 고정 종료 시각
            start_info = event.get('start', {})
            start_str = start_info.get('dateTime', '')

            if start_str:
                try:
                    # ISO 8601 파싱 (타임존 포함)
                    if '+' in start_str or start_str.endswith('Z'):
                        # Python 3.7+ fromisoformat은 Z를 지원하지 않을 수 있음
                        start_str_clean = start_str.replace('Z', '+00:00')
                        event_start = datetime.fromisoformat(start_str_clean)
                    else:
                        event_start = datetime.fromisoformat(start_str)

                    hard_end = event_start + timedelta(minutes=total_minutes)
                    now = datetime.now(timezone.utc)

                    # 로컬 타임존이 없으면 UTC로 가정
                    if hard_end.tzinfo is None:
                        hard_end = hard_end.replace(tzinfo=timezone.utc)

                    remaining = (hard_end - now).total_seconds() / 60.0
                    remaining = max(0, int(remaining))

                    result['hard_end_time'] = hard_end
                    result['remaining_minutes'] = remaining

                    if self.log:
                        self.log.log_action("CALENDAR_SESSION_CALC",
                                            package=package_type,
                                            event_start=str(event_start),
                                            hard_end=str(hard_end),
                                            remaining_min=remaining)
                except (ValueError, TypeError) as e:
                    if self.log:
                        self.log.log_error(f"캘린더 시간 파싱 실패: {e}")

        return result


# =============================================================================
# 메인 윈도우
# =============================================================================
class MainWindow(QMainWindow):
    def __init__(self, config: ConfigManager, actions: MacroActions,
                 calendar: CalendarSync = None,
                 ha_controller: HomeAssistantController = None):
        super().__init__()

        self.config = config
        self.actions = actions
        self.calendar = calendar or CalendarSync()
        self.ha = ha_controller
        self.current_worker = None
        self.session_timer = None
        self.current_package = "basic"
        self._session_minutes = 30
        self._hard_end_time = None  # 캘린더 기준 고정 종료 시각
        self._current_state = STATE_IDLE

        self.gui_config = config.get('gui_settings', {})

        self.setWindowTitle(APP_NAME)

        if self.gui_config.get('always_on_top', True):
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        self._setup_ui()
        self._move_to_monitor()

    def _setup_ui(self):
        self.setStyleSheet("background-color: #1C1C1E;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === QStackedWidget: 상태별 화면 전환 ===
        self.stacked = QStackedWidget()
        main_layout.addWidget(self.stacked)

        # --- 화면 1: IDLE (촬영 시작 대기) ---
        self.idle_page = self._create_idle_page()
        self.stacked.addWidget(self.idle_page)

        # --- 화면 1.5: CONFIRM (촬영 확인) ---
        self.confirm_page = self._create_confirm_page()
        self.stacked.addWidget(self.confirm_page)

        # --- 화면 2: SHOOTING (촬영 중 타이머) ---
        self.shooting_page = self._create_shooting_page()
        self.stacked.addWidget(self.shooting_page)

        # --- 화면 3: EXPORT_READY (내보내기) ---
        self.export_page = self._create_export_page()
        self.stacked.addWidget(self.export_page)

        # 초기 상태
        self.stacked.setCurrentWidget(self.idle_page)

    def _create_idle_page(self) -> QWidget:
        """화면 1: IDLE - 촬영 시작 (Apple Style, 대형 버튼)"""
        page = QWidget()
        page.setStyleSheet("background-color: #000000;")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        studio_name = self.config.get('studio_name', 'Studio Birthday')

        # ── 상단 스튜디오 이름 ──
        header_label = QLabel(studio_name.upper())
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.2);
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 10px;
            padding-top: 50px;
        """)
        layout.addWidget(header_label)

        layout.addStretch(2)

        # ── 중앙: 촬영 시작 버튼 (카메라 아이콘 + 텍스트 통합) ──
        self.start_button = StartShootingButton()
        self.start_button.setFixedSize(340, 380)
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self._on_start_clicked)
        self.start_button.setStyleSheet("background: transparent; border: none;")

        layout.addWidget(self.start_button, alignment=Qt.AlignCenter)
        layout.addStretch(3)

        # ── 하단 상태바 ──
        self.idle_status = StatusWidget()
        layout.addWidget(self.idle_status)

        return page

    def _create_confirm_page(self) -> QWidget:
        """화면 1.5: CONFIRM - 촬영 시작 확인 (스크린샷 매칭)"""
        page = QWidget()
        page.setStyleSheet("background-color: #000000;")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        theme = CURRENT_THEME
        studio_name = self.config.get('studio_name', 'Studio Birthday')

        # 상단 스튜디오 이름
        header_label = QLabel(studio_name.upper())
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet(f"""
            color: rgba(255, 255, 255, 0.3);
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 8px;
            padding-top: 40px;
        """)
        layout.addWidget(header_label)

        layout.addStretch(2)

        # === 중앙 콘텐츠 ===
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(16)

        # 뱃지 라벨 (패키지 타입)
        badge_container = QHBoxLayout()
        badge_container.setAlignment(Qt.AlignCenter)
        self.confirm_badge = QLabel("BASIC")
        self.confirm_badge.setFixedHeight(32)
        self.confirm_badge.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 16px;
            padding: 4px 20px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 4px;
        """)
        badge_container.addWidget(self.confirm_badge)
        center_layout.addLayout(badge_container)

        center_layout.addSpacing(8)

        # 타이틀: 촬영을\n시작할까요?
        title_label = QLabel("촬영을\n시작할까요?")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 42px;
            font-weight: 700;
            line-height: 1.3;
        """)
        center_layout.addWidget(title_label)

        center_layout.addSpacing(4)

        # 서브타이틀
        subtitle = QLabel("촬영 시작 버튼을 누르면 카메라와 조명이 켜집니다")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            color: rgba(255, 255, 255, 0.35);
            font-size: 14px;
            font-weight: 400;
        """)
        center_layout.addWidget(subtitle)

        center_layout.addSpacing(30)

        # 시간 표시 (50분)
        self.confirm_time_label = QLabel("50분")
        self.confirm_time_label.setAlignment(Qt.AlignCenter)
        self.confirm_time_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 72px;
            font-weight: 300;
            font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
        """)
        center_layout.addWidget(self.confirm_time_label)

        # "분" 단위 라벨
        unit_label = QLabel("분")
        unit_label.setAlignment(Qt.AlignCenter)
        unit_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.4);
            font-size: 16px;
            font-weight: 400;
            margin-top: -10px;
        """)
        center_layout.addWidget(unit_label)

        center_layout.addSpacing(30)

        # 촬영 시작 버튼 (흰색 라운드)
        btn_start_container = QHBoxLayout()
        btn_start_container.setAlignment(Qt.AlignCenter)

        confirm_start_btn = QPushButton("촬영 시작")
        confirm_start_btn.setFixedSize(280, 56)
        confirm_start_btn.setCursor(Qt.PointingHandCursor)
        confirm_start_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                border: none;
                border-radius: 28px;
                font-size: 18px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
            }
            QPushButton:pressed {
                background-color: #CCCCCC;
            }
        """)
        confirm_start_btn.clicked.connect(self._on_confirm_start)
        btn_start_container.addWidget(confirm_start_btn)
        center_layout.addLayout(btn_start_container)

        center_layout.addSpacing(12)

        # 이전으로 링크
        back_btn = QPushButton("이전으로")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255, 255, 255, 0.35);
                border: none;
                font-size: 14px;
                font-weight: 400;
            }
            QPushButton:hover {
                color: rgba(255, 255, 255, 0.6);
            }
        """)
        back_btn.clicked.connect(self._on_confirm_back)
        center_layout.addWidget(back_btn, alignment=Qt.AlignCenter)

        layout.addWidget(center)
        layout.addStretch(3)

        return page

    def _create_shooting_page(self) -> QWidget:
        """화면 2: SHOOTING - 타이머 표시"""
        page = QWidget()
        page.setStyleSheet("background-color: #000000;")

        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 120px;
            font-weight: 200;
            font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
        """)
        layout.addWidget(self.timer_label)

        self.timer_sub_label = QLabel("남은 시간")
        self.timer_sub_label.setAlignment(Qt.AlignCenter)
        self.timer_sub_label.setStyleSheet("""
            color: #8E8E93;
            font-size: 24px;
            font-weight: 400;
        """)
        layout.addWidget(self.timer_sub_label)

        return page

    def _create_export_page(self) -> QWidget:
        """화면 3: EXPORT_READY - 촬영 완료 + 내보내기 버튼"""
        page = QWidget()
        page.setStyleSheet("background-color: #000000;")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 상단: 촬영 완료 메시지 ──
        layout.addStretch(2)

        complete_label = QLabel("촬영이 완료되었습니다")
        complete_label.setAlignment(Qt.AlignCenter)
        complete_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.4);
            font-size: 16px;
            font-weight: 400;
            letter-spacing: 4px;
        """)
        layout.addWidget(complete_label)

        layout.addSpacing(40)

        # ── 중앙: 내보내기 버튼 (QPainter 커스텀) ──
        self.export_button = ExportButton()
        self.export_button.setFixedSize(340, 380)
        self.export_button.setCursor(Qt.PointingHandCursor)
        self.export_button.clicked.connect(self._on_export_clicked)
        self.export_button.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.export_button, alignment=Qt.AlignCenter)

        layout.addStretch(1)

        # ── 하단: 내보내기 상태 표시 ──
        self.export_status_label = QLabel("")
        self.export_status_label.setAlignment(Qt.AlignCenter)
        self.export_status_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.3);
            font-size: 13px;
            padding-bottom: 40px;
        """)
        layout.addWidget(self.export_status_label)

        layout.addStretch(1)

        return page

    def _move_to_monitor(self):
        app = QApplication.instance()
        screens = app.screens()

        monitor_index = self.gui_config.get('monitor_index', 1)
        if monitor_index >= len(screens):
            monitor_index = 0

        target_screen = screens[monitor_index]
        geometry = target_screen.geometry()

        self.move(geometry.x(), geometry.y())

        if self.gui_config.get('fullscreen', True):
            self.setGeometry(geometry)
            self.showFullScreen()
        else:
            self.setGeometry(geometry)
            self.showMaximized()

    def switch_state(self, new_state: str):
        """상태 전환"""
        self._current_state = new_state
        if new_state == STATE_IDLE:
            self.stacked.setCurrentWidget(self.idle_page)
        elif new_state == STATE_CONFIRM:
            self.stacked.setCurrentWidget(self.confirm_page)
        elif new_state == STATE_SHOOTING:
            self.stacked.setCurrentWidget(self.shooting_page)
        elif new_state == STATE_EXPORT_READY:
            self.stacked.setCurrentWidget(self.export_page)

    def _on_start_clicked(self):
        """촬영 시작 버튼 → Google Calendar에서 패키지 자동 감지 → 확인 화면"""
        # Google Calendar에서 현재 예약 조회
        session = self.calendar.get_current_session_info()

        package_type = session['package']
        remaining = session['remaining_minutes']
        self._hard_end_time = session['hard_end_time']

        # 늦게 온 경우: 남은 시간이 0 이하면 촬영 불가
        if self._hard_end_time and remaining <= 0:
            QMessageBox.information(self, "예약 시간 초과",
                                   "예약된 촬영 시간이 이미 종료되었습니다.\n다음 예약을 확인해 주세요.")
            return

        self.current_package = package_type
        # 캘린더 연동 시 남은 시간 사용, 미연동 시 전체 시간 사용
        self._session_minutes = remaining if self._hard_end_time else session['total_minutes']
        self.confirm_time_label.setText(f"{self._session_minutes}")

        # 패키지 타입에 따라 뱃지 업데이트
        badge_text = "PREMIUM" if package_type == "premium" else "BASIC"
        badge_color = "rgba(255, 214, 10, 0.7)" if package_type == "premium" else "rgba(255, 255, 255, 0.7)"
        self.confirm_badge.setText(badge_text)
        self.confirm_badge.setStyleSheet(f"""
            color: {badge_color};
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 16px;
            padding: 4px 20px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 4px;
        """)
        self.switch_state(STATE_CONFIRM)

    def _on_confirm_back(self):
        """이전으로 → IDLE 화면 복귀"""
        self.switch_state(STATE_IDLE)

    def _on_confirm_start(self):
        """촬영 시작 확인 → 조명 ON + Lightroom 실행 + 타이머 시작"""
        if self.current_worker is not None and self.current_worker.isRunning():
            return

        minutes = self._session_minutes

        # Home Assistant: 조명 + 카메라 전원 ON (별도 스레드 → 테더링 블로킹 방지)
        if self.ha and self.ha.is_available:
            threading.Thread(target=self.ha.turn_on_studio, daemon=True).start()

        # SHOOTING 화면으로 전환
        self.switch_state(STATE_SHOOTING)
        self._update_timer_display(minutes * 60)

        # 세션 타이머 시작
        self._start_session_timer(minutes)

        # Lightroom 테더링 실행 (백그라운드)
        self._run_action_in_thread(self.actions.action_start_tethering, "촬영 시작")

    def _update_timer_display(self, remaining_seconds: int):
        """타이머 라벨 업데이트"""
        mins = remaining_seconds // 60
        secs = remaining_seconds % 60
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")

    def _start_session_timer(self, minutes=30):
        """세션 타이머 시작"""
        if self.session_timer and self.session_timer.isRunning():
            self.session_timer.stop()
            self.session_timer.wait()

        self.session_timer = SessionTimer(duration_minutes=minutes)
        self.session_timer.reminder_signal.connect(self._on_timer_reminder)
        self.session_timer.timer_tick.connect(self._update_timer_display)
        self.session_timer.session_ended.connect(self._on_session_ended)
        self.session_timer.start()

    def _on_timer_reminder(self, message: str):
        self.timer_sub_label.setText(f"⏰ {message}")

    def _on_session_ended(self):
        """세션 종료 → 조명 OFF + EXPORT_READY 화면으로 전환"""
        # Home Assistant: 조명 + 카메라 전원 OFF (별도 스레드)
        if self.ha and self.ha.is_available:
            threading.Thread(target=self.ha.turn_off_studio, daemon=True).start()

        self.switch_state(STATE_EXPORT_READY)

    def _on_export_clicked(self):
        """내보내기 버튼 → Lightroom 이전 설정 내보내기 (Ctrl+A → Ctrl+Alt+Shift+E)"""
        if self.current_worker is not None and self.current_worker.isRunning():
            return

        self.export_status_label.setText("내보내기 진행 중...")
        self.export_button.setEnabled(False)

        self._run_action_in_thread(self.actions.action_export_all, "내보내기")

    def _run_action_in_thread(self, func, action_name):
        """액션을 스레드에서 실행"""
        if self.current_worker is not None and self.current_worker.isRunning():
            return

        if hasattr(self, 'idle_status'):
            self.idle_status.update_status(f"'{action_name}' 작업 중...")

        self.current_worker = ActionWorker(func, action_name)
        self.current_worker.finished.connect(self._on_action_finished)
        self.current_worker.start()

    def _on_action_finished(self, success: bool, message: str):
        """액션 완료 핸들러"""
        if not success:
            QMessageBox.warning(self, "오류", message)

        # 내보내기 완료 시 상태 업데이트
        if self._current_state == STATE_EXPORT_READY and hasattr(self, 'export_status_label'):
            if success:
                self.export_status_label.setText("내보내기가 완료되었습니다")
                self.export_status_label.setStyleSheet("""
                    color: rgba(48, 209, 88, 0.7);
                    font-size: 13px;
                    padding-bottom: 40px;
                """)
            else:
                self.export_status_label.setText("내보내기 실패 - 다시 시도해주세요")
                self.export_button.setEnabled(True)

        self.current_worker = None
        self.activateWindow()

    def closeEvent(self, event):
        # 키오스크 모드: 종료 차단
        event.ignore()


def main():
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)

    config = ConfigManager(CONFIG_FILE)

    log_path = config.get('log_path', 'logs/macro_log.txt')
    log_manager = LogManager(log_path)
    log_manager.log_action("APP_START", version=APP_VERSION)

    win_controller = WindowsController(config, log_manager)
    actions = MacroActions(config, log_manager, win_controller)
    calendar = CalendarSync(log_manager)
    ha_controller = HomeAssistantController(config, log_manager)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow(config, actions, calendar, ha_controller)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
