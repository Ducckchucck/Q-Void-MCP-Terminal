import os
import warnings
warnings.filterwarnings("ignore")

from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

from qvoid_fusion.qcrypt.qvoidcrypt_qkd import simulate_qkd_keypair


class QVoidCrypt:
    def __init__(self):
        
        qkd_session = simulate_qkd_keypair()
        print(f"🔑 [QKD] Using Quantum Session Key: {qkd_session['key']}")

        
        raw_key = qkd_session["key"]
        if raw_key != "0000":
            base_key = bytes.fromhex(raw_key)
            self.session_key = (base_key * (32 // len(base_key) + 1))[:32]  # Pad
        else:
            self.session_key = os.urandom(32)

        
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

        
        self.iv = os.urandom(16)

    def encrypt(self, plaintext: str):
        cipher = Cipher(algorithms.AES(self.session_key), modes.CFB(self.iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        return ciphertext

    def decrypt(self, ciphertext: bytes):
        cipher = Cipher(algorithms.AES(self.session_key), modes.CFB(self.iv))
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode(errors="replace")

    def tag(self, data: bytes):
        h = hmac.HMAC(self.session_key, hashes.SHA256())
        h.update(data)
        return h.finalize()

    def encrypt_and_tag(self, plaintext: str):
        ciphertext = self.encrypt(plaintext)
        tag = self.tag(ciphertext)
        return ciphertext, tag

    def verify_and_decrypt(self, ciphertext: bytes, tag: bytes):
        h = hmac.HMAC(self.session_key, hashes.SHA256())
        h.update(ciphertext)
        h.verify(tag)
        return self.decrypt(ciphertext)
