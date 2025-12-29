#!/usr/bin/env python3
import sys
from typing import Optional

import typer
from service_forge.sft.util.logger import log_error, log_info
from service_forge.sft.cmd.list_tars import list_tars
from service_forge.sft.cmd.upload_service import upload_service
from service_forge.sft.cmd.deploy_service import deploy_service
from service_forge.sft.cmd.config_command import list_config, get_config, set_config
from service_forge.sft.cmd.service_command import list_services, delete_service, show_service_logs

app = typer.Typer(
    name="sft",
    help="Service Forge CLI - Service management tool",
    add_completion=False,
)

@app.command(name="upload")
def upload_service_command(
    project_path: Optional[str] = typer.Argument(
        default=".",
        help="Project path, default is the current directory"
    )
) -> None:
    upload_service(project_path)

@app.command(name="list")
def list_tars_command() -> None:
    list_tars()

@app.command(name="deploy")
def deploy_service_command(name: str, version: str) -> None:
    deploy_service(name, version)

config_app = typer.Typer(
    name="config",
    help="Configuration management commands",
    add_completion=False,
)

@config_app.command(name="list")
def config_list_command() -> None:
    list_config()

@config_app.command(name="get")
def config_get_command(
    key: str = typer.Argument(help="Configuration item key")
) -> None:
    get_config(key)

@config_app.command(name="set")
def config_set_command(
    key: str = typer.Argument(help="Configuration item key"),
    value: str = typer.Argument(help="Configuration item value")
) -> None:
    set_config(key, value)

app.add_typer(config_app)

service_app = typer.Typer(
    name="service",
    help="Kubernetes service management commands",
    add_completion=False,
)

@service_app.command(name="list")
def service_list_command() -> None:
    list_services()

@service_app.command(name="delete")
def service_delete_command(
    service_name: str = typer.Argument(help="Service name to delete (must start with sf-)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force delete")
) -> None:
    delete_service(service_name, force)

@service_app.command(name="logs")
def service_logs_command(
    service_name: str = typer.Argument(help="Service name to view logs for (must start with sf-)"),
    container: Optional[str] = typer.Option(None, "--container", "-c", help="Container name (if pod has multiple containers)"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show from the end of logs"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    previous: bool = typer.Option(False, "--previous", "-p", help="Get logs from previous instance of container")
) -> None:
    show_service_logs(service_name, container, tail, follow, previous)

app.add_typer(service_app)

def main() -> None:
    app()
