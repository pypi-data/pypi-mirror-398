import click

from sleakops.commands.base import BaseCommand
from sleakops.config import BUILD_ENDPOINT


class BuildCommand(BaseCommand):
    """Command class for handling build operations."""

    def execute(
        self,
        project: str,
        branch: str,
        environment: str = None,
        commit: str = None,
        tag: str = None,
        provider: str = None,
        docker_args: str = None,
        wait: bool = False,
    ) -> None:
        """Execute a build command.

        Args:
            project: Project name
            branch: Repository branch
            environment: Environment name (optional)
            commit: Commit hash (optional)
            tag: Tag for the image (optional)
            provider: Provider name (optional)
            docker_args: Docker build arguments (optional)
            wait: Whether to wait for completion
        """
        data = {
            "project_env": {
                "project_name": project,
            },
            "branch": branch,
        }

        self.add_optional_fields(
            data,
            environment=environment,
            commit=commit,
            tag=tag,
            provider=provider,
            docker_args=self.parse_docker_args(docker_args),
        )

        self.api_client.execute_action(BUILD_ENDPOINT, data, wait, "Build")


def create_build_command():
    """Create and configure the build CLI command."""

    @click.command()
    @click.option("-p", "--project", required=True, help="Project name.")
    @click.option("-b", "--branch", required=True, help="Repository branch.")
    @click.option(
        "-e",
        "--environment",
        required=False,
        help=(
            "Environment name to differentiate \
            between projects with the same branch."
        )
    )
    @click.option("-c", "--commit", show_default=True, help="Commit.")
    @click.option("-t", "--tag", help="Tag for the image")
    @click.option(
        "-prov",
        "--provider",
        required=False,
        show_default=True,
        help="Provider name",
    )
    @click.option(
        "--docker-args",
        help=(
            "Docker build arguments in format 'key1=value1,key2=value2'"
        )
    )
    @click.option(
        "-w",
        "--wait",
        is_flag=True,
        default=False,
        show_default=True,
        help="Run build and wait for it to finish.",
    )
    @click.option(
        "-k",
        "--key",
        envvar="SLEAKOPS_KEY",
        help="Sleakops access key. It can be used with this option or \
            get from SLEAKOPS_KEY environment var.",
    )
    def build(
        project,
        branch,
        environment,
        commit,
        tag,
        provider,
        docker_args,
        wait,
        key
    ):
        """Build a project in SleakOps."""
        build_command = BuildCommand(key)
        build_command.execute(
            project=project,
            branch=branch,
            environment=environment,
            commit=commit,
            tag=tag,
            provider=provider,
            docker_args=docker_args,
            wait=wait
        )

    return build
