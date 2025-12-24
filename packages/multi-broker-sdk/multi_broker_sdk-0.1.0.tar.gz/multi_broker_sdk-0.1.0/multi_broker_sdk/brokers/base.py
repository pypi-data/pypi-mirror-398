"""
Base broker interface for multi-broker-sdk.

This module defines the abstract base class that all broker implementations
must inherit from, ensuring a consistent interface across different brokers.
"""

from abc import ABC, abstractmethod


class BaseBroker(ABC):
    """
    Abstract base class for all broker implementations.
    
    All broker classes must implement these methods to provide a consistent
    interface for authentication, account management, and trading operations.
    """

    @abstractmethod
    def authenticate(self, refresh: bool = False) -> str:
        """
        Authenticate with the broker and obtain access token.
        
        Args:
            refresh: Force re-authentication even if token exists
        
        Returns:
            Access token string
        
        Raises:
            AuthenticationError: If authentication fails
        """
        pass

    def is_authenticated(self) -> bool:
        """
        Check if the broker session is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return hasattr(self, 'access_token') and self.access_token is not None

    def logout(self) -> None:
        """
        Log out and clear session tokens.
        
        Default implementation clears access token. Override if broker
        requires explicit logout API call.
        """
        if hasattr(self, 'access_token'):
            self.access_token = None
        if hasattr(self, 'refresh_token'):
            self.refresh_token = None
        if hasattr(self, 'feed_token'):
            self.feed_token = None