import sys
import time
import requests
from requests.exceptions import ConnectionError
import click
from functools import wraps

from sleakops.config import (
    API_URL, MAX_POLLING, SLEEP_TIME, CONSOLE_API_URL,
    LOGIN_ENDPOINT, TOKEN_REFRESH_ENDPOINT, ACCOUNT_ENDPOINT
)
from sleakops.auth import auth_manager


def handle_api_errors(func):
    """Decorator to handle API errors and token refresh automatically.

    This decorator intercepts API errors, attempts to refresh the token
    if possible, and retries the original request.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        response = func(self, *args, **kwargs)

        if isinstance(response, list):
            return response

        if (
            response.status_code == 401 and
            hasattr(self, 'auth_type') and
            self.auth_type == "token"
        ):
            if self._handle_token_refresh():
                response = func(self, *args, **kwargs)

                if response.status_code == 401:
                    click.echo("Authentication failed")
                    click.echo("Please run 'sleakops login' again")
                    sys.exit(1)
            else:
                click.echo("Authentication failed")
                click.echo("Please run 'sleakops login' again")
                sys.exit(1)
        if not response.ok:
            result_message = (
                response.json()
                if response.status_code in [400, 412]
                else response.reason
            )
            click.echo(f"Something went wrong: {result_message}")
            sys.exit(1)

        return response.json()

    return wrapper


class SleakOpsAPIClient:
    """Client for interacting with SleakOps API."""

    def __init__(self, api_key: str = None, access_token: str = None):
        """Initialize the API client with either an API key or access token.

        Args:
            api_key: The SleakOps API key for authentication
            access_token: JWT access token for authentication
        """
        if access_token:
            self.headers = {"Authorization": f"Bearer {access_token}"}
            self.auth_type = "token"
        elif api_key:
            self.headers = {"Authorization": f"Api-Key {api_key}"}
            self.auth_type = "api_key"

        self.api_key = api_key
        self.access_token = access_token
        self.account_id = None

    @handle_api_errors
    def _make_request(self, endpoint: str, data: dict) -> requests.Response:
        """Make a POST request to the API.

        Args:
            endpoint: The API endpoint to call
            data: The data to send in the request body

        Returns:
            The response object

        Raises:
            SystemExit: If connection fails or request is not successful
        """
        path = f"{API_URL}{endpoint}"

        try:
            response = requests.post(path, json=data, headers=self.headers)
        except ConnectionError:
            click.echo(f"Could not reach {path}")
            sys.exit(1)

        return response

    @handle_api_errors
    def _poll_for_completion(
        self,
        endpoint: str,
        resource_id: str,
        resource_name: str,
    ) -> None:
        """Poll the API until the resource is ready.

        Args:
            endpoint: The API endpoint to check
            resource_id: The ID of the resource to check
            resource_name: The name of the resource for display purposes
        """
        created = False
        retries = 0

        while not created and retries < MAX_POLLING:
            try:
                state_response = requests.get(
                    f"{API_URL}{endpoint}{resource_id}/",
                    headers=self.headers,
                )
            except ConnectionError:
                click.echo(f"Could not reach {API_URL}{endpoint}")
                sys.exit(1)

            if state_response.ok:
                state = state_response.json()["state"]

                if state == "initial":
                    click.echo(f"{resource_name} queued...")
                elif state == "creating":
                    click.echo(f"{resource_name}ing project...")
                elif state == "error":
                    click.echo(f"Something went wrong:\
                        {state_response.json()['errors']}")
                    sys.exit(1)
                elif state == "created":
                    click.echo(f"{resource_name} is ready!")
                    created = True
                    sys.exit(0)

            retries += 1
            time.sleep(SLEEP_TIME)

        sys.exit(0)

    def execute_action(
        self,
        endpoint: str,
        data: dict,
        wait: bool,
        resource_name: str,
    ) -> None:
        """Execute an action on the API with optional waiting.

        Args:
            endpoint: The API endpoint to call
            data: The data to send in the request
            wait: Whether to wait for completion
            resource_name: The name of the resource for display purposes
        """
        response = self._make_request(endpoint, data)

        if wait:
            resource_id = response["id"]
            self._poll_for_completion(endpoint, resource_id, resource_name)

        sys.exit(0)

    def login(self, email: str, password: str) -> dict:
        """Authenticate with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Dictionary containing access token, refresh token, and user info

        Raises:
            SystemExit: If authentication fails
        """
        path = f"{API_URL}{LOGIN_ENDPOINT}"
        data = {"email": email, "password": password}

        try:
            response = requests.post(path, json=data)
        except ConnectionError:
            click.echo(f"Could not reach {path}")
            sys.exit(1)

        if not response.ok:
            result_message = (
                response.json()
                if response.status_code in [400, 401]
                else response.reason
            )
            click.echo(f"Authentication failed: {result_message}")
            sys.exit(1)

        response_data = response.json()

        refresh_token = response_data.get('refresh')
        if not refresh_token:
            cookies = response.cookies
            refresh_token = (cookies.get('refresh_token') or
                             cookies.get('refresh'))

        if refresh_token and not response_data.get('refresh'):
            response_data['refresh'] = refresh_token

        return response_data

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token.

        Args:
            refresh_token: The refresh token

        Returns:
            Dictionary containing new access token

        Raises:
            SystemExit: If refresh fails
        """
        path = f"{API_URL}{TOKEN_REFRESH_ENDPOINT}"
        data = {"refresh": refresh_token}

        try:
            response = requests.post(path, json=data)
        except ConnectionError:
            click.echo(f"Could not reach {path}")
            sys.exit(1)

        if not response.ok:
            # Logging error is handled by the caller
            sys.exit(1)

        response_data = response.json()

        new_refresh_token = response_data.get('refresh')
        if not new_refresh_token:
            cookies = response.cookies
            new_refresh_token = (cookies.get('refresh_token') or
                                 cookies.get('refresh'))

        if new_refresh_token and not response_data.get('refresh'):
            response_data['refresh'] = new_refresh_token

        return response_data

    def set_account_id(self, account_id: str) -> None:
        """Set the account ID for subsequent requests.

        Args:
            account_id: The account ID to use
        """
        self.account_id = account_id
        if self.auth_type == "token":
            self.headers["account"] = account_id

    def _handle_token_refresh(self) -> bool:
        """Handle automatic token refresh for expired tokens.

        Returns:
            True if token was refreshed successfully, False otherwise
        """
        if self.auth_type != "token":
            return False

        tokens = auth_manager.load_tokens()
        refresh_token = tokens.get('refresh')

        if not refresh_token:
            return False

        try:
            new_tokens = self.refresh_access_token(refresh_token)
            # Update stored tokens
            tokens.update(new_tokens)
            auth_manager.save_tokens(tokens)

            # Update current headers
            self.access_token = new_tokens.get('access')
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            return True
        except SystemExit:
            return False

    @handle_api_errors
    def get_accounts(self) -> list:
        """Get available accounts for the authenticated user.

        Returns:
            List of account dictionaries

        Raises:
            SystemExit: If request fails
        """
        path = f"{API_URL}{ACCOUNT_ENDPOINT}"

        try:
            response = requests.get(path, headers=self.headers)
        except ConnectionError:
            click.echo(f"Could not reach {path}")
            sys.exit(1)

        return response.json()

    @handle_api_errors
    def get_resources(self, endpoint: str, params: dict = None) -> dict:
        """Get resources from the API.

        Args:
            endpoint: The API endpoint to call
            params: Query parameters to send

        Returns:
            The JSON response from the API

        Raises:
            SystemExit: If connection fails or request is not successful
        """
        path = f"{API_URL}{endpoint}"

        try:
            response = requests.get(path, params=params, headers=self.headers)
        except ConnectionError:
            click.echo(f"Could not reach {path}")
            sys.exit(1)

        return response

    @handle_api_errors
    def get_resources_from_console(
        self,
        endpoint: str,
        params: dict = None
    ) -> dict:
        """Get resources from the console API.

        Args:
            endpoint: The API endpoint to call
            params: Query parameters to send

        Returns:
            The JSON response from the console API

        Raises:
            SystemExit: If connection fails or request is not successful
        """
        path = f"{CONSOLE_API_URL}{endpoint}"

        try:
            response = requests.get(path, params=params, headers=self.headers)
        except ConnectionError:
            click.echo(f"Could not reach {path}")
            sys.exit(1)

        return response
