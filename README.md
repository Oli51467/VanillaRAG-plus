# VanillaRAGPlus ..逐步完善中 👨🏻‍💻

这是一个基于 FastAPI 和 Vue3 的文档问答系统，支持文档上传、管理和智能问答功能，使用 Milvus 向量数据库进行文档存储和检索。

## 项目结构

```
.
├── backend/                # 后端代码
│   ├── api/                # API路由
│   │   ├── documents.py    # 文档管理接口
│   │   ├── rag.py          # RAG检索接口
│   │   └── conversations.py # 对话历史接口
│   ├── service/            # 业务服务
│   │   ├── document_service.py  # 文档处理服务
│   │   ├── milvus_service.py    # Milvus向量库服务
│   │   ├── rag_service.py       # RAG检索服务
│   │   ├── llm_service.py       # 大语言模型服务
│   │   ├── conversation_service.py # 对话历史服务
│   │   └── config.py            # 系统配置
│   ├── utils/              # 工具函数
│   ├── db/                 # 数据库相关
│   ├── model_weight/       # 本地模型权重
│   ├── uploads/            # 上传文件存储目录
│   ├── milvus/             # Milvus相关配置
│   ├── main.py             # 主应用入口
│   ├── run.py              # 启动脚本
│   └── requirements.txt    # 依赖项
├── frontend/               # 前端代码
│   ├── src/                # 源代码
│   │   ├── components/     # 组件
│   │   │   ├── Chat.vue           # 聊天组件
│   │   │   └── DocumentManagement.vue # 文档管理组件
│   │   ├── views/          # 视图
│   │   ├── assets/         # 静态资源
│   │   ├── App.vue         # 主应用组件
│   │   └── main.js         # 入口文件
│   ├── index.html          # HTML入口
│   ├── package.json        # 依赖项
│   └── vite.config.js      # Vite配置
├── docker/                 # Docker配置
│   ├── docker-compose.yml  # Docker组合配置
│   └── init-scripts/       # 初始化脚本
├── start.sh                # 项目启动脚本
└── README.md               # 项目说明
```

## 技术栈

### 后端

- FastAPI: 高性能 Web 框架，用于构建 API 接口
- LangChain: 大语言模型应用框架，用于构建 RAG 应用
- Milvus: 开源向量数据库，用于高效向量检索
- PyPDF/docx2txt: 文档解析库，支持多种格式的文档解析
- PostgreSQL: 关系型数据库，用于存储对话历史和文档元数据
- BGE 模型: 用于文本向量化和相关性重排序

### 前端

- Vue 3: 渐进式 JavaScript 框架
- Element Plus: UI 组件库
- Axios: HTTP 客户端

## 功能特性

- 文档上传与管理：支持 PDF、TXT、DOCX 格式文档的上传、查看和删除
- 文档向量化：自动解析文档内容并存储到 Milvus 向量数据库
- 智能问答：基于 RAG(检索增强生成)技术的文档智能问答
- 混合检索技术：结合语义检索和关键词检索的混合检索策略，提高检索精度和召回率
- 对话历史：保存与文档的交互对话历史
- 问题优化：支持问题重写扩展和相关性判断，提高检索质量
- 检索结果重排：使用 BGE-Reranker 优化检索结果相关性

## 安装与运行

### 数据库

Step1：使用 Docker Compose 启动 PostgreSQL 数据库：

```bash
cd docker
docker-compose up -d
```

这将启动以下服务：

- PostgreSQL: 存储对话历史和文档元数据
- pgAdmin: 数据库管理工具(可选)，访问地址为 http://localhost:5050

Step2：安装基础中间件

