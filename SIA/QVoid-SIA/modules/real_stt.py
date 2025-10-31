# modules/real_stt.py

import speech_recognition as sr

def recognize_speech():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("🎙️ Listening...")
        # Increase duration for better ambient noise calibration
        recognizer.adjust_for_ambient_noise(source, duration=1.5)  # type: ignore  # 1.5 seconds
        try:
            # Increase phrase_time_limit for longer utterances
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
        except sr.WaitTimeoutError:
            print("⏱️ Timeout: No speech detected.")
            return ""

    try:
        text = recognizer.recognize_google(audio)  # type: ignore
        print(f"🧠 Transcribed: {text}")
        return text
    except sr.UnknownValueError:
        print("❓ Could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"🚨 API Error: {e}")
        return ""
