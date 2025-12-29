# Tamar Model Client

**Tamar Model Client** 是一款高性能的 Python SDK，通过 gRPC 协议连接 Model Manager 服务，为多个 AI 模型服务商提供统一的调用接口。无论您使用 OpenAI、Google、Azure 还是其他 AI 服务，都可以通过一套 API 轻松切换和管理。

## 🎯 为什么选择 Tamar Model Client？

### 您遇到过这些问题吗？

❌ 需要同时集成 OpenAI、Google、Azure 等多个 AI 服务，每个都有不同的 API？  
❌ 难以统计和控制不同服务商的使用成本？  
❌ 在不同 AI 提供商之间切换需要修改大量代码？  
❌ 每个服务商都有自己的错误处理和重试逻辑？  

### ✅ Tamar Model Client 一站式解决！

🎉 **一个 SDK，访问所有 AI 服务**  
📊 **统一的使用量和成本统计**  
🔄 **无缝切换，一行代码搞定**  
🛡️ **生产级的错误处理和重试机制**

## ✨ 核心特性

### 🔌 多服务商支持
- **OpenAI** (GPT-3.5/4, DALL-E)
- **Google** (Gemini - AI Studio & Vertex AI, Imagen 图像生成)
- **Azure OpenAI** (企业级部署)
- **Anthropic** (Claude)
- **DeepSeek** (深度求索)
- **Perplexity** (搜索增强生成)

### ⚡ 灵活的调用方式
- 🧩 **同步/异步** 双模式客户端
- 📡 **流式/非流式** 响应支持
- 📦 **批量请求** 并行处理
- 🔄 **自动重试** 指数退避策略

### 🛡️ 生产级特性
- 🛡️ **熔断降级** 服务故障时自动切换到 HTTP
- 🚀 **快速降级** 失败立即降级，最大化成功率
- 🔐 **JWT 认证** 安全可靠
- 📊 **使用量追踪** Token 统计与成本计算
- 🆔 **请求追踪** 唯一 request_id 和 origin_request_id 全链路追踪
- ⚠️ **完善错误处理** 详细错误信息和异常堆栈追踪
- ✅ **类型安全** Pydantic v2 验证
- 📦 **批量降级** HTTP 降级支持批量请求
- 🔍 **结构化日志** JSON 格式日志便于监控分析

### 🚀 高性能设计
- 🔗 **gRPC 通信** HTTP/2 长连接
- ♻️ **连接复用** 减少握手开销
- 🎯 **智能路由** 自动选择最优通道
- 📈 **性能监控** 延迟与吞吐量指标

## 📋 安装

```bash
pip install tamar-model-client
```

### 系统要求

- Python ≥ 3.8
- 支持 Windows / Linux / macOS
- 依赖项会自动安装（包括以下核心库）：
  - `grpcio>=1.67.1` - gRPC 通信协议
  - `pydantic` - 数据验证和序列化
  - `PyJWT` - JWT 认证
  - `requests>=2.25.0` - HTTP 降级功能（同步）
  - `aiohttp>=3.7.0` - HTTP 降级功能（异步）
  - `openai` - OpenAI 服务商支持
  - `google-genai` - Google AI 服务商支持

## 🏗️ 项目架构

```
tamar_model_client/
├── 📁 generated/              # gRPC 生成的代码
│   ├── model_service.proto    # Protocol Buffer 定义
│   └── *_pb2*.py             # 生成的 Python 代码
├── 📁 schemas/                # Pydantic 数据模型
│   ├── inputs.py             # 请求模型（ModelRequest, UserContext）
│   └── outputs.py            # 响应模型（ModelResponse, Usage）
├── 📁 enums/                  # 枚举定义
│   ├── providers.py          # AI 服务商（OpenAI, Google, Azure...）
│   ├── invoke.py             # 调用类型（generation, images, image-generation-genai...）
│   └── channel.py            # 服务通道（openai, vertexai...）
├── 📁 core/                   # 核心功能模块
│   ├── base_client.py        # 客户端基类（熔断、降级、配置）
│   ├── http_fallback.py      # HTTP 降级功能（支持批量请求）
│   ├── request_builder.py    # 请求构建器
│   ├── response_handler.py   # 响应处理器
│   ├── logging_setup.py      # 结构化日志配置
│   └── utils.py              # 请求ID管理和工具函数
├── 📄 sync_client.py          # 同步客户端 TamarModelClient
├── 📄 async_client.py         # 异步客户端 AsyncTamarModelClient
├── 📄 error_handler.py        # 增强错误处理和重试策略
├── 📄 circuit_breaker.py      # 熔断器实现
├── 📄 exceptions.py           # 异常层级定义
├── 📄 auth.py                 # JWT 认证管理
├── 📄 json_formatter.py       # JSON 日志格式化器
└── 📄 utils.py                # 工具函数
```

## 🚀 快速开始

### 1️⃣ 客户端初始化

```python
from tamar_model_client import TamarModelClient, AsyncTamarModelClient

# 方式一：使用环境变量（推荐）
client = TamarModelClient()  # 自动读取环境变量配置

# 方式二：代码配置
client = TamarModelClient(
    server_address="localhost:50051",
    jwt_token="your-jwt-token"
)

# 异步客户端
async_client = AsyncTamarModelClient(
    server_address="localhost:50051",
    jwt_secret_key="your-jwt-secret-key"  # 使用密钥自动生成 JWT
)
```

