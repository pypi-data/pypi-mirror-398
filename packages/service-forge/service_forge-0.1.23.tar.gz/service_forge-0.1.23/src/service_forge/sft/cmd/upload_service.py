import typer
from pathlib import Path
from service_forge.sft.util.logger import log_error, log_success
from service_forge.sft.file.sft_file_manager import sft_file_manager
from service_forge.sft.util.assert_util import assert_dir_exists, assert_file_exists
from service_forge.sft.config.sf_metadata import load_metadata

def upload_service(project_path: str) -> None:
    project_dir = Path(project_path).resolve()
    assert_dir_exists(project_dir)
    
    metadata_path = project_dir / "sf-meta.yaml"
    assert_file_exists(metadata_path)
    
    try:
        meta_data = load_metadata(metadata_path)
    except Exception as e:
        log_error(f"Failed to read sf-meta.yaml: {e}")
        raise typer.Exit(1)
        
    try:
        tar_file = sft_file_manager.create_tar(project_dir, meta_data.name, meta_data.version)
    except Exception as e:
        log_error(f"Failed to create tar file: {e}")
        raise typer.Exit(1)

    log_success(f"Packaging successful: {tar_file}")

    # upload to the service
    try:
        sft_file_manager.upload_tar(tar_file)
    except Exception as e:
        log_error(f"Failed to upload tar file: {e}")
        raise typer.Exit(1)

    log_success(f"Upload successful: {tar_file}")