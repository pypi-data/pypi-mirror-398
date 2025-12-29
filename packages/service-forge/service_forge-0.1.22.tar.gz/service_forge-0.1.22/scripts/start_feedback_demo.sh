#!/bin/bash

# Service Forge 反馈系统本地验证脚本

set -e  # 遇到错误立即退出

echo "=================================="
echo "Service Forge 反馈系统本地验证"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 检查 Docker 是否运行
echo "📦 步骤 1: 检查 Docker..."
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行或未安装，请先启动 Docker${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 正在运行${NC}"
echo ""

# 2. 启动 PostgreSQL 容器
echo "🗄️  步骤 2: 启动 PostgreSQL 数据库..."
if docker ps -a | grep -q service-forge-postgres; then
    echo "容器已存在，正在删除旧容器..."
    docker stop service-forge-postgres 2>/dev/null || true
    docker rm service-forge-postgres 2>/dev/null || true
fi

docker run -d \
  --name service-forge-postgres \
  -e POSTGRES_PASSWORD=Luxuyang410641F \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=service_forge_feedback \
  -p 5433:5432 \
  postgres:15-alpine

echo "等待数据库启动..."
sleep 5
echo -e "${GREEN}✅ PostgreSQL 已启动 (端口: 5433)${NC}"
echo ""

# 3. 初始化数据库表
echo "📋 步骤 3: 创建反馈数据表..."
source .venv/bin/activate && python scripts/create_feedback_table.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 数据表创建成功${NC}"
else
    echo -e "${RED}❌ 数据表创建失败${NC}"
    exit 1
fi
echo ""

# 4. 提示用户选择启动服务的方式
echo "🚀 步骤 4: 启动服务"
echo ""
echo "请选择启动方式:"
echo "  1) 使用 tag-service 示例 (推荐)"
echo "  2) 使用 main_with_feedback.py"
echo "  3) 跳过，手动启动"
echo ""
read -p "请输入选项 [1-3]: " choice

case $choice in
    1)
        echo ""
        echo -e "${YELLOW}正在启动 tag-service...${NC}"
        echo "服务将在 http://localhost:37200 启动"
        echo ""
        echo "在新终端运行以下命令启动服务:"
        echo -e "${GREEN}cd example/tag-service && python main.py${NC}"
        ;;
    2)
        echo ""
        echo -e "${YELLOW}正在启动 main_with_feedback.py...${NC}"
        echo ""
        echo "在新终端运行以下命令启动服务:"
        echo -e "${GREEN}python main_with_feedback.py${NC}"
        ;;
    3)
        echo ""
        echo "已跳过服务启动"
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo "=================================="
echo "✅ 环境准备完成！"
echo "=================================="
echo ""
echo "📝 接下来的步骤:"
echo ""
echo "1. 启动服务 (如果还没启动)"
echo ""
echo "2. 创建测试反馈:"
echo -e "${GREEN}curl -X POST 'http://localhost:37200/api/feedback/' \\
  -H 'Content-Type: application/json' \\
  -d '{
    \"task_id\": \"test-task-001\",
    \"workflow_name\": \"query_tags_workflow\",
    \"rating\": 5,
    \"comment\": \"测试反馈\",
    \"metadata\": {\"test\": \"data\"}
  }'${NC}"
echo ""
echo "3. 查看所有反馈:"
echo -e "${GREEN}curl 'http://localhost:37200/api/feedback/'${NC}"
echo ""
echo "4. 查看数据库内容 (选择一种方式):"
echo ""
echo "   方式 A - 使用 psql:"
echo -e "${GREEN}   docker exec -it service-forge-postgres psql -U postgres -d service_forge_feedback${NC}"
echo "   然后执行: SELECT * FROM feedback ORDER BY created_at DESC;"
echo ""
echo "   方式 B - 使用 Python:"
echo -e "${GREEN}   python scripts/view_feedback_db.sh${NC}"
echo ""
echo "   方式 C - 使用数据库客户端工具连接:"
echo "   Host: localhost, Port: 5433"
echo "   Database: service_forge_feedback"
echo "   User: postgres, Password: postgres"
echo ""
echo "5. 清理环境:"
echo -e "${GREEN}bash scripts/cleanup_feedback_demo.sh${NC}"
echo ""
