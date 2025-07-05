from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64


class MiniController:
    def __init__(self, name="MiniController"):
        self.name = name
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        print(f"[🔐] {self.name} RSA key pair generated.")

    def get_public_key(self):
        return self.public_key

    def receive_encrypted_session_key(self, encrypted_key):
        print(f"[📥] {self.name} received encrypted session key.")
        return self.private_key.decrypt(
            encrypted_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )

    def verify_and_decrypt(self, encrypted_data, iv, hmac_tag, session_key):
        print(f"[🔓] {self.name} verifying integrity and decrypting message...")
        
        h = hmac.HMAC(session_key, hashes.SHA256())
        h.update(encrypted_data)
        try:
            h.verify(hmac_tag)
            print(f"[✅] Message integrity verified.")
        except Exception as e:
            print(f"[❌] Message integrity verification failed! Possible tampering.")
            raise

        
        cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv))
        decryptor = cipher.decryptor()
        return decryptor.update(encrypted_data) + decryptor.finalize()


class Controller:
    def __init__(self, receiver_public_key):
        self.receiver_public_key = receiver_public_key

    def generate_session_key(self):
        return os.urandom(32)  

    def encrypt_session_key(self, session_key):
        encrypted = self.receiver_public_key.encrypt(
            session_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        print(f"[📤] Session key encrypted with receiver's public key.")
        return encrypted

    def encrypt_and_sign(self, message, session_key):
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv))
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(message.encode()) + encryptor.finalize()

        
        h = hmac.HMAC(session_key, hashes.SHA256())
        h.update(encrypted)
        tag = h.finalize()

        print(f"[🔐] Message encrypted and HMAC tag generated.")
        return encrypted, iv, tag



print("\n Initializing QCrypt Layer Simulation...\n")


mini = MiniController("Mini-Alpha")
mini_pub = mini.get_public_key()


controller = Controller(mini_pub)
session_key = controller.generate_session_key()
encrypted_session_key = controller.encrypt_session_key(session_key)


decrypted_session_key = mini.receive_encrypted_session_key(encrypted_session_key)


command = "STOP MOTOR IMMEDIATELY"
encrypted_msg, iv, hmac_tag = controller.encrypt_and_sign(command, session_key)


decrypted_msg = mini.verify_and_decrypt(encrypted_msg, iv, hmac_tag, decrypted_session_key)


print("\n📦 QCrypt Layer Summary:")
print("-" * 40)
print(f"Original Command       : {command}")
print(f"Encrypted (base64)     : {base64.b64encode(encrypted_msg).decode()}")
print(f"Decrypted Command      : {decrypted_msg.decode()}")
print("-" * 40)
