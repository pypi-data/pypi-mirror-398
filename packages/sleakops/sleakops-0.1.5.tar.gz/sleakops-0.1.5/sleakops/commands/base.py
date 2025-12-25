import click
import sys

from sleakops.api.client import SleakOpsAPIClient
from sleakops.auth import auth_manager


class BaseCommand:
    """Base class for SleakOps CLI commands."""

    def __init__(self, api_key: str = None, use_token_auth: bool = False):
        """Initialize the command with an API client.

        Args:
            api_key: The SleakOps API key
            use_token_auth: Whether to use token authentication
        """
        if use_token_auth:
            access_token = auth_manager.get_access_token()
            if not access_token:
                click.echo(
                    click.style(
                        "Not authenticated. Run 'sleakops login' first.",
                        fg="red"
                    )
                )
                sys.exit(1)

            account_id = auth_manager.get_account_id()
            if not account_id:
                click.echo(
                    click.style(
                        "No account selected. Run 'sleakops login' again.",
                        fg="red"
                    )
                )
                sys.exit(1)

            self.api_client = SleakOpsAPIClient(access_token=access_token)
            self.api_client.set_account_id(account_id)
        else:
            if not api_key:
                click.echo(
                    click.style(
                        "Error: API key required for this command.",
                        fg="red"
                    )
                )
                sys.exit(1)
            self.api_client = SleakOpsAPIClient(api_key=api_key)

    def parse_docker_args(self, docker_args: str) -> dict:
        """Parse docker arguments from string format.

        Args:
            docker_args: Docker args in format 'key1=value1,key2=value2'

        Returns:
            Dictionary with parsed docker arguments

        Raises:
            SystemExit: If parsing fails
        """
        if not docker_args:
            return {}

        try:
            docker_args_dict = {}
            for arg in docker_args.split(','):
                if '=' not in arg:
                    click.echo(
                        click.style(
                            "Error: docker-args must be in format \
                            'key1=value1,key2=value2'",
                            fg="red"
                        )
                    )
                    sys.exit(1)
                key, value = arg.split('=', 1)
                docker_args_dict[key.strip()] = value.strip()
            return docker_args_dict
        except Exception:
            click.echo(
                click.style(
                    "Error: docker-args must be in format \
                    'key1=value1,key2=value2'",
                    fg="red"
                )
            )
            sys.exit(1)

    def add_optional_fields(self, data: dict, **kwargs) -> dict:
        """Add optional fields to data dictionary if they are not None.

        Args:
            data: The data dictionary to update
            **kwargs: Optional fields to add

        Returns:
            Updated data dictionary
        """
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value
        return data
