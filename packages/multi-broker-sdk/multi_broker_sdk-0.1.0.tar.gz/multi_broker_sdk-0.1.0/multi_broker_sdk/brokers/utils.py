"""
Utility functions for omnibroker.

This module provides helper functions for TOTP generation, authentication,
and other common operations across different broker implementations.
"""

import hmac
import time
import struct
import base64
import hashlib
from typing import Union

try:
    import pyotp
    HAS_PYOTP = True
except ImportError:
    HAS_PYOTP = False


def generate_totp(secret: str, interval: int = 30) -> str:
    """
    Generate TOTP (Time-based One-Time Password) using pyotp library.
    
    This is the standard TOTP implementation used by most brokers
    like Angel One, Upstox, etc.
    
    Args:
        secret: Base32-encoded TOTP secret key
        interval: Time interval in seconds (default: 30)
    
    Returns:
        6-digit TOTP code as string
    
    Raises:
        ImportError: If pyotp is not installed
        ValueError: If secret is invalid
    
    Example:
        >>> totp = generate_totp("JBSWY3DPEHPK3PXP")
        >>> print(totp)
        '123456'
    """
    if not HAS_PYOTP:
        raise ImportError(
            "pyotp is required for TOTP generation. "
            "Install it with: pip install pyotp"
        )
    
    try:
        totp = pyotp.TOTP(secret, interval=interval)
        return totp.now()
    except Exception as e:
        raise ValueError(f"Failed to generate TOTP: {e}") from e


def generate_manual_totp(
    key: str,
    time_step: int = 30,
    digits: int = 6,
    digest: str = "sha1"
) -> str:
    """
    Generate TOTP manually without external dependencies.
    
    This is a custom implementation used by some brokers like Fyers
    that may have slight variations from the standard TOTP algorithm.
    
    Args:
        key: Base32-encoded TOTP secret key
        time_step: Time step in seconds (default: 30)
        digits: Number of digits in OTP (default: 6)
        digest: Hash algorithm name (default: "sha1")
    
    Returns:
        TOTP code as string with specified number of digits
    
    Example:
        >>> totp = generate_manual_totp("JBSWY3DPEHPK3PXP")
        >>> print(totp)
        '123456'
    """
    # Normalize and decode the key
    key_upper = key.upper()
    # Add padding if necessary
    padding = (8 - len(key_upper) % 8) % 8
    key_padded = key_upper + ("=" * padding)
    
    try:
        key_bytes = base64.b32decode(key_padded)
    except Exception as e:
        raise ValueError(f"Invalid base32 key: {e}") from e
    
    # Get the current time counter
    counter = int(time.time() / time_step)
    counter_bytes = struct.pack(">Q", counter)
    
    # Get the hash algorithm
    hash_algo = getattr(hashlib, digest, hashlib.sha1)
    
    # Generate HMAC
    mac = hmac.new(key_bytes, counter_bytes, hash_algo).digest()
    
    # Dynamic truncation
    offset = mac[-1] & 0x0F
    binary = struct.unpack(">L", mac[offset:offset + 4])[0] & 0x7FFFFFFF
    
    # Generate OTP
    otp = str(binary)[-digits:].zfill(digits)
    return otp


def validate_credentials(credentials: dict, required_fields: list) -> None:
    """
    Validate that required credential fields are present and non-empty.
    
    Args:
        credentials: Dictionary of credential key-value pairs
        required_fields: List of required field names
    
    Raises:
        ValueError: If any required field is missing or empty
    
    Example:
        >>> validate_credentials(
        ...     {"api_key": "abc", "secret": "xyz"},
        ...     ["api_key", "secret", "username"]
        ... )
        ValueError: Missing required credentials: username
    """
    missing = [
        field for field in required_fields
        if field not in credentials or not credentials[field]
    ]
    
    if missing:
        raise ValueError(
            f"Missing required credentials: {', '.join(missing)}"
        )


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging purposes.
    
    Args:
        data: Sensitive string to mask
        visible_chars: Number of characters to leave visible at the end
    
    Returns:
        Masked string
    
    Example:
        >>> mask_sensitive_data("MY_SECRET_API_KEY_123456", 4)
        '**********************3456'
    """
    if not data or len(data) <= visible_chars:
        return "*" * len(data) if data else ""
    
    masked_length = len(data) - visible_chars
    return ("*" * masked_length) + data[-visible_chars:]


def parse_broker_response(
    response: dict,
    success_key: str = "status",
    success_value: Union[str, bool] = True,
    data_key: str = "data"
) -> dict:
    """
    Parse and validate broker API responses.
    
    Args:
        response: Response dictionary from broker API
        success_key: Key in response that indicates success
        success_value: Value that indicates success
        data_key: Key containing the actual data
    
    Returns:
        Parsed data dictionary
    
    Raises:
        ValueError: If response indicates failure
    
    Example:
        >>> response = {"status": "success", "data": {"balance": 10000}}
        >>> parse_broker_response(response, success_value="success")
        {'balance': 10000}
    """
    if not isinstance(response, dict):
        raise ValueError("Response must be a dictionary")
    
    if response.get(success_key) != success_value:
        error_msg = response.get("message", "Unknown error")
        raise ValueError(f"API request failed: {error_msg}")
    
    return response.get(data_key, response)


def format_symbol(
    symbol: str,
    exchange: str = None,
    broker: str = None
) -> str:
    """
    Format trading symbol according to broker requirements.
    
    Different brokers have different symbol formats:
    - Zerodha: "SBIN"
    - Fyers: "NSE:SBIN-EQ"
    - Angel One: "SBIN-EQ"
    
    Args:
        symbol: Base symbol name
        exchange: Exchange name (NSE, BSE, etc.)
        broker: Broker name for specific formatting
    
    Returns:
        Formatted symbol string
    
    Example:
        >>> format_symbol("SBIN", "NSE", "fyers")
        'NSE:SBIN-EQ'
    """
    if broker == "fyers" and exchange:
        return f"{exchange}:{symbol}-EQ"
    elif broker == "angelone":
        return f"{symbol}-EQ"
    else:
        return symbol


def retry_on_failure(func, max_retries: int = 3, delay: int = 1):
    """
    Decorator to retry a function on failure.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    
    Returns:
        Decorated function
    
    Example:
        >>> @retry_on_failure(max_retries=3, delay=2)
        >>> def unstable_api_call():
        ...     # API call that might fail
        ...     pass
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    time.sleep(delay)
                continue
        
        raise last_exception
    
    return wrapper