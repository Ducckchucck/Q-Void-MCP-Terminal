from modules.wake_word_listener import listen_for_wake_word
import time

def on_wake():
    print("🎉 SIA would wake now!")

listen_for_wake_word(on_wake)

while True:
    time.sleep(1)