### 2️⃣ 基础示例 - 与 AI 对话

```python
from tamar_model_client import TamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext
from tamar_model_client.enums import ProviderType

# 创建客户端
client = TamarModelClient()

# 构建请求
request = ModelRequest(
    provider=ProviderType.OPENAI,
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己。"}
    ],
    user_context=UserContext(
        user_id="test_user",
        org_id="test_org",
        client_type="python-sdk"
    )
)

# 发送请求
response = client.invoke(request)
print(f"AI 回复: {response.content}")
```


## 📚 详细使用示例

### OpenAI 调用示例

```python
from tamar_model_client import TamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext
from tamar_model_client.enums import ProviderType, InvokeType, Channel

# 创建同步客户端
client = TamarModelClient()

# OpenAI 调用示例
request_data = ModelRequest(
    provider=ProviderType.OPENAI,  # 选择 OpenAI 作为提供商
    channel=Channel.OPENAI,  # 使用 OpenAI 渠道
    invoke_type=InvokeType.CHAT_COMPLETIONS,  # 使用 chat completions 调用类型
    model="gpt-4",  # 指定具体模型
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己。"}
    ],
    user_context=UserContext(
        user_id="test_user",
        org_id="test_org",
        client_type="python-sdk"
    ),
    stream=False,  # 非流式调用
    temperature=0.7,  # 可选参数
    max_tokens=1000,  # 可选参数
)

# 发送请求并获取响应
response = client.invoke(request_data)
if response.error:
    print(f"错误: {response.error}")
else:
    print(f"响应: {response.content}")
    if response.usage:
        print(f"Token 使用情况: {response.usage}")
```

### Google 调用示例 （AI Studio / Vertex AI）

```python
from tamar_model_client import TamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext
from tamar_model_client.enums import ProviderType, InvokeType, Channel

# 创建同步客户端
client = TamarModelClient()

# Google AI Studio 调用示例
request_data = ModelRequest(
    provider=ProviderType.GOOGLE,  # 选择 Google 作为提供商
    channel=Channel.AI_STUDIO,  # 使用 AI Studio 渠道
    invoke_type=InvokeType.GENERATION,  # 使用生成调用类型
    model="gemini-pro",  # 指定具体模型
    contents=[
        {"role": "user", "parts": [{"text": "你好，请介绍一下你自己。"}]}
    ],
    user_context=UserContext(
        user_id="test_user",
        org_id="test_org",
        client_type="python-sdk"
    ),
    temperature=0.7,  # 可选参数
)

# 发送请求并获取响应
response = client.invoke(request_data)
if response.error:
    print(f"错误: {response.error}")
else:
    print(f"响应: {response.content}")
    if response.usage:
        print(f"Token 使用情况: {response.usage}")

# Google Vertex AI 调用示例
vertex_request = ModelRequest(
    provider=ProviderType.GOOGLE,  # 选择 Google 作为提供商
    channel=Channel.VERTEXAI,  # 使用 Vertex AI 渠道
    invoke_type=InvokeType.GENERATION,  # 使用生成调用类型
    model="gemini-pro",  # 指定具体模型
    contents=[
        {"role": "user", "parts": [{"text": "你好，请介绍一下你自己。"}]}
    ],
    user_context=UserContext(
        user_id="test_user",
        org_id="test_org",
        client_type="python-sdk"
    ),
    temperature=0.7,  # 可选参数
)

# 发送请求并获取响应
vertex_response = client.invoke(vertex_request)
if vertex_response.error:
    print(f"错误: {vertex_response.error}")
else:
    print(f"响应: {vertex_response.content}")
    if vertex_response.usage:
        print(f"Token 使用情况: {vertex_response.usage}")

# Google GenAI 图像生成示例
from google.genai import types

genai_image_request = ModelRequest(
    provider=ProviderType.GOOGLE,  # 选择 Google 作为提供商
    channel=Channel.AI_STUDIO,  # 使用 AI Studio 渠道
    invoke_type=InvokeType.IMAGE_GENERATION_GENAI,  # 使用 GenAI 图像生成调用类型
    model="imagen-3.0-generate-001",  # 指定图像生成模型
    prompt="一只可爱的小猫在花园里玩耍",  # 图像描述提示词
    user_context=UserContext(
        user_id="test_user",
        org_id="test_org",
        client_type="python-sdk"
    ),
    # 使用 Google GenAI 类型构建配置
    config=types.GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="1:1",
        safety_filter_level="block_some"
    )
)

# 发送图像生成请求并获取响应
image_response = client.invoke(genai_image_request)
if image_response.error:
    print(f"错误: {image_response.error}")
else:
    print(f"图像生成成功: {image_response.content}")
    if image_response.usage:
        print(f"使用情况: {image_response.usage}")
```

### Azure OpenAI 调用示例

