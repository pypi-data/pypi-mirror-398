import yaml
from pathlib import Path
from service_forge.sft.util.logger import log_info, log_error
from service_forge.sft.config.injector_default_files import *
from service_forge.sft.config.sf_metadata import load_metadata
from service_forge.sft.config.sft_config import sft_config
from service_forge.service_config import ServiceConfig, ServiceFeedbackConfig
from service_forge.sft.util.name_util import get_service_name
from service_forge.sft.util.yaml_utils import load_sf_metadata_as_string

class Injector:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.deployment_yaml_path = project_dir / "deployment.yaml"
        self.metadata_path = project_dir / "sf-meta.yaml"
        self.ingress_yaml_path = project_dir / "ingress.yaml"
        self.dockerfile_path = project_dir / "Dockerfile"
        self.pyproject_toml_path = project_dir / "pyproject.toml"
        self.start_sh_path = project_dir / "start.sh"
        self.metadata = load_metadata(self.metadata_path)
        self.name = self.metadata.name
        self.version = self.metadata.version
        self.namespace = sft_config.k8s_namespace

        try:
            self.sf_metadata_string = load_sf_metadata_as_string(self.metadata_path)
        except Exception as e:
            log_error(f"Failed to load sf-metadata as string: {e}")
            self.sf_metadata_string = ""

    @property
    def service_name(self) -> str:
        return get_service_name(self.name, self.version)

    def inject_deployment(self) -> None:
        single_line_metadata = self.sf_metadata_string.replace('\n', '\\n').replace('"', '\\"')

        envs = {
            "DEEPSEEK_API_KEY": sft_config.deepseek_api_key,
            "DEEPSEEK_BASE_URL": sft_config.deepseek_base_url,
        }

        for env in self.metadata.env:
            envs[env['name']] = env['value']

        env_str = ""
        for key, value in envs.items():
            env_str += f"          - name: {key}\n            value: {value}\n"

        deployment_yaml = DEFAULT_DEPLOYMENT_YAML.format(
            service_name=self.service_name,
            name=self.name,
            version=self.version,
            namespace=self.namespace,
            sf_metadata=f'"{single_line_metadata}"',
            env=env_str,
        )
        with open(self.deployment_yaml_path, "w") as f:
            f.write(deployment_yaml)
        print("deployment_yaml_path: ", self.deployment_yaml_path)

    def inject_service_config(self) -> None:
        service_config_path = self.project_dir / Path(self.metadata.service_config)

        config = ServiceConfig.from_yaml_file(service_config_path)

        config.http_port = sft_config.inject_http_port
        config.kafka_host = sft_config.inject_kafka_host
        config.kafka_port = sft_config.inject_kafka_port
        if config.databases is not None:
            for database in config.databases:
                if database.postgres_host is not None:
                    database.postgres_host = sft_config.inject_postgres_host
                    database.postgres_port = sft_config.inject_postgres_port
                    database.postgres_user = sft_config.inject_postgres_user
                    database.postgres_password = sft_config.inject_postgres_password
                    database.postgres_db = self.service_name
                if database.mongo_host is not None:
                    database.mongo_host = sft_config.inject_mongo_host
                    database.mongo_port = sft_config.inject_mongo_port
                    database.mongo_user = sft_config.inject_mongo_user
                    database.mongo_password = sft_config.inject_mongo_password
                    database.mongo_db = sft_config.inject_mongo_db
                if database.redis_host is not None:
                    database.redis_host = sft_config.inject_redis_host
                    database.redis_port = sft_config.inject_redis_port
                    database.redis_password = sft_config.inject_redis_password
        if config.feedback is not None:
            config.feedback.api_url = sft_config.inject_feedback_api_url
            config.feedback.api_timeout = sft_config.inject_feedback_api_timeout
        else:
            config.feedback = ServiceFeedbackConfig(
                api_url=sft_config.inject_feedback_api_url,
                api_timeout=sft_config.inject_feedback_api_timeout,
            )

        with open(service_config_path, "w", encoding="utf-8") as f:
            yaml.dump(config.model_dump(), f, allow_unicode=True, indent=2)

    def inject_ingress(self) -> None:
        ingress_yaml = DEFAULT_TRAEFIK_INGRESS_YAML.format(
            name=self.name,
            version=self.version.replace(".", "-"),
            namespace=self.namespace,
        )
        with open(self.ingress_yaml_path, "w") as f:
            f.write(ingress_yaml)
        print("ingress_yaml_path: ", self.ingress_yaml_path)

    def inject_dockerfile(self) -> None:
        dockerfile = DEFAULT_DOCKERFILE
        with open(self.dockerfile_path, "w") as f:
            f.write(dockerfile)
        print("dockerfile_path: ", self.dockerfile_path)

    def inject_pyproject_toml(self) -> None:
        pyproject_toml = DEFAULT_PYPROJECT_TOML
        with open(self.pyproject_toml_path, "r") as f:
            existing_pyproject_toml = f.read()
        if pyproject_toml.strip() not in existing_pyproject_toml.strip():
            with open(self.pyproject_toml_path, "a") as f:
                f.write(pyproject_toml)
        print("pyproject_toml_path: ", self.pyproject_toml_path)

    def clear_start_sh(self) -> None:
        if Path(self.start_sh_path).exists():
            with open(self.start_sh_path, "rb") as f:
                content = f.read()
            content_str = content.decode("utf-8")
            lines = content_str.splitlines()
            new_content = "\n".join(lines) + ("\n" if content_str.endswith(('\n', '\r')) else "")
            with open(self.start_sh_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(new_content)

    def inject(self) -> None:
        self.inject_deployment()
        self.inject_service_config()
        self.inject_ingress()
        self.inject_dockerfile()
        self.inject_pyproject_toml()
        self.clear_start_sh()