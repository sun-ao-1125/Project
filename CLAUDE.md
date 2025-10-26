# CLAUDE.md - AI Navigator 项目指南

本文档为 AI 助手（如 Claude）提供项目架构、开发约定和最佳实践指南，帮助 AI 更好地理解和协助开发本项目。

## 项目概述

**AI Map Navigator** 是一个基于 MCP（Model Context Protocol）架构的 AI 驱动地图导航程序。它通过自然语言理解用户的导航需求，调用高德地图 API 获取地理坐标，并在浏览器中自动打开导航。

### 核心特性
- 自然语言导航指令解析
- 基于 MCP 协议的模块化架构
- 支持多种 AI 提供商（Anthropic Claude、OpenAI 兼容 API）
- 高德地图集成（通过 MCP Server）
- 浏览器自动控制
- 语音识别输入支持

## 项目架构

### 架构图

```
用户输入（文本/语音）
   ↓
AI Provider（Claude/OpenAI）→ 解析导航意图
   ↓
Amap MCP Client → 高德地图 MCP Server → 获取坐标
   ↓
Browser Control MCP Server → 打开浏览器导航
```

### 关键模块

#### 1. AI Provider 层 (`ai_provider.py`)
- **职责**: AI 服务提供商抽象层
- **支持的提供商**:
  - Anthropic Claude (claude-3.5-sonnet)
  - OpenAI 兼容 API（七牛、OpenAI、Azure 等）
- **主要功能**:
  - `create_ai_provider()`: 工厂方法，根据环境变量创建 AI 提供商
  - `get_completion()`: 统一的 AI 调用接口

#### 2. MCP 客户端层
##### 通用 MCP 客户端 (`mcp_client.py`)
- **职责**: 实现 MCP 协议客户端
- **支持的传输方式**:
  - STDIO: 标准输入输出（用于本地 MCP 服务器）
  - SSE: Server-Sent Events（用于远程 HTTP 服务器）
- **认证方式**:
  - Bearer Token
  - API Key
- **主要功能**:
  - `create_mcp_client()`: 创建 MCP 客户端实例
  - `connect()`: 连接到 MCP 服务器
  - `list_tools()`: 列出可用工具
  - `call_tool()`: 调用 MCP 工具

##### 高德地图 MCP 客户端 (`amap_mcp_client.py`)
- **职责**: 高德地图服务的 MCP 客户端封装
- **模式**:
  - **真实模式**: 连接到官方高德 MCP 服务器
  - **Mock 模式**: 使用内置模拟数据（用于开发测试）
- **主要功能**:
  - `create_amap_client()`: 工厂方法，根据配置创建客户端
  - `geocode()`: 地理编码（地址 → 坐标）

#### 3. MCP 服务器层 (`mcp_browser_server.py`)
- **职责**: 浏览器控制 MCP 服务器
- **提供的工具**:
  - `open_url`: 在默认浏览器中打开 URL
  - `open_map_navigation`: 打开地图导航（带起点终点坐标）
- **特点**: 可独立运行，供其他 MCP 客户端调用

#### 4. 语音识别模块 (`voice_recognizer.py`)
- **职责**: 语音输入识别
- **支持的引擎**:
  - Vosk（离线识别）
  - Google Speech Recognition（在线识别）
- **模型**: 使用中文语音模型 (`model-small-cn`)

#### 5. 主应用程序 (`main.py`)
- **职责**: 协调所有模块，实现完整的导航流程
- **流程**:
  1. 连接到高德 MCP 服务器
  2. 使用 AI 解析用户输入（提取起点和终点）
  3. 通过 MCP 调用高德地图服务获取坐标
  4. 打开浏览器导航

## 文件夹结构和命名规则

