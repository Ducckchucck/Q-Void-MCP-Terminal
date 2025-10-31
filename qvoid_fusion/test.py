import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from qvoid_fusion.qcrypt.qvoidcrypt_core import QVoidCrypt

qcrypt = QVoidCrypt()

plaintext = "OR 0x61646D696E=0x61646D696E --"
ciphertext, tag = qcrypt.encrypt_and_tag(plaintext)

print("\n🔒 Encrypted Blob:", ciphertext.hex())
print("🔖 HMAC Tag:", tag.hex())

try:
    decrypted = qcrypt.verify_and_decrypt(ciphertext, tag)
    print("\n✅ Decryption Verified! Output:")
    print(decrypted)
except Exception as e:
    print("\n❌ Verification Failed:", e)
