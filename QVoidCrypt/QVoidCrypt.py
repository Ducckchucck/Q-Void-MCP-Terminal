import os
import base64
import time
from datetime import datetime
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac as crypto_hmac
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from scapy.all import Ether, IP, TCP, sendp, sniff

qlog_path = ".qvoidlog"

def qvoid_pulse_signature(data, key):
    pulse = crypto_hmac.HMAC(key, hashes.SHA512(), backend=default_backend())
    pulse.update(data + key[:16])
    return pulse.finalize()[:16]

class MiniController:
    def __init__(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

    def get_public_key(self):
        return self.public_key

    def receive_encrypted_session_key(self, encrypted_session_key):
        return self.private_key.decrypt(
            encrypted_session_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(),
                         label=None)
        )

    def verify_and_decrypt(self, encrypted_data, iv, tag, pulse_signature, session_key):
        h = crypto_hmac.HMAC(session_key, hashes.SHA256(), backend=default_backend())
        h.update(encrypted_data)
        try:
            h.verify(tag)
        except Exception:
            with open(qlog_path, "a") as log:
                log.write(f"[!] Tampering detected at {datetime.now()}\n")
            raise ValueError("[❌] Tampering detected!")
        cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv))
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
        return decrypted

class Controller:
    def __init__(self, receiver_public_key):
        self.receiver_public_key = receiver_public_key

    def generate_session_key(self):
        return os.urandom(32)

    def encrypt_session_key(self, session_key):
        return self.receiver_public_key.encrypt(
            session_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(),
                         label=None)
        )

    def encrypt_and_tag(self, message, session_key):
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv))
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(message.encode()) + encryptor.finalize()
        h = crypto_hmac.HMAC(session_key, hashes.SHA256(), backend=default_backend())
        h.update(encrypted)
        tag = h.finalize()
        pulse = qvoid_pulse_signature(encrypted, session_key)
        return encrypted, iv, tag, pulse

    def save_blob(self, encrypted, path):
        with open(path, "wb") as f:
            f.write(encrypted)

    def load_blob(self, path):
        with open(path, "rb") as f:
            return f.read()

def simulate_packet():
    pkt = Ether()/IP(dst="192.168.1.1")/TCP(dport=80)
    sendp(pkt, verbose=0)

def packet_feed():
    sniff(filter="tcp", prn=lambda x: open(qlog_path, "a").write(f"[packet] {x.summary()}\n"), count=5)

if __name__ == "__main__":
    mini = MiniController()
    controller = Controller(mini.get_public_key())
    session_key = controller.generate_session_key()
    encrypted_session_key = controller.encrypt_session_key(session_key)
    decrypted_session_key = mini.receive_encrypted_session_key(encrypted_session_key)

    while True:
        msg = input("Enter command (or 'exit'): ")
        if msg.lower() == 'exit':
            break
        start = time.time()
        encrypted_data, iv, tag, pulse = controller.encrypt_and_tag(msg, session_key)
        decrypted_message = mini.verify_and_decrypt(encrypted_data, iv, tag, pulse, decrypted_session_key)
        end = time.time()

        print("\n--- QVoidCrypt Layer ---")
        print(f"Original        : {msg}")
        print(f"Encrypted Blob  : {base64.b64encode(encrypted_data).decode()[:60]}...")
        try:
            decoded_message = decrypted_message.decode('utf-8')
            print(f"Decrypted       : {decoded_message}")
        except Exception as e:
            print(f"❌ Failed to decode decrypted bytes: {e}")
            print(f"Raw bytes       : {decrypted_message}")
        print(f"QuantumPulse    : {base64.b64encode(pulse).decode()[:24]}...")
        print(f"⏱ Time Taken    : {round(end - start, 4)} seconds\n")

        with open(qlog_path, "a") as log:
            log.write(f"[log] Command '{msg}' processed in {round(end - start, 4)}s at {datetime.now()}\n")