```
.
├── src/
│   └── ai_navigator/           # 主要源代码包
│       ├── __init__.py         # 包初始化，版本信息
│       ├── main.py             # 主应用程序入口
│       ├── ai_provider.py      # AI 提供商抽象层
│       ├── mcp_client.py       # 通用 MCP 客户端实现
│       ├── amap_mcp_client.py  # 高德地图 MCP 客户端
│       ├── mcp_browser_server.py # 浏览器控制 MCP 服务器
│       └── voice_recognizer.py # 语音识别模块
│
├── tests/                      # 测试文件（镜像 src 结构）
│   ├── __init__.py
│   ├── conftest.py            # pytest 配置和共享 fixtures
│   ├── test_main.py           # 主应用程序测试
│   ├── test_ai_provider.py    # AI 提供商测试
│   ├── test_mcp_client.py     # MCP 客户端测试
│   ├── test_amap_mcp_client.py # 高德客户端测试
│   ├── test_mcp_browser_server.py # 浏览器服务器测试
│   └── test_voice_recognizer.py # 语音识别测试
│
├── examples/                   # 示例代码和用法演示
│   └── mcp_client_example.py  # MCP 客户端使用示例
│
├── .github/
│   └── workflows/
│       └── ci.yml             # CI/CD 流水线配置
│
├── model-small-cn/            # Vosk 中文语音识别模型
│
├── pyproject.toml             # 项目配置（PEP 621 标准）
├── requirements.txt           # Python 依赖列表
├── README.md                  # 项目文档（中文）
├── MCP_CLIENT_README.md       # MCP 客户端专项文档
└── CLAUDE.md                  # 本文件（AI 助手指南）
```

### 命名约定

#### Python 文件和模块
- **文件名**: 小写字母 + 下划线（snake_case）
  - 示例: `ai_provider.py`, `mcp_client.py`
- **测试文件**: `test_` 前缀
  - 示例: `test_ai_provider.py`

#### 类命名
- **类名**: 大驼峰命名（PascalCase）
  - 示例: `AIProvider`, `MCPClient`, `AmapMCPClient`

#### 函数和方法
- **函数名**: 小写字母 + 下划线（snake_case）
  - 示例: `create_ai_provider()`, `get_completion()`, `call_tool()`
- **私有方法**: 单下划线前缀
  - 示例: `_parse_response()`, `_validate_input()`

#### 变量
- **局部变量**: 小写字母 + 下划线
  - 示例: `start_location`, `end_coordinates`
- **常量**: 全大写 + 下划线
  - 示例: `DEFAULT_MODEL`, `MAX_RETRIES`

#### 环境变量
- 全大写 + 下划线
- 示例: `AI_PROVIDER`, `ANTHROPIC_API_KEY`, `AMAP_MCP_SERVER_PATH`

## 代码约定和最佳实践

### 1. 类型提示
- **必须**: 所有函数参数和返回值都应使用类型提示
```python
async def get_location_coordinates(location_name: str, mcp_client: MCPClient) -> dict:
    pass
```

### 2. 异步编程
- **MCP 客户端**: 所有 MCP 相关操作必须使用 `async/await`
- **AI 调用**: 推荐使用异步方式
```python
async def call_tool(self, tool_name: str, arguments: dict) -> dict:
    result = await self._send_request("tools/call", {
        "name": tool_name,
        "arguments": arguments
    })
    return result
```

### 3. 错误处理
- **使用具体异常**: 避免捕获通用 `Exception`
- **提供清晰错误信息**: 包含上下文信息
```python
try:
    result = await mcp_client.call_tool("geocode", {"address": location})
except ConnectionError as e:
    raise RuntimeError(f"Failed to connect to MCP server: {e}")
```

### 4. 文档字符串
- **格式**: 使用 Google 风格的 docstring
- **必须包含**: 简短描述、参数说明、返回值说明
```python
def create_ai_provider():
    """
    Create an AI provider based on environment configuration.
    
    Environment variables:
        AI_PROVIDER: Provider type ('anthropic' or 'openai')
        ANTHROPIC_API_KEY: Anthropic API key (if using Anthropic)
        OPENAI_API_KEY: OpenAI API key (if using OpenAI)
        OPENAI_BASE_URL: OpenAI API base URL (optional)
        OPENAI_MODEL: Model name (optional, defaults to gpt-3.5-turbo)
    
    Returns:
        AIProvider: Configured AI provider instance
        
    Raises:
        ValueError: If AI_PROVIDER is not set or invalid
    """
```

### 5. 依赖注入
- **推荐**: 通过参数传递依赖，而非全局变量
- **工厂模式**: 使用工厂函数创建复杂对象
```python
# 好的实践
def create_amap_client() -> AmapMCPClient:
    server_path = os.getenv("AMAP_MCP_SERVER_PATH")
    if server_path:
        return AmapMCPClient(server_path=server_path)
    return MockAmapClient()
```

