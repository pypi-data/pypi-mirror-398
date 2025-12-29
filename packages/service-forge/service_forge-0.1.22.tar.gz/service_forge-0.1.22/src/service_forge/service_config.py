from __future__ import annotations

import yaml
from pydantic import BaseModel

class ServiceFeedbackConfig(BaseModel):
    api_url: str
    api_timeout: int = 5

class ServiceDatabaseConfig(BaseModel):
    name: str
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_host: str | None = None
    postgres_port: int | None = None
    postgres_db: str | None = None

    mongo_host: str | None = None
    mongo_port: int | None = None
    mongo_user: str | None = None
    mongo_password: str | None = None
    mongo_db: str | None = None

    redis_host: str | None = None
    redis_port: int | None = None
    redis_password: str | None = None

class ServiceConfig(BaseModel):
    name: str
    workflows: list[str]
    enable_http: bool
    http_host: str | None = None
    http_port: int | None = None
    enable_kafka: bool
    kafka_host: str | None = None
    kafka_port: int | None = None
    databases: list[ServiceDatabaseConfig] | None = None
    feedback: ServiceFeedbackConfig | None = None

    @classmethod
    def from_yaml_file(cls, filepath: str) -> ServiceConfig:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)
