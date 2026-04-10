#!/bin/bash

# API 服务部署脚本
# 使用 Docker Compose 一键部署

set -e

echo "=================================================="
echo "API 服务部署脚本"
echo "=================================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 创建环境变量文件
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cat > .env << EOF
# 数据库配置
POSTGRES_DB=api_service
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# API Keys
GEMINI_API_KEY=AIzaSyAcR7gXsIDENrgnXSyoA-SXidpqo8nBz-M
INFERENCE_API_KEY=your_inference_key_here

# 其他配置
FLASK_ENV=production
EOF
    echo "✅ .env 文件已创建，请检查配置"
fi

# 创建必要目录
echo "📁 创建目录..."
mkdir -p ssl logs backups

# 拉取镜像
echo "📦 拉取 Docker 镜像..."
docker-compose pull

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
echo "🔍 健康检查..."
curl -s http://localhost:5005/health | python3 -m json.tool
curl -s http://localhost:5006/health | python3 -m json.tool
curl -s http://localhost:5007/health | python3 -m json.tool

# 显示状态
echo ""
echo "=================================================="
echo "✅ 部署完成！"
echo "=================================================="
echo ""
echo "服务地址："
echo "  - API 优化版:    http://localhost:5005"
echo "  - API 专业版:    http://localhost:5006"
echo "  - 视频生成:      http://localhost:5007"
echo ""
echo "数据库："
echo "  - PostgreSQL:    localhost:5432"
echo "  - Redis:         localhost:6379"
echo ""
echo "管理命令："
echo "  - 查看日志:      docker-compose logs -f"
echo "  - 停止服务:      docker-compose stop"
echo "  - 重启服务:      docker-compose restart"
echo "  - 完全删除:      docker-compose down -v"
echo ""
echo "=================================================="
