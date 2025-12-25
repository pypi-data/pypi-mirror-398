import click
import sys

from sleakops.api.client import SleakOpsAPIClient
from sleakops.auth import auth_manager


class LoginCommand:
    """Command class for handling login operations."""

    def execute(self, email: str, password: str) -> None:
        """Execute login with email and password.

        Args:
            email: User email
            password: User password
        """
        api_client = SleakOpsAPIClient()
        api_client.auth_type = None
        api_client.headers = {}

        try:
            response = api_client.login(email, password)

            user_info = response.get('user', {})
            tokens = {
                'access': response.get('access'),
                'refresh': response.get('refresh'),
                'user': user_info
            }

            auth_manager.save_tokens(tokens)

            user_email = user_info.get('email', email)
            click.echo(f"Successfully logged in as {user_email}")

            click.echo("Fetching available accounts...")
            api_client.headers = {
                "Authorization": f"Bearer {tokens['access']}",
            }
            accounts = api_client.get_accounts()

            if not accounts:
                click.echo("No accounts found for this user")
                sys.exit(1)

            selected_account = self._select_account(accounts)
            account_id = selected_account['id']

            auth_manager.save_account_id(account_id)
            click.echo(
                f"Selected account: {selected_account.get('name', 'Unknown')}"
            )

        except SystemExit:
            sys.exit(1)

    def _select_account(self, accounts: list) -> dict:
        """Show interactive selection for accounts.

        Args:
            accounts: List of account dictionaries

        Returns:
            Selected account dictionary
        """
        if len(accounts) == 1:
            return accounts[0]

        click.echo("\nSelect an account:")
        for i, account in enumerate(accounts, 1):
            account_name = account.get('name', 'Unknown')
            account_id = account.get('id', 'Unknown')
            click.echo(
                click.style(
                    f"[{i}] {account_name} (ID: {account_id})",
                    fg="blue"
                )
            )

        choice = click.prompt(
            "Choice",
            type=click.IntRange(1, len(accounts))
        )
        return accounts[choice - 1]


def create_login_command():
    """Create and configure the login CLI command."""

    @click.command()
    @click.option(
        "-e",
        "--email",
        prompt="Email",
        help="Your SleakOps email address"
    )
    @click.option(
        "-p",
        "--password",
        prompt="Password",
        hide_input=True,
        help="Your SleakOps password"
    )
    def login(email, password):
        """Authenticate with SleakOps using email and password."""
        login_command = LoginCommand()
        login_command.execute(email, password)

    return login
