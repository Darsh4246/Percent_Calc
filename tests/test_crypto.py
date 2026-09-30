import pytest
from src.crypto import (
    derive_key_from_password, 
    store_password_meta, 
    verify_password, 
    encrypt_field, 
    decrypt_field
)

def test_key_derivation_deterministic():
    password = "test_password"
    salt = b"fixed_salt_16bytes"
    key1, _ = derive_key_from_password(password, salt=salt)
    key2, _ = derive_key_from_password(password, salt=salt)
    assert key1 == key2

def test_encryption_decryption():
    key, _ = derive_key_from_password("secret")
    plaintext = "Hello World 123!"
    encrypted = encrypt_field(plaintext, key)
    decrypted = decrypt_field(encrypted, key)
    assert plaintext == decrypted

def test_password_verification():
    password = "my_secure_password"
    meta = store_password_meta(password)
    key = verify_password(password, meta)
    assert key is not None
    
    # Test wrong password
    wrong_key = verify_password("wrong_password", meta)
    assert wrong_key is None
