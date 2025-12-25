import base64

from Crypto.Cipher import AES
from Crypto.Hash import SHA512
from Crypto.Protocol.KDF import PBKDF2

KEY_HASH_ITERATION = 100000
KEY_HASH_SALT = b""
KEY_HASH_SIZE = 64
ENCRYPTED_KEY_START = 32
ENCRYPTED_MSG_SIGNATURE_END = -32


def _decrypt_key(key: str) -> bytes:
    hashed_key = PBKDF2(  # type: ignore
        key,
        KEY_HASH_SALT,
        KEY_HASH_SIZE,
        count=KEY_HASH_ITERATION,
        hmac_hash_module=SHA512,
    )
    return hashed_key[ENCRYPTED_KEY_START:]


def _unpad(s: bytes) -> bytes:
    return s[: -ord(s[len(s) - 1 :])]


def decrypt(raw: str, secret_key: str) -> str:
    """
    Decryption function that takes
     * a raw encrypted string
     * the associated secret key required to decode the message
     and returns the decrypted message.
    """
    enc = base64.b64decode(raw)
    key = _decrypt_key(secret_key)
    iv = enc[: AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    enc_message = enc[AES.block_size : ENCRYPTED_MSG_SIGNATURE_END]
    return _unpad(cipher.decrypt(enc_message)).decode("utf-8")
