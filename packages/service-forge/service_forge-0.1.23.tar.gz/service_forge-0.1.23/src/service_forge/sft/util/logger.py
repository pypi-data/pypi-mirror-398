from rich.console import Console
from typing import Any

console = Console()

def log_error(message: str, **kwargs: Any) -> None:
    console.print(f"[red]{message}[/red]", **kwargs)

def log_info(message: str, **kwargs: Any) -> None:
    console.print(f"{message}", **kwargs)

def log_success(message: str, **kwargs: Any) -> None:
    console.print(f"[green]{message}[/green]", **kwargs)

def log_warning(message: str, **kwargs: Any) -> None:
    console.print(f"[yellow]{message}[/yellow]", **kwargs)