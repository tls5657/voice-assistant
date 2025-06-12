# main_realtime_quicksilence.py

import io
import time
import webbrowser
import threading
import subprocess
import platform
import sys

import speech_recognition as sr
import whisper
import soundfile as sf    # PySoundFile (soundfile) for WAV → NumPy
import numpy as np        # NumPy
import librosa            # Resampling

from intent_classifier import classify_intent

# -------------------------------
# Windows 전용 볼륨 조절 (pycaw)
# -------------------------------
if platform.system() == "Windows":
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
else:
    print("▶ 이 스크립트는 Windows 전용으로 작성되었습니다.")
    sys.exit(1)


# ========================================
# 1) Whisper ASR 모델 로드 (글로벌)
# ========================================
ASR_MODEL_SIZE = "small"  # "tiny", "base", "small" 중 택 1. 한국어용은 "small" 권장.
print("▶ Whisper ASR 모델 로드 중... (최초 로드 시 체크포인트 다운로드 필요)")
asr_model = whisper.load_model(ASR_MODEL_SIZE)
print(f"▶ Whisper '{ASR_MODEL_SIZE}' 모델 로드 완료.")

# SpeechRecognition Recognizer 객체 (백그라운드 리스너용)
recognizer = sr.Recognizer()
# 음성 끝맺음 후 1초간 침묵 감지하면 바로 발화 완료로 간주
recognizer.pause_threshold = 1.0
# 필요하다면 잡음에 덜 민감하도록 energy_threshold도 조정 가능
# recognizer.energy_threshold = 300


# ========================================
# 2) Windows 볼륨 조절 함수 (pycaw)
# ========================================
def adjust_volume(delta: float):
    """
    Windows 시스템 마스터 볼륨을 delta만큼 조절 (예: +0.1, -0.1).
    """
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))

    current = volume.GetMasterVolumeLevelScalar()  # 0.0 ~ 1.0
    new = min(max(current + delta, 0.0), 1.0)
    volume.SetMasterVolumeLevelScalar(new, None)

# ========================================
# 4) 명령 처리 함수
# ========================================
def handle_intent(text: str) -> bool:
    """
    Whisper가 인식한 텍스트(text)를 intent_classifier에 넘겨서 intent/parameter를 얻고,
    해당 동작을 즉시 실행. 'EXIT'가 들어오면 False 반환해서 프로그램 종료.
    """
    intent_info = classify_intent(text)
    intent = intent_info["intent"]
    param = intent_info["parameter"]

    # 1) 종료
    if intent == "EXIT":
        print("▶ 종료 명령을 감지했습니다. 프로그램을 종료합니다.")
        return False

    # 2) 볼륨 높이기
    if intent == "VOLUME_UP":
        print("▶ 볼륨을 10% 높입니다.")
        adjust_volume(+0.1)
        return True

    # 3) 볼륨 낮추기
    if intent == "VOLUME_DOWN":
        print("▶ 볼륨을 10% 낮춥니다.")
        adjust_volume(-0.1)
        return True

    # 4) 계산기 실행
    if intent == "OPEN_CALCULATOR":
        print("▶ 계산기를 엽니다...")
        subprocess.Popen(["calc.exe"])
        return True

    # 5) 메모장 실행
    if intent == "OPEN_NOTEPAD":
        print("▶ 메모장을 엽니다...")
        subprocess.Popen(["notepad.exe"])
        return True

    # 6) 유튜브 검색
    if intent == "SEARCH_YOUTUBE":
        import urllib.parse
        query = urllib.parse.unquote(param)
        print(f"▶ 유튜브 검색: \"{query}\" → 브라우저 실행")
        webbrowser.open(f"https://www.youtube.com/results?search_query={param}")
        return True

    # 7) 구글 검색
    if intent == "SEARCH_GOOGLE":
        import urllib.parse
        query = urllib.parse.unquote(param)
        print(f"▶ 구글 검색: \"{query}\" → 브라우저 실행")
        webbrowser.open(f"https://www.google.com/search?q={param}")
        return True

    # 8) 네이버 검색
    if intent == "SEARCH_NAVER":
        import urllib.parse
        query = urllib.parse.unquote(param)
        print(f"▶ 네이버 검색: \"{query}\" → 브라우저 실행")
        webbrowser.open(f"https://search.naver.com/search.naver?query={param}")
        return True

    # 알 수 없는 명령
    print("▶ <알 수 없는 명령> 이해하지 못했습니다. 다시 시도해 주세요.")
    return True


# ========================================
# 5) 백그라운드 콜백 함수
# ========================================
stop_listening = None  # 리스너 중지 함수가 여기에 담김

def callback(recognizer, audio_data):
    """
    백그라운드 리스너가 오디오를 받으면 호출되는 콜백.
    audio_data는 sr.AudioData 객체.
    """
    try:
        # 1) WAV 바이트 → NumPy(float64)
        wav_bytes = audio_data.get_wav_data()
        audio_np, sr_ = sf.read(io.BytesIO(wav_bytes))

        # 2) 스테레오→모노
        if audio_np.ndim == 2:
            audio_np = audio_np.mean(axis=1)

        # 3) 44.1kHz (또는 기타 sr_) → 16kHz 리샘플링
        if sr_ != 16000:
            audio_np = librosa.resample(audio_np, orig_sr=sr_, target_sr=16000)

        # 4) float64 → float32 캐스팅
        if audio_np.dtype != np.float32:
            audio_np = audio_np.astype(np.float32)

        # 5) Whisper 인식
        result = asr_model.transcribe(audio_np, language="ko")
        text = result["text"].strip()

        if text:
            print(f"\n▶ (인식된 텍스트) \"{text}\"")
            should_continue = handle_intent(text)
            if not should_continue:
                # 'EXIT'가 인식되면 백그라운드 리스너 중지
                if stop_listening is not None:
                    stop_listening(wait_for_stop=False)
    except Exception as e:
        print("▶ 백그라운드 인식 중 오류 발생:", e)


# ========================================
# 6) 메인: 백그라운드 리스닝 시작 후 대기
# ========================================
def main():
    print("============================================")
    print("   실시간 음성 비서(백그라운드 리스너)   ")
    print("============================================")
    print("  • 발화 후 1초(=pause_threshold) 동안 침묵이 감지되면 즉시 인식합니다.")
    print("  • 예: '계산기 열어줘'라고 말하고 1초간 아무 말 없으면 바로 계산기 실행")
    print("  • '종료', '그만', '끝내' 등을 말하면 프로그램이 종료됩니다.")
    print("  • '볼륨 높여줘', '볼륨 낮춰줘' → 바로 볼륨 제어")
    print("  • '계산기 열어줘' → 바로 계산기 실행")
    print("  • '메모장 열어줘' → 바로 메모장 실행")
    print("  • '유튜브에서 ○○ 검색해줘' → 유튜브 검색")
    print("  • '○○ 검색해줘' → 바로 구글 검색")
    print("  • '네이버에서 ○○ 검색해줘' → 네이버 검색")
    print("--------------------------------------------\n")

    mic = sr.Microphone()
    global stop_listening

    # 백그라운드 리스너 시작: pause_threshold=1.0이 적용되어,
    # 발화 후 1초간 침묵 감지 시 callback 호출
    stop_listening = recognizer.listen_in_background(mic, callback)

    try:
        # 메인 스레드는 종료 직전까지 대기만 함
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        # Ctrl+C로 종료 시 백그라운드도 중지
        if stop_listening is not None:
            stop_listening(wait_for_stop=False)
        print("\n▶ 프로그램을 종료합니다.")


if __name__ == "__main__":
    main()