```python
from tamar_model_client import TamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext
from tamar_model_client.enums import ProviderType, InvokeType, Channel

# 创建同步客户端
client = TamarModelClient()

# Azure OpenAI 调用示例
request_data = ModelRequest(
    provider=ProviderType.AZURE,  # 选择 Azure 作为提供商
    channel=Channel.OPENAI,  # 使用 OpenAI 渠道
    invoke_type=InvokeType.CHAT_COMPLETIONS,  # 使用 chat completions 调用类型
    model="gpt-4o-mini",  # 指定具体模型
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己。"}
    ],
    user_context=UserContext(
        user_id="test_user",
        org_id="test_org",
        client_type="python-sdk"
    ),
    stream=False,  # 非流式调用
    temperature=0.7,  # 可选参数
    max_tokens=1000,  # 可选参数
)

# 发送请求并获取响应
response = client.invoke(request_data)
if response.error:
    print(f"错误: {response.error}")
else:
    print(f"响应: {response.content}")
    if response.usage:
        print(f"Token 使用情况: {response.usage}")
```

### 异步调用示例

```python
import asyncio
from tamar_model_client import AsyncTamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext
from tamar_model_client.enums import ProviderType, InvokeType, Channel


async def main():
    # 创建异步客户端
    client = AsyncTamarModelClient()

    # 组装请求参数
    request_data = ModelRequest(
        provider=ProviderType.OPENAI,
        channel=Channel.OPENAI,
        invoke_type=InvokeType.CHAT_COMPLETIONS,
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "你好，请介绍一下你自己。"}
        ],
        user_context=UserContext(
            user_id="test_user",
            org_id="test_org",
            client_type="python-sdk"
        ),
        stream=False,
        temperature=0.7,
        max_tokens=1000,
    )

    # 发送请求并获取响应
    async for r in await client.invoke(request_data):
        if r.error:
            print(f"错误: {r.error}")
        else:
            print(f"响应: {r.content}")
            if r.usage:
                print(f"Token 使用情况: {r.usage}")


# 运行异步示例
asyncio.run(main())
```

### 流式调用示例

```python
import asyncio
from tamar_model_client import AsyncTamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext
from tamar_model_client.enums import ProviderType, InvokeType, Channel


async def stream_example():
    # 创建异步客户端
    client = AsyncTamarModelClient()

    # 组装请求参数
    request_data = ModelRequest(
        provider=ProviderType.OPENAI,
        channel=Channel.OPENAI,
        invoke_type=InvokeType.CHAT_COMPLETIONS,
        model="gpt-4",
        messages=[
            {"role": "user", "content": "你好，请介绍一下你自己。"}
        ],
        user_context=UserContext(
            user_id="test_user",
            org_id="test_org",
            client_type="python-sdk"
        ),
        stream=True,  # 启用流式输出
        temperature=0.7,
    )

    # 发送请求并获取流式响应
    async for response in client.invoke(request_data):
        if response.error:
            print(f"错误: {response.error}")
        else:
            print(f"响应片段: {response.content}", end="", flush=True)
            if response.usage:
                print(f"\nToken 使用情况: {response.usage}")


# 运行流式示例
asyncio.run(stream_example())
```

### 批量调用示例

支持批量处理多个模型请求：

```python
import asyncio
from tamar_model_client import AsyncTamarModelClient
from tamar_model_client.schemas import (
    BatchModelRequest, BatchModelRequestItem,
    UserContext
)
from tamar_model_client.enums import ProviderType, InvokeType, Channel


async def batch_example():
    # 创建异步客户端
    client = AsyncTamarModelClient()

    # 组装批量请求参数
    batch_request = BatchModelRequest(
        user_context=UserContext(
            user_id="test_user",
            org_id="test_org",
            client_type="python-sdk"
        ),
        items=[
            BatchModelRequestItem(
                provider=ProviderType.OPENAI,
                channel=Channel.OPENAI,
                invoke_type=InvokeType.CHAT_COMPLETIONS,
                model="gpt-4",
                messages=[
                    {"role": "user", "content": "第一个问题：什么是人工智能？"}
                ],
                priority=1,
                custom_id="q1"
            ),
            BatchModelRequestItem(
                provider=ProviderType.GOOGLE,
                channel=Channel.AI_STUDIO,
                invoke_type=InvokeType.GENERATION,
                model="gemini-pro",
                contents=[
                    {"role": "user", "parts": [{"text": "第二个问题：什么是机器学习？"}]}
                ],
                priority=2,
                custom_id="q2"
            )
        ]
    )

    # 发送批量请求并获取响应
    response = await client.invoke_batch(batch_request)
    if response.responses:
        for resp in response.responses:
            print(f"\n问题 {resp.custom_id} 的响应:")
            if resp.error:
                print(f"错误: {resp.error}")
            else:
                print(f"内容: {resp.content}")
                if resp.usage:
                    print(f"Token 使用情况: {resp.usage}")


# 运行批量调用示例
asyncio.run(batch_example())
```

### 图像生成调用示例

支持 OpenAI DALL-E、Google Vertex AI 和 Google GenAI 图像生成：

