"""
Security utilities for authentication and authorization.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext


class SecurityManager:
    """Security manager for authentication and authorization."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        """
        Initialize security manager.

        Args:
            secret_key: Secret key for JWT tokens
            algorithm: JWT algorithm
            access_token_expire_minutes: Access token expiration time
            refresh_token_expire_days: Refresh token expiration time
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(self, data: dict[str, Any]) -> str:
        """
        Create JWT access token.

        Args:
            data: Token payload data

        Returns:
            JWT access token
        """
        to_encode = data.copy()

        # Add expiration time
        expire = datetime.now(UTC) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, subject: str | int) -> str:
        """
        Create JWT refresh token.

        Args:
            subject: Token subject (usually user ID)

        Returns:
            JWT refresh token
        """
        to_encode = {
            "sub": str(subject),
            "exp": datetime.now(UTC) + timedelta(days=self.refresh_token_expire_days),
            "type": "refresh",
        }

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """
        Verify JWT token.

        Args:
            token: JWT token

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return dict(payload)
        except JWTError:
            return None

    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches hash
        """
        return self.pwd_context.verify(plain_password, hashed_password)


# Global security manager
_security_manager: SecurityManager | None = None


def get_security_manager() -> SecurityManager:
    """Get global security manager instance."""
    global _security_manager
    if _security_manager is None:
        raise RuntimeError(
            "Security manager not initialized. Call initialize_security() first."
        )
    return _security_manager


def initialize_security(
    secret_key: str,
    algorithm: str = "HS256",
    access_token_expire_minutes: int = 30,
    refresh_token_expire_days: int = 7,
) -> SecurityManager:
    """
    Initialize global security manager.

    Args:
        secret_key: Secret key for JWT tokens
        algorithm: JWT algorithm
        access_token_expire_minutes: Access token expiration time
        refresh_token_expire_days: Refresh token expiration time

    Returns:
        Security manager instance
    """
    global _security_manager
    _security_manager = SecurityManager(
        secret_key=secret_key,
        algorithm=algorithm,
        access_token_expire_minutes=access_token_expire_minutes,
        refresh_token_expire_days=refresh_token_expire_days,
    )
    return _security_manager


# Convenience functions
def create_access_token(data: dict[str, Any]) -> str:
    """Create JWT access token using global security manager."""
    return get_security_manager().create_access_token(data)


def create_refresh_token(subject: str | int) -> str:
    """Create JWT refresh token using global security manager."""
    return get_security_manager().create_refresh_token(subject)


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify JWT token using global security manager."""
    return get_security_manager().verify_token(token)


def hash_password(password: str) -> str:
    """Hash password using global security manager."""
    return get_security_manager().hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using global security manager."""
    return get_security_manager().verify_password(plain_password, hashed_password)
