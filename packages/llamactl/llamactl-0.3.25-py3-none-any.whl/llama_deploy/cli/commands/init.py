from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

import click
from click.exceptions import Exit
from llama_deploy.cli.app import app
from llama_deploy.cli.options import (
    global_options,
    interactive_option,
)
from llama_deploy.cli.styles import HEADER_COLOR_HEX
from rich import print as rprint
from rich.text import Text

if TYPE_CHECKING:
    pass


_ClickPath = getattr(click, "Path")


@app.command()
@click.option(
    "--update",
    is_flag=True,
    help="Instead of creating a new app, update the current app to the latest version. Other options will be ignored.",
)
@click.option(
    "--template",
    help="The template to use for the new app",
)
@click.option(
    "--dir",
    help="The directory to create the new app in",
    type=_ClickPath(
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
@click.option(
    "--force",
    is_flag=True,
    help="Force overwrite the directory if it exists",
)
@global_options
@interactive_option
def init(
    update: bool,
    template: str | None,
    dir: Path | None,
    force: bool,
    interactive: bool,
) -> None:
    """Create a new app repository from a template"""
    if update:
        _update()
    else:
        _create(template, dir, force, interactive)


def _create(
    template: str | None, dir: Path | None, force: bool, interactive: bool
) -> None:
    import questionary

    @dataclass
    class TemplateOption:
        id: str
        name: str
        description: str
        source: GithubTemplateRepo
        llama_cloud: bool

    @dataclass
    class GithubTemplateRepo:
        url: str

    ui_options = [
        TemplateOption(
            id="basic-ui",
            name="Basic UI",
            description="A basic starter workflow with a React Vite UI",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-basic-ui"
            ),
            llama_cloud=False,
        ),
        TemplateOption(
            id="showcase",
            name="Showcase",
            description="A collection of workflow and UI patterns to build LlamaDeploy apps",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-showcase"
            ),
            llama_cloud=False,
        ),
        TemplateOption(
            id="document-qa",
            name="Document Question & Answer",
            description="Upload documents and run question answering through a React UI",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-document-qa"
            ),
            llama_cloud=True,
        ),
        TemplateOption(
            id="extraction-review",
            name="Extraction Agent with Review UI",
            description="Extract data from documents using a custom schema and Llama Cloud. Includes a UI to review and correct the results",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-data-extraction"
            ),
            llama_cloud=True,
        ),
        TemplateOption(
            id="classify-extract-sec",
            name="SEC Insights",
            description="Upload SEC filings, classifying them to the appropriate type and extracting key information",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-classify-extract-sec"
            ),
            llama_cloud=True,
        ),
        TemplateOption(
            id="extract-reconcile-invoice",
            name="Invoice Extraction & Reconciliation",
            description="Extract and reconcile invoice data against contracts",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-extract-reconcile-invoice"
            ),
            llama_cloud=True,
        ),
    ]

    headless_options = [
        TemplateOption(
            id="basic",
            name="Basic Workflow",
            description="A base example that showcases usage patterns for workflows",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-basic"
            ),
            llama_cloud=False,
        ),
        TemplateOption(
            id="document_parsing",
            name="Document Parser",
            description="A workflow that, using LlamaParse, parses unstructured documents and returns their raw text content",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-document-parsing"
            ),
            llama_cloud=True,
        ),
        TemplateOption(
            id="human_in_the_loop",
            name="Human in the Loop",
            description="A workflow showcasing how to use human in the loop with LlamaIndex workflows",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-human-in-the-loop"
            ),
            llama_cloud=False,
        ),
        TemplateOption(
            id="invoice_extraction",
            name="Invoice Extraction",
            description="A workflow that, given an invoice, extracts several key details using LlamaExtract",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-invoice-extraction"
            ),
            llama_cloud=True,
        ),
        TemplateOption(
            id="rag",
            name="RAG",
            description="A workflow that embeds, indexes and queries your documents on the fly, providing you with a simple RAG pipeline",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-rag"
            ),
            llama_cloud=False,
        ),
        TemplateOption(
            id="web_scraping",
            name="Web Scraping",
            description="A workflow that, given several urls, scrapes and summarizes their content using Google's Gemini API",
            source=GithubTemplateRepo(
                url="https://github.com/run-llama/template-workflow-web-scraping"
            ),
            llama_cloud=False,
        ),
    ]

    # Initialize git repository if git is available
    has_git = False
    git_initialized = False
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        has_git = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # git is not available or broken; continue without git
        has_git = False

    if not has_git:
        rprint(
            "git is required to initialize a template. Make sure you have it installed and available in your PATH."
        )
        raise Exit(1)

    if template is None and interactive:
        rprint(
            "[bold]Select a template to start from.[/bold] Either with javascript frontend UI, or just a python workflow that can be used as an API."
        )
        template = questionary.select(
            "",
            choices=[questionary.Separator("------------ With UI -------------")]
            + [
                questionary.Choice(title=o.name, value=o.id, description=o.description)
                for o in ui_options
            ]
            + [
                questionary.Separator(" "),
                questionary.Separator("--- Headless Workflows (No UI) ---"),
            ]
            + [
                questionary.Choice(title=o.name, value=o.id, description=o.description)
                for o in headless_options
            ],
            style=questionary.Style(
                [
                    ("separator", f"fg:{HEADER_COLOR_HEX}"),
                ]
            ),
        ).ask()
    if template is None:
        options = [o.id for o in ui_options + headless_options]
        rprint(
            Text(
                f"No template selected. Select a template or pass a template name with --template <{'|'.join(options)}>"
            )
        )
        raise Exit(1)
    if dir is None:
        if interactive:
            dir_str = questionary.text(
                "Enter the directory to create the new app in", default=template
            ).ask()
            if dir_str:
                dir = Path(dir_str)
            else:
                return
        else:
            rprint(f"[yellow]No directory provided. Defaulting to {template}[/]")
            dir = Path(template)

    resolved_template: TemplateOption | None = next(
        (o for o in ui_options + headless_options if o.id == template), None
    )
    if resolved_template is None:
        rprint(f"Template {template} not found")
        raise Exit(1)
    if dir.exists():
        is_ok = force or (
            interactive
            and questionary.confirm("Directory exists. Overwrite?", default=False).ask()
        )

        if not is_ok:
            rprint(
                f"[yellow]Try again with another directory or pass --force to overwrite the existing directory '{str(dir)}'[/]"
            )
            raise Exit(1)
        else:
            shutil.rmtree(dir, ignore_errors=True)

    # Import copier lazily at call time to keep CLI startup light while still
    # allowing tests to patch ``copier.run_copy`` directly.
    import copier

    copier.run_copy(
        resolved_template.source.url,
        dir,
        quiet=True,
        defaults=not interactive,
    )

    # Change to the new directory and initialize git repo
    original_cwd = Path.cwd()
    os.chdir(dir)

    try:
        # Dump in a bunch of docs for AI agents (best-effort)
        docs_downloaded = asyncio.run(
            _download_and_write_agents_md(
                include_llama_cloud=resolved_template.llama_cloud
            )
        )
        # Create symlink for Claude.md to point to AGENTS.md
        if docs_downloaded:
            for alternate in [
                "CLAUDE.md",
                "GEMINI.md",
            ]:  # don't support AGENTS.md (yet?)
                claude_path = Path(alternate)  # not supported yet
                agents_path = Path("AGENTS.md")
                if agents_path.exists() and not claude_path.exists():
                    claude_path.symlink_to("AGENTS.md")

        # Initialize a git repo unless we're already inside one.
        if has_git:
            # Detect whether the target directory is already inside a git work tree
            inside_existing_repo = False
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--is-inside-work-tree"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                inside_existing_repo = result.stdout.strip().lower() == "true"
            except (subprocess.CalledProcessError, FileNotFoundError):
                inside_existing_repo = False

            if inside_existing_repo:
                # Do not create a nested repo; user likely wants this within the parent repo
                rprint(
                    "[yellow]Detected an existing Git repository in a parent directory; skipping git initialization for this app.[/]"
                )
                # Treat as initialized for purposes of what instructions to show later
                git_initialized = True
            else:
                try:
                    subprocess.run(["git", "init"], check=True, capture_output=True)
                    subprocess.run(["git", "add", "."], check=True, capture_output=True)
                    subprocess.run(
                        ["git", "commit", "-m", "Initial commit"],
                        check=True,
                        capture_output=True,
                    )
                    git_initialized = True
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    # Extract a short error message if present
                    err_msg = ""
                    if isinstance(e, subprocess.CalledProcessError):
                        stderr_bytes = e.stderr or b""
                        if isinstance(stderr_bytes, (bytes, bytearray)):
                            try:
                                stderr_text = stderr_bytes.decode("utf-8", "ignore")
                            except Exception:
                                stderr_text = ""
                        else:
                            stderr_text = str(stderr_bytes)
                        if stderr_text.strip():
                            err_msg = stderr_text.strip().split("\n")[-1]
                    elif isinstance(e, FileNotFoundError):
                        err_msg = "git executable not found"

                    rprint("")
                    rprint("⚠️  [bold]Skipping git initialization due to an error.[/]")
                    if err_msg:
                        rprint(f"    {err_msg}")
                    rprint("    You can initialize it manually:")
                    rprint(
                        "      git init && git add . && git commit -m 'Initial commit'"
                    )
                    rprint("")
    finally:
        os.chdir(original_cwd)

    # If git is not available at all, let the user know how to proceed
    if not has_git:
        rprint("")
        rprint("⚠️  [bold]Skipping git initialization due to an error.[/]")
        rprint("    git executable not found")
        rprint("    You can initialize it manually:")
        rprint("      git init && git add . && git commit -m 'Initial commit'")
        rprint("")

    rprint(
        f"Successfully created [blue]{dir}[/] using the [blue]{resolved_template.name}[/] template! 🎉 🦙 💾"
    )
    rprint("")
    rprint("[bold]To run locally:[/]")
    rprint(f"    [orange3]cd[/] {dir}")
    rprint("    [orange3]uvx[/] llamactl serve")
    rprint("")
    rprint("[bold]To deploy:[/]")
    # Only show manual git init steps if repository failed to initialize earlier
    if not git_initialized:
        rprint("    [orange3]git[/] init")
        rprint("    [orange3]git[/] add .")
        rprint("    [orange3]git[/] commit -m 'Initial commit'")
        rprint("")
    rprint("[dim](Create a new repo and add it as a remote)[/]")
    rprint("")
    rprint("    [orange3]git[/] remote add origin <your-repo-url>")
    rprint("    [orange3]git[/] push -u origin main")
    rprint("")
    # rprint("  [orange3]uvx[/] llamactl login")
    rprint("    [orange3]uvx[/] llamactl deploy create")
    rprint("")


def _update() -> None:
    """Update the app to the latest version"""
    try:
        # Import copier lazily so the init command remains lightweight when
        # unused, while tests can patch ``copier.run_update`` directly.
        import copier

        copier.run_update(
            overwrite=True,
            skip_answered=True,
            quiet=True,
        )
    except Exception as e:  # scoped to copier errors; type opaque here
        rprint(f"{e}")
        raise Exit(1)

    # Check git status and warn about conflicts
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        )

        if result.stdout.strip():
            conflicted_files = []
            modified_files = []

            for line in result.stdout.strip().split("\n"):
                status = line[:2]
                filename = line[3:]

                if "UU" in status or "AA" in status or "DD" in status:
                    conflicted_files.append(filename)
                elif status.strip():
                    modified_files.append(filename)

            if conflicted_files:
                rprint("")
                rprint("⚠️  [bold]Files with conflicts detected:[/]")
                for file in conflicted_files:
                    rprint(f"    {file}")
                rprint("")
                rprint(
                    "Please manually resolve conflicts with a merge editor before proceeding."
                )

    except (subprocess.CalledProcessError, FileNotFoundError):
        # Git not available or not in a git repo - continue silently
        pass


async def _download_and_write_agents_md(include_llama_cloud: bool) -> bool:
    """Fetch a small set of reference docs and write AGENTS.md.

    Replaces the previous vibe-llama usage with direct HTTP downloads.

    Returns True if any documentation was fetched, False otherwise.
    """
    from vibe_llama_core.docs import get_agent_rules
    from vibe_llama_core.docs.utils import LibraryName

    selected_services: list[str] = [
        "LlamaDeploy",
        "LlamaIndex",
        "llama-index-workflows",
    ]
    if include_llama_cloud:
        selected_services.append("LlamaCloud Services")

    downloads = 0

    for service in selected_services:
        try:
            await get_agent_rules(
                agent="OpenAI Codex CLI",
                service=cast(LibraryName, service),
                overwrite_files=False,
                verbose=False,
            )
        except Exception:
            rprint(f"[yellow]Failed to fetch documentation for {service}, skipping[/]")
        else:
            downloads += 1

    return downloads > 0
