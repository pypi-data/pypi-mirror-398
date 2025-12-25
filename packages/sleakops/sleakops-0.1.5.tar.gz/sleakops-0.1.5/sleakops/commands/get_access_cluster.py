import click
import sys
import os
import yaml

from sleakops.commands.base import BaseCommand
from sleakops.config import (
    CLUSTER_ENDPOINT, KUBECONFIG_PATH
)


class GetAccessClusterCommand(BaseCommand):
    """Command class for handling cluster access operations."""

    def execute(self) -> None:
        """Execute cluster access configuration."""
        click.echo("Fetching available clusters...")
        clusters = self._get_clusters()

        if not clusters:
            click.echo("No clusters found")
            sys.exit(1)

        # Select cluster
        selected_cluster = self._select_cluster(clusters)
        cluster_id = selected_cluster['id']
        cluster_name = selected_cluster.get(
            'name', f'cluster-{cluster_id}'
        )

        # Get kubeconfig from API
        click.echo("Fetching kubeconfig...")
        kubeconfig_content = self._get_kubeconfig(cluster_id)

        # Prompt for AWS credentials
        click.echo(f"\nConfiguring access for cluster: {cluster_name}")
        aws_credentials = self._prompt_aws_credentials()

        # Insert AWS credentials
        kubeconfig_with_credentials = self._insert_aws_credentials(
            kubeconfig_content,
            aws_credentials['access_key_id'],
            aws_credentials['secret_access_key']
        )

        # Save kubeconfig
        self._save_kubeconfig(kubeconfig_with_credentials)

        click.echo(
            click.style(
                f"Successfully configured access to cluster "
                f"'{cluster_name}'\n"
                f"The kubeconfig file has been saved at: {KUBECONFIG_PATH}",
                fg="green"
            )
        )

    def _get_clusters(self) -> list:
        """Get clusters from API."""
        try:
            return self.api_client.get_resources(CLUSTER_ENDPOINT)
        except Exception as e:
            click.echo(f"Error fetching clusters: {e}")
            sys.exit(1)

    def _select_cluster(self, clusters: list) -> dict:
        """Show interactive selection for clusters."""
        if len(clusters) == 1:
            return clusters[0]

        click.echo("\nSelect a cluster:")
        for i, cluster in enumerate(clusters, 1):
            cluster_name = cluster.get(
                'name', f'cluster-{cluster.get("id", "unknown")}'
            )
            click.echo(
                click.style(
                    f"[{i}] {cluster_name}",
                    fg="blue"
                )
            )

        choice = click.prompt(
            "Choice",
            type=click.IntRange(1, len(clusters))
        )
        return clusters[choice - 1]

    def _prompt_aws_credentials(self) -> dict:
        """Prompt user for AWS credentials."""
        click.echo("\nAWS credentials are required to access the cluster.")

        access_key_id = click.prompt(
            "AWS Access Key ID",
            type=str
        )

        secret_access_key = click.prompt(
            "AWS Secret Access Key",
            hide_input=True,
            type=str
        )

        return {
            'access_key_id': access_key_id,
            'secret_access_key': secret_access_key
        }

    def _get_kubeconfig(self, cluster_id: str) -> str:
        """Get kubeconfig from API."""
        try:
            endpoint = f"{CLUSTER_ENDPOINT}{cluster_id}/kube-config/"
            return self.api_client.get_resources_from_console(
                endpoint
            )
        except Exception as e:
            click.echo(f"Error fetching kubeconfig: {e}")
            sys.exit(1)

    def _insert_aws_credentials(
        self,
        kubeconfig_content: str,
        aws_access_key_id: str,
        aws_secret_access_key: str
    ) -> str:
        """Insert AWS credentials into kubeconfig content."""
        kubeconfig_with_credentials = kubeconfig_content.replace(
            '<INSERT_AWS_ACCESS_KEY_ID>',
            aws_access_key_id
        ).replace(
            '<INSERT_AWS_SECRET_ACCESS_KEY>',
            aws_secret_access_key
        )

        return kubeconfig_with_credentials

    def _save_kubeconfig(self, kubeconfig_content: str) -> None:
        """Save kubeconfig to file, merging with existing if present."""
        kube_dir = os.path.dirname(KUBECONFIG_PATH)
        os.makedirs(kube_dir, exist_ok=True)

        try:
            new_kubeconfig = yaml.safe_load(kubeconfig_content)
        except yaml.YAMLError as e:
            click.echo(f"Error parsing kubeconfig: {e}")
            sys.exit(1)

        if os.path.exists(KUBECONFIG_PATH):
            try:
                with open(KUBECONFIG_PATH, 'r') as f:
                    existing_content = f.read()
                existing_kubeconfig = yaml.safe_load(existing_content)

                new_kubeconfig = self._merge_kubeconfigs(
                    existing_kubeconfig,
                    new_kubeconfig
                )
            except (yaml.YAMLError, IOError) as e:
                click.echo(
                    click.style(
                        f"Warning: Could not merge with existing kubeconfig: "
                        f"{e}",
                        fg="yellow"
                    )
                )

        try:
            with open(KUBECONFIG_PATH, 'w') as f:
                yaml.dump(new_kubeconfig, f, default_flow_style=False)
            os.chmod(KUBECONFIG_PATH, 0o600)

        except IOError as e:
            click.echo(f"Error saving kubeconfig: {e}")
            sys.exit(1)

    def _merge_kubeconfigs(self, existing: dict, new: dict) -> dict:
        """Merge two kubeconfig dictionaries."""
        merged = existing.copy()

        # Merge clusters
        if 'clusters' in new:
            if 'clusters' not in merged:
                merged['clusters'] = []

            # Add new clusters that don't already exist
            existing_cluster_names = {c['name'] for c in merged['clusters']}
            for cluster in new['clusters']:
                if cluster['name'] not in existing_cluster_names:
                    merged['clusters'].append(cluster)

        # Merge contexts
        if 'contexts' in new:
            if 'contexts' not in merged:
                merged['contexts'] = []

            # Add new contexts that don't already exist
            existing_context_names = {c['name'] for c in merged['contexts']}
            for context in new['contexts']:
                if context['name'] not in existing_context_names:
                    merged['contexts'].append(context)

        # Merge users
        if 'users' in new:
            if 'users' not in merged:
                merged['users'] = []

            # Add new users that don't already exist
            existing_user_names = {u['name'] for u in merged['users']}
            for user in new['users']:
                if user['name'] not in existing_user_names:
                    merged['users'].append(user)

        # Set current context to the new one
        if 'current-context' in new:
            merged['current-context'] = new['current-context']

        return merged


def create_get_access_cluster_command():
    """Create and configure the get-access-cluster CLI command."""

    @click.command()
    def get_access_cluster():
        """Configure access to a Kubernetes cluster."""
        get_access_cluster_command = GetAccessClusterCommand(
            use_token_auth=True
        )
        get_access_cluster_command.execute()

    return get_access_cluster