```python
from tamar_model_client import TamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext
from tamar_model_client.enums import ProviderType, InvokeType, Channel

client = TamarModelClient()

# OpenAI DALL-E 图像生成
openai_image_request = ModelRequest(
    provider=ProviderType.OPENAI,
    channel=Channel.OPENAI,
    invoke_type=InvokeType.IMAGE_GENERATION,
    model="dall-e-3",
    prompt="一只穿着西装的猫在办公室里工作",
    user_context=UserContext(
        user_id="test_user",
        org_id="test_org",
        client_type="python-sdk"
    ),
    size="1024x1024",
    quality="hd",
    n=1
)

# Google Vertex AI 图像生成
vertex_image_request = ModelRequest(
    provider=ProviderType.GOOGLE,
    channel=Channel.VERTEXAI,
    invoke_type=InvokeType.IMAGE_GENERATION,
    model="imagegeneration@006",
    prompt="一座美丽的山峰在日出时分",
    user_context=UserContext(
        user_id="test_user",
        org_id="test_org",
        client_type="python-sdk"
    ),
    number_of_images=1,
    aspect_ratio="1:1",
    safety_filter_level="block_some"
)

# Google GenAI 图像生成（新增功能）
genai_image_request = ModelRequest(
    provider=ProviderType.GOOGLE,
    channel=Channel.AI_STUDIO,
    invoke_type=InvokeType.IMAGE_GENERATION_GENAI,  # 新增的调用类型
    model="imagen-3.0-generate-001",
    prompt="科幻风格的城市夜景，霓虹灯闪烁",
    user_context=UserContext(
        user_id="test_user",
        org_id="test_org",
        client_type="python-sdk"
    ),
    config=types.GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="16:9"
    )
)

# 发送请求
for request in [openai_image_request, vertex_image_request, genai_image_request]:
    response = client.invoke(request)
    if response.error:
        print(f"图像生成失败: {response.error}")
    else:
        print(f"图像生成成功: {response.content}")
```

### 文件输入示例

支持处理图像等文件输入（需使用支持多模态的模型，如 gemini-2.0-flash）：

```python
from tamar_model_client import TamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext
from tamar_model_client.enums import ProviderType
from google.genai.types import Part
model_request = ModelRequest(
    provider=ProviderType.GOOGLE,  # 选择 Google作为提供商
    model="gemini-2.0-flash",
    contents=[
        "What is shown in this image?",
        Part.from_uri( # 这个是Google那边的参数支持
            file_uri="https://images.pexels.com/photos/248797/pexels-photo-248797.jpeg",
            mime_type="image/jpeg",
        ),
    ],
    user_context=UserContext(
        org_id="testllm",
        user_id="testllm",
        client_type="conversation-service"
    ),
)
client = TamarModelClient("localhost:50051")
response = client.invoke(
    model_request=model_request
)
```

### 🔄 错误处理最佳实践

SDK 提供了完善的异常体系，便于精确处理不同类型的错误：

```python
from tamar_model_client import TamarModelClient
from tamar_model_client.exceptions import (
    TamarModelException,
    NetworkException,
    AuthenticationException,
    RateLimitException,
    ProviderException,
    TimeoutException
)

client = TamarModelClient()

try:
    response = client.invoke(request)
except TimeoutException as e:
    # 处理超时错误
    logger.warning(f"请求超时: {e.message}, request_id: {e.request_id}")
    # 可以重试或使用更快的模型
except RateLimitException as e:
    # 处理限流错误
    logger.error(f"触发限流: {e.message}")
    # 等待一段时间后重试
    time.sleep(60)
except AuthenticationException as e:
    # 处理认证错误
    logger.error(f"认证失败: {e.message}")
    # 检查 JWT 配置
except NetworkException as e:
    # 处理网络错误（已自动重试后仍失败）
    logger.error(f"网络错误: {e.message}")
    # 可能需要检查网络连接或服务状态
except ProviderException as e:
    # 处理提供商特定错误
    logger.error(f"提供商错误: {e.message}")
    # 根据错误码进行特定处理
    if "insufficient_quota" in str(e):
        # 切换到其他提供商
        pass
except TamarModelException as e:
    # 处理其他所有模型相关错误
    logger.error(f"模型错误: {e.message}")
    logger.error(f"错误上下文: {e.error_context}")
```

### 🔀 多提供商无缝切换

轻松实现提供商之间的切换和降级：

```python
from tamar_model_client import TamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext
from tamar_model_client.enums import ProviderType
from tamar_model_client.exceptions import ProviderException, RateLimitException

client = TamarModelClient()

# 定义提供商优先级
providers = [
    (ProviderType.OPENAI, "gpt-4"),
    (ProviderType.GOOGLE, "gemini-pro"),
    (ProviderType.AZURE, "gpt-4o-mini")
]

user_context = UserContext(
    user_id="test_user",
    org_id="test_org",
    client_type="python-sdk"
)

# 尝试多个提供商直到成功
for provider, model in providers:
    try:
        request = ModelRequest(
            provider=provider,
            model=model,
            messages=[{"role": "user", "content": "Hello"}] if provider != ProviderType.GOOGLE else None,
            contents=[{"role": "user", "parts": [{"text": "Hello"}]}] if provider == ProviderType.GOOGLE else None,
            user_context=user_context
        )
        
        response = client.invoke(request)
        print(f"成功使用 {provider.value} - {model}")
        print(f"响应: {response.content}")
        break
        
    except (ProviderException, RateLimitException) as e:
        logger.warning(f"{provider.value} 失败: {e.message}")
        continue
```

### 🎯 请求上下文管理

使用上下文管理器确保资源正确释放：

```python
from tamar_model_client import TamarModelClient, AsyncTamarModelClient
import asyncio

# 同步客户端上下文管理器
with TamarModelClient() as client:
    response = client.invoke(request)
    print(response.content)
# 自动调用 client.close()

# 异步客户端上下文管理器
async def async_example():
    async with AsyncTamarModelClient() as client:
        response = await client.invoke(request)
        print(response.content)
    # 自动调用 await client.close()

asyncio.run(async_example())
```

