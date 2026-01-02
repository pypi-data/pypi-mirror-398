"""CLI Chat Application Entry Point."""

import json
import os
import subprocess

import typer
from rich import box
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from ai_term.cli.ui.app import ChatApp

app = typer.Typer(
    help="AI-Term: A modern, voice-enabled AI terminal assistant.",
    add_completion=False,
    invoke_without_command=True,
)


def force_exit():
    """Force exit on interpreter shutdown."""
    os._exit(0)


def check_docker_compose():
    """Check if docker compose is available."""
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_compose_file_path() -> str:
    """Get the path to the bundled docker-compose.yml file."""
    try:
        from importlib.resources import files
        resource_path = files("ai_term.cli.resources").joinpath("docker-compose.yml")
        # For Python 3.9+, we can use as_file for a context manager
        # but for simplicity, we'll convert to string path
        return str(resource_path)
    except Exception:
        # Fallback: check current directory
        if os.path.exists("docker-compose.yml"):
            return os.path.abspath("docker-compose.yml")
        elif os.path.exists("docker-compose.yaml"):
            return os.path.abspath("docker-compose.yaml")
        return ""


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    AI-Term CLI Entry Point.
    
    Runs the main TUI application by default.
    Use 'start' to run background services.
    Use 'status' to check service status.
    """
    if ctx.invoked_subcommand is None:
        # Default behavior: Run the TUI
        tui_app = ChatApp()
        try:
            tui_app.run()
        except KeyboardInterrupt:
            pass
        finally:
            force_exit()


@app.command()
def start(
    build: Annotated[
        bool, 
        typer.Option("--build", help="Force rebuild of Docker images.")
    ] = False,
    detach: Annotated[
        bool, 
        typer.Option("--detach", "-d", help="Run in detached mode.")
    ] = True
):
    """
    Start the backend services (STT/TTS) using Docker Compose.
    
    Uses the bundled docker-compose.yml file automatically.
    Pass --build to force rebuild of images.
    """
    if not check_docker_compose():
        typer.secho(
            "Error: 'docker compose' is not available.", 
            fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    compose_file = get_compose_file_path()
    if not compose_file:
        typer.secho(
            "Error: Could not locate docker-compose.yml file.",
            fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    cmd = ["docker", "compose", "-f", compose_file, "up"]
    if detach:
        cmd.append("-d")

    if build:
        cmd.append("--build")
    
    typer.echo("Starting services...")
    try:
        subprocess.run(cmd, check=True)
        typer.secho("Services started successfully.", fg=typer.colors.GREEN)
    except subprocess.CalledProcessError:
        typer.secho("Failed to start services.", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def status():
    """
    Check the status of backend services.
    """
    if not check_docker_compose():
        typer.secho(
            "Error: 'docker compose' is not available.", 
            fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    compose_file = get_compose_file_path()
    if not compose_file:
        typer.secho(
            "Error: Could not locate docker-compose.yml file.",
            fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    try:
        result = subprocess.run(
            ["docker", "compose", "-f", compose_file, "ps", "--format", "json"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Parse JSON output (one JSON object per line)
        services = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    services.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        if not services:
            typer.secho("No services are currently running.", fg=typer.colors.YELLOW)
            return

        console = Console()
        table = Table(title="AI-Term Services Status", box=box.ROUNDED)

        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("State", style="green")
        table.add_column("Status", style="magenta")
        table.add_column("Ports", style="yellow")

        for service in services:
            # Extract relevant fields
            name = service.get("Service", "Unknown")
            state = service.get("State", "Unknown")
            status = service.get("Status", "Unknown")
            
            # Format ports
            ports = service.get("Publishers", [])
            port_str = ""
            if ports:
                port_list = []
                for p in ports:
                    if isinstance(p, dict):
                         # Handle list of dicts format from newer docker compose versions
                         url = p.get("URL", "0.0.0.0")
                         pub_port = p.get("PublishedPort", "")
                         target_port = p.get("TargetPort", "")
                         if pub_port:
                             port_list.append(
                                 f"{url}:{pub_port}->{target_port}"
                             )
                port_str = ", ".join(port_list)
            
            # Fallback for older formats or if Publishers structure is different
            if not port_str:
                 port_str = service.get("Ports", "")

            # Colorize state
            state_style = "green" if state.lower() == "running" else "red"
            
            table.add_row(
                name,
                f"[{state_style}]{state}[/{state_style}]",
                status,
                port_str
            )

        console.print(table)

    except subprocess.CalledProcessError:
        typer.secho("Failed to check status. Is docker running?", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
         typer.secho(f"An unexpected error occurred: {e}", fg=typer.colors.RED)
         raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
