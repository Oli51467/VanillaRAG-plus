#!/bin/bash

# 显示彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}启动文档管理系统...${NC}"

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

# 检查虚拟环境是否存在
if [ ! -d "backend/venv" ]; then
  echo -e "${YELLOW}警告: 找不到Python虚拟环境，正在创建...${NC}"
  cd backend
  python -m venv venv
  cd ..
fi

# 检查requirements.txt是否存在
if [ ! -f "backend/requirements.txt" ]; then
  echo -e "${RED}错误: 找不到backend/requirements.txt文件${NC}"
  exit 1
fi

# 启动后端服务
echo -e "${GREEN}启动后端服务...${NC}"
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
echo -e "${GREEN}依赖项安装完成，启动后端服务...${NC}"
python run.py &
BACKEND_PID=$!
cd ..

# 等待后端服务启动
echo -e "${YELLOW}等待后端服务启动...${NC}"
sleep 10

# 启动前端服务
echo -e "${GREEN}启动前端服务...${NC}"
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

# 显示访问信息
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}文档管理系统已启动!${NC}"
echo -e "${GREEN}后端API: http://localhost:8080${NC}"
echo -e "${GREEN}前端界面: http://localhost:3000${NC}"
echo -e "${GREEN}==================================${NC}"
echo -e "${YELLOW}按Ctrl+C停止所有服务${NC}"

# 捕获中断信号
trap "echo -e '${YELLOW}正在停止服务...${NC}'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# 保持脚本运行
wait 