### ⏱️ 超时控制

通过环境变量或代码控制请求超时：

```python
import os
from tamar_model_client import TamarModelClient

# 方式一：环境变量设置全局超时
os.environ['MODEL_MANAGER_SERVER_GRPC_TIMEOUT'] = '30'  # 30秒超时

# 方式二：创建客户端时设置
client = TamarModelClient(
    server_address="localhost:50051",
    timeout=30.0  # 30秒超时
)

# 处理超时
try:
    response = client.invoke(request)
except TimeoutException as e:
    logger.error(f"请求超时: {e.message}")
    # 可以尝试更小的模型或减少 max_tokens
```

### 📊 性能监控与指标

获取详细的性能指标和使用统计：

```python
from tamar_model_client import TamarModelClient
import time

client = TamarModelClient()

# 监控单次请求性能
start_time = time.time()
response = client.invoke(request)
latency = time.time() - start_time

print(f"请求延迟: {latency:.2f}秒")
print(f"Request ID: {response.request_id}")
if response.usage:
    print(f"输入 Tokens: {response.usage.prompt_tokens}")
    print(f"输出 Tokens: {response.usage.completion_tokens}")
    print(f"总 Tokens: {response.usage.total_tokens}")
    print(f"预估成本: ${response.usage.total_cost:.4f}")

# 获取熔断器指标
metrics = client.get_resilient_metrics()
if metrics:
    print(f"\n熔断器状态:")
    print(f"- 状态: {metrics['circuit_state']}")
    print(f"- 失败次数: {metrics['failure_count']}")
    print(f"- 上次失败: {metrics['last_failure_time']}")
    print(f"- HTTP降级地址: {metrics['http_fallback_url']}")
```

### 🔧 自定义配置示例

灵活的配置选项满足不同场景需求：

```python
from tamar_model_client import TamarModelClient

# 完整配置示例
client = TamarModelClient(
    # 服务器配置
    server_address="grpc.example.com:443",
    use_tls=True,
    default_authority="grpc.example.com",
    
    # 认证配置
    jwt_secret_key="your-secret-key",
    jwt_expiration=3600,  # 1小时过期
    
    # 重试配置
    max_retries=5,
    retry_delay=1.0,
    
    # 超时配置
    timeout=60.0,
    
    # 熔断降级配置
    resilient_enabled=True,
    http_fallback_url="https://backup.example.com",
    circuit_breaker_threshold=3,
    circuit_breaker_timeout=30
)
```

### 🔐 安全最佳实践

确保 SDK 使用的安全性：

```python
import os
from tamar_model_client import TamarModelClient

# 1. 使用环境变量存储敏感信息
os.environ['MODEL_MANAGER_SERVER_JWT_SECRET_KEY'] = os.getenv('JWT_SECRET')

# 2. 启用 TLS 加密
client = TamarModelClient(
    server_address="grpc.example.com:443",
    use_tls=True
)

# 3. 最小权限原则 - 只请求需要的数据
request = ModelRequest(
    provider=ProviderType.OPENAI,
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "分析这段文本"}],
    user_context=UserContext(
        user_id="limited_user",
        org_id="restricted_org",
        client_type="analysis-service"
    ),
    max_tokens=100  # 限制输出长度
)

# 4. 审计日志
response = client.invoke(request)
logger.info(f"AI请求审计: user={request.user_context.user_id}, model={request.model}, request_id={response.request_id}")
```

### 🚀 并发请求优化

高效处理大量并发请求：

```python
import asyncio
from tamar_model_client import AsyncTamarModelClient
from tamar_model_client.schemas import ModelRequest, UserContext

async def process_batch_async(questions: list[str]):
    """异步并发处理多个问题"""
    async with AsyncTamarModelClient() as client:
        tasks = []
        
        for i, question in enumerate(questions):
            request = ModelRequest(
                provider=ProviderType.OPENAI,
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": question}],
                user_context=UserContext(
                    user_id="batch_user",
                    org_id="test_org",
                    client_type="batch-processor"
                )
            )
            
            # 创建异步任务
            task = asyncio.create_task(client.invoke(request))
            tasks.append((i, task))
        
        # 并发执行所有请求
        results = []
        for i, task in tasks:
            try:
                response = await task
                results.append((i, response.content))
            except Exception as e:
                results.append((i, f"Error: {str(e)}"))
        
        return results

# 使用示例
questions = [
    "什么是人工智能？",
    "解释机器学习的原理",
    "深度学习和机器学习的区别",
    "什么是神经网络？"
]

results = asyncio.run(process_batch_async(questions))
for i, content in results:
    print(f"问题 {i+1} 的回答: {content[:100]}...")
```

## 🛠️ 高级功能

### 🔥 使用场景和最佳实践

#### 使用场景
1. **多模型比较**：同时调用多个服务商的模型，比较输出质量
2. **成本优化**：根据任务类型自动选择性价比最高的模型
3. **高可用架构**：主备模型自动切换，确保服务稳定
4. **统一监控**：集中管理所有 AI 服务的使用量和成本

#### 最佳实践
1. **客户端管理**
   ```python
   # ✅ 推荐：单例模式使用
   client = TamarModelClient()
   # 整个应用生命周期使用同一个客户端
   
   # ❌ 避免：频繁创建客户端
   for i in range(100):
       client = TamarModelClient()  # 不推荐！
   ```

