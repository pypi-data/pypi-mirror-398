import os
import tarfile
from pathlib import Path
import requests

from service_forge.sft.file.ignore_pattern import load_ignore_patterns
from service_forge.sft.config.sft_config import sft_config
from service_forge.sft.util.logger import log_success, log_info, log_error

class SftTarFile:
    # example: sf_tag_service_0.0.1.tar
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.size = path.stat().st_size
        self.modified_time = path.stat().st_mtime
        self.project_name = '_'.join(path.name.split('_')[1:-1])
        self.version = path.name.split('_')[-1][:-4]

    def _format_size(self) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.size < 1024.0:
                return f"{self.size:.2f} {unit}"
            self.size /= 1024.0
        return f"{self.size:.2f} TB"

    def _format_modified_time(self) -> str:
        from datetime import datetime
        return datetime.fromtimestamp(self.modified_time).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def is_valid_path(path: Path) -> bool:
        return path.is_file() and path.suffix == '.tar' and path.name.startswith('sf_')


class SftFileManager:
    def __init__(self):
        self.tar_path = Path(sft_config.sft_file_root) / "service-tar"
        self.tars: list[SftTarFile] = []
        os.makedirs(self.tar_path, exist_ok=True)
        self.load_tars()

    def create_tar(self, project_path: Path, name: str, version: str) -> Path:
        project_path = Path(project_path).resolve()
        tar_path = Path(self.tar_path) / f"sf_{name}_{version}.tar"
        
        ignore_pattern = load_ignore_patterns(project_path)
        
        with tarfile.open(tar_path, 'w') as tar:
            for root, dirs, files in os.walk(project_path):
                root_path = Path(root)
                
                dirs[:] = [
                    d for d in dirs 
                    if not ignore_pattern.should_ignore(root_path / d)
                ]
                
                for file in files:
                    file_path = root_path / file
                    if ignore_pattern.should_ignore(file_path):
                        continue
                    
                    arcname = file_path.relative_to(project_path)
                    tar.add(file_path, arcname=Path(f"{name}_{version}") / arcname)
        self.load_tars()
        return tar_path

    def load_tars(self) -> list[SftTarFile]:
        self.tars = [SftTarFile(p) for p in self.tar_path.iterdir() if SftTarFile.is_valid_path(p)]
        return self.tars
    
    def upload_tar(self, tar_path: Path) -> None:
        if not tar_path.exists():
            raise FileNotFoundError(f"File not found: {tar_path}")
        
        upload_url = f"{sft_config.server_url}/api/v1/services/upload-tar"
        
        try:
            with open(tar_path, 'rb') as file:
                files = {'file': (tar_path.name, file)}
                
                response = requests.post(
                    upload_url,
                    files=files,
                    timeout=sft_config.upload_timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 200:
                        log_success(f"Upload successful: {result.get('message')}")
                        log_info(f"File saved path: {result.get('data', {}).get('file_path')}")
                    else:
                        raise Exception(f"Upload failed: {result.get('message')}")
                else:
                    try:
                        error_detail = response.json()
                        error_message = error_detail.get('message', f"HTTP错误: {response.status_code}")
                        if 'debug' in error_detail and error_detail['debug']:
                            log_error(f"Error details: {error_detail['debug']}")
                        raise Exception(error_message)
                    except ValueError:
                        raise Exception(f"Server returned error status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Upload request failed: {str(e)}")

sft_file_manager = SftFileManager()