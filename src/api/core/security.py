"""Security utilities for JWT authentication and password hashing."""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from passlib.context import CryptContext

from api.core.config import get_settings
from api.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt (truncates to 72 bytes if needed)."""
    # Bcrypt has a 72-byte limitation, truncate if necessary
    password_bytes = password.encode("utf-8")[:72]
    return pwd_context.hash(password_bytes.decode("utf-8", errors="ignore"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (truncates to 72 bytes if needed)."""
    # Truncate to match hashing behavior
    password_bytes = plain_password.encode("utf-8")[:72]
    return pwd_context.verify(password_bytes.decode("utf-8", errors="ignore"), hashed_password)


class JWTManager:
    """JWT token manager using RS256 (asymmetric) algorithm."""

    def __init__(
        self, private_key_path: str, public_key_path: str, private_key_password: str | None = None
    ) -> None:
        """Initialize JWT manager with RSA key paths.

        Args:
            private_key_path: Path to encrypted private key file
            public_key_path: Path to public key file
            private_key_password: Password to decrypt private key (if None, reads from env)
        """
        self.algorithm = "RS256"
        self._private_key = self._load_private_key(private_key_path, private_key_password)
        self._public_key = self._load_key(public_key_path)

    def _load_key(self, key_path: str) -> bytes:
        """Load RSA key from file."""
        path = Path(key_path)
        if not path.exists():
            raise FileNotFoundError(f"Key file not found: {key_path}")
        return path.read_bytes()

    def _load_private_key(self, key_path: str, password: str | None = None) -> bytes:
        """Load and decrypt private RSA key from file.

        Args:
            key_path: Path to encrypted private key file
            password: Password to decrypt the key (if None, reads from env)

        Returns:
            Decrypted private key bytes in PEM format

        Raises:
            FileNotFoundError: If key file doesn't exist
            ValueError: If password is missing or incorrect
        """
        path = Path(key_path)
        if not path.exists():
            raise FileNotFoundError(f"Private key file not found: {key_path}")

        # Get password from parameter or environment
        if password is None:
            password = os.environ.get("JWT_PRIVATE_KEY_PASSWORD")
            if password is None:
                raise ValueError(
                    "JWT_PRIVATE_KEY_PASSWORD environment variable is required "
                    "to decrypt the private key"
                )

        # Load encrypted private key
        encrypted_key = path.read_bytes()

        try:
            # Deserialize and decrypt the private key
            private_key = serialization.load_pem_private_key(
                encrypted_key, password=password.encode(), backend=None
            )

            # Return the key in PEM format for JWT library
            return private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        except ValueError as e:
            raise ValueError(f"Failed to decrypt private key. Check password: {e}") from e

    def create_access_token(
        self, subject: str, expires_delta: timedelta | None = None
    ) -> str:
        """Create JWT access token.

        Args:
            subject: The subject (typically user ID or username)
            expires_delta: Optional expiration time delta

        Returns:
            Encoded JWT token
        """
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=15)

        payload = {
            "exp": expire,
            "iat": datetime.now(UTC),
            "sub": str(subject),
        }

        encoded_jwt = jwt.encode(payload, self._private_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        return jwt.decode(token, self._public_key, algorithms=[self.algorithm])


def get_jwt_manager() -> JWTManager:
    """Get JWT manager instance."""
    return JWTManager(
        settings.jwt_private_key_path,
        settings.jwt_public_key_path,
        settings.jwt_private_key_password,
    )
