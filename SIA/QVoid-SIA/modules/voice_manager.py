# modules/voice_manager.py
from gtts import gTTS
import pygame
import pyttsx3
import os
import threading
import time
import uuid

class TTSManager:
    def __init__(self):
        self.engine_name = 'gtts'  # Default to online gTTS
        self.pyttsx3_engine = pyttsx3.init()
        self.setup_pyttsx3()
        pygame.mixer.init()
        self.play_thread = None
        self._stop_flag = threading.Event()

    def setup_pyttsx3(self):
        self.pyttsx3_engine.setProperty('rate', 150)
        self.pyttsx3_engine.setProperty('volume', 0.9)
        voices = self.pyttsx3_engine.getProperty('voices')
        if len(voices) > 1:
            try:
                self.pyttsx3_engine.setProperty('voice', voices[1].id)
            except:
                pass

    def speak(self, text):
        self._stop_flag.clear()
        if self.engine_name == 'gtts':
            self._speak_gtts(text)
        else:
            self._speak_pyttsx3(text)

    def _speak_gtts(self, text):
        def run_tts():
            try:
                filename = f"sia_output_{uuid.uuid4().hex[:8]}.mp3"
                tts = gTTS(text=text)
                tts.save(filename)
                for _ in range(10):
                    if os.path.exists(filename):
                        try:
                            with open(filename, 'rb'):
                                break
                        except PermissionError:
                            time.sleep(0.05)
                else:
                    print(f"❌ Timeout waiting for file: {filename}")
                    return
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    if self._stop_flag.is_set():
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.1)
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception as e:
                print(f"⚠️ TTS error: {e}")
        self.play_thread = threading.Thread(target=run_tts)
        self.play_thread.start()

    def _speak_pyttsx3(self, text):
        def run_tts():
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()
        self.play_thread = threading.Thread(target=run_tts)
        self.play_thread.start()

    def stop(self):
        self._stop_flag.set()
        if self.engine_name == 'gtts':
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                print("🛑 Speech interrupted.")
            else:
                print("⚠️ No active speech to stop.")
        else:
            self.pyttsx3_engine.stop()
            print("🛑 Speech interrupted.")

    def switch_engine(self, engine_name):
        if engine_name.lower() in ['gtts', 'online', 'natural']:
            self.engine_name = 'gtts'
            print("🔊 Switched to online (gTTS) voice.")
        elif engine_name.lower() in ['pyttsx3', 'offline', 'robotic']:
            self.engine_name = 'pyttsx3'
            print("🔊 Switched to offline (pyttsx3) voice.")
        else:
            print(f"⚠️ Unknown TTS engine: {engine_name}")

tts_manager = TTSManager()
