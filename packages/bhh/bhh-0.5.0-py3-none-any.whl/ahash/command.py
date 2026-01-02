import os
import hmac

SBOX = [(i*29 + 37) % 256 for i in range(256)]
STATE_BITS = 256

def _core_hash(password: str, salt: bytes, rounds: int = 1000) -> str:
    combined = int(''.join(format(ord(c), '08b') for c in password), 2) ^ int.from_bytes(salt, 'big')

    for _ in range(rounds):
        rotated = ((combined << 13) | (combined >> (STATE_BITS - 13))) & ((1 << STATE_BITS) - 1)
        state_bytes = rotated.to_bytes(STATE_BITS // 8, 'big')
        substituted = bytes(SBOX[b] for b in state_bytes)
        mixed = int.from_bytes(substituted, 'big') * 1_000_003
        combined = mixed % (2**STATE_BITS)

    hash_hex = combined.to_bytes(STATE_BITS // 8, 'big').hex()
    return f"@bhh@hash@v0.5.0@{hash_hex}:{salt.hex()}@"


def hash_password(password: str, rounds: int = 1000, salt_len: int = 16) -> str:
    salt = os.urandom(salt_len)
    return _core_hash(password, salt, rounds)


def hash_password_with_salt(password: str, salt: bytes, rounds: int = 1000) -> str:
    return _core_hash(password, salt, rounds)


def verify_password(password: str, stored: str, rounds: int = 1000) -> bool:
    hash_hex, salt_hex = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    recomputed = _core_hash(password, salt, rounds)
    return hmac.compare_digest(recomputed, stored)