

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

class QCrypt:
    def __init__(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

    def get_public_key(self):
        return self.public_key

    def encrypt_message(self, message: str):
        session_key = os.urandom(32)  # AES-256
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv))
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(message.encode()) + encryptor.finalize()

        encrypted_session_key = self.public_key.encrypt(
            session_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(), label=None)
        )

        return (encrypted_data, iv)  
