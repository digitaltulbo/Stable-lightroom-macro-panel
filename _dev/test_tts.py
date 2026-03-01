# -*- coding: utf-8 -*-
import subprocess
import os
import tempfile
import uuid
import threading
import time

def speak(text: str):
    """Edge TTS 테스트"""
    def _speak_thread():
        try:
            # 임시 파일 경로 생성
            temp_dir = tempfile.gettempdir()
            audio_file = os.path.join(temp_dir, f"tts_{uuid.uuid4().hex[:8]}.mp3")
            
            print(f"생성할 파일: {audio_file}")
            
            # Edge TTS로 음성 파일 생성
            result = subprocess.run(
                [
                    'edge-tts',
                    '--voice', 'ko-KR-SunHiNeural',
                    '--pitch', '-10Hz',
                    '--rate', '-10%',
                    '--text', text,
                    '--write-media', audio_file
                ],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            print(f"edge-tts 결과: {result.returncode}")
            if result.stderr:
                print(f"stderr: {result.stderr.decode()}")
            
            if result.returncode == 0 and os.path.exists(audio_file):
                print(f"파일 생성 성공: {os.path.getsize(audio_file)} bytes")
                
                # Windows Media Player COM 객체로 재생
                ps_script = f'''
$wmp = New-Object -ComObject WMPlayer.OCX
$wmp.URL = "{audio_file}"
$wmp.controls.play()
Start-Sleep -Seconds 1
while ($wmp.playState -eq 3) {{ Start-Sleep -Milliseconds 200 }}
$wmp.close()
Remove-Item "{audio_file}" -Force -ErrorAction SilentlyContinue
'''
                print("재생 시작...")
                subprocess.run(
                    ['powershell', '-Command', ps_script],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                print("재생 완료")
            else:
                print("파일 생성 실패")
        except Exception as e:
            print(f"TTS Error: {e}")
    
    # 별도 스레드에서 실행
    thread = threading.Thread(target=_speak_thread, daemon=False)
    thread.start()
    thread.join()  # 테스트용으로 대기

if __name__ == "__main__":
    print("TTS 테스트 시작...")
    speak("안녕하세요, 촬영을 시작합니다.")
    print("테스트 종료")
