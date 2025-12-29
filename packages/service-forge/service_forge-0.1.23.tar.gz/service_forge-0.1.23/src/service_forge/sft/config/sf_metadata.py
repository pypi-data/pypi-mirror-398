from omegaconf import OmegaConf

class SfMetadata:
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        service_config: str,
        config_only: bool,
        env: list[dict],
    ) -> None:
        self.name = name
        self.version = version
        self.description = description
        self.service_config = service_config
        self.config_only = config_only
        self.env = env

def load_metadata(path: str) -> SfMetadata:
    with open(path, 'r') as file:
        data = OmegaConf.load(file)
        return SfMetadata(
            name=data.get('name'),
            version=data.get('version'),
            description=data.get('description'),
            service_config=data.get('service_config'),
            config_only=data.get('config_only'),
            env=data.get('env', []),
        )
