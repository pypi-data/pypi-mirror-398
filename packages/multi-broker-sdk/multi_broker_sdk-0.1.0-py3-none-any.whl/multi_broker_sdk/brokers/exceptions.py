"""
Custom exceptions for omnibroker.

This module defines all custom exceptions used throughout the package
for better error handling and debugging.
"""


class OmniBrokerError(Exception):
    """Base exception class for all omnibroker errors."""
    pass


class AuthenticationError(OmniBrokerError):
    """
    Raised when authentication with a broker fails.
    
    This can occur due to:
    - Invalid credentials
    - Expired tokens
    - Network issues during authentication
    - Invalid TOTP codes
    """
    pass


class BrokerAPIError(OmniBrokerError):
    """
    Raised when a broker API request fails.
    
    This can occur due to:
    - Invalid API parameters
    - Rate limiting
    - Server errors
    - Network timeouts
    """
    pass


class OrderError(BrokerAPIError):
    """
    Raised when order placement or modification fails.
    
    This can occur due to:
    - Insufficient funds
    - Invalid order parameters
    - Market not open
    - Symbol not found
    """
    pass


class ConfigurationError(OmniBrokerError):
    """
    Raised when there's a configuration issue.
    
    This can occur due to:
    - Missing required credentials
    - Invalid configuration values
    - Missing environment variables
    """
    pass


class BrokerNotFoundError(OmniBrokerError):
    """
    Raised when trying to access a broker that doesn't exist.
    
    This occurs when using the factory with an invalid broker name.
    """
    pass


class DataError(BrokerAPIError):
    """
    Raised when market data retrieval fails.
    
    This can occur due to:
    - Invalid symbols
    - Data not available
    - Subscription issues
    """
    pass


class NetworkError(OmniBrokerError):
    """
    Raised when network-related issues occur.
    
    This can occur due to:
    - Connection timeouts
    - DNS resolution failures
    - SSL/TLS errors
    """
    pass