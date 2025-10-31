# main.py

import asyncio
import sys
from sia import SIA
from dotenv import load_dotenv
from modules.wake_word_listener import is_wake_phrase, play_beep
from modules.real_stt import recognize_speech

# Wake trigger flag
woke_up = asyncio.Event()

def handle_exception(exc_type, exc_value, exc_traceback):
    if exc_type is KeyboardInterrupt:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print(f"⚠️ Unhandled exception: {exc_value}", file=sys.stderr)

sys.excepthook = handle_exception

def wake_callback():
    print("🎉 Wake phrase confirmed! Launching SIA now...")
    woke_up.set()

def listen_for_wake_word():
    print("👂 SIA is asleep. Say a wake word to activate...")
    while True:
        recognized = recognize_speech()
        if recognized:
            text = recognized.lower()
            print(f"🗣️ Heard: {text}")
            if is_wake_phrase(text):
                print("🔊 Wake word detected!")
                play_beep()
                print("🎉 Wake phrase confirmed! Launching SIA now...")
                break

def main():
    load_dotenv()
    while True:
        listen_for_wake_word()
        print("🧠 SIA is awake! Initializing...\n")
        sia = SIA()
        try:
            import asyncio
            asyncio.run(sia.run())
        except Exception as e:
            print(f"❌ Runtime crash: {e}")
        print("😴 SIA returned to sleep. Waiting for next wake word...\n")

if __name__ == "__main__":
    main()
