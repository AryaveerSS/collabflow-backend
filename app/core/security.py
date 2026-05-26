"""
app/core/security.py

Password hashing and verification using bcrypt via passlib.
This module handles everything related to password security.

Usage:
    from app.core.security import hash_password, verify_password
"""

from passlib.context import CryptContext

# ================================
# Password Hashing Context
# ================================

# bcrypt is the industry standard for password hashing
# auto means it will automatically upgrade hashes if the algorithm changes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ================================
# Password Functions
# ================================


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    Returns a hashed string that is safe to store in the database.

    Example:
        hashed = hash_password("mypassword123")
        # "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a stored bcrypt hash.
    Returns True if match, False otherwise.

    Example:
        is_valid = verify_password("mypassword123", hashed)
        # True
    """
    return pwd_context.verify(plain_password, hashed_password)


def is_password_strong(password: str) -> tuple[bool, str]:
    """
    Validates password strength before hashing.
    Returns (is_valid: bool, message: str)

    Rules:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."

    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character."

    return True, "Password is strong."
