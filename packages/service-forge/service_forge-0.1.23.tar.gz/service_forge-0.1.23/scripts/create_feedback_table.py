#!/usr/bin/env python3
"""
创建 feedback 数据表
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from service_forge.db.database import PostgresDatabase
from service_forge.feedback.models import Base

async def create_table():
    """创建 feedback 表"""
    db = PostgresDatabase(
        name='feedback_db',
        postgres_host='localhost',
        postgres_port=5433,
        postgres_user='postgres',
        postgres_password='Luxuyang410641F',
        postgres_db='service_forge_feedback'
    )

    print("连接数据库...")
    await db.init()
    engine = db.engine

    print("创建 feedback 表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await db.close()
    print('✅ 数据库表创建成功!')
    print('\n表结构:')
    print('  - feedback_id: UUID (主键)')
    print('  - task_id: VARCHAR(255) (索引)')
    print('  - workflow_name: VARCHAR(255) (索引)')
    print('  - rating: INTEGER (可选)')
    print('  - comment: TEXT (可选)')
    print('  - metadata: JSONB (可选)')
    print('  - created_at: TIMESTAMP (索引)')
    print('  - updated_at: TIMESTAMP (可选)')

if __name__ == "__main__":
    asyncio.run(create_table())
