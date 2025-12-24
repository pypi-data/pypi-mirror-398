"""
Fyers broker implementation for omnibroker.

This module provides authentication and trading operations for Fyers broker
using their v3 API with automatic TOTP-based login.
"""

import os
import json
import base64
import logging
from typing import Optional, Dict, Any
from urllib.parse import parse_qs, urlparse
from datetime import datetime, time
from pathlib import Path
from cryptography.fernet import Fernet
import hashlib

import requests
from fyers_apiv3 import fyersModel


from ..base import BaseBroker
from ..exceptions import AuthenticationError, BrokerAPIError
from ..utils import generate_manual_totp

logger = logging.getLogger(__name__)


class FyersBroker(BaseBroker):
    """
    Fyers broker integration with automatic authentication.
    
    Supports TOTP-based login and provides access to trading operations.
    Token caching is implemented to avoid regenerating tokens before 12 AM.
    
    Attributes:
        username: Fyers user ID
        totp_key: TOTP secret key for 2FA
        pin: Trading PIN
        client_id: Fyers API client ID
        secret_key: Fyers API secret key
        redirect_uri: OAuth redirect URI
        access_token: Current session access token
    
    Example:
        >>> broker = FyersBroker(
        ...     username="XY12345",
        ...     totp_key="YOUR_TOTP_KEY",
        ...     pin="1234",
        ...     client_id="YOUR_CLIENT_ID",
        ...     secret_key="YOUR_SECRET"
        ... )
        >>> broker.authenticate()
        >>> profile = broker.get_account_info()
    """

    BASE_URL = "https://api-t2.fyers.in"
    TOKEN_URL = "https://api-t1.fyers.in/api/v3/token"
    
    def __init__(
        self,
        username: str,
        totp_key: str,
        pin: str,
        client_id: str,
        secret_key: str,
        redirect_uri: str,
        response_type: str = "code",
        grant_type: str = "authorization_code"
    ):
        """
        Initialize Fyers broker connection.
        
        Args:
            username: Fyers user ID (or set FYERS_ID env var)
            totp_key: TOTP secret key (or set FYERS_TOTP_KEY env var)
            pin: Trading PIN (or set FYERS_PIN env var)
            client_id: API client ID (or set FYERS_CLIENT_ID env var)
            secret_key: API secret key (or set FYERS_SECRET_KEY env var)
            redirect_uri: OAuth redirect URI (or set FYERS_REDIRECT_URI env var)
            response_type: OAuth response type (default: "code")
            grant_type: OAuth grant type (default: "authorization_code")
        
        Raises:
            ValueError: If required credentials are missing
        """
        self.username = username
        self.totp_key = totp_key
        self.pin = pin
        self.client_id = client_id
        self.secret_key = secret_key
        self.redirect_uri = redirect_uri
        self.broker_name = "fyers"
        self.response_type = response_type
        self.grant_type = grant_type
        self.access_token: Optional[str] = None
        self._fyers_client: Optional[fyersModel.FyersModel] = None
        
        self._validate_credentials()
        self._cache_dir = Path.home() / ".multi_broker_sdk"
        self._cache_file = self._cache_dir / "tokens" / f".fyers_token_{self.username}.enc"

    def _validate_credentials(self) -> None:
        """Validate that all required credentials are provided."""
        required = {
            "username": self.username,
            "totp_key": self.totp_key,
            "pin": self.pin,
            "client_id": self.client_id,
            "secret_key": self.secret_key
        }
        
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(
                f"Missing required credentials: {', '.join(missing)}. "
                f"Please provide them or set environment variables."
            )

    def _get_encryption_key(self) -> bytes:
        """Generate encryption key from user credentials."""
        # Create a deterministic key from user's credentials
        key_material = f"{self.username}:{self.client_id}:{self.secret_key}".encode()
        key_hash = hashlib.sha256(key_material).digest()
        return base64.urlsafe_b64encode(key_hash)

    def _is_token_valid(self, token_data: Dict[str, Any]) -> bool:
        """
        Check if cached token is still valid (not past 12 AM IST).
        
        Args:
            token_data: Dictionary containing token and timestamp
        
        Returns:
            True if token is valid, False otherwise
        """
        try:
            from datetime import timezone, timedelta
            
            # Define IST timezone (UTC+5:30)
            IST = timezone(timedelta(hours=5, minutes=30))
            
            generated_at = datetime.fromisoformat(token_data["generated_at"])
            now = datetime.now(IST)
            
            # Convert generated_at to IST if it doesn't have timezone info
            if generated_at.tzinfo is None:
                generated_at = generated_at.replace(tzinfo=IST)
            
            # Check if we've passed 12 AM IST since token generation
            if generated_at.date() < now.date():
                logger.info("Token expired: past 12 AM IST")
                return False
            
            # Check if current time is past midnight IST of the same day
            midnight_today_ist = datetime.combine(now.date(), time(0, 0, 0), tzinfo=IST)
            if generated_at < midnight_today_ist:
                logger.info("Token expired: generated before today's midnight IST")
                return False
            
            return True
        except (KeyError, ValueError) as e:
            logger.warning(f"Invalid token data format: {e}")
            return False

    def _save_token_cache(self, token: str) -> None:
        """
        Save access token to encrypted cache file.
        
        Args:
            token: Access token to cache
        """
        try:
            from datetime import timezone, timedelta
            
            fernet = Fernet(self._get_encryption_key())
            
            # Define IST timezone (UTC+5:30)
            IST = timezone(timedelta(hours=5, minutes=30))
            
            token_data = {
                "access_token": token,
                "generated_at": datetime.now(IST).isoformat(),
                "username": self.username
            }
            
            # Encrypt and save
            encrypted_data = fernet.encrypt(json.dumps(token_data).encode())
            
            # Ensure directory exists
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            self._cache_file.write_bytes(encrypted_data)
            logger.info(f"Token cached successfully at {self._cache_file}")
        except Exception as e:
            logger.warning(f"Failed to cache token: {e}")

    def _load_token_cache(self) -> Optional[str]:
        """
        Load and decrypt cached access token.
        
        Returns:
            Access token if valid cache exists, None otherwise
        """
        if not self._cache_file.exists():
            logger.debug("No cached token found")
            return None
        
        try:
            fernet = Fernet(self._get_encryption_key())
            
            # Read and decrypt
            encrypted_data = self._cache_file.read_bytes()
            decrypted_data = fernet.decrypt(encrypted_data)
            token_data = json.loads(decrypted_data.decode())
            
            # Validate token data
            if token_data.get("username") != self.username:
                logger.warning("Cached token belongs to different user")
                return None
            
            if not self._is_token_valid(token_data):
                logger.info("Cached token is expired")
                self._cache_file.unlink()  # Delete expired cache
                return None
            
            logger.info("Loaded valid token from cache")
            return token_data["access_token"]
        except Exception as e:
            logger.warning(f"Failed to load cached token: {e}")
            # Delete corrupted cache file
            if self._cache_file.exists():
                self._cache_file.unlink()
            return None

    def authenticate(self, refresh: bool = False) -> fyersModel.FyersModel:
        """
        Authenticate with Fyers and obtain access token.
        Uses cached token if available and valid, otherwise generates new one.
        
        Args:
            refresh: Force re-authentication even if token exists
        
        Returns:
            Access token string
        
        Raises:
            AuthenticationError: If authentication fails
        """
        # Try to use existing token in memory
        if self.access_token and not refresh:
            logger.info("Using existing access token from memory")
            return self.access_token

        # Try to load from cache
        if not refresh:
            cached_token = self._load_token_cache()
            if cached_token:
                self.access_token = cached_token
                self._fyers_client = None  # Reset client to use cached token
                return self.access_token

        # Generate new token
        try:
            logger.info("Starting Fyers authentication process")
            self.access_token = self._generate_token()
            self._fyers_client = None  # Reset client to use new token
            
            # Cache the new token
            self._save_token_cache(self.access_token)
            
            logger.info("Authentication successful")
            return self.access_token
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Fyers authentication failed: {e}") from e

    def _generate_token(self) -> str:
        """
        Generate access token using TOTP-based login flow.
        
        Returns:
            Access token string
        
        Raises:
            AuthenticationError: If any step in the authentication flow fails
        """
        session = requests.Session()
        session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        try:
            # Step 1: Send login OTP request
            logger.debug("Step 1: Sending login OTP")
            request_key = self._send_login_otp(session)
            
            # Step 2: Verify OTP using TOTP
            logger.debug("Step 2: Verifying OTP")
            request_key = self._verify_otp(session, request_key)
            
            # Step 3: Verify PIN
            logger.debug("Step 3: Verifying PIN")
            access_token_temp = self._verify_pin(session, request_key)

            # Step 4: Get authorization code
            logger.debug("Step 4: Getting authorization code")
            auth_code = self._get_auth_code(session, access_token_temp)
            
            # Step 5: Exchange for final access token
            logger.debug("Step 5: Generating final access token")
            return self._exchange_token(auth_code)
            
        except requests.RequestException as e:
            raise AuthenticationError(f"Network error during authentication: {e}") from e
        except KeyError as e:
            raise AuthenticationError(f"Unexpected API response format: {e}") from e
        finally:
            session.close()

    def _send_login_otp(self, session: requests.Session) -> str:
        """Send login OTP request."""
        data = {
            "fy_id": base64.b64encode(self.username.encode()).decode(),
            "app_id": "2",
        }
        response = session.post(
            f"{self.BASE_URL}/vagator/v2/send_login_otp_v2",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()["request_key"]

    def _verify_otp(self, session: requests.Session, request_key: str) -> str:
        """Verify OTP using TOTP."""
        totp = generate_manual_totp(self.totp_key)
        data = {
            "request_key": request_key,
            "otp": totp
        }
        response = session.post(
            f"{self.BASE_URL}/vagator/v2/verify_otp",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()["request_key"]

    def _verify_pin(self, session: requests.Session, request_key: str) -> str:
        """Verify trading PIN."""
        data = {
            "request_key": request_key,
            "identity_type": "pin",
            "identifier": base64.b64encode(self.pin.encode()).decode(),
        }
        response = session.post(
            f"{self.BASE_URL}/vagator/v2/verify_pin_v2",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()["data"]["access_token"]

    def _get_auth_code(self, session: requests.Session, access_token: str) -> str:
        """Get authorization code."""
        headers = {
            "authorization": f"Bearer {access_token}",
            "content-type": "application/json; charset=UTF-8",
        }
        data = {
            "fyers_id": self.username,
            "app_id": self.client_id[:-4],
            "redirect_uri": self.redirect_uri,
            "appType": "100",
            "response_type": "code",
            "state": "autologin",
            "create_cookie": True,
        }

        response = session.post(
            self.TOKEN_URL,
            headers=headers,
            json=data,
            timeout=10
        )
        response.raise_for_status()
        
        redirect_url = response.json()["Url"]
        parsed = urlparse(redirect_url)
        return parse_qs(parsed.query)["auth_code"][0]

    def _exchange_token(self, auth_code: str) -> str:
        """Exchange authorization code for access token."""
        session = fyersModel.SessionModel(
            client_id=self.client_id,
            secret_key=self.secret_key,
            redirect_uri=self.redirect_uri,
            response_type=self.response_type,
            grant_type=self.grant_type,
        )
        session.set_token(auth_code)
        response = session.generate_token()
        
        if "access_token" not in response:
            raise AuthenticationError(f"Failed to get access token: {response}")
        
        return response["access_token"]

    def get_client(self) -> fyersModel.FyersModel:
        """Get or create Fyers API client."""
        self.authenticate()
        
        if not self.access_token:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")
        
        if self._fyers_client is None:
            self._fyers_client = fyersModel.FyersModel(
                client_id=self.client_id,
                token=self.access_token,
                log_path=os.getcwd(),
            )
        
        return self._fyers_client

    def __repr__(self) -> str:
        """String representation of the broker instance."""
        return f"FyersBroker(username={self.username}, authenticated={bool(self.access_token)})"
    