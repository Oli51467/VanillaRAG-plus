# 开发阶段
FROM node:latest AS development
WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY frontend/package*.json ./

# 安装依赖
RUN npm install --verbose

# 复制源代码
COPY frontend/ .

# 暴露端口
EXPOSE 3000

# 开发环境启动命令
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

# 生产阶段
FROM node:latest AS build-stage
WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# 生产环境运行阶段
FROM nginx:alpine AS production
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]