#!/bin/bash

# 显示彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}启动VanillaRAGPlus使用Docker...${NC}"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装，请先安装Docker${NC}"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose未安装，请先安装Docker Compose${NC}"
    exit 1
fi

# 检查后端目录是否存在
if [ ! -d "backend" ]; then
  echo -e "${RED}错误: 找不到backend目录${NC}"
  exit 1
fi

# 检查前端目录是否存在
if [ ! -d "frontend" ]; then
  echo -e "${RED}错误: 找不到frontend目录${NC}"
  exit 1
fi

# 检查Docker目录是否存在
if [ ! -d "docker" ]; then
  echo -e "${RED}错误: 找不到docker目录${NC}"
  exit 1
fi

# 创建必要的目录
echo -e "${GREEN}创建必要的目录...${NC}"
mkdir -p docker/nginx
mkdir -p docker/init-scripts
mkdir -p backend/uploads
mkdir -p backend/logs

# 确保nginx配置文件存在
if [ ! -f "docker/nginx/nginx.conf" ] || [ ! -f "docker/nginx/default.conf" ]; then
  echo -e "${YELLOW}警告: nginx配置文件不存在，请检查${NC}"
fi

# 确保数据库初始化脚本存在
if [ ! -f "docker/init-scripts/01-init.sql" ]; then
  echo -e "${YELLOW}警告: 数据库初始化脚本不存在，请检查${NC}"
fi

# 启动容器
echo -e "${GREEN}启动Docker容器...${NC}"
cd docker
docker-compose up -d

# 检查容器状态
echo -e "${YELLOW}检查容器状态...${NC}"
docker-compose ps

# 显示访问信息
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}VanillaRAGPlus (Docker)已启动!${NC}"
echo -e "${GREEN}后端API: http://localhost:8080${NC}"
echo -e "${GREEN}前端界面: http://localhost:3000${NC}"
echo -e "${GREEN}==================================${NC}"
echo -e "${YELLOW}使用 'docker-compose logs -f' 查看日志${NC}"
echo -e "${YELLOW}使用 'docker-compose down' 停止所有服务${NC}"

# 返回到根目录
cd .. 