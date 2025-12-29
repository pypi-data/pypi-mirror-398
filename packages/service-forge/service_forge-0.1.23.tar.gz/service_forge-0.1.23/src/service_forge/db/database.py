from __future__ import annotations

import redis
import pymongo
import psycopg2
from typing import AsyncGenerator
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from service_forge.service_config import ServiceConfig

class PostgresDatabase:
    def __init__(
        self,
        name: str,
        postgres_user: str,
        postgres_password: str,
        postgres_host: str,
        postgres_port: int,
        postgres_db: str,
    ) -> None:
        self.name = name
        self.postgres_user = postgres_user
        self.postgres_password = postgres_password
        self.postgres_host = postgres_host
        self.postgres_port = postgres_port
        self.postgres_db = postgres_db
        self.engine = None
        self.session_factory = None
        self.test_connection()

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def database_base_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/postgres"

    async def init(self) -> None:
        if self.engine is None:
            self.engine = await self.create_engine()
            self.session_factory = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    async def close(self) -> None:
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None
            logger.info("Database connection closed")

    async def create_engine(self) -> AsyncEngine:
        if not all([self.postgres_user, self.postgres_host, self.postgres_port, self.postgres_db]):
            raise ValueError("Missing required database configuration. Please check your .env file or configuration.")
        logger.info(f"Creating database engine: {self.database_url}")
        return create_async_engine(self.database_url)

    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        if self.session_factory is None:
            await self.init()
        
        if self.session_factory is None:
            raise RuntimeError("Session factory is not initialized")
        
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
            yield session

    async def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self.engine is None:
            await self.init()

        if self.session_factory is None:
            raise RuntimeError("Session factory is not initialized")

        return self.session_factory

    def test_connection(self) -> bool:
        try:
            conn = psycopg2.connect(
                host=self.postgres_host,
                port=self.postgres_port,
                user=self.postgres_user,
                password=self.postgres_password,
                database=self.postgres_db,
                connect_timeout=5
            )
            conn.close()
            logger.info(f"PostgreSQL connection test successful for database '{self.name}'")
            return True
        except Exception as e:
            logger.warning(f"PostgreSQL connection test failed for database '{self.name}': {e}")
            return False

class MongoDatabase:
    def __init__(
        self,
        name: str,
        mongo_host: str,
        mongo_port: int,
        mongo_user: str,
        mongo_password: str,
        mongo_db: str,
    ) -> None:
        self.name = name
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port
        self.mongo_user = mongo_user
        self.mongo_password = mongo_password
        self.mongo_db = mongo_db or ""
        self.client = pymongo.MongoClient(self.database_url)
        self.test_connection()

    @property
    def database_url(self) -> str:
        return f"mongodb://{self.mongo_user}:{self.mongo_password}@{self.mongo_host}:{self.mongo_port}/{self.mongo_db}"

    def test_connection(self) -> bool:
        try:
            self.client.admin.command('ping')
            logger.info(f"MongoDB connection test successful for database '{self.name}'")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection test failed for database '{self.name}': {e}")
            return False

class RedisDatabase:
    def __init__(
        self,
        name: str,
        redis_host: str,
        redis_port: int,
        redis_password: str,
    ) -> None:
        self.name = name
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_password = redis_password
        self.client = redis.Redis(host=redis_host, port=redis_port, password=redis_password)
        self.test_connection()

    def test_connection(self) -> bool:
        try:
            self.client.ping()
            logger.info(f"Redis connection test successful for database '{self.name}'")
            return True
        except Exception as e:
            logger.error(f"Redis connection test failed for database '{self.name}': {e}")
            return False


class DatabaseManager:
    def __init__(
        self,
        postgres_databases: list[PostgresDatabase],
        mongo_databases: list[MongoDatabase],
        redis_databases: list[RedisDatabase],
    ) -> None:
        self.postgres_databases = postgres_databases
        self.mongo_databases = mongo_databases
        self.redis_databases = redis_databases

    def get_database(self, name: str) ->  PostgresDatabase | MongoDatabase | RedisDatabase | None:
        for database in self.postgres_databases:
            if database.name == name:
                return database
        return None

    def get_default_postgres_database(self) -> PostgresDatabase | None:
        if len(self.postgres_databases) > 0:
            return self.postgres_databases[0]
        return None

    def get_default_mongo_database(self) -> MongoDatabase | None:
        if len(self.mongo_databases) > 0:
            return self.mongo_databases[0]
        return None

    def get_default_redis_database(self) -> RedisDatabase | None:
        if len(self.redis_databases) > 0:
            return self.redis_databases[0]
        return None

    @staticmethod
    def from_config(config_path: str = None, config: ServiceConfig = None) -> DatabaseManager:
        if config is None:
            config = ServiceConfig.from_yaml_file(config_path)

        postgres_databases = []
        mongo_databases = []
        redis_databases = []

        databases_config = config.databases

        if databases_config is not None:
            for database_config in databases_config:
                if all([database_config.postgres_host is None, database_config.mongo_host is None, database_config.redis_host is None]):
                    raise ValueError(f"Database '{database_config.name}' is missing required configuration. Please check your service.yaml file.")

                if (database_config.postgres_host is not None) + (database_config.mongo_host is not None) + (database_config.redis_host is not None) > 1:
                    raise ValueError(f"Database '{database_config['name']}' has multiple host configurations. Please check your service.yaml file.")

                if database_config.postgres_host is not None:
                    postgres_databases.append(PostgresDatabase(
                        name=database_config.name,
                        postgres_user=database_config.postgres_user,
                        postgres_password=database_config.postgres_password,
                        postgres_host=database_config.postgres_host,
                        postgres_port=database_config.postgres_port,
                        postgres_db=database_config.postgres_db,
                    ))
                elif database_config.mongo_host is not None:
                    mongo_databases.append(MongoDatabase(
                        name=database_config.name,
                        mongo_host=database_config.mongo_host,
                        mongo_port=database_config.mongo_port,
                        mongo_user=database_config.mongo_user,
                        mongo_password=database_config.mongo_password,
                        mongo_db=database_config.mongo_db,
                    ))
                elif database_config.redis_host is not None:
                    redis_databases.append(RedisDatabase(
                        name=database_config.name,
                        redis_host=database_config.redis_host,
                        redis_port=database_config.redis_port,
                        redis_password=database_config.redis_password,
                    ))

        return DatabaseManager(postgres_databases=postgres_databases, mongo_databases=mongo_databases, redis_databases=redis_databases)

def create_database_manager(config_path: str = None, config = None) -> DatabaseManager:
    return DatabaseManager.from_config(config_path, config)
