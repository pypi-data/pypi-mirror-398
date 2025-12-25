import click

from sleakops.commands.base import BaseCommand
from sleakops.config import DEPLOY_ENDPOINT


class DeployCommand(BaseCommand):
    """Command class for handling deploy operations."""

    def execute(
        self,
        project: str,
        env: str,
        build: str = None,
        image: str = "latest",
        tag: str = None,
        provider: str = None,
        wait: bool = False,
    ) -> None:
        """Execute a deploy command.

        Args:
            project: Project name
            env: Environment name
            build: Build ID (optional)
            image: Image tag (default: "latest")
            tag: Tag for the image (optional)
            provider: Provider name (optional)
            wait: Whether to wait for completion
        """
        data = {
            "project_env": {
                "project_name": project,
                "environment_name": env,
            }
        }

        self.add_optional_fields(
            data,
            build=build,
            image=image,
            tag=tag,
            provider=provider,
        )

        self.api_client.execute_action(DEPLOY_ENDPOINT, data, wait, "Deploy")


def create_deploy_command():
    """Create and configure the deploy CLI command."""

    @click.command()
    @click.option("-p", "--project", required=True, help="Project name.")
    @click.option("-e", "--env", required=True, help="Environment.")
    @click.option("-b", "--build", required=False, help="Build id.")
    @click.option(
        "-t",
        "--image",
        default="latest",
        show_default=True,
        help="Image tag.",
    )
    @click.option("--tag", help="Tag for the image")
    @click.option(
        "-prov",
        "--provider",
        required=False,
        show_default=True,
        help="Provider name",
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
    def deploy(
        project,
        env,
        build,
        image,
        tag,
        provider,
        wait,
        key,
    ):
        """Deploy a project in SleakOps."""
        deploy_command = DeployCommand(key)
        deploy_command.execute(
            project=project,
            env=env,
            build=build,
            image=image,
            tag=tag,
            provider=provider,
            wait=wait
        )

    return deploy
