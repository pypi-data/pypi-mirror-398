"""CLI commands for managing LlamaDeploy deployments.

This command group lets you list, create, edit, refresh, and delete deployments.
A deployment points the control plane at your Git repository and deployment file
(e.g., `llama_deploy.yaml`). The control plane pulls your code at the selected
git ref, reads the config, and runs your app.
"""

import asyncio

import click
from llama_deploy.cli.styles import HEADER_COLOR, MUTED_COL, PRIMARY_COL, WARNING
from llama_deploy.core.schema.deployments import (
    DeploymentHistoryResponse,
    DeploymentResponse,
    DeploymentUpdate,
)
from rich import print as rprint
from rich.table import Table
from rich.text import Text

from ..app import app, console
from ..options import global_options, interactive_option


@app.group(
    help="Deploy your app to the cloud.",
    no_args_is_help=True,
)
@global_options
def deployments() -> None:
    """Manage deployments"""
    pass


# Deployments commands
@deployments.command("list")
@global_options
@interactive_option
def list_deployments(interactive: bool) -> None:
    """List deployments for the configured project."""
    from llama_deploy.cli.commands.auth import validate_authenticated_profile

    from ..client import get_project_client

    validate_authenticated_profile(interactive)
    try:
        client = get_project_client()
        deployments = asyncio.run(client.list_deployments())

        if not deployments:
            rprint(
                f"[{WARNING}]No deployments found for project {client.project_id}[/]"
            )
            return

        table = Table(show_edge=False, box=None, header_style=f"bold {HEADER_COLOR}")
        table.add_column("Name", style=PRIMARY_COL)
        table.add_column("Status", style=MUTED_COL)
        table.add_column("URL", style=MUTED_COL)
        table.add_column("Repository", style=MUTED_COL)

        for deployment in deployments:
            name = deployment.id
            status = deployment.status
            repo_url = deployment.repo_url
            gh = "https://github.com/"
            if repo_url.startswith(gh):
                repo_url = "gh:" + repo_url.removeprefix(gh)

            table.add_row(
                name,
                status,
                str(deployment.apiserver_url or ""),
                repo_url,
            )

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@deployments.command("get")
@global_options
@click.argument("deployment_id", required=False)
@interactive_option
def get_deployment(deployment_id: str | None, interactive: bool) -> None:
    """Get details of a specific deployment"""
    from llama_deploy.cli.commands.auth import validate_authenticated_profile

    from ..client import get_project_client
    from ..textual.deployment_monitor import monitor_deployment_screen

    validate_authenticated_profile(interactive)
    try:
        client = get_project_client()

        deployment_id = select_deployment(deployment_id, interactive=interactive)
        if not deployment_id:
            rprint(f"[{WARNING}]No deployment selected[/]")
            return
        if interactive:
            monitor_deployment_screen(deployment_id)
            return

        deployment = asyncio.run(client.get_deployment(deployment_id))

        table = Table(show_edge=False, box=None, header_style=f"bold {HEADER_COLOR}")
        table.add_column("Property", style=MUTED_COL, justify="right")
        table.add_column("Value", style=PRIMARY_COL)

        table.add_row("ID", Text(deployment.id))
        table.add_row("Project ID", Text(deployment.project_id))
        table.add_row("Status", Text(deployment.status))
        table.add_row("Repository", Text(deployment.repo_url))
        table.add_row("Deployment File", Text(deployment.deployment_file_path))
        table.add_row("Git Ref", Text(deployment.git_ref or "-"))
        table.add_row("Last Deployed Commit", Text((deployment.git_sha or "-")[:7]))

        apiserver_url = deployment.apiserver_url
        table.add_row(
            "API Server URL",
            Text(str(apiserver_url) if apiserver_url else "-"),
        )

        secret_names = deployment.secret_names or []
        table.add_row("Secrets", Text("\n".join(secret_names), style="italic"))

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@deployments.command("create")
@global_options
@interactive_option
def create_deployment(
    interactive: bool,
) -> None:
    """Interactively create a new deployment"""
    from llama_deploy.cli.commands.auth import validate_authenticated_profile

    from ..textual.deployment_form import create_deployment_form

    if not interactive:
        raise click.ClickException(
            "This command requires an interactive session. Run in a terminal or provide required arguments explicitly."
        )
    validate_authenticated_profile(interactive)

    # Use interactive creation
    deployment_form = create_deployment_form()
    if deployment_form is None:
        rprint(f"[{WARNING}]Cancelled[/]")
        return

    rprint(
        f"[green]Created deployment: {deployment_form.name} (id: {deployment_form.id})[/green]"
    )


