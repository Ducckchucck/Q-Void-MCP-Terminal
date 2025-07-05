import os
import base64
import hmac
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hmac as crypto_hmac
from cryptography.hazmat.backends import default_backend



def qvoid_obfuscate(data, key):
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])



class MiniController:
    def __init__(self):
        print("[Alert!] Mini-Alpha RSA key pair generated.")
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

    def get_public_key(self):
        return self.public_key

    def receive_encrypted_session_key(self, encrypted_session_key):
        print("[Alert!] Mini-Alpha received encrypted session key.")
        session_key = self.private_key.decrypt(
            encrypted_session_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(),
                         label=None)
        )
        return session_key

    def verify_and_decrypt(self, encrypted_data, iv, tag, session_key):
        print("[Alert!] Mini-Alpha verifying integrity and decrypting message...")

        
        h = crypto_hmac.HMAC(session_key, hashes.SHA256(), backend=default_backend())
        h.update(encrypted_data)
        try:
            h.verify(tag)
        except Exception:
            with open("tamper_log.txt", "a") as log:
                log.write(f"[!] Tampered message detected at {datetime.now()}\n")
            raise ValueError("[❌] Tampering detected! Check tamper_log.txt")

        
        deobfuscated = qvoid_obfuscate(encrypted_data, session_key)
        cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv))
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(deobfuscated) + decryptor.finalize()

        return decrypted



class Controller:
    def __init__(self, receiver_public_key):
        self.receiver_public_key = receiver_public_key

    def generate_session_key(self):
        return os.urandom(32)  # AES-256

    def encrypt_session_key(self, session_key):
        print("[Alert!] Session key encrypted with receiver's public key.")
        encrypted = self.receiver_public_key.encrypt(
            session_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(),
                         label=None)
        )
        return encrypted

    def encrypt_message(self, message, session_key):
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(message.encode()) + encryptor.finalize()

        
        obfuscated = qvoid_obfuscate(ciphertext, session_key)

        
        h = crypto_hmac.HMAC(session_key, hashes.SHA256(), backend=default_backend())
        h.update(obfuscated)
        tag = h.finalize()

        print("[Alert!] Message encrypted and QVoid layer applied.")
        return obfuscated, iv, tag



if __name__ == "__main__":
    print("\n🛰 Initializing QVoidCrypt Layer Simulation...\n")

    
    mini = MiniController()
    mini_public_key = mini.get_public_key()

    
    controller = Controller(mini_public_key)
    session_key = controller.generate_session_key()
    encrypted_session_key = controller.encrypt_session_key(session_key)

    
    decrypted_session_key = mini.receive_encrypted_session_key(encrypted_session_key)

    
    command = "EMERGENCY SHUTDOWN SEQUENCE INITIATE!"
    encrypted_data, iv, tag = controller.encrypt_message(command, session_key)

    
    decrypted_message = mini.verify_and_decrypt(encrypted_data, iv, tag, decrypted_session_key)

    
    print("\n📦 QVoidCrypt Layer Summary:")
    print("----------------------------------------")
    print(f"Original Command       : {command}")
    print(f"Encrypted (base64)     : {base64.b64encode(encrypted_data).decode()[:60]}...")
    print(f"Decrypted Command      : {decrypted_message.decode()}")
    print("----------------------------------------")