2. **错误处理**
   ```python
   try:
       response = client.invoke(request)
   except TamarModelException as e:
       logger.error(f"Model error: {e.message}, request_id: {e.request_id}")
       # 实施降级策略或重试
   ```

3. **性能优化**
   - 使用批量 API 处理大量请求
   - 启用流式响应减少首字延迟
   - 合理设置 max_tokens 避免浪费

### 🛡️ 熔断降级功能（高可用保障）

SDK 内置了熔断降级机制，当 gRPC 服务不可用时自动切换到 HTTP 服务，确保业务连续性。

#### 工作原理
1. **正常状态**：所有请求通过高性能的 gRPC 协议
2. **熔断触发**：当连续失败达到阈值时，熔断器打开
3. **自动降级**：切换到 HTTP 协议继续提供服务
4. **定期恢复**：熔断器会定期尝试恢复到 gRPC

#### 启用方式
```bash
# 设置环境变量
export MODEL_CLIENT_RESILIENT_ENABLED=true
export MODEL_CLIENT_HTTP_FALLBACK_URL=http://localhost:8080
export MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD=5
export MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT=60
```

#### 使用示例
```python
from tamar_model_client import TamarModelClient

# 客户端会自动处理熔断降级，对使用者透明
client = TamarModelClient()

# 正常使用，无需关心底层协议
response = client.invoke(request)

# 获取熔断器状态（可选）
metrics = client.get_resilient_metrics()
if metrics:
    print(f"熔断器状态: {metrics['circuit_state']}")
    print(f"失败次数: {metrics['failure_count']}")
```

#### 熔断器状态
- **CLOSED**（关闭）：正常工作状态，请求正常通过
- **OPEN**（打开）：熔断状态，所有请求直接降级到 HTTP
- **HALF_OPEN**（半开）：恢复测试状态，允许少量请求测试 gRPC 是否恢复

#### 监控指标
```python
# 获取熔断降级指标
metrics = client.get_resilient_metrics()
# 返回示例：
# {
#     "enabled": true,
#     "circuit_state": "closed",
#     "failure_count": 0,
#     "last_failure_time": null,
#     "http_fallback_url": "http://localhost:8080"
# }
```

### 🚀 快速降级功能（用户体验优化）

在传统的熔断降级基础上，SDK 新增了快速降级功能，进一步提升用户体验：

#### 传统降级 vs 快速降级

**传统模式**：
```
gRPC请求 → 失败 → 重试1 → 失败 → 重试2 → 失败 → ... → 重试N → 失败 → HTTP降级
耗时：(重试次数 × 退避时间) + 降级时间  // 可能需要十几秒
```

**快速降级模式**：
```
gRPC请求 → 失败 → 立即HTTP降级 (或重试1次后降级)
耗时：降级时间  // 通常1-2秒内完成
```

#### 降级策略配置

- **立即降级错误**：`UNAVAILABLE`, `DEADLINE_EXCEEDED`, `CANCELLED` (网络问题)
- **延迟降级错误**：其他错误重试指定次数后降级
- **永不降级错误**：`UNAUTHENTICATED`, `PERMISSION_DENIED`, `INVALID_ARGUMENT` (客户端问题)

#### 批量请求降级支持

快速降级同时支持单个请求和批量请求：

```python
# 单个请求降级
response = client.invoke(request)  # 自动降级到 /v1/invoke

# 批量请求降级  
batch_response = client.invoke_batch(batch_request)  # 自动降级到 /v1/batch-invoke
```

#### 使用示例

```python
from tamar_model_client import TamarModelClient

# 启用快速降级（通过环境变量）
# MODEL_CLIENT_FAST_FALLBACK_ENABLED=true
# MODEL_CLIENT_FALLBACK_AFTER_RETRIES=1

client = TamarModelClient()

# 正常使用，快速降级对用户透明
response = client.invoke(request)
# 如果gRPC不可用，会在1-2秒内自动切换到HTTP并返回结果
```

#### 配置选项详解

```bash
# 启用快速降级（默认false，建议开启）
MODEL_CLIENT_FAST_FALLBACK_ENABLED=true

# 非立即降级的错误，重试多少次后降级（默认1次）
MODEL_CLIENT_FALLBACK_AFTER_RETRIES=1

# 网络错误立即降级（默认配置）
MODEL_CLIENT_IMMEDIATE_FALLBACK_ERRORS=UNAVAILABLE,DEADLINE_EXCEEDED,CANCELLED

# 认证错误永不降级（避免无效降级）
MODEL_CLIENT_NEVER_FALLBACK_ERRORS=UNAUTHENTICATED,PERMISSION_DENIED,INVALID_ARGUMENT
```

### 🔍 请求追踪与监控

SDK 提供了完善的请求追踪功能，便于问题排查和性能监控：

#### 请求 ID 追踪

每个请求都会自动生成唯一的 `request_id`，用于追踪单次请求：

```python
from tamar_model_client import TamarModelClient
from tamar_model_client.core import generate_request_id, set_request_id

# 自动生成 request_id
response = client.invoke(request)
print(f"Request ID: {response.request_id}")

# 手动设置 request_id
custom_request_id = generate_request_id()
set_request_id(custom_request_id)
response = client.invoke(request)
```

#### 原始请求 ID 追踪

对于需要跨多个服务调用的场景，可以使用 `origin_request_id` 进行全链路追踪：