@deployments.command("delete")
@global_options
@click.argument("deployment_id", required=False)
@interactive_option
def delete_deployment(deployment_id: str | None, interactive: bool) -> None:
    """Delete a deployment"""
    from llama_deploy.cli.commands.auth import validate_authenticated_profile

    from ..client import get_project_client
    from ..interactive_prompts.utils import (
        confirm_action,
    )

    validate_authenticated_profile(interactive)
    try:
        client = get_project_client()

        deployment_id = select_deployment(deployment_id, interactive=interactive)
        if not deployment_id:
            rprint(f"[{WARNING}]No deployment selected[/]")
            return

        if interactive:
            if not confirm_action(f"Delete deployment '{deployment_id}'?"):
                rprint(f"[{WARNING}]Cancelled[/]")
                return

        asyncio.run(client.delete_deployment(deployment_id))
        rprint(f"[green]Deleted deployment: {deployment_id}[/green]")

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@deployments.command("edit")
@global_options
@click.argument("deployment_id", required=False)
@interactive_option
def edit_deployment(deployment_id: str | None, interactive: bool) -> None:
    """Interactively edit a deployment"""
    from llama_deploy.cli.commands.auth import validate_authenticated_profile

    from ..client import get_project_client
    from ..textual.deployment_form import edit_deployment_form

    validate_authenticated_profile(interactive)
    try:
        client = get_project_client()

        deployment_id = select_deployment(deployment_id, interactive=interactive)
        if not deployment_id:
            rprint(f"[{WARNING}]No deployment selected[/]")
            return

        # Get current deployment details
        current_deployment = asyncio.run(client.get_deployment(deployment_id))

        # Use the interactive edit form
        updated_deployment = edit_deployment_form(current_deployment)
        if updated_deployment is None:
            rprint(f"[{WARNING}]Cancelled[/]")
            return

        rprint(
            f"[green]Successfully updated deployment: {updated_deployment.name}[/green]"
        )

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@deployments.command("update")
@global_options
@click.argument("deployment_id", required=False)
@click.option(
    "--git-ref",
    help="Reference branch or commit SHA for the deployment. If not provided, the current reference branch and latest commit on it will be used.",
    default=None,
)
@interactive_option
def refresh_deployment(
    deployment_id: str | None, git_ref: str | None, interactive: bool
) -> None:
    """Update the deployment, pulling the latest code from it's branch"""
    from llama_deploy.cli.commands.auth import validate_authenticated_profile

    from ..client import get_project_client

    validate_authenticated_profile(interactive)
    try:
        deployment_id = select_deployment(deployment_id, interactive=interactive)
        if not deployment_id:
            rprint(f"[{WARNING}]No deployment selected[/]")
            return

        # Get current deployment details to show what we're refreshing
        current_deployment = asyncio.run(
            get_project_client().get_deployment(deployment_id)
        )
        deployment_name = current_deployment.name
        old_git_sha = current_deployment.git_sha or ""

        # Create an empty update to force git SHA refresh with spinner
        with console.status(f"Refreshing {deployment_name}..."):
            deployment_update = DeploymentUpdate(
                git_ref=git_ref,
            )
            updated_deployment = asyncio.run(
                get_project_client().update_deployment(
                    deployment_id,
                    deployment_update,
                )
            )

        # Show the git SHA change with short SHAs
        new_git_sha = updated_deployment.git_sha or ""
        old_short = old_git_sha[:7] if old_git_sha else "none"
        new_short = new_git_sha[:7] if new_git_sha else "none"

        if old_git_sha == new_git_sha:
            rprint(f"No changes: already at {new_short}")
        else:
            rprint(f"Updated: {old_short} → {new_short}")

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@deployments.command("history")
@global_options
@click.argument("deployment_id", required=False)
@interactive_option
def show_history(deployment_id: str | None, interactive: bool) -> None:
    """Show release history for a deployment."""
    from llama_deploy.cli.commands.auth import validate_authenticated_profile

    from ..client import project_client_context

    validate_authenticated_profile(interactive)
    try:
        deployment_id = select_deployment(deployment_id, interactive=interactive)
        if not deployment_id:
            rprint(f"[{WARNING}]No deployment selected[/]")
            return

        async def _fetch_history() -> DeploymentHistoryResponse:
            async with project_client_context() as client:
                return await client.get_deployment_history(deployment_id)

        history = asyncio.run(_fetch_history())
        items = history.history
        if not items:
            rprint(f"No history recorded for {deployment_id}")
            return

        table = Table(show_edge=False, box=None, header_style=f"bold {HEADER_COLOR}")
        table.add_column("Released At", style=MUTED_COL)
        table.add_column("Git SHA", style=PRIMARY_COL)
        # newest first
        items_sorted = sorted(
            items,
            key=lambda it: it.released_at,
            reverse=True,
        )
        for item in items_sorted:
            ts = item.released_at.isoformat()
            sha = item.git_sha
            table.add_row(ts, sha)
        console.print(table)
    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@deployments.command("rollback", hidden=True)
