import asyncio
import json
import sys
import uuid

from asyncpg import InvalidCatalogNameError
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from alembic import command
from alembic.config import Config

from service_forge.db.database import DatabaseManager, PostgresDatabase, MongoDatabase, RedisDatabase

async def ensure_database_exists(database: PostgresDatabase):
    target_url = database.database_url
    base_url = database.database_base_url

    logger.info(f"Checking database: {database.postgres_db}")
    
    try:
        engine = create_async_engine(target_url)
        async with engine.begin() as conn:
            logger.info(f"Database {database.postgres_db} already exists")
        await engine.dispose()
    except InvalidCatalogNameError:
        logger.info(f"Creating database: {database.postgres_db}")
        try:
            admin_engine = create_async_engine(base_url, isolation_level="AUTOCOMMIT")
            async with admin_engine.connect() as conn:
                await conn.execute(text(f'CREATE DATABASE "{database.postgres_db}"'))
            await admin_engine.dispose()
            logger.info(f"Database {database.postgres_db} created successfully")
        except Exception as e:
            logger.error(f"Failed to create database {database.postgres_db}: {e}")
            sys.exit(1)


async def run_migrations(database: PostgresDatabase) -> bool:
    try:
        logger.info("Starting database migrations...")
        
        from sqlalchemy.ext.asyncio import create_async_engine
        
        async_engine = create_async_engine(database.database_url)
        async with async_engine.begin() as conn:
            alembic_cfg = Config("alembic.ini")
            
            def run_upgrade(connection, cfg):
                cfg.attributes["connection"] = connection
                command.upgrade(cfg, "head")
            
            await conn.run_sync(run_upgrade, alembic_cfg)
        
        await async_engine.dispose()
        logger.info("Database migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Database migrations failed: {e}")
        return False
        
async def update_default_tag(database: PostgresDatabase):
    tags = json.load(open("prompt/default_tag.json"))

    session_factory = await database.get_session_factory()

    async with session_factory() as session:
        tag_names = [tag['name'] for tag in tags['tags']]
        if tag_names:
            placeholders = ','.join([f':name_{i}' for i in range(len(tag_names))])
            params = {f'name_{i}': name for i, name in enumerate(tag_names)}
            await session.execute(
                text(f"DELETE FROM tag WHERE type = 'DEFAULT' AND name NOT IN ({placeholders})"),
                params
            )
        else:
            await session.execute(
                text("DELETE FROM tag WHERE type = 'DEFAULT'")
            )
        await session.commit()

        for tag in tags['tags']:
            result = await session.execute(text("SELECT * FROM tag WHERE name = :name"), {"name": tag['name']})
            if result.fetchone() is None:
                await session.execute(
                    text("INSERT INTO tag (id, name, type, description, example, created_at, updated_at) VALUES (:id, :name, 'DEFAULT', :description, :example, now(), now())"),
                    {"id": str(uuid.uuid4()), "name": tag['name'], "description": tag['description'], "example": tag['example']}
                )
                await session.commit()
                print(f"Tag {tag['name']} created")
            else:
                await session.execute(
                    text("UPDATE tag SET description = :description, example = :example, updated_at = now() WHERE name = :name AND type = 'DEFAULT'"),
                    {"name": tag['name'], "description": tag['description'], "example": tag['example']}
                )
                await session.commit()
                print(f"Tag {tag['name']} updated")

async def main():
    logger.info("Starting database migration process")

    database_manager = DatabaseManager.from_config(config_path="configs/service.yaml")
    database = database_manager.get_default_postgres_database()
    if database is None:
        logger.error("No database found")
        return

    await ensure_database_exists(database)
    success = await run_migrations(database)
    await update_default_tag(database)
    
    if success:
        logger.info("Migration process completed successfully")
    else:
        logger.error("Migration process failed")

if __name__ == '__main__':
    asyncio.run(main())