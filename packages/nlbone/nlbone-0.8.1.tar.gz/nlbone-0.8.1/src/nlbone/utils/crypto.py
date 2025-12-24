import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet

from nlbone.config.settings import get_settings


def _get_fernet_key() -> bytes:
    settings = get_settings()
    fernet_key = settings.FERNET_KEY

    if not fernet_key or not fernet_key.strip():
        raise Exception("❌ FERNET_KEY is required in .env")

    digest = hashlib.sha256(fernet_key.encode()).digest()

    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def get_fernet():
    return Fernet(_get_fernet_key())


def encrypt_text(plaintext: str) -> str:
    return get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_text(token: str) -> str:
    return get_fernet().decrypt(token.encode()).decode()
