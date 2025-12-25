"""
Password Hashing

Argon2id-based password hashing utilities.
"""

from passlib.context import CryptContext
from loguru import logger

# Argon2id configuration
# Winner of Password Hashing Competition 2015
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,  # 3 iterations
    argon2__parallelism=4,  # 4 parallel threads
)


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2id.

    Argon2id is memory-hard and resistant to GPU/ASIC attacks.

    Args:
        password: Plain text password

    Returns:
        Hashed password (includes salt and parameters)

    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> verify_password("my_secure_password", hashed)
        True
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its Argon2id hash.

    Args:
        plain_password: Plain text password
        hashed_password: Argon2id hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False
