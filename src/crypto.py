import os
import base64
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def derive_key_from_password(password: str, salt: bytes = None, iterations: int = 200_000) -> (bytes, bytes):
    """Derive a 256‑bit AES key from the password.
    Returns (key, salt). If salt is None a new random 16‑byte salt is generated.
    """
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    key = kdf.derive(password.encode())
    return key, salt

def store_password_meta(password: str) -> dict:
    """Create the JSON‑serialisable meta for storing in app_meta.json.
    The verifier is SHA‑256 of the derived key.
    """
    key, salt = derive_key_from_password(password)
    digest = hashes.Hash(hashes.SHA256())
    digest.update(key)
    verifier = digest.finalize()
    return {
        "salt": base64.b64encode(salt).decode(),
        "verifier": base64.b64encode(verifier).decode(),
    }

def verify_password(password: str, meta: dict) -> bytes:
    """Return the derived key if password matches the stored meta, else None."""
    try:
        salt = base64.b64decode(meta["salt"])
        stored_verifier = base64.b64decode(meta["verifier"])
    except Exception:
        return None
    key, _ = derive_key_from_password(password, salt)
    digest = hashes.Hash(hashes.SHA256())
    digest.update(key)
    if digest.finalize() == stored_verifier:
        return key
    return None

# Encryption helpers for individual fields

def encrypt_field(plaintext: str, key: bytes) -> str:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    payload = {
        "nonce": base64.b64encode(nonce).decode(),
        "ct": base64.b64encode(ct).decode(),
    }
    return json.dumps(payload)

def decrypt_field(payload_json: str, key: bytes) -> str:
    payload = json.loads(payload_json)
    nonce = base64.b64decode(payload["nonce"])
    ct_bytes = base64.b64decode(payload["ct"])
    aesgcm = AESGCM(key)
    data = aesgcm.decrypt(nonce, ct_bytes, None)
    return data.decode()
