import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

import typer
from omegaconf import OmegaConf
from service_forge.sft.util.logger import log_error, log_info, log_success, log_warning
from service_forge.sft.file.sft_file_manager import sft_file_manager
from service_forge.sft.config.sft_config import sft_config
from service_forge.sft.util.assert_util import assert_file_exists, assert_dir_exists
from service_forge.sft.config.sf_metadata import load_metadata
from service_forge.sft.kubernetes.kubernetes_manager import KubernetesManager
from service_forge.sft.config.injector import Injector
from service_forge.sft.util.name_util import get_service_name

def _extract_tar_file(tar_file: Path, temp_path: Path) -> None:
    log_info(f"Extracting tar file to: {temp_path}")
    
    try:
        with tarfile.open(tar_file, 'r') as tar:
            tar.extractall(temp_path)
    except Exception as e:
        log_error(f"Failed to extract tar file: {e}")
        raise typer.Exit(1)
    
    log_success("Tar file extracted successfully")

def _build_docker_image(project_dir: Path, name: str, version: str) -> None:
    image_name = f"sf-{name}:{version}"
    full_image_name = sft_config.registry_address + "/" + image_name
    log_info(f"Building Docker image: {image_name}")
    try:
        # build docker image
        build_result = subprocess.run(
            ["docker", "build", "-t", full_image_name, str(project_dir)],
            capture_output=True,
            text=True,
            check=True
        )
        log_success(f"Docker image built successfully: {image_name}")
        if build_result.stdout:
            log_info(build_result.stdout)

        # push docker image to registry
        log_info(f"Pushing Docker image to registry: {full_image_name}")
        push_result = subprocess.run(
            ["docker", "push", full_image_name],
            capture_output=True,
            text=True,
            check=True
        )
        log_success(f"Docker image pushed successfully: {full_image_name}")
        if push_result.stdout:
            log_info(push_result.stdout)

    except subprocess.CalledProcessError as e:
        log_error(f"Docker operation failed: {e}")
        if e.stderr:
            log_error(e.stderr)
        raise typer.Exit(1)
    except FileNotFoundError:
        log_error("Docker command not found. Please install Docker.")
        raise typer.Exit(1)

def _apply_k8s_deployment(deployment_yaml: Path, ingress_yaml: Path, name: str, version: str) -> None:
    log_info("Applying k8s deployment...")
    
    try:
        k8s_manager = KubernetesManager()
        k8s_manager.delete_service(sft_config.k8s_namespace, get_service_name(name, version), force=True)
        k8s_manager.apply_deployment_yaml(deployment_yaml, sft_config.k8s_namespace)
        k8s_manager.apply_deployment_yaml(ingress_yaml, sft_config.k8s_namespace)
        log_success("K8s deployment applied successfully")
    except Exception as e:
        log_error(f"K8s deployment failed: {e}")
        raise typer.Exit(1)
    
    log_success(f"Deployment process completed for {name}:{version}")

def _inject_config(project_dir: Path) -> None:
    injector = Injector(project_dir)
    injector.inject()

def deploy_service(name: str, version: str) -> None:
    tar_file = sft_file_manager.tar_path / f"sf_{name}_{version}.tar"

    assert_file_exists(tar_file)
    
    temp_parent = os.path.join(tempfile.gettempdir(), "sft")
    os.makedirs(temp_parent, exist_ok=True)
    
    with tempfile.TemporaryDirectory(prefix=f"deploy_{name}_{version}", dir=temp_parent) as temp_dir:
        temp_path = Path(temp_dir)

        _extract_tar_file(tar_file, temp_path)

        project_dir = temp_path / f"{name}_{version}"

        _inject_config(project_dir)

        dockerfile_path = project_dir / "Dockerfile"
        metadata_path = project_dir / "sf-meta.yaml"
        deployment_yaml = project_dir / "deployment.yaml"
        ingress_yaml = project_dir / "ingress.yaml"
        
        assert_dir_exists(project_dir)
        assert_file_exists(dockerfile_path)
        assert_file_exists(metadata_path)
        assert_file_exists(deployment_yaml)
        assert_file_exists(ingress_yaml)

        try:
            meta_data = load_metadata(metadata_path)
        except Exception as e:
            log_error(f"Failed to read sf-meta.yaml: {e}")
            raise typer.Exit(1)
        
        _build_docker_image(project_dir, meta_data.name, meta_data.version)
        # TODO: create new user in mongodb and redis
        _apply_k8s_deployment(deployment_yaml, ingress_yaml, meta_data.name, meta_data.version)