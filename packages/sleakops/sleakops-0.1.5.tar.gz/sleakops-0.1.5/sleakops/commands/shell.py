import click
import subprocess
import sys
import json
import os

from sleakops.commands.base import BaseCommand
from sleakops.config import (
    PROJECT_ENV_ENDPOINT, SERVICE_ENDPOINT, KUBECONFIG_PATH
)


class ShellCommand(BaseCommand):
    """Command class for handling shell operations."""

    def __init__(
        self,
        api_key: str = None,
        use_token_auth: bool = False,
        kubeconfig_path: str = None
    ):
        """Initialize the command with an API client and optional kubeconfig.

        Args:

        Args:
            api_key: The SleakOps API key
            use_token_auth: Whether to use token authentication
            kubeconfig_path: Optional path to kubeconfig file
        """
        super().__init__(api_key=api_key, use_token_auth=use_token_auth)
        self.kubeconfig_path = kubeconfig_path

    def execute(self) -> None:
        """Execute a shell command with interactive selection."""
        if not self._check_kubectl():
            click.echo(
                click.style(
                    "Error: kubectl is not installed or not in PATH",
                    fg="red"
                )
            )
            sys.exit(1)

        # Check and select kubectl context
        if not self._check_kubeconfig_exists():
            sys.exit(1)

        contexts = self._validate_contexts_available()
        self._handle_context_selection(contexts)

        # Get core projects
        click.echo("Fetching core projects...")
        project_envs = self._get_project_envs()

        if not project_envs:
            click.echo("No core projects found")
            sys.exit(1)

        selected_project_env = self._select_project_env(project_envs)

        # Get services for the selected project environment
        click.echo(
            f"\nFetching services for {selected_project_env['name']}..."
        )
        services = self._get_services(selected_project_env['id'])

        if not services:
            click.echo("No services found for this project environment")
            sys.exit(1)

        selected_service = self._select_service(services)
        formatted_service_name = (
            selected_project_env['name'] + '-' + selected_service['name']
        )

        # Get pods for selected service
        namespace = selected_project_env['name']
        click.echo(
            f"\nFetching pods for service '{formatted_service_name}' "
            f"in namespace '{namespace}'..."
        )
        pods = self._get_pods(namespace, formatted_service_name)

        if not pods:
            click.echo("No pods found for this service")
            sys.exit(1)

        selected_pod = self._select_pod(pods)
        containers = self._get_containers(selected_pod, namespace)
        selected_container = self._select_container(containers)
        self._open_shell(selected_pod, namespace, selected_container)

    def _check_kubectl(self) -> bool:
        """Check if kubectl is installed and accessible."""
        try:
            result = subprocess.run(
                ['kubectl', 'version', '--client'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _check_kubeconfig_exists(self) -> bool:
        """Check if kubeconfig file exists."""
        kubeconfig = self.kubeconfig_path or KUBECONFIG_PATH
        if not os.path.exists(kubeconfig):
            click.echo(
                click.style(
                    "No kubeconfig found. Run "
                    "'sleakops get-access-cluster' first.",
                    fg="red"
                )
            )
            return False
        return True

    def _validate_contexts_available(self) -> bool:
        """Validate that contexts are available."""
        contexts = self._get_available_contexts()
        if not contexts:
            click.echo(
                click.style(
                    "No contexts found in kubeconfig. Run "
                    "'sleakops get-access-cluster' first.",
                    fg="red"
                )
            )
            sys.exit(1)
        return contexts

    def _handle_context_selection(self, contexts: list) -> None:
        """Handle the context selection logic."""
        if len(contexts) == 1:
            context_name = contexts[0]['name']
            click.echo(f"Using context: {context_name}")
            return

        current_context = self._get_current_context()

        if current_context:
            click.echo(f"Current context: {current_context}")
            if click.confirm("Do you want to change the context?"):
                selected_context = self._select_context(
                    contexts, current_context
                )
                if selected_context != current_context:
                    self._switch_context(selected_context)
        else:
            selected_context = self._select_context(contexts, None)
            self._switch_context(selected_context)

    def _get_available_contexts(self) -> list:
        """Get list of available kubectl contexts."""
        try:
            cmd = ['kubectl', 'config', 'view', '-o', 'json']
            if self.kubeconfig_path:
                cmd.extend(['--kubeconfig', self.kubeconfig_path])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            contexts_data = json.loads(result.stdout)
            return contexts_data.get('contexts', [])
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            click.echo(f"Error getting contexts: {e}")
            return []

    def _get_current_context(self) -> str:
        """Get current kubectl context."""
        try:
            cmd = ['kubectl', 'config', 'current-context']
            if self.kubeconfig_path:
                cmd.extend(['--kubeconfig', self.kubeconfig_path])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def _select_context(self, contexts: list, current: str) -> str:
        """Show interactive selection for contexts."""
        click.echo("\nAvailable contexts:")
        for i, context in enumerate(contexts, 1):
            context_name = context['name']
            current_marker = " (current)" if context_name == current else ""
            click.echo(
                click.style(
                    f"[{i}] {context_name}{current_marker}",
                    fg="blue"
                )
            )

        choice = click.prompt(
            "Select context",
            type=click.IntRange(1, len(contexts))
        )
        return contexts[choice - 1]['name']

    def _switch_context(self, context_name: str) -> None:
        """Switch to specified kubectl context."""
        try:
            cmd = ['kubectl', 'config', 'use-context', context_name]
            if self.kubeconfig_path:
                cmd.extend(['--kubeconfig', self.kubeconfig_path])
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            click.echo(f"Switched to context: {context_name}")
        except subprocess.CalledProcessError as e:
            click.echo(f"Error switching context: {e}")
            sys.exit(1)

    def _get_project_envs(self) -> list:
        """Get project environments from API and filter for core projects."""
        try:
            return self.api_client.get_resources(PROJECT_ENV_ENDPOINT)
        except Exception as e:
            click.echo(f"Error fetching project environments: {e}")
            sys.exit(1)

    def _select_project_env(self, project_envs: list) -> dict:
        """Show interactive selection for project environments."""
        if len(project_envs) == 1:
            return project_envs[0]

        click.echo("\nSelect a project environment:")
        for i, pe in enumerate(project_envs, 1):
            env_name = pe['environment']['name']
            click.echo(
                click.style(
                    f"[{i}] {pe['project_name']}-{env_name}",
                    fg="blue"
                )
            )

        choice = click.prompt(
            "Choice",
            type=click.IntRange(1, len(project_envs))
        )
        return project_envs[choice - 1]

    def _get_services(self, project_env_id: str) -> list:
        """Get services for a project environment."""
        try:
            return self.api_client.get_resources(
                SERVICE_ENDPOINT,
                {'project_env_id': project_env_id}
            )
        except Exception as e:
            click.echo(f"Error fetching services: {e}")
            sys.exit(1)

    def _select_service(self, services: list) -> dict:
        """Show interactive selection for services."""
        if len(services) == 1:
            return services[0]

        click.echo("\nSelect a service:")
        for i, service in enumerate(services, 1):
            click.echo(
                click.style(
                    f"[{i}] {service['name']}",
                    fg="blue"
                )
            )

        choice = click.prompt(
            "Choice",
            type=click.IntRange(1, len(services))
        )
        return services[choice - 1]

    def _get_pods(self, namespace: str, service_name: str) -> list:
        """Get pods for a service using kubectl."""
        label_selectors = [
            f"app={service_name}",
            f"service={service_name}",
            f"name={service_name}"
        ]

        for selector in label_selectors:
            try:
                cmd = [
                    'kubectl', 'get', 'pods', '-n', namespace,
                    '-l', selector, '-o', 'json'
                ]
                if self.kubeconfig_path:
                    cmd.extend(['--kubeconfig', self.kubeconfig_path])
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                pods_data = json.loads(result.stdout)
                pods = pods_data.get('items', [])
                if pods:
                    return [pod['metadata']['name'] for pod in pods]
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                continue

        # If no pods found with labels, get all pods and filter by name
        try:
            cmd = ['kubectl', 'get', 'pods', '-n', namespace, '-o', 'json']
            if self.kubeconfig_path:
                cmd.extend(['--kubeconfig', self.kubeconfig_path])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            pods_data = json.loads(result.stdout)
            all_pods = pods_data.get('items', [])
            # Filter pods that contain the service name
            filtered_pods = [
                pod['metadata']['name'] for pod in all_pods
                if service_name in pod['metadata']['name']
            ]
            return filtered_pods
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            click.echo(f"Error getting pods: {e}")
            return []

    def _select_pod(self, pods: list) -> str:
        """Show interactive selection for pods."""
        if len(pods) == 1:
            return pods[0]

        click.echo("\nSelect a pod:")
        for i, pod in enumerate(pods, 1):
            click.echo(
                click.style(
                    f"[{i}] {pod}",
                    fg="blue"
                )
            )

        choice = click.prompt(
            "Choice",
            type=click.IntRange(1, len(pods))
        )
        return pods[choice - 1]

    def _get_containers(self, pod_name: str, namespace: str) -> list:
        """Get containers for a pod using kubectl."""
        try:
            cmd = [
                'kubectl', 'get', 'pod', pod_name, '-n', namespace,
                '-o', 'jsonpath={.spec.containers[*].name}'
            ]
            if self.kubeconfig_path:
                cmd.extend(['--kubeconfig', self.kubeconfig_path])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            containers = result.stdout.strip().split()
            return containers if containers else ['default']
        except subprocess.CalledProcessError as e:
            click.echo(f"Error getting containers: {e}")
            return ['default']

    def _select_container(self, containers: list) -> str:
        """Show interactive selection for containers if multiple."""
        if len(containers) == 1:
            return containers[0]

        click.echo("\nSelect a container:")
        for i, container in enumerate(containers, 1):
            click.echo(
                click.style(
                    f"[{i}] {container}",
                    fg="blue"
                )
            )

        choice = click.prompt(
            "Choice",
            type=click.IntRange(1, len(containers))
        )
        return containers[choice - 1]

    def _open_shell(
        self, pod_name: str, namespace: str, container: str
    ) -> None:
        """Open interactive shell in the pod."""
        click.echo(
            f"\nOpening shell in pod '{pod_name}', container '{container}'..."
            "\nTo leave the shell you have to execute 'exit'"
        )

        # Try bash first, then sh
        shells = ['/bin/bash', '/bin/ash', '/bin/sh']

        for shell in shells:
            try:
                # First check if shell exists
                check_cmd = [
                    'kubectl', 'exec', pod_name, '-n', namespace,
                    '-c', container, '--', 'test', '-f', shell
                ]
                if self.kubeconfig_path:
                    check_cmd.insert(2, '--kubeconfig')
                    check_cmd.insert(3, self.kubeconfig_path)
                check_result = subprocess.run(
                    check_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL
                )

                # If shell exists, try to execute it interactively
                if check_result.returncode == 0:
                    cmd = [
                        'kubectl', 'exec', '-it', pod_name, '-n', namespace,
                        '-c', container, '--', shell
                    ]
                    if self.kubeconfig_path:
                        cmd.insert(2, '--kubeconfig')
                        cmd.insert(3, self.kubeconfig_path)
                    command = subprocess.run(cmd)
                    if command.returncode == 0:
                        return
            except (OSError, subprocess.CalledProcessError):
                continue

        # If all shells fail, try without specifying shell
        try:
            cmd = [
                'kubectl', 'exec', '-it', pod_name, '-n', namespace,
                '-c', container
            ]
            if self.kubeconfig_path:
                cmd.insert(2, '--kubeconfig')
                cmd.insert(3, self.kubeconfig_path)
            subprocess.run(cmd)
        except OSError as e:
            click.echo(f"Error opening shell: {e}")
            sys.exit(1)


def create_shell_command():
    """Create and configure the shell CLI command."""

    @click.command()
    @click.option(
        "-k",
        '--kubeconfig',
        type=click.Path(
            exists=True, file_okay=True, dir_okay=False, resolve_path=True
        ),
        help='Path to kubeconfig file (default: ~/.kube/config)'
    )
    def shell(kubeconfig):
        """Open an interactive shell in a Kubernetes pod for a core project."""
        shell_command = ShellCommand(
            use_token_auth=True, kubeconfig_path=kubeconfig
        )
        shell_command.execute()

    return shell
