"""
Password utilities – hashing & verification.

Uses SHA-256 for deterministic hashing so the stored hash can be
compared directly in SQL queries / stored procedures.

The DB column [Password] is varchar(50), so the 64-char hex digest
is truncated to 50 chars to match the column width.

On registration / update: hash(plain)[:50] → store in DB.
On login: hash(plain)[:50] → compare against stored value.
"""

import hashlib

# DB column Password is varchar(50)
_MAX_HASH_LEN = 50


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using SHA-256, truncated to 50 chars
    to fit the DB column [Password] varchar(50).
    """
    full_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return full_hash[:_MAX_HASH_LEN]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored hash.
    """
    return hash_password(plain_password) == hashed_password
