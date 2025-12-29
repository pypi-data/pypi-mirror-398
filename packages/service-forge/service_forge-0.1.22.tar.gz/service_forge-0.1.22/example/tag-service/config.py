from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # OpenAI/LLM Configuration
    openai_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    openai_api_key: str = ""
    openai_model: str = "deepseek-v3-250324"
    openai_timeout: int = 30
    
    # DeepSeek Configuration
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_api_key: str = ""
    deepseek_timeout: int = 30
    
    # Doubao Configuration
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    doubao_api_key: str = ""
    doubao_timeout: int = 30
    
    # Dashscope Configuration
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    dashscope_api_key: str = ""
    dashscope_timeout: int = 30
    
    # Azure OpenAI Configuration
    azure_base_url: str = ""
    azure_api_key: str = ""
    azure_api_version: str = "2023-12-01-preview"
    azure_timeout: int = 30
    
    # LLM General Configuration
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_default_provider: str = "deepseek"
    llm_default_model: str = "deepseek-v3-250324"
    
    # Kafka Configuration
    kafka_host: str = "localhost:9092"
    kafka_group_id: str = "kafka-pipeline-template"
    kafka_auto_offset_reset: str = "earliest"
    
    # Database Configuration
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "kafka_pipeline"
    
    # HTTP Client Configuration
    http_timeout: float = 30.0
    http_max_connections: int = 100
    http_max_keepalive_connections: int = 20
    
    # Application Configuration
    app_name: str = "kafka-pipeline-template"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    @property
    def database_url(self) -> str:
        """Generate database URL from components."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def database_url_sync(self) -> str:
        """Generate synchronous database URL for Alembic."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache()
def get_config() -> Config:
    """
    Get cached configuration instance (singleton pattern).
    
    Returns:
        Config: Application configuration instance
        
    Usage:
        from config import get_config
        
        config = get_config()
        print(config.openai_api_key)
    """
    return Config()


# Global config instance for convenience
config = get_config() 