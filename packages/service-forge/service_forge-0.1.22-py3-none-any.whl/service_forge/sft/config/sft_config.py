from __future__ import annotations

import inspect
from pathlib import Path
from typing import Optional
from omegaconf import OmegaConf

class SftConfig:
    CONFIG_ROOT = Path.home() / ".sft"
    
    # Configuration descriptions mapping
    CONFIG_DESCRIPTIONS = {
        "sft_file_root": "SFT file storage root directory",
        "service_center_address": "Service center address",
        "k8s_namespace": "Kubernetes namespace",
        "registry_address": "Registry address",
        "inject_http_port": "HTTP port for services",
        "inject_kafka_host": "Kafka host for services",
        "inject_kafka_port": "Kafka port for services",
        "inject_postgres_host": "Postgres host for services",
        "inject_postgres_port": "Postgres port for services",
        "inject_postgres_user": "Postgres user for services",
        "inject_postgres_password": "Postgres password for services",
        "inject_feedback_api_url": "Feedback API URL for services",
        "inject_feedback_api_timeout": "Feedback API timeout for services",
        "deepseek_api_key": "DeepSeek API key",
        "deepseek_base_url": "DeepSeek base URL",
    }

    def __init__(
        self,
        sft_file_root: str = "/tmp/sft",
        service_center_address: str = "http://vps.shiweinan.com:37919/service_center",
        k8s_namespace: str = "secondbrain",
        registry_address: str = "crpi-cev6qq28wwgwwj0y.cn-beijing.personal.cr.aliyuncs.com/nexthci",

        inject_http_port: int = 8000,

        inject_kafka_host: str = "localhost",
        inject_kafka_port: int = 9092,

        inject_postgres_host: str = "second-brain-postgres-postgresql",
        inject_postgres_port: int = 5432,
        inject_postgres_user: str = "postgres",
        inject_postgres_password: str = "gnBGWg7aL4",

        inject_mongo_host: str = "mongo-mongodb",
        inject_mongo_port: int = 27017,
        inject_mongo_user: str = "secondbrain",
        inject_mongo_password: str = "secondbrain",
        inject_mongo_db: str = "secondbrain",

        inject_redis_host: str = "redis-master",
        inject_redis_port: int = 6379,
        inject_redis_password: str = "rDdM2Y2gX9",

        inject_feedback_api_url: str = "http://vps.shiweinan.com:37919/api/v1/feedback",
        inject_feedback_api_timeout: int = 5,

        deepseek_api_key: str = "82c9df22-f6ed-411e-90d7-c5255376b7ca",
        deepseek_base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
    ):
        self.sft_file_root = sft_file_root
        self.service_center_address = service_center_address
        self.k8s_namespace = k8s_namespace
        self.registry_address = registry_address

        self.inject_http_port = inject_http_port

        self.inject_kafka_host = inject_kafka_host
        self.inject_kafka_port = inject_kafka_port

        self.inject_postgres_host = inject_postgres_host
        self.inject_postgres_port = inject_postgres_port
        self.inject_postgres_user = inject_postgres_user
        self.inject_postgres_password = inject_postgres_password

        self.inject_mongo_host = inject_mongo_host
        self.inject_mongo_port = inject_mongo_port
        self.inject_mongo_user = inject_mongo_user
        self.inject_mongo_password = inject_mongo_password
        self.inject_mongo_db = inject_mongo_db

        self.inject_redis_host = inject_redis_host
        self.inject_redis_port = inject_redis_port
        self.inject_redis_password = inject_redis_password

        self.inject_feedback_api_url = inject_feedback_api_url
        self.inject_feedback_api_timeout = inject_feedback_api_timeout

        self.deepseek_api_key = deepseek_api_key
        self.deepseek_base_url = deepseek_base_url

    @property
    def server_url(self) -> str:
        return self.service_center_address

    @property
    def upload_timeout(self) -> int:
        return 300  # 5 minutes default timeout

    def get_config_keys(self) -> list[str]:
        # Get initial configuration parameters from __init__ method
        sig = inspect.signature(self.__class__.__init__)
        init_keys = [param for param in sig.parameters.keys() if param != 'self']
        
        # Get all instance attributes (including dynamically added configurations)
        instance_keys = []
        for attr_name in dir(self):
            # Exclude special methods, private attributes, class attributes, and methods
            if (not attr_name.startswith('_') and
                not callable(getattr(self, attr_name)) and
                attr_name not in ['CONFIG_ROOT', 'CONFIG_DESCRIPTIONS']):
                instance_keys.append(attr_name)
        
        # Merge and deduplicate, maintaining order (initial configs first, then dynamically added)
        all_keys = list(dict.fromkeys(init_keys + instance_keys))
        return all_keys
    
    @property
    def config_file_path(self) -> Path:
        return self.CONFIG_ROOT / "config.yaml"
    
    def ensure_config_dir(self) -> None:
        self.CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> dict:
        config_keys = self.get_config_keys()
        result = {}
        for key in config_keys:
            value = getattr(self, key)
            # Convert Path objects to strings for JSON serialization
            if isinstance(value, Path):
                value = str(value)
            result[key] = value
        return result
    
    def from_dict(self, data: dict) -> None:
        # Get initial configuration parameters from __init__ method
        sig = inspect.signature(self.__class__.__init__)
        init_keys = [param for param in sig.parameters.keys() if param != 'self']
        
        # First, set all initial configuration parameters
        for key in init_keys:
            if key in data:
                setattr(self, key, data[key])
        
        # Then, handle any additional keys that might be dynamically added configurations
        for key, value in data.items():
            if key not in init_keys and key not in ['CONFIG_ROOT', 'CONFIG_DESCRIPTIONS']:
                # This might be a dynamically added configuration
                setattr(self, key, value)
    
    def save(self) -> None:
        self.ensure_config_dir()
        config_dict = self.to_dict()
        OmegaConf.save(config_dict, self.config_file_path)
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return getattr(self, key, default)
    
    def set(self, key: str, value: str, description: Optional[str] = None) -> None:
        if key in ["config_root"]:
            raise ValueError(f"{key} is read-only")
        if hasattr(self, key):
            setattr(self, key, value)
            if description:
                self.CONFIG_DESCRIPTIONS[key] = description
        else:
            raise ValueError(f"Unknown config key: {key}")
        
    def add(self, key: str, value: str, description: Optional[str] = None) -> None:
        if hasattr(self, key):
            raise ValueError(f"{key} already exists")
        setattr(self, key, value)
        if description:
            self.CONFIG_DESCRIPTIONS[key] = description
    
    def update(self, updates: dict) -> None:
        for key, value in updates.items():
            self.set(key, value)


def load_config() -> SftConfig:
    # config = SftConfig()
    config = SftConfig()
    config_file = config.config_file_path
    
    if config_file.exists():
        try:
            data = OmegaConf.load(config_file)
            config = SftConfig(**OmegaConf.to_container(data, resolve=True))
        except Exception as e:
            ...

    config.save()
    
    return config

sft_config = load_config()