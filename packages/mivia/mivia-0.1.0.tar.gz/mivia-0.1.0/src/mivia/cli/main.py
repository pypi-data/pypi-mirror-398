"""MiViA CLI application."""

import os
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from mivia.exceptions import MiviaError
from mivia.sync_client import SyncMiviaClient

app = typer.Typer(
    name="mivia",
    help="MiViA (Microstructure Analysis) API client CLI",
    no_args_is_help=True,
)
jobs_app = typer.Typer(help="Job management commands")
report_app = typer.Typer(help="Report generation commands")

app.add_typer(jobs_app, name="jobs")
app.add_typer(report_app, name="report")

console = Console()


def get_client() -> SyncMiviaClient:
    """Get configured client."""
    return SyncMiviaClient()


def handle_error(e: MiviaError) -> None:
    """Handle and display error."""
    rprint(f"[red]Error:[/red] {e.message}")
    raise typer.Exit(1)


# --- Models ---


@app.command()
def models():
    """List available models."""
    try:
        client = get_client()
        result = client.list_models()

        table = Table(title="Available Models")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("Display Name")
        table.add_column("Access")

        for m in result:
            table.add_row(
                str(m.id),
                m.name,
                m.display_name,
                m.access_type.value,
            )

        console.print(table)
    except MiviaError as e:
        handle_error(e)


# --- Customizations ---


@app.command()
def customizations(
    model_id: Annotated[str, typer.Argument(help="Model UUID")],
):
    """List customizations for a model."""
    try:
        client = get_client()
        result = client.get_model_customizations(UUID(model_id))

        if not result:
            rprint(f"[yellow]No customizations available for model {model_id}[/yellow]")
            return

        table = Table(title="Available Customizations")
        table.add_column("ID", style="dim")
        table.add_column("Name (EN)")
        table.add_column("Name (DE)")

        for c in result:
            table.add_row(
                str(c.id),
                c.name.en,
                c.name.de,
            )

        console.print(table)
    except MiviaError as e:
        handle_error(e)


# --- Upload ---


@app.command()
def upload(
    files: Annotated[list[Path], typer.Argument(help="Image files to upload")],
    forced: Annotated[bool, typer.Option("--forced", "-f", help="Bypass quality check")] = False,
):
    """Upload image(s)."""
    try:
        client = get_client()
        forced_list = [forced] * len(files) if forced else None
        result = client.upload_images(files, forced_list)

        table = Table(title="Uploaded Images")
        table.add_column("ID", style="dim")
        table.add_column("Filename")
        table.add_column("Size")
        table.add_column("Validated")

        for img in result:
            size = f"{img.width}x{img.height}" if img.width else "-"
            table.add_row(
                str(img.id),
                img.original_filename,
                size,
                "Yes" if img.validated else "No",
            )

        console.print(table)
    except MiviaError as e:
        handle_error(e)


# --- Images ---


@app.command()
def images():
    """List uploaded images."""
    try:
        client = get_client()
        result = client.list_images()

        table = Table(title="Your Images")
        table.add_column("ID", style="dim")
        table.add_column("Filename")
        table.add_column("Created")
        table.add_column("Validated")

        for img in result:
            table.add_row(
                str(img.id),
                img.original_filename,
                img.created_at.strftime("%Y-%m-%d %H:%M"),
                "Yes" if img.validated else "No",
            )

        console.print(table)
    except MiviaError as e:
        handle_error(e)


# --- Analyze ---


def resolve_customization(
    client: SyncMiviaClient,
    model_id: UUID,
    customization: str | None,
) -> UUID | None:
    """Resolve customization by UUID or name."""
    if not customization:
        return None

    # Try UUID first
    try:
        return UUID(customization)
    except ValueError:
        pass

    # Search by name
    customs = client.get_model_customizations(model_id)
    for c in customs:
        if customization.lower() in (c.name.en.lower(), c.name.de.lower()):
            return c.id

    # Partial match
    for c in customs:
        if customization.lower() in c.name.en.lower() or customization.lower() in c.name.de.lower():
            return c.id

    rprint(f"[red]Error:[/red] Customization '{customization}' not found")
    if customs:
        rprint("[yellow]Available customizations:[/yellow]")
        for c in customs:
            rprint(f"  - {c.name.en} ({c.id})")
    raise typer.Exit(1)


@app.command()
def analyze(
    files: Annotated[list[Path], typer.Argument(help="Image files to analyze")],
    model: Annotated[str, typer.Option("--model", "-m", help="Model UUID")] = None,
    customization: Annotated[str, typer.Option("--customization", "-c", help="Customization UUID or name")] = None,
    list_customizations: Annotated[bool, typer.Option("--list-customizations", "-l", help="List available customizations")] = False,
    no_wait: Annotated[bool, typer.Option("--no-wait", help="Don't wait for completion")] = False,
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="Wait timeout in seconds")] = 300.0,
):
    """Upload images and run analysis."""
    if not model:
        rprint("[red]Error:[/red] --model is required")
        raise typer.Exit(1)

    try:
        client = get_client()
        model_id = UUID(model)

        # List customizations if requested
        if list_customizations:
            customs = client.get_model_customizations(model_id)
            if not customs:
                rprint("[yellow]No customizations available for this model[/yellow]")
            else:
                rprint("[bold]Available customizations:[/bold]")
                for c in customs:
                    rprint(f"  - [cyan]{c.name.en}[/cyan] ({c.id})")
            return

        customization_id = resolve_customization(client, model_id, customization)

        rprint(f"[blue]Uploading {len(files)} file(s)...[/blue]")

        result = client.analyze(
            file_paths=files,
            model_id=model_id,
            customization_id=customization_id,
            wait=not no_wait,
            timeout=timeout,
        )

        table = Table(title="Analysis Results")
        table.add_column("Job ID", style="dim")
        table.add_column("Image")
        table.add_column("Status")
        table.add_column("Has Results")

        for job in result:
            status_color = {
                "CACHED": "green",
                "NEW": "green",
                "PENDING": "yellow",
                "FAILED": "red",
            }.get(job.status.value, "white")

            table.add_row(
                str(job.id),
                job.image,
                f"[{status_color}]{job.status.value}[/{status_color}]",
                "Yes" if job.has_results else "No",
            )

        console.print(table)
    except MiviaError as e:
        handle_error(e)


