"""
数据库迁移脚本 - 创建 feedback 表

使用方法:
1. 确保你的 service.yaml 中配置了数据库连接
2. 运行此脚本: python -m src.service_forge.db.migrations.feedback_migration

此脚本会:
- 检查 feedback 表是否存在
- 如果不存在,创建 feedback 表及索引
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from sqlalchemy import text
from src.service_forge.db.database import DatabaseManager
from src.service_forge.db.models.feedback import Base, FeedbackBase


async def create_database_if_not_exists(db):
    """如果数据库不存在，则创建数据库"""
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError
    import asyncpg

    try:
        # 先尝试连接目标数据库
        await db.init()
        logger.info(f"✓ 数据库 '{db.postgres_db}' 已存在")
        await db.close()
        return True
    except Exception as e:
        logger.info(f"数据库 '{db.postgres_db}' 不存在，准备创建...")

        try:
            # 连接到 postgres 默认数据库
            conn = await asyncpg.connect(
                host=db.postgres_host,
                port=db.postgres_port,
                user=db.postgres_user,
                password=db.postgres_password,
                database='postgres'
            )

            # 创建数据库
            await conn.execute(f'CREATE DATABASE {db.postgres_db}')
            await conn.close()

            logger.info(f"✓ 数据库 '{db.postgres_db}' 创建成功!")
            return True

        except Exception as create_error:
            logger.error(f"创建数据库失败: {create_error}")
            return False


async def create_feedback_table(database_manager: DatabaseManager):
    """创建 feedback 表"""
    db = database_manager.get_default_postgres_database()

    if db is None:
        logger.error("未找到默认 PostgreSQL 数据库配置")
        return False

    try:
        # 1. 先确保数据库存在
        db_created = await create_database_if_not_exists(db)
        if not db_created:
            return False

        # 2. 连接到数据库
        await db.init()
        engine = db.engine

        logger.info(f"连接到数据库: {db.database_url}")

        # 3. 检查表是否存在
        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'feedback');"
                )
            )
            table_exists = result.scalar()

            if table_exists:
                logger.info("✓ feedback 表已存在,跳过创建")
                return True

            logger.info("创建 feedback 表...")

            # 4. 创建表
            await conn.run_sync(Base.metadata.create_all)

            logger.info("✓ feedback 表创建成功!")
            logger.info("表结构:")
            logger.info("  - feedback_id: UUID (主键)")
            logger.info("  - task_id: VARCHAR(255) (索引)")
            logger.info("  - workflow_name: VARCHAR(255) (索引)")
            logger.info("  - rating: INTEGER (可选, 1-5)")
            logger.info("  - comment: TEXT (可选)")
            logger.info("  - metadata: JSONB (可选)")
            logger.info("  - created_at: TIMESTAMP (索引)")
            logger.info("  - updated_at: TIMESTAMP (可选)")

        await db.close()
        return True

    except Exception as e:
        logger.error(f"创建 feedback 表失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("=== Feedback 表迁移脚本 ===")

    # 提示用户提供配置文件路径
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        logger.info("请提供 service 配置文件路径:")
        logger.info("  python -m src.service_forge.db.migrations.feedback_migration <config_path>")
        logger.info("例如:")
        logger.info("  python -m src.service_forge.db.migrations.feedback_migration configs/service/my_service.yaml")
        return

    logger.info(f"读取配置文件: {config_path}")

    try:
        database_manager = DatabaseManager.from_config(config_path=config_path)
        success = await create_feedback_table(database_manager)

        if success:
            logger.info("✓ 迁移完成!")
        else:
            logger.error("✗ 迁移失败")
            sys.exit(1)

    except Exception as e:
        logger.error(f"迁移过程出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
