import json
import os
import sys
from typing import Dict, Optional
import click
import jwt
from datetime import datetime


class AuthManager:
    """Manages authentication tokens for SleakOps CLI."""

    def __init__(self, credentials_file: str = None):
        """Initialize the auth manager.

        Args:
            credentials_file: Path to credentials file.
            Defaults to ~/.sleakops/credentials.json
        """
        if credentials_file is None:
            credentials_file = os.path.expanduser(
                "~/.sleakops/credentials.json"
            )

        self.credentials_file = credentials_file
        self._ensure_credentials_dir()

    def _ensure_credentials_dir(self) -> None:
        """Ensure the credentials directory exists."""
        credentials_dir = os.path.dirname(self.credentials_file)
        if not os.path.exists(credentials_dir):
            os.makedirs(credentials_dir, mode=0o700)

    def save_tokens(self, tokens: Dict[str, str]) -> None:
        """Save authentication tokens to file.

        Args:
            tokens: Dictionary containing access and refresh tokens
        """
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            os.chmod(self.credentials_file, 0o600)
        except Exception as e:
            click.echo(f"Error saving credentials: {e}")
            sys.exit(1)

    def load_tokens(self) -> Dict[str, str]:
        """Load authentication tokens from file.

        Returns:
            Dictionary containing tokens, empty dict if file doesn't exist
        """
        if not os.path.exists(self.credentials_file):
            return {}

        try:
            with open(self.credentials_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            click.echo(f"Error loading credentials: {e}")
            return {}

    def clear_tokens(self) -> None:
        """Clear stored authentication tokens."""
        if os.path.exists(self.credentials_file):
            try:
                os.remove(self.credentials_file)
            except OSError as e:
                click.echo(f"Error clearing credentials: {e}")

    def get_access_token(self) -> Optional[str]:
        """Get the current access token.

        Returns:
            Access token if available and not expired, None otherwise
        """
        tokens = self.load_tokens()
        access_token = tokens.get('access')
        if not access_token:
            return None

        try:
            payload = jwt.decode(
                access_token, options={"verify_signature": False}
            )
            exp = payload.get('exp')
            if exp and datetime.now().timestamp() >= exp:
                return access_token
        except Exception:
            return None

        return access_token

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated.

        Returns:
            True if valid access token exists, False otherwise
        """
        return self.get_access_token() is not None

    def get_user_info(self) -> Optional[Dict]:
        """Get stored user information.

        Returns:
            User information if available, None otherwise
        """
        tokens = self.load_tokens()
        return tokens.get('user')

    def get_account_id(self) -> Optional[str]:
        """Get the selected account ID.

        Returns:
            Account ID if available, None otherwise
        """
        tokens = self.load_tokens()
        return tokens.get('account_id')

    def save_account_id(self, account_id: str) -> None:
        """Save the selected account ID.

        Args:
            account_id: The account ID to save
        """
        tokens = self.load_tokens()
        tokens['account_id'] = account_id
        self.save_tokens(tokens)


auth_manager = AuthManager()
