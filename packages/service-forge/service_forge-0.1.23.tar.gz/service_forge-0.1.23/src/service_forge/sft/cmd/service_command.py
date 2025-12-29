from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from service_forge.sft.config.sft_config import sft_config
from service_forge.sft.util.logger import log_error, log_info, log_success, log_warning
from service_forge.sft.kubernetes.kubernetes_manager import KubernetesManager

def list_services() -> None:
    namespace = sft_config.k8s_namespace
    kubernetes_manager = KubernetesManager()
    services = kubernetes_manager.get_services_in_namespace(namespace)
    
    if not services:
        log_warning(f"No services starting with 'sf-' found in namespace '{namespace}'")
        return
    
    console = Console()
    table = Table(title=f"Services in namespace '{namespace}' (sf-*)", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Port", style="yellow")
    table.add_column("Target Port", style="yellow")
    
    for service_name in sorted(services):
        details = kubernetes_manager.get_service_details(namespace, service_name)
        table.add_row(
            details.name,
            details.type or "-",
            str(details.port or "-"),
            str(details.target_port or "-")
        )
    
    console.print(table)
    log_info(f"Found {len(services)} service(s)")

def show_logs(
    namespace: str,
    pod_name: str,
    container_name: str,
    tail: int,
    follow: bool,
    previous: bool
) -> None:
    kubernetes_manager = KubernetesManager()
    try:
        if not follow:
            log_info(f"Fetching logs from pod '{pod_name}' (container: {container_name})...")
        
        logs = kubernetes_manager.get_pod_logs(
            namespace=namespace,
            pod_name=pod_name,
            container_name=container_name,
            tail=tail,
            follow=follow,
            previous=previous
        )
        
        if follow:
            try:
                for line in logs:
                    log_info(line, end="")
            except KeyboardInterrupt:
                log_warning("Log streaming interrupted")
                raise typer.Exit(0)
        else:
            if logs:
                log_info(logs)
            else:
                log_warning(f"No logs available for pod '{pod_name}' container '{container_name}'")
                
    except ApiException as e:
        if e.status == 404:
            log_error(f"Pod '{pod_name}' or container '{container_name}' not found")
        elif e.status == 400:
            log_error(f"Bad request: {e.reason}")
            if "previous" in str(e.body).lower():
                log_info("Note: 'previous' flag only works for stopped containers")
        else:
            log_error(f"Failed to get logs: {e.reason}")
            if e.body:
                log_error(f"Error details: {e.body}")
    except Exception as e:
        log_error(f"Failed to get logs: {e}")


def show_service_logs(
    service_name: str,
    container: Optional[str] = None,
    tail: int = 100,
    follow: bool = False,
    previous: bool = False
) -> None:
    namespace = sft_config.k8s_namespace
    kubernetes_manager = KubernetesManager()
    
    if not service_name.startswith("sf-"):
        log_warning(f"Service name '{service_name}' does not start with 'sf-'. Proceeding anyway...")
    
    services = kubernetes_manager.get_services_in_namespace(namespace)
    if service_name not in services:
        log_error(f"Service '{service_name}' not found in namespace '{namespace}'")
        log_info(f"Available services: {', '.join(services) if services else 'None'}")
        raise typer.Exit(1)
    
    pod_names = kubernetes_manager.get_pods_for_service(namespace, service_name)
    if not pod_names:
        log_error(f"No pods found for service '{service_name}' in namespace '{namespace}'")
        raise typer.Exit(1)
    
    log_info(f"Found {len(pod_names)} pod(s) for service '{service_name}'")
    
    for pod_name in pod_names:
        containers = kubernetes_manager.get_pod_containers(namespace, pod_name)
        
        if not containers:
            log_warning(f"No containers found in pod '{pod_name}'")
            continue

        if container and container not in containers:
            log_error(f"Container '{container}' not found in pod '{pod_name}'")
            log_info(f"Available containers: {', '.join(containers)}")
            continue
        
        target_containers = [container] if container else containers
        
        for container_name in target_containers:
            show_logs(namespace, pod_name, container_name, tail, follow, previous)

def delete_service(service_name: str, force: bool = False) -> None:
    namespace = sft_config.k8s_namespace
    
    if not service_name.startswith("sf-"):
        log_error(f"Service name '{service_name}' does not start with 'sf-'")
        raise typer.Exit(1)
    
    kubernetes_manager = KubernetesManager()

    services = kubernetes_manager.get_services_in_namespace(namespace)
    if service_name not in services:
        log_warning(f"Service '{service_name}' not found in namespace '{namespace}'")
        log_info(f"Available services: {', '.join(services) if services else 'None'}")
    
    log_info(f"Deleting service '{service_name}' from namespace '{namespace}'...")
    kubernetes_manager.delete_service(namespace, service_name, force)
    