```shell
// 安装Redis
$ docker pull redis:6.2.12
$ docker run --name redis -p 6379:6379 -d redis:6.2.12 --requirepass "52497Vr62K94qeksg82679o22kr774ee" --appendonly yes

// 安装Milvus
$ mkdir milvus && cd milvus
$ curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
$ ./standalone_embed.sh start

// 建议打开Milvus的账号验证
$ docker exec -it milvus-standalone /bin/bash
$ apt-get update && apt-get install vim -y
$ vim /milvus/configs/milvus.yaml                    //  将authorizationEnabled参数改为true
$ exit
$ docker restart milvus-standalone
$ cd script
$ python3 milvus_password.py
```

Step3：下载所需模型

```shell
$ mkdir model_weight
$ cd script
$ python3 download_models.py
```

### 一键启动

使用项目根目录的`start.sh`脚本一键启动整个应用：

```bash
chmod +x start.sh  # 添加执行权限
./start.sh
```

系统启动后：

- 后端 API: http://localhost:8080
- 前端界面: http://localhost:3000

## 使用说明

1. 在"文档管理"页面，您可以上传、查看和删除文档
2. 上传文档后，系统会自动解析文档内容并存储到向量数据库
3. 在"开启对话"页面，您可以与上传的文档进行问答交互
4. 系统会保存对话历史，您可以查看历史对话内容

## 部署方式

### 方式一：使用 Docker 部署

#### 前提条件

- 安装 [Docker](https://docs.docker.com/get-docker/)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/)

#### 部署步骤

1. 克隆代码仓库

```bash
git clone <仓库地址>
cd VanillaRAGPlus
```

2. 运行部署脚本

```bash
./start-docker.sh
```

或者手动执行以下命令：

```bash
# 创建必要的目录
mkdir -p docker/nginx
mkdir -p docker/init-scripts
mkdir -p backend/uploads
mkdir -p backend/logs

# 启动服务
cd docker
docker-compose up -d
```

3. 访问系统

- 前端界面：http://localhost:3000
- 后端 API：http://localhost:8080

4. 停止服务

```bash
cd docker
docker-compose down
```

### 方式二：本地开发环境

#### 前提条件

- Python 3.12+
- Node.js 18+
- 安装 Conda 或其他虚拟环境管理工具

#### 启动步骤

1. 克隆代码仓库

```bash
git clone <仓库地址>
cd VanillaRAGPlus
```

2. 使用启动脚本

```bash
./start.sh
```

## Docker 容器说明

本项目使用以下 Docker 容器：

1. **API 容器**：

   - 运行后端 FastAPI 服务
   - 暴露端口：8080

2. **Web 容器**：

   - 开发环境：运行 Vue.js 开发服务器
   - 生产环境：Nginx 服务静态文件
   - 暴露端口：3000 (开发) / 80 (生产)

3. **PostgreSQL 容器**：

   - 存储系统元数据
   - 暴露端口：5433 (宿主机) -> 5432 (容器内)

4. **Redis 容器**：

   - 用于缓存
   - 暴露端口：6379

5. **Milvus 容器**：
   - 向量数据库
   - 暴露端口：19530, 9091

## 生产环境部署

对于生产环境部署，推荐以下配置：

1. 修改 docker-compose.yml，将 web 服务的构建目标改为 production：

```yaml
web:
  build:
    context: ..
    dockerfile: docker/web.Dockerfile
    target: production # 改为 production
```

2. 添加 HTTPS 支持：

   - 在 Nginx 配置中添加 SSL 证书
   - 使用反向代理如 Traefik 或 Nginx Proxy Manager

3. 添加环境变量文件 .env，设置敏感配置：
   - 数据库密码
   - API 密钥
   - 其他配置

## 常见问题

1. **容器无法启动**

   - 检查端口是否被占用
   - 查看日志：`docker-compose logs -f [服务名]`

2. **前端无法连接后端**

   - 检查 VITE_API_URL 环境变量是否正确设置
   - 检查后端容器是否正常运行

3. **数据库连接失败**
   - 检查 DATABASE_URL 环境变量
   - 确认 PostgreSQL 容器健康状态
