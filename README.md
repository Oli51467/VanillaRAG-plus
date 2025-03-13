# OrdinaryRAG 超普通的RAG..逐步完善中👨🏻‍💻

这是一个基于FastAPI和Vue3的文档问答系统，支持文档上传、管理和智能问答功能，使用Milvus向量数据库进行文档存储和检索。

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
- FastAPI: 高性能Web框架，用于构建API接口
- LangChain: 大语言模型应用框架，用于构建RAG应用
- Milvus: 开源向量数据库，用于高效向量检索
- PyPDF/docx2txt: 文档解析库，支持多种格式的文档解析
- PostgreSQL: 关系型数据库，用于存储对话历史和文档元数据
- BGE模型: 用于文本向量化和相关性重排序

### 前端
- Vue 3: 渐进式JavaScript框架
- Element Plus: UI组件库
- Axios: HTTP客户端

## 功能特性

- 文档上传与管理：支持PDF、TXT、DOCX格式文档的上传、查看和删除
- 文档向量化：自动解析文档内容并存储到Milvus向量数据库
- 智能问答：基于RAG(检索增强生成)技术的文档智能问答
- 混合检索技术：结合语义检索和关键词检索的混合检索策略，提高检索精度和召回率
- 对话历史：保存与文档的交互对话历史
- 问题优化：支持问题重写扩展和相关性判断，提高检索质量
- 检索结果重排：使用BGE-Reranker优化检索结果相关性

## 安装与运行

### 数据库

使用Docker Compose启动PostgreSQL数据库：

```bash
cd docker
docker-compose up -d
```

这将启动以下服务：
- PostgreSQL: 存储对话历史和文档元数据
- pgAdmin: 数据库管理工具(可选)，访问地址为http://localhost:5050

### 一键启动

使用项目根目录的`start.sh`脚本一键启动整个应用：

```bash
chmod +x start.sh  # 添加执行权限
./start.sh
```

系统启动后：
- 后端API: http://localhost:8080
- 前端界面: http://localhost:3000

## 使用说明

1. 在"文档管理"页面，您可以上传、查看和删除文档
2. 上传文档后，系统会自动解析文档内容并存储到向量数据库
3. 在"开启对话"页面，您可以与上传的文档进行问答交互
4. 系统会保存对话历史，您可以查看历史对话内容 