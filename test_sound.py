import os
import time

print("=== 사운드 재생 테스트 (pygame) ===\n")

# 현재 디렉토리 확인
print(f"Current dir: {os.getcwd()}")

# Sounds 폴더 확인
sounds_dir = os.path.join(os.getcwd(), 'Sounds')
sound_file = os.path.join(sounds_dir, 'Start_shoot.mp3')
print(f"Sound file: {sound_file}")
print(f"File exists: {os.path.exists(sound_file)}")

if os.path.exists(sound_file):
    print("\n사운드 재생 시도 (pygame 사용)...")
    
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
        
        print("재생 중... 5초 대기")
        time.sleep(5)
        
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        
        print("\n사운드가 들렸으면 성공!")
    except Exception as e:
        print(f"오류 발생: {e}")
else:
    print("사운드 파일을 찾을 수 없습니다!")

input("\n아무 키나 누르면 종료...")
