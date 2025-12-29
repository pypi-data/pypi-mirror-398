from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from service_forge.sft.config.sft_config import SftConfig
from service_forge.sft.util.logger import log_error, log_info, log_success, log_warning
from service_forge.sft.config.sft_config import sft_config

def list_config() -> None:
    try:
        console = Console()
        
        table = Table(title="SFT Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Description", style="yellow")
        
        # Automatically add rows for all config items
        config_dict = sft_config.to_dict()
        for key, value in sorted(config_dict.items()):
            description = SftConfig.CONFIG_DESCRIPTIONS.get(key, "No description available")
            table.add_row(key, str(value), description)
        
        console.print(table)
        console.print(f"\n[dim]Config file location: {sft_config.config_file_path}[/dim]")
    except Exception as e:
        log_error(f"Failed to load config: {e}")
        raise typer.Exit(1)

def get_config(key: str) -> None:
    try:
        value = sft_config.get(key)
        
        if value is None:
            log_error(f"Config key '{key}' not found")
            log_info("Available keys: config_root, sft_file_root, k8s_namespace")
            raise typer.Exit(1)
        
        log_info(f"{key} = {value}")
    except ValueError as e:
        log_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        log_error(f"Failed to get config: {e}")
        raise typer.Exit(1)

def set_config(key: str, value: str) -> None:
    try:
        current_value = sft_config.get(key)
        if current_value is None:
            log_error(f"Unknown config key: {key}")
            log_info("Available keys: config_root, sft_file_root, k8s_namespace")
            raise typer.Exit(1)
        
        sft_config.set(key, value)
        sft_config.save()
        
        log_success(f"Updated {key} = {value}")
        log_info(f"Config saved to {sft_config.config_file_path}")
    except ValueError as e:
        log_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        log_error(f"Failed to set config: {e}")
        raise typer.Exit(1)