### 6. 环境配置
- **环境变量**: 所有配置通过环境变量管理
- **.env 文件支持**: 使用 `python-dotenv` 自动加载 `.env` 文件
- **优先级**: 系统环境变量 > `.env` 文件
- **默认值**: 提供合理的默认值或 Mock 模式
```python
# 在应用入口加载配置
from ai_navigator.config import load_config
load_config()  # 自动加载 .env 文件

# 然后使用 os.getenv() 读取配置
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
```

### 7. 日志和调试
- **使用 print 输出**: 项目使用简单的 print 语句提供用户反馈
- **进度提示**: 关键步骤显示进度（如 `[1/5] Connecting...`）
- **emoji 标记**: 使用 ✓ 表示成功，✗ 表示失败
```python
print(f"[{step}/{total_steps}] Getting coordinates for start location via MCP...")
print(f"✓ Start: {location_name} ({lng}, {lat})")
```

## 测试规则

### 测试框架
- **主框架**: pytest
- **异步测试**: pytest-asyncio
- **Mock 工具**: pytest-mock
- **覆盖率**: pytest-cov

### 测试组织
```python
# tests/test_module_name.py
import pytest
from ai_navigator.module_name import function_to_test

class TestClassName:
    """测试类应该对应源代码中的类"""
    
    def test_method_name_scenario(self):
        """测试方法名应描述测试场景"""
        pass
    
    @pytest.mark.asyncio
    async def test_async_method(self):
        """异步测试使用 pytest.mark.asyncio 装饰器"""
        pass
```

### 测试覆盖率要求
- **最低覆盖率**: 目标 80%+
- **关键模块**: AI Provider, MCP Client 应达到 90%+
- **Mock 测试**: 外部 API 调用必须使用 Mock

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_ai_provider.py

# 查看覆盖率
pytest --cov=src --cov-report=html

# 详细输出
pytest -v
```

### Fixtures
- **共享 fixtures**: 定义在 `tests/conftest.py`
- **作用域**: 根据需要选择 `function`, `class`, `module`, `session`
```python
# conftest.py
import pytest

@pytest.fixture
def mock_ai_provider():
    """提供 Mock AI Provider"""
    pass
```

## CI/CD 工作流

### Lint 阶段
- **Black**: 代码格式化检查
- **isort**: import 排序检查
- **Flake8**: 代码风格检查（PEP 8）
- **Pylint**: 代码质量分析
- **MyPy**: 类型检查

### Test 阶段
- **Python 版本**: 3.10, 3.11, 3.12（矩阵构建）
- **覆盖率报告**: 上传到 Codecov
- **覆盖率工件**: 保存 HTML 报告（30 天）

### Build 阶段
- **依赖验证**: 确保所有模块可导入
- **语法检查**: 使用 `py_compile`
- **构建分发包**: 生成 wheel 和 tar.gz

### Security 阶段
- **Bandit**: 安全漏洞扫描
- **Safety**: 依赖项漏洞检查

## 依赖管理

### 核心依赖
```toml
[project.dependencies]
aiohttp>=3.9.0              # 异步 HTTP 客户端
websockets>=12.0            # WebSocket 支持
anthropic>=0.18.0           # Anthropic API
httpx>=0.25.0               # HTTP 客户端
mcp>=0.9.0                  # MCP 协议实现
SpeechRecognition>=3.8.1    # 语音识别
pyaudio>=0.2.11             # 音频输入/输出
vosk>=0.3.44                # 离线语音识别
python-dotenv>=1.0.0        # .env 文件支持
```

### 开发依赖
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-mock>=3.11.0",
    "pytest-cov>=4.1.0",
]
```

## AI 生成代码时的特殊注意事项

### 1. MCP 协议实现
- **遵循 MCP 规范**: 确保请求/响应格式符合 MCP 协议
- **工具调用**: 工具名称和参数必须与 MCP Server 定义一致
```python
# 高德地图 MCP Server 工具
tools = ["maps_geo", "maps_text_search", "maps_route_planning"]

# 调用示例
result = await mcp_client.call_tool("maps_geo", {
    "address": "北京市朝阳区"
})
```

### 2. 多 AI 提供商支持
- **统一接口**: 所有 AI 提供商必须实现相同的接口
- **环境变量**: 通过 `AI_PROVIDER` 切换提供商
- **错误处理**: 处理不同提供商的特定错误

