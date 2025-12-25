# Hexin Proxy Server

一个 FastAPI 服务器，提供 OpenAI 兼容的 API 接口，通过代理 Hexin 后端服务来提供 AI 功能。

## 功能特性

- **Chat Completions API**: 兼容 OpenAI 的聊天完成接口
- **Responses API**: 兼容 OpenAI 的推理响应接口 (支持 o3、o4-mini)
- **Embeddings API**: 兼容 OpenAI 的文本嵌入接口
- **模型列表**: 支持列出可用的 AI 模型
- **流式响应**: 支持实时流式聊天响应和推理响应
- **多模型支持**: 支持多种大语言模型和嵌入模型

## 支持的接口

### Chat Completions
- `POST /v1/chat/completions` - 创建聊天完成
- 支持流式和非流式响应
- 支持工具调用和函数调用
- 支持多种模型：GPT、Claude、Gemini、DeepSeek 等

### Responses (推理响应)
- `POST /v1/responses` - 创建推理响应 (专为 o3、o4-mini 等推理模型设计)
- 支持流式和非流式响应
- 支持推理配置 (effort: low/medium/high, summary: brief/detailed)
- 返回详细的推理过程和结果

### Embeddings
- `POST /v1/embeddings` - 创建文本嵌入
- 支持的模型：text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large
- 支持单个和批量文本处理

### Models
- `GET /v1/models` - 列出可用模型
- 返回聊天、推理和嵌入模型列表

## 快速开始

### 1. 安装依赖

```bash
pip install hexin-server --upgrade
```

或者本地安装

```bash
git clone https://github.com/LinXueyuanStdio/hexin-proxy-server.git
cd hexin-proxy-server
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

创建 `.env` 文件：

```env
HITHINK_APP_ID=your_app_id
HITHINK_APP_SECRET=your_app_secret
HITHINK_APP_URL=your_app_url
```

### 3. 启动服务器

```bash
# 直接运行
python -m hexin_server

# 或者指定参数
python -m hexin_server --host 0.0.0.0 --port 8777 --reload
```

### 4. 测试接口

#### Chat Completions 示例

```bash
curl -X POST "http://localhost:8777/v1/chat/completions" \
  -H "Authorization: Bearer sk-fastapi-proxy-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

#### Responses 推理示例

```bash
# 非流式推理响应
curl -X POST "http://localhost:8777/v1/responses" \
  -H "Authorization: Bearer sk-fastapi-proxy-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "o3",
    "input": "估算下海水的总重量",
    "reasoning": {
      "effort": "medium",
      "summary": "detailed"
    }
  }'

# 流式推理响应
curl -X POST "http://localhost:8777/v1/responses" \
  -H "Authorization: Bearer sk-fastapi-proxy-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "o3",
    "input": "估算下海水的总重量",
    "reasoning": {
      "effort": "medium",
      "summary": "detailed"
    },
    "stream": true
  }'
```

#### Embeddings 示例

```bash
curl -X POST "http://localhost:8777/v1/embeddings" \
  -H "Authorization: Bearer sk-fastapi-proxy-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, world!",
    "model": "text-embedding-ada-002"
  }'
```

## 使用 OpenAI 客户端库

```python
import openai

# 配置客户端
client = openai.OpenAI(
    api_key="sk-fastapi-proxy-key-12345",
    base_url="http://localhost:8777/v1"
)

# 聊天完成
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

# 推理响应 (需要使用 requests 库，因为 OpenAI 客户端暂不支持 responses API)
import requests

response = requests.post(
    "http://localhost:8777/v1/responses",
    headers={
        "Authorization": "Bearer sk-fastapi-proxy-key-12345",
        "Content-Type": "application/json"
    },
    json={
        "model": "o3",
        "input": "估算下海水的总重量",
        "reasoning": {
            "effort": "medium",
            "summary": "detailed"
        }
    }
)

# 创建嵌入
embeddings = client.embeddings.create(
    model="text-embedding-ada-002",
    input="Hello, world!"
)
```

## 详细文档

- [Responses API 使用指南](./RESPONSES_API.md) - 详细的推理接口文档
- [Embedding API 使用指南](./EMBEDDING_API.md) - 详细的嵌入接口文档
<!-- - [完整 API 文档](./build/doc_final.md) - 包含所有接口的详细文档 -->

## 项目结构

```
hexin-proxy-server/
├── hexin_server/
│   ├── __init__.py
│   └── __main__.py          # 主服务器代码
├── tests/
│   └── test_embedding.py    # 嵌入接口测试脚本
├── test_openai_client.py    # 增强 OpenAI 客户端测试 (推荐)
├── test_responses.py        # 基础推理接口测试
├── check_server.py          # 服务器验证脚本
├── start_test_server.sh     # 服务器启动脚本
├── RESPONSES_API.md         # 推理API使用指南
├── EMBEDDING_API.md         # 嵌入API使用指南
├── README.md
├── requirements.txt
└── .env.example
```

## 测试

项目包含多种测试脚本来验证功能：

```bash
# 测试嵌入接口
python tests/test_embedding.py

# 使用 OpenAI 标准库测试 (推荐)
python test_openai_client.py

# 基础响应接口测试
python test_responses.py

# 服务器状态检查
python check_server.py
```

### OpenAI 标准库集成

推荐使用 `test_openai_client.py`，它提供了一个增强的 OpenAI 客户端，支持：

- 标准 OpenAI APIs (chat, embeddings, models)
- 自定义 responses API，采用 OpenAI 风格的接口
- 流式和非流式响应支持
- 一致的错误处理和响应格式

```python
from test_openai_client import EnhancedOpenAIClient

client = EnhancedOpenAIClient(
    api_key="sk-fastapi-proxy-key-12345",
    base_url="http://localhost:8777/v1"
)

# 标准聊天完成
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)

# 推理响应
response = client.create_response(
    model="o3",
    input_data="估算下海水的总重量",
    reasoning={"effort": "medium", "summary": "detailed"}
)
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

[License file](./LICENSE)
