"""Generate RSA keys for JWT authentication."""

import getpass
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_keys(key_size: int = 2048) -> None:
    """Generate RSA public/private key pair for JWT."""
    keys_dir = Path("keys")
    keys_dir.mkdir(exist_ok=True)

    # Get password for private key encryption
    print("\nPrivate key encryption setup:")
    print("You can either provide a password or use an environment variable.")

    password = os.environ.get("JWT_PRIVATE_KEY_PASSWORD")
    if password:
        print("Using password from JWT_PRIVATE_KEY_PASSWORD environment variable")
    else:
        while True:
            password = getpass.getpass("Enter password to encrypt private key: ")
            password_confirm = getpass.getpass("Confirm password: ")

            if password != password_confirm:
                print("Passwords do not match. Please try again.\n")
                continue
            if len(password) < 8:
                print("Password must be at least 8 characters. Please try again.\n")
                continue
            break

    # Generate private key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)

    # Save private key with password encryption
    private_key_path = keys_dir / "private_key.pem"
    with open(private_key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(
                    password.encode()
                ),
            )
        )

    # Generate and save public key
    public_key = private_key.public_key()
    public_key_path = keys_dir / "public_key.pem"
    with open(public_key_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

    print("\n✓ RSA keys generated successfully:")
    print(f"  - Private key (encrypted): {private_key_path}")
    print(f"  - Public key: {public_key_path}")
    print(f"\nKey size: {key_size} bits")
    print("\nIMPORTANT:")
    print("1. Keep private_key.pem secure and never commit it to version control!")
    print("2. Set JWT_PRIVATE_KEY_PASSWORD environment variable with the password")
    print("3. Add to your .env file: JWT_PRIVATE_KEY_PASSWORD=your_password_here")


if __name__ == "__main__":
    generate_rsa_keys()
