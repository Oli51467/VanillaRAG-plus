# 文档管理系统

这是一个基于FastAPI和Vue 3的文档管理系统，支持文档上传、查看和删除功能，并使用Faiss向量数据库进行文档存储和检索。

## 项目结构

```
.
├── backend/                # 后端代码
│   ├── app/                # 应用代码
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务服务
│   │   └── utils/          # 工具函数
│   ├── uploads/            # 上传文件存储目录
│   ├── vector_db/          # 向量数据库存储目录
│   ├── .env                # 环境变量
│   ├── requirements.txt    # 依赖项
│   └── run.py              # 启动脚本
├── frontend/               # 前端代码
│   ├── src/                # 源代码
│   │   ├── components/     # 组件
│   │   ├── views/          # 视图
│   │   ├── App.vue         # 主应用组件
│   │   └── main.js         # 入口文件
│   ├── index.html          # HTML入口
│   ├── package.json        # 依赖项
│   └── vite.config.js      # Vite配置
└── README.md               # 项目说明
```

## 技术栈

### 后端
- FastAPI: 高性能Web框架
- LangChain: 大语言模型应用框架
- Faiss: 高效向量检索库
- PyPDF, docx2txt: 文档解析库

### 前端
- Vue 3: 渐进式JavaScript框架
- Element Plus: UI组件库
- Axios: HTTP客户端

## 功能特性

- 文档上传：支持PDF、TXT、DOCX格式
- 文档管理：查看和删除已上传的文档
- 文档向量化：自动解析文档内容并存储到Faiss向量数据库

## 安装与运行

### 后端

1. 进入后端目录
   ```
   cd backend
   ```

2. 创建并激活虚拟环境
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. 安装依赖
   ```
   pip install -r requirements.txt
   ```

4. 配置环境变量
   编辑`.env`文件，设置OpenAI API密钥
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

5. 启动服务
   ```
   python run.py
   ```

### 前端

1. 进入前端目录
   ```
   cd frontend
   ```

2. 安装依赖
   ```
   npm install
   ```

3. 启动开发服务器
   ```
   npm run dev
   ```

4. 访问应用
   打开浏览器访问 http://localhost:3000

## 使用说明

1. 在"文档管理"页面，可以上传、查看和删除文档
2. 上传文档后，系统会自动解析文档内容并存储到向量数据库
3. 聊天功能将在后续版本中实现 