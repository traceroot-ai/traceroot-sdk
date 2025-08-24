from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from traceroot.config import TraceRootConfig


class CredentialManager:
    """Centralized credential management for both
    tracer and logger
    """

    def __init__(self, config: TraceRootConfig):
        self.config = config
        self._cached_credentials: dict[str, Any] | None = None
        self._credentials_expiry: datetime | None = None

    def get_credentials(
        self,
        force_refresh: bool = False,
    ) -> dict[str, Any] | None:
        """Get credentials, refreshing if needed

        Args:
            force_refresh: If True, always refresh credentials
                regardless of expiry

        Returns:
            Dictionary containing AWS credentials or None if unavailable
        """
        if self.config.local_mode:
            return None

        if not self.config.enable_span_cloud_export:
            return None

        if self.needs_refresh(force_refresh):
            self._fetch_and_cache_credentials()

        return self._cached_credentials

    def needs_refresh(self, force_refresh: bool = False) -> bool:
        """Check if credentials need to be refreshed

        Args:
            force_refresh: If True, always refresh credentials

        Returns:
            True if credentials need to be refreshed, False otherwise
        """
        if force_refresh:
            return True

        if not self._cached_credentials or not self._credentials_expiry:
            return True

        utc_now = datetime.now(timezone.utc)
        # Refresh if credentials expire within 30 minutes
        return utc_now >= (self._credentials_expiry - timedelta(minutes=30))

    def _fetch_and_cache_credentials(self) -> None:
        """Fetch credentials from API and update config automatically"""
        try:
            url = self.config.verification_endpoint
            params = {"token": self.config.token}
            headers = {"Content-Type": "application/json"}

            response = requests.get(url, params=params, headers=headers)
            if not response.ok:
                return

            credentials = response.json()

            # Parse expiration time from credentials
            utc_now = datetime.now(timezone.utc)
            expiration_str = credentials.get('expiration_utc')
            if isinstance(expiration_str, str):
                # Parse ISO format datetime string and ensure timezone-aware
                expiration_dt = datetime.fromisoformat(
                    expiration_str.replace('Z', '+00:00'))
                # Ensure timezone-aware, convert to UTC if not already
                if expiration_dt.tzinfo is None:
                    expiration_dt = expiration_dt.replace(tzinfo=timezone.utc)
            else:
                # Fallback: assume 12 hours from now if no expiration provided
                expiration_dt = utc_now + timedelta(hours=12)

            # Cache the credentials and expiration time
            self._cached_credentials = {
                'aws_access_key_id': credentials['aws_access_key_id'],
                'aws_secret_access_key': credentials['aws_secret_access_key'],
                'aws_session_token': credentials['aws_session_token'],
                'region': credentials['region'],
                'hash': credentials['hash'],
                'expiration_utc': expiration_str,
                'otlp_endpoint': credentials['otlp_endpoint'],
            }
            self._credentials_expiry = expiration_dt

            # Automatically update config with new values
            # This ensures both tracer and logger get updated endpoint/hash
            self.config._name = credentials['hash']
            self.config.otlp_endpoint = credentials['otlp_endpoint']

        except Exception:
            # Silently handle credential fetch errors
            # Return cached credentials if available, even if expired
            pass

    def check_and_refresh_if_needed(self) -> bool:
        """Check credentials and refresh if they're near expiration

        This is the method that should be called by both tracer and logger
        before performing operations that need fresh credentials.

        Returns:
            True if credentials were changed/refreshed, False otherwise
        """
        if self.config.local_mode:
            return False

        if not self.needs_refresh():
            return False

        try:
            # Store old credentials to check if they changed
            old_credentials = self._cached_credentials

            # Fetch new credentials (this will update config automatically)
            self.get_credentials()

            # Return whether credentials actually changed
            new_credentials = self._cached_credentials
            return (new_credentials and old_credentials
                    and new_credentials != old_credentials)

        except Exception:
            # Silently handle credential refresh errors
            return False

    def force_refresh(self) -> bool:
        """Force refresh credentials immediately

        Returns:
            True if refresh was successful, False otherwise
        """
        try:
            self._cached_credentials
            self.get_credentials(force_refresh=True)
            return self._cached_credentials is not None
        except Exception:
            return False
