from pathlib import Path

from rich.console import Console
from rich.table import Table

from service_forge.sft.util.logger import log_error, log_info
from service_forge.sft.file.sft_file_manager import sft_file_manager

def list_tars() -> None:
    tar_files = sft_file_manager.load_tars()
    
    if not tar_files:
        log_info("No tar files found.")
        return
    
    console = Console()
    table = Table(title="Service Tar Files", show_header=True, header_style="bold magenta")
    table.add_column("Project", style="cyan", no_wrap=True)
    table.add_column("Version", style="cyan", no_wrap=True)
    table.add_column("File Name", style="cyan", no_wrap=True)
    table.add_column("Size", justify="right", style="green")
    table.add_column("Modified Time", style="yellow")
    
    for tar_file in tar_files:
        table.add_row(tar_file.project_name, tar_file.version, tar_file.path.name, tar_file._format_size(), tar_file._format_modified_time())
    
    console.print(table)


def _format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def _format_time(timestamp: float) -> str:
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

