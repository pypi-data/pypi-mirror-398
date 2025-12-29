import typer
from pathlib import Path
from typing import Callable, TypeVar, Any
from service_forge.sft.util.logger import log_error, log_info
from service_forge.sft.config.sf_metadata import load_metadata, SfMetadata

T = TypeVar('T')

def assert_dir_exists(path: Path) -> None:
    if not path.exists():
        log_error(f"Directory does not exist: {path}")
        raise typer.Exit(1)
    if not path.is_dir():
        log_error(f"Path is not a directory: {path}")
        raise typer.Exit(1)
    log_info(f"Directory exists: {path}")

def assert_file_exists(path: Path) -> None:
    if not path.exists():
        log_error(f"File does not exist: {path}")
        raise typer.Exit(1)
    if not path.is_file():
        log_error(f"Path is not a file: {path}")
        raise typer.Exit(1)
    log_info(f"File exists: {path}")
