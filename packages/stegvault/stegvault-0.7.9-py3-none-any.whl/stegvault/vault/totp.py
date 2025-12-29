"""
TOTP (Time-based One-Time Password) support for vault entries.
"""

import pyotp
import qrcode  # type: ignore[import-untyped]
from typing import Optional
import io


def generate_totp_secret() -> str:
    """
    Generate a new random TOTP secret (base32 encoded).

    Returns:
        Base32-encoded secret string
    """
    return pyotp.random_base32()


def generate_totp_code(secret: str) -> str:
    """
    Generate current TOTP code from secret.

    Args:
        secret: Base32-encoded TOTP secret

    Returns:
        6-digit TOTP code as string

    Raises:
        ValueError: If secret is invalid
    """
    try:
        totp = pyotp.TOTP(secret)
        return totp.now()
    except Exception as e:
        raise ValueError(f"Invalid TOTP secret: {e}")


def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verify a TOTP code against secret.

    Args:
        secret: Base32-encoded TOTP secret
        code: 6-digit code to verify

    Returns:
        True if code is valid, False otherwise
    """
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    except Exception:
        return False


def get_totp_provisioning_uri(secret: str, account_name: str, issuer: str = "StegVault") -> str:
    """
    Get provisioning URI for TOTP (for QR code generation).

    Args:
        secret: Base32-encoded TOTP secret
        account_name: Account name (e.g., username or key)
        issuer: Service name (default: "StegVault")

    Returns:
        Provisioning URI (otpauth://totp/...)
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=account_name, issuer_name=issuer)


def generate_qr_code_ascii(provisioning_uri: str) -> str:
    """
    Generate ASCII art QR code for provisioning URI.

    Args:
        provisioning_uri: TOTP provisioning URI

    Returns:
        ASCII art representation of QR code
    """
    # Use larger QR code with higher error correction for better scanning
    qr = qrcode.QRCode(
        version=1,  # Auto-adjust size
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # type: ignore[attr-defined]
        box_size=1,
        border=2,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    # Get ASCII representation with inverted colors for better visibility
    output = io.StringIO()
    qr.print_ascii(out=output, invert=True)
    return output.getvalue()


def get_totp_time_remaining() -> int:
    """
    Get seconds remaining until next TOTP code.

    Returns:
        Seconds remaining (0-29, typically)
    """
    import time

    return 30 - int(time.time()) % 30