```python
from tamar_model_client.core import set_origin_request_id

# 设置原始请求 ID（通常来自上游服务）
set_origin_request_id("user-provided-id-123")

# 所有后续请求都会携带这个 origin_request_id
response = client.invoke(request)
```

#### 结构化日志

启用 JSON 日志格式后，每条日志都包含完整的追踪信息：

```json
{
  "timestamp": "2025-07-03T14:40:32.729313",
  "level": "INFO",
  "type": "request",
  "uri": "/invoke/openai/chat",
  "request_id": "448a64f4-3bb0-467c-af15-d4181d0ac499",
  "data": {
    "origin_request_id": "user-provided-id-123",
    "provider": "openai",
    "model": "gpt-4",
    "stream": false
  },
  "message": "🚀 Invoke request started"
}
```

#### 错误追踪

错误日志包含异常堆栈和完整上下文：

```json
{
  "timestamp": "2025-07-03T14:40:35.123456",
  "level": "ERROR",
  "type": "response",
  "request_id": "448a64f4-3bb0-467c-af15-d4181d0ac499",
  "data": {
    "origin_request_id": "user-provided-id-123",
    "error_code": "DEADLINE_EXCEEDED",
    "error_message": "Request timeout after 30 seconds",
    "retry_count": 2,
    "fallback_attempted": true
  },
  "exception": {
    "type": "TimeoutException",
    "message": "Request timeout after 30 seconds",
    "traceback": ["Traceback (most recent call last):", "..."]
  }
}
```

### ⚠️ 注意事项

1. **参数说明**
   - **必填参数**：`provider`, `model`, `user_context`
   - **可选参数**：`channel`, `invoke_type`（系统可自动推断）
   - **流式控制**：通过 `stream=True/False` 参数控制

2. **连接管理**
   - gRPC 使用 HTTP/2 长连接，客户端应作为单例使用
   - 如需多实例，务必调用 `client.close()` 释放资源

3. **错误处理**
   - 所有错误包含 `request_id` 和 `origin_request_id` 用于全链路问题追踪
   - 网络错误会自动重试（指数退避）
   - 提供商错误保留原始错误信息
   - 支持异常堆栈追踪，便于问题排查
   - 结构化 JSON 日志格式，便于监控系统集成

## ⚙️ 环境变量配置（推荐）

可以通过 .env 文件或系统环境变量，自动配置连接信息

```bash
export MODEL_MANAGER_SERVER_ADDRESS="localhost:50051"
export MODEL_MANAGER_SERVER_JWT_TOKEN="your-jwt-secret"
export MODEL_MANAGER_SERVER_GRPC_USE_TLS="false"
export MODEL_MANAGER_SERVER_GRPC_DEFAULT_AUTHORITY="localhost"
export MODEL_MANAGER_SERVER_GRPC_MAX_RETRIES="5"
export MODEL_MANAGER_SERVER_GRPC_RETRY_DELAY="1.5"

# 快速降级配置（可选，优化用户体验）
export MODEL_CLIENT_FAST_FALLBACK_ENABLED="true"
export MODEL_CLIENT_HTTP_FALLBACK_URL="http://localhost:8080"
export MODEL_CLIENT_FALLBACK_AFTER_RETRIES="1"
```

或者本地 `.env` 文件

```
# ========================
# 🔌 gRPC 通信配置
# ========================

# gRPC 服务端地址（必填）
MODEL_MANAGER_SERVER_ADDRESS=localhost:50051

# 是否启用 TLS 加密通道（true/false，默认 true）
MODEL_MANAGER_SERVER_GRPC_USE_TLS=true

# 当使用 TLS 时指定 authority（域名必须和证书匹配才需要）
MODEL_MANAGER_SERVER_GRPC_DEFAULT_AUTHORITY=localhost


# ========================
# 🔐 鉴权配置（JWT）
# ========================

# JWT 签名密钥（用于生成 Token）
MODEL_MANAGER_SERVER_JWT_SECRET_KEY=your_jwt_secret_key


# ========================
# 🔁 重试配置（可选）
# ========================

# 最大重试次数（默认 3）
MODEL_MANAGER_SERVER_GRPC_MAX_RETRIES=3

# 初始重试延迟（秒，默认 1.0），指数退避
MODEL_MANAGER_SERVER_GRPC_RETRY_DELAY=1.0


# ========================
# 🛡️ 熔断降级配置（可选）
# ========================

# 是否启用熔断降级功能（默认 false）
MODEL_CLIENT_RESILIENT_ENABLED=false

# HTTP 降级服务地址（当 gRPC 不可用时的备用地址）
MODEL_CLIENT_HTTP_FALLBACK_URL=http://localhost:8080

# 熔断器触发阈值（连续失败多少次后熔断，默认 5）
MODEL_CLIENT_CIRCUIT_BREAKER_THRESHOLD=5

# 熔断器恢复超时（秒，熔断后多久尝试恢复，默认 60）
MODEL_CLIENT_CIRCUIT_BREAKER_TIMEOUT=60


# ========================
# 🚀 快速降级配置（可选，优化体验）
# ========================

# 是否启用快速降级功能（默认 false，建议开启）
# 启用后，gRPC 请求失败时会立即尝试 HTTP 降级，而不是等待所有重试完成
MODEL_CLIENT_FAST_FALLBACK_ENABLED=true

# 降级前的最大 gRPC 重试次数（默认 1）
# 对于非立即降级的错误，重试指定次数后才尝试降级
MODEL_CLIENT_FALLBACK_AFTER_RETRIES=1

# 立即降级的错误类型（逗号分隔，默认网络相关错误）
# 这些错误类型会在第一次失败后立即尝试降级
MODEL_CLIENT_IMMEDIATE_FALLBACK_ERRORS=UNAVAILABLE,DEADLINE_EXCEEDED,CANCELLED

# 永不降级的错误类型（逗号分隔，默认认证相关错误）
# 这些错误类型不会触发降级，通常是客户端问题而非服务不可用
MODEL_CLIENT_NEVER_FALLBACK_ERRORS=UNAUTHENTICATED,PERMISSION_DENIED,INVALID_ARGUMENT


# ========================
# 🔍 日志与监控配置（可选）
# ========================

# 启用结构化 JSON 日志格式（默认 false，建议开启）
# 启用后日志将以 JSON 格式输出，便于监控系统集成
MODEL_CLIENT_ENABLE_JSON_LOGGING=true

# 日志级别设置（DEBUG, INFO, WARNING, ERROR，默认 INFO）
MODEL_CLIENT_LOG_LEVEL=INFO
```

