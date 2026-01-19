from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


_PBKDF2_NAME = "pbkdf2_sha256"
_PBKDF2_ITERATIONS = 260_000
_SALT_BYTES = 16
_DKLEN = 32


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256.

    Stored format: pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>
    """
    if not isinstance(password, str) or password == "":
        raise ValueError("password required")
    salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS, dklen=_DKLEN)
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    dk_b64 = base64.urlsafe_b64encode(dk).decode("ascii").rstrip("=")
    return f"{_PBKDF2_NAME}${_PBKDF2_ITERATIONS}${salt_b64}${dk_b64}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iter_s, salt_b64, dk_b64 = stored.split("$", 3)
        if algo != _PBKDF2_NAME:
            return False
        iterations = int(iter_s)
        salt = base64.urlsafe_b64decode(_pad_b64(salt_b64))
        expected = base64.urlsafe_b64decode(_pad_b64(dk_b64))
    except Exception:
        return False

    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=len(expected))
    return hmac.compare_digest(dk, expected)


def _pad_b64(s: str) -> str:
    # urlsafe_b64decode requires proper padding.
    return s + "=" * (-len(s) % 4)

