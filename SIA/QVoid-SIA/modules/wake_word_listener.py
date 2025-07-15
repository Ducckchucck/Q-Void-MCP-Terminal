import threading
import time
import sys
from modules.real_stt import recognize_speech
from rapidfuzz import fuzz

# For sound confirmation
try:
    import winsound
    def play_beep():
        winsound.Beep(1000, 200)  # 1000 Hz, 200 ms
except ImportError:
    def play_beep():
        print("[BEEP]")  # Fallback: print if not on Windows

WAKE_WORDS = ["hey sia", "okay sia", "wake up sia", "hello sia"]

# Use a threading.Event to signal the thread to stop
stop_event = threading.Event()

def is_wake_phrase(text):
    for wake in WAKE_WORDS:
        score = fuzz.partial_ratio(wake, text)
        if score >= 90:  # Increased threshold for accuracy
            return True
    return False

def listen_for_wake_word(wake_callback):
    def _run():
        print("👂 SIA is asleep. Say a wake word to activate...")
        stop_event.clear()
        while not stop_event.is_set():
            recognized = recognize_speech()
            if recognized:
                text = recognized.lower()
                print(f"🗣️ Heard: {text}")
                if is_wake_phrase(text):
                    print("🔊 Wake word detected!")
                    play_beep()
                    stop_event.set()  # Signal to stop listening
                    wake_callback()
                    break
    # Before starting a new thread, ensure any previous one is stopped
    stop_event.set()
    time.sleep(0.1)  # Give time for any previous thread to exit
    thread = threading.Thread(target=_run, daemon=True)
    thread.start() 