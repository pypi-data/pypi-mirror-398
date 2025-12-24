import typer
import sys
import platform
from rich.console import Console
from rich.panel import Panel
from hypella import __version__

app = typer.Typer(
    name="hypella",
    help="CLI tool for the Hypella execution layer",
    add_completion=False,
)
console = Console()

def version_callback(value: bool):
    if value:
        console.print(f"Hypella CLI Version: [bold cyan]{__version__}[/bold cyan]")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=version_callback,
        is_eager=True,
    )
):
    """
    Hypella CLI - Your gateway to algorithmic trading on Hyperliquid.
    """
    pass

@app.command()
def doctor():
    """
    Check your environment health and configuration.
    """
    python_version = sys.version.split()[0]
    os_info = f"{platform.system()} {platform.release()}"
    
    info_text = (
        f"[bold]Hypella Version:[/bold] {__version__}\n"
        f"[bold]Python Version:[/bold] {python_version}\n"
        f"[bold]OS:[/bold] {os_info}\n\n"
        "All systems nominal. Ready for ignition."
    )
    
    console.print(Panel(info_text, title="[bold green]Hypella Doctor[/bold green]", expand=False))

if __name__ == "__main__":
    app()