### 3. Mock 模式
- **开发友好**: 在没有真实 API Key 时也能运行
- **测试数据**: 提供常见城市的坐标数据
```python
MOCK_LOCATIONS = {
    "北京": {"lng": 116.397128, "lat": 39.916527},
    "上海": {"lng": 121.473701, "lat": 31.230416},
    # ... 更多城市
}
```

### 4. 异步上下文管理
- **资源清理**: 使用 `async with` 确保资源正确释放
```python
async with create_mcp_client(...) as client:
    await client.connect()
    result = await client.call_tool(...)
```

### 5. 用户体验
- **进度反馈**: 每个步骤提供清晰的进度提示
- **错误提示**: 错误信息应易于理解，包含解决建议
- **自然语言**: 支持多种自然语言表达方式

## 常见任务和命令

### 开发环境设置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -e ".[dev]"
```

### 代码质量检查
```bash
# 格式化代码
black src/ tests/

# 排序 imports
isort src/ tests/

# 代码检查
flake8 src/ tests/
pylint src/**/*.py tests/**/*.py

# 类型检查
mypy src/ tests/ --ignore-missing-imports
```

### 运行应用
```bash
# 使用 Anthropic Claude
export AI_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="sk-ant-..."
python -m ai_navigator.main

# 使用 OpenAI 兼容 API
export AI_PROVIDER="openai"
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.qiniu.com/v1"
python -m ai_navigator.main

# 独立运行 MCP 服务器
python -m ai_navigator.mcp_browser_server
```

## 自动更新 CLAUDE.md

### 触发条件
当以下文件或目录发生变化时，应自动更新本文件：
- `src/ai_navigator/**/*.py` - 源代码结构变化
- `tests/**/*.py` - 测试结构变化
- `pyproject.toml` - 依赖或配置变化
- `.github/workflows/*.yml` - CI/CD 流程变化
- `README.md` - 项目文档重大更新

### 实施方案
由于可能没有工作流修改权限，建议采用以下方式：
1. **手动审查**: 在 PR review 时检查是否需要更新 CLAUDE.md
2. **定期更新**: 每次重大功能发布时更新本文件
3. **Patch 方式**: 使用 git patch 提供更新建议

如果需要添加自动更新 workflow，可参考以下 patch：

```yaml
# .github/workflows/update-claude-md.yml
name: Update CLAUDE.md

on:
  push:
    branches: [ main ]
    paths:
      - 'src/**/*.py'
      - 'tests/**/*.py'
      - 'pyproject.toml'
      - '.github/workflows/*.yml'
      - 'README.md'

jobs:
  update-documentation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Check if CLAUDE.md needs update
        id: check
        run: |
          # 添加检查逻辑
          echo "需要手动审查并更新 CLAUDE.md"
          
      - name: Create Issue
        if: steps.check.outputs.needs_update == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '📝 CLAUDE.md 需要更新',
              body: '检测到项目结构变化，请更新 CLAUDE.md 文件',
              labels: ['documentation']
            })
```

**说明**: 由于自动化更新文档内容需要 AI 参与且较为复杂，建议采用"创建 Issue 提醒"的方式，而非完全自动更新。这样可以确保文档质量和准确性。

## 扩展和未来计划

### 待实现功能
- [ ] 支持更多地图服务（百度地图、腾讯地图）
- [ ] 桌面应用版本（Electron）
- [ ] 路线偏好设置（避开高速、最短时间等）
- [ ] POI 搜索功能
- [ ] 实时路况信息
- [ ] 多目的地路径规划

### 架构改进
- [ ] 插件化的 AI Provider
- [ ] 可配置的 MCP Server 注册表
- [ ] 完整的日志系统（替换 print）
- [x] .env 配置文件支持（已实现 v0.1.0）
- [ ] 高级配置文件支持（YAML/TOML）

## 参考资源

- **MCP 协议文档**: https://modelcontextprotocol.io/
- **高德地图 API**: https://lbs.amap.com/
- **Anthropic Claude API**: https://docs.anthropic.com/
- **OpenAI API**: https://platform.openai.com/docs/
- **七牛 AI Token API**: https://developer.qiniu.com/aitokenapi/

## 版本历史

- **v0.1.0** (当前版本)
  - 初始版本
  - 基本的导航功能
  - 多 AI 提供商支持
  - MCP 架构实现
  - 语音识别支持

---

**最后更新**: 2025-10-25
**维护者**: AI Navigator Team
