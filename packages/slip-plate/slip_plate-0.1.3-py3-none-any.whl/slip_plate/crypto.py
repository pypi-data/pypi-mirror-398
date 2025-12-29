import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_dek(bit_length: int = 256) -> bytes:
    return AESGCM.generate_key(bit_length=bit_length)


def encrypt_with_dek(dek: bytes, plaintext: bytes, associated_data: bytes = b"") -> tuple[bytes, bytes, bytes]:
    aesgcm = AESGCM(dek)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    return nonce, ciphertext, associated_data


def decrypt_with_dek(dek: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes = b"") -> bytes:
    aesgcm = AESGCM(dek)
    return aesgcm.decrypt(nonce, ciphertext, associated_data)
