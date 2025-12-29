#!/bin/bash

# 清理反馈系统演示环境

echo "🧹 清理反馈系统演示环境..."
echo ""

# 停止并删除 PostgreSQL 容器
if docker ps -a | grep -q service-forge-postgres; then
    echo "正在停止 PostgreSQL 容器..."
    docker stop service-forge-postgres 2>/dev/null || true
    echo "正在删除 PostgreSQL 容器..."
    docker rm service-forge-postgres 2>/dev/null || true
    echo "✅ 容器已清理"
else
    echo "⚠️  未找到 service-forge-postgres 容器"
fi

echo ""
echo "✅ 清理完成！"
echo ""
echo "如需删除数据卷，请手动执行:"
echo "docker volume ls | grep postgres"
echo "docker volume rm <volume_name>"
