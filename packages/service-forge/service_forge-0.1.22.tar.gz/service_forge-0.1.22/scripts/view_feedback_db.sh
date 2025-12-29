#!/bin/bash

# 快速查看数据库中的反馈内容

echo "🔍 查看反馈数据库内容..."
echo ""

python3 -c "
import asyncio
from service_forge.db.database import DatabaseManager
from service_forge.feedback.models import FeedbackBase
from sqlalchemy import select

async def view():
    config = {
        'databases': [{
            'name': 'default',
            'postgres_host': 'localhost',
            'postgres_port': 5433,
            'postgres_user': 'postgres',
            'postgres_password': 'postgres',
            'postgres_db': 'service_forge_feedback'
        }]
    }

    db = DatabaseManager.from_config(config).get_default_postgres_database()
    session_factory = await db.get_session_factory()

    async with session_factory() as session:
        result = await session.execute(
            select(FeedbackBase).order_by(FeedbackBase.created_at.desc())
        )
        feedbacks = result.scalars().all()

        if not feedbacks:
            print('📭 数据库中暂无反馈记录')
            return

        print(f'📊 共找到 {len(feedbacks)} 条反馈记录:\n')
        print('=' * 100)

        for i, f in enumerate(feedbacks, 1):
            rating_stars = '⭐' * f.rating if f.rating else '未评分'
            print(f'\n[{i}] 反馈 ID: {f.feedback_id}')
            print(f'    任务 ID: {f.task_id}')
            print(f'    工作流: {f.workflow_name}')
            print(f'    评分: {rating_stars}')
            print(f'    评论: {f.comment or \"无评论\"}')
            print(f'    元数据: {f.metadata or {}}')
            print(f'    创建时间: {f.created_at}')
            print('-' * 100)

asyncio.run(view())
"