加载后，初始化时无需传参：

```python
from tamar_model_client import TamarModelClient

client = TamarModelClient()  # 将使用环境变量中的配置
```

## 🔧 开发指南

### 环境设置

1. **克隆仓库**
```bash
git clone https://github.com/your-org/tamar-model-client.git
cd tamar-model-client
```

2. **创建虚拟环境**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows
```

3. **安装开发依赖**
```bash
pip install -e .
pip install -r requirements-dev.txt  # 如果有开发依赖
```

### 代码生成

如果需要更新 gRPC 定义：
```bash
# 生成 gRPC 代码
python make_grpc.py

# 验证生成的代码
python -m pytest tests/
```

### 发布流程

```bash
# 1. 更新版本号 (setup.py)
# 2. 构建包
python setup.py sdist bdist_wheel

# 3. 检查构建
twine check dist/*

# 4. 上传到 PyPI
twine upload dist/*
```

### 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📊 性能指标

- **响应延迟**: 平均 < 10ms（gRPC 开销）
- **并发支持**: 1000+ 并发请求
- **连接复用**: HTTP/2 多路复用
- **自动重试**: 指数退避，最多 5 次
- **降级时间**: 快速降级 < 2 秒内完成
- **熔断恢复**: 自动恢复检测，60 秒周期

## 🔧 故障排除

### 常见问题

#### 1. gRPC 连接失败
```bash
# 错误: failed to connect to all addresses
# 解决方案: 检查服务地址和网络连接
export MODEL_MANAGER_SERVER_ADDRESS="correct-host:port"
```

#### 2. JWT 认证失败
```bash
# 错误: UNAUTHENTICATED
# 解决方案: 检查 JWT 密钥或令牌
export MODEL_MANAGER_SERVER_JWT_SECRET_KEY="your-secret-key"
```

#### 3. HTTP 降级失败
```bash
# 错误: HTTP fallback URL not configured
# 解决方案: 配置 HTTP 降级地址
export MODEL_CLIENT_HTTP_FALLBACK_URL="http://backup-server:8080"
```

#### 4. 依赖包缺失
```bash
# 错误: aiohttp library is not installed
# 解决方案: 安装 HTTP 客户端依赖
pip install aiohttp requests
```

### 调试技巧

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或使用环境变量
# MODEL_CLIENT_LOG_LEVEL=DEBUG
```

#### 检查熔断器状态
```python
client = TamarModelClient()
metrics = client.get_resilient_metrics()
print(f"Circuit state: {metrics.get('circuit_state')}")
print(f"Failure count: {metrics.get('failure_count')}")
```

#### 追踪请求流程
```python
from tamar_model_client.core import set_origin_request_id
set_origin_request_id("debug-trace-001")

# 在日志中搜索这个 ID 可以看到完整请求流程
response = client.invoke(request)
```

### 性能优化建议

1. **使用单例客户端**：避免频繁创建客户端实例
2. **启用快速降级**：减少用户感知的错误延迟
3. **合理设置超时**：根据业务需求调整超时时间
4. **监控熔断状态**：及时发现服务问题
5. **使用批量 API**：提高批量处理效率

## 🤝 支持与贡献

### 获取帮助

- 📖 [API 文档](https://docs.tamar-model-client.com)
- 🐛 [提交 Issue](https://github.com/your-org/tamar-model-client/issues)
- 💬 [讨论区](https://github.com/your-org/tamar-model-client/discussions)
- 📝 [更新日志](CHANGELOG.md)

### 相关项目

- [Model Manager Server](https://github.com/your-org/model-manager) - 后端 gRPC 服务
- [Model Manager Dashboard](https://github.com/your-org/model-manager-dashboard) - 管理控制台

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 团队

- **Oscar Ou** - 项目负责人 - [oscar.ou@tamaredge.ai](mailto:oscar.ou@tamaredge.ai)
- [贡献者列表](https://github.com/your-org/tamar-model-client/graphs/contributors)

---

<div align="center">
  <p>
    <b>⭐ 如果这个项目对您有帮助，请给个 Star 支持我们！⭐</b>
  </p>
  <p>
    Made with ❤️ by Tamar Edge Team
  </p>
</div> 