# --- Jobs Subcommands ---


@jobs_app.command("list")
def jobs_list(
    model: Annotated[str, typer.Option("--model", "-m", help="Filter by model UUID")] = None,
    page: Annotated[int, typer.Option("--page", "-p", help="Page number")] = 1,
    size: Annotated[int, typer.Option("--size", "-s", help="Page size")] = 10,
):
    """List jobs."""
    try:
        client = get_client()
        model_id = UUID(model) if model else None

        result = client.list_jobs(model_id=model_id, page=page, page_size=size)

        table = Table(
            title=f"Jobs (Page {result.pagination.page}/{result.pagination.total_pages})"
        )
        table.add_column("ID", style="dim")
        table.add_column("Image")
        table.add_column("Status")
        table.add_column("Created")

        for job in result.data:
            status_color = {
                "CACHED": "green",
                "NEW": "green",
                "PENDING": "yellow",
                "FAILED": "red",
            }.get(job.status.value, "white")

            table.add_row(
                str(job.id),
                job.image,
                f"[{status_color}]{job.status.value}[/{status_color}]",
                job.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)
        rprint(f"Total: {result.pagination.total} jobs")
    except MiviaError as e:
        handle_error(e)


@jobs_app.command("get")
def jobs_get(
    job_id: Annotated[str, typer.Argument(help="Job UUID")],
):
    """Get job details."""
    try:
        client = get_client()
        job = client.get_job(UUID(job_id))

        rprint(f"[bold]Job ID:[/bold] {job.id}")
        rprint(f"[bold]Image:[/bold] {job.image}")
        rprint(f"[bold]Model ID:[/bold] {job.model_id}")
        rprint(f"[bold]Status:[/bold] {job.status.value}")
        rprint(f"[bold]Has Results:[/bold] {job.has_results}")
        rprint(f"[bold]Created:[/bold] {job.created_at}")

        if job.results:
            rprint(f"\n[bold]Results:[/bold]")
            for i, r in enumerate(job.results):
                rprint(f"  {i + 1}. {r}")
    except MiviaError as e:
        handle_error(e)


@jobs_app.command("wait")
def jobs_wait(
    job_ids: Annotated[list[str], typer.Argument(help="Job UUIDs")],
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="Timeout in seconds")] = 300.0,
    interval: Annotated[float, typer.Option("--interval", "-i", help="Poll interval")] = 2.0,
):
    """Wait for job(s) to complete."""
    try:
        client = get_client()
        uuids = [UUID(jid) for jid in job_ids]

        rprint(f"[blue]Waiting for {len(uuids)} job(s)...[/blue]")

        result = client.wait_for_jobs(uuids, timeout=timeout, poll_interval=interval)

        for job in result:
            status_color = "green" if job.status.value in ("CACHED", "NEW") else "red"
            rprint(f"Job {job.id}: [{status_color}]{job.status.value}[/{status_color}]")
    except MiviaError as e:
        handle_error(e)


# --- Report Subcommands ---


@report_app.command("pdf")
def report_pdf(
    job_ids: Annotated[list[str], typer.Argument(help="Job UUIDs")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output file path")] = Path("report.pdf"),
):
    """Download PDF report."""
    try:
        client = get_client()
        uuids = [UUID(jid) for jid in job_ids]

        rprint(f"[blue]Generating PDF report...[/blue]")
        path = client.download_pdf(uuids, output)
        rprint(f"[green]Saved to:[/green] {path}")
    except MiviaError as e:
        handle_error(e)


@report_app.command("csv")
def report_csv(
    job_ids: Annotated[list[str], typer.Argument(help="Job UUIDs")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output file path")] = Path("report.zip"),
    no_images: Annotated[bool, typer.Option("--no-images", help="Exclude images")] = False,
):
    """Download CSV report (as ZIP)."""
    try:
        client = get_client()
        uuids = [UUID(jid) for jid in job_ids]

        rprint(f"[blue]Generating CSV report...[/blue]")
        path = client.download_csv(uuids, output, include_images=not no_images)
        rprint(f"[green]Saved to:[/green] {path}")
    except MiviaError as e:
        handle_error(e)


# --- Config ---


@app.command()
def config():
    """Show current configuration."""
    api_key = os.environ.get("MIVIA_API_KEY", "")
    base_url = os.environ.get("MIVIA_BASE_URL", "https://app.mivia.ai/api")

    rprint("[bold]Configuration:[/bold]")
    rprint(f"  MIVIA_API_KEY: {'***' + api_key[-4:] if api_key else '[red]Not set[/red]'}")
    rprint(f"  MIVIA_BASE_URL: {base_url}")


if __name__ == "__main__":
    app()