@global_options
@click.argument("deployment_id", required=False)
@click.option("--git-sha", required=False, help="Git SHA to roll back to")
@interactive_option
def rollback(deployment_id: str | None, git_sha: str | None, interactive: bool) -> None:
    """Rollback a deployment to a previous git sha."""
    import questionary
    from llama_deploy.cli.commands.auth import validate_authenticated_profile

    from ..client import project_client_context
    from ..interactive_prompts.utils import (
        confirm_action,
    )

    validate_authenticated_profile(interactive)
    try:
        deployment_id = select_deployment(deployment_id, interactive=interactive)
        if not deployment_id:
            rprint(f"[{WARNING}]No deployment selected[/]")
            return

        if not git_sha:
            # If not provided, prompt from history
            async def _fetch_current_and_history() -> tuple[
                DeploymentResponse, DeploymentHistoryResponse
            ]:
                async with project_client_context() as client:
                    current = await client.get_deployment(deployment_id)
                    hist = await client.get_deployment_history(deployment_id)
                    return current, hist

            current_deployment, history = asyncio.run(_fetch_current_and_history())
            current_sha = current_deployment.git_sha or ""

            items = history.history or []
            # Sort newest first
            items_sorted = sorted(items, key=lambda it: it.released_at, reverse=True)
            choices = []
            for it in items_sorted:
                short = it.git_sha[:7]
                suffix = (
                    " [current]" if current_sha and it.git_sha == current_sha else ""
                )
                choices.append(
                    questionary.Choice(
                        title=f"{short}{suffix} ({it.released_at})", value=it.git_sha
                    )
                )
            if not choices:
                rprint(f"[{WARNING}]No history available to rollback[/]")
                return
            git_sha = questionary.select("Select git sha:", choices=choices).ask()
            if not git_sha:
                rprint(f"[{WARNING}]Cancelled[/]")
                return

        if interactive and not confirm_action(
            f"Rollback '{deployment_id}' to {git_sha[:7]}?"
        ):
            rprint(f"[{WARNING}]Cancelled[/]")
            return

        async def _do_rollback() -> DeploymentResponse:
            async with project_client_context() as client:
                return await client.rollback_deployment(deployment_id, git_sha)

        updated = asyncio.run(_do_rollback())
        rprint(
            f"[green]Rollback initiated[/green]: {deployment_id} → {updated.git_sha[:7] if updated.git_sha else 'unknown'}"
        )
    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


def select_deployment(deployment_id: str | None, interactive: bool) -> str | None:
    """
    Select a deployment interactively if ID not provided.
    Returns the selected deployment ID or None if cancelled.

    In non-interactive sessions, returns None if deployment_id is not provided.
    """
    import questionary

    from ..client import get_project_client

    if deployment_id:
        return deployment_id

    # Don't attempt interactive selection in non-interactive sessions
    if not interactive:
        return None
    client = get_project_client()
    deployments = asyncio.run(client.list_deployments())

    if not deployments:
        rprint(f"[{WARNING}]No deployments found for project {client.project_id}[/]")
        return None

    choices = []
    for deployment in deployments:
        name = deployment.name
        deployment_id = deployment.id
        status = deployment.status
        choices.append(
            questionary.Choice(
                title=f"{name} ({deployment_id}) - {status}", value=deployment_id
            )
        )

    return questionary.select("Select deployment:", choices=choices).ask()
