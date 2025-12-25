import click

from sleakops.commands.build import create_build_command
from sleakops.commands.deploy import create_deploy_command
from sleakops.commands.shell import create_shell_command
from sleakops.commands.login import create_login_command
from sleakops.commands.get_access_cluster import (
    create_get_access_cluster_command
)


@click.group()
def cli_build():
    """Build commands for SleakOps."""
    pass


@click.group()
def cli_deploy():
    """Deploy commands for SleakOps."""
    pass


@click.group()
def cli_shell():
    """Shell commands for SleakOps."""
    pass


@click.group()
def cli_auth():
    """Authentication commands for SleakOps."""
    pass


cli_build.add_command(create_build_command(), name="build")
cli_deploy.add_command(create_deploy_command(), name="deploy")
cli_shell.add_command(create_shell_command(), name="shell")
cli_auth.add_command(create_login_command(), name="login")
cli_auth.add_command(
    create_get_access_cluster_command(), name="get-access-cluster"
)

cli = click.CommandCollection(
    sources=[cli_build, cli_deploy, cli_shell, cli_auth],
    help="""
    ███████╗██╗     ███████╗ █████╗ ██╗  ██╗ ██████╗ ██████╗ ███████╗
    ██╔════╝██║     ██╔════╝██╔══██╗██║ ██╔╝██╔═══██╗██╔══██╗██╔════╝
    ███████╗██║     █████╗  ███████║█████╔╝ ██║   ██║██████╔╝███████╗
    ╚════██║██║     ██╔══╝  ██╔══██║██╔═██╗ ██║   ██║██╔═══╝ ╚════██║
    ███████║███████╗███████╗██║  ██║██║  ██╗╚██████╔╝██║     ███████║
    ╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚══════╝

    Welcome to SleakOps CLI!\n
    SleakOps CLI is a tool to build and deploy projects efficiently.

    For more information about a specific command:\n
    sleakops <command> --help

    Documentation: https://docs.sleakops.com/cli
    """
)

if __name__ == "__main__":
    cli()
