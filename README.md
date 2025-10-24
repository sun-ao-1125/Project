# AI Map Navigator (MCP架构)

基于MCP(Model Context Protocol)架构的AI驱动地图导航程序。

## 功能特性

- ✅ 通过AI理解自然语言导航指令
- ✅ 使用高德地图API获取地理坐标
- ✅ 基于MCP架构的浏览器控制服务器
- ✅ 自动打开浏览器并进入导航状态

## 架构设计

```
用户输入
   ↓
AI解析(Claude)
   ↓
高德地图MCP Server → 获取坐标(通过MCP协议)
   ↓
浏览器控制MCP Server → 打开导航(通过MCP协议)
```

### MCP组件

1. **Browser Control MCP Server** (`mcp_browser_server.py`)
   - 提供浏览器控制能力
   - 工具: `open_url`, `open_map_navigation`
   - 遵循MCP协议标准

2. **Amap MCP Client** (`amap_mcp_client.py`)
   - 连接到高德地图MCP服务器
   - 提供地理编码功能
   - 支持Mock模式用于测试

3. **主应用程序** (`main.py`)
   - AI指令解析(Claude)
   - 通过MCP协议调用高德地图服务
   - 协调各MCP服务器

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置环境变量

#### 方式一: 使用Anthropic Claude

```bash
export AI_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# 配置高德MCP服务器(二选一):
# 方式1: 指定MCP服务器路径
export AMAP_MCP_SERVER_PATH="/path/to/amap-mcp-server"

# 方式2: 使用API Key(将使用Mock客户端)
export AMAP_API_KEY="your-amap-api-key"

# 如果都不设置，将使用内置Mock客户端进行测试
```

#### 方式二: 使用OpenAI兼容API (如七牛)

```bash
export AI_PROVIDER="openai"
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_BASE_URL="https://api.qiniu.com/v1"  # 七牛API端点
export OPENAI_MODEL="gpt-3.5-turbo"  # 可选，默认为gpt-3.5-turbo
export AMAP_API_KEY="your-amap-api-key"  # 可选，不设置将使用模拟数据
```

**支持的OpenAI兼容服务:**
- 七牛AI Token API
- OpenAI官方API
- Azure OpenAI
- 其他遵循OpenAI API标准的服务

### 3. 运行程序

```bash
python main.py
```

### 4. 输入导航请求

支持多种自然语言格式:
- "从北京到上海"
- "我要从广州去深圳"
- "导航到杭州西湖"

## MCP Server独立运行

浏览器控制MCP服务器可以独立运行并被其他MCP客户端调用:

```bash
python mcp_browser_server.py
```

### MCP Server工具列表

**open_url**
- 描述: 在默认浏览器中打开URL
- 参数: `url` (string)

**open_map_navigation**
- 描述: 打开地图导航
- 参数:
  - `start_lng`, `start_lat`: 起点经纬度
  - `end_lng`, `end_lat`: 终点经纬度
  - `start_name`, `end_name`: 地点名称(可选)

## 技术栈

- **AI模型**: 支持多种提供商
  - Anthropic Claude 3.5 Sonnet
  - OpenAI兼容API (包括七牛、OpenAI、Azure等)
- **MCP协议**: Model Context Protocol
- **地图服务**: 高德地图API
- **编程语言**: Python 3.8+

## 项目结构

```
.
├── main.py                 # 主应用程序
├── ai_provider.py          # AI提供商抽象层
├── amap_mcp_client.py      # 高德地图MCP客户端
├── mcp_browser_server.py   # 浏览器控制MCP服务器
├── requirements.txt        # Python依赖
└── README.md              # 项目文档
```

## 配置说明

### AI提供商配置

#### 选项1: Anthropic Claude

1. 注册账号: https://console.anthropic.com/
2. 创建API Key
3. 设置环境变量:
   ```bash
   export AI_PROVIDER="anthropic"
   export ANTHROPIC_API_KEY="your-api-key"
   ```

#### 选项2: 七牛AI Token API

1. 注册账号: https://portal.qiniu.com/
2. 获取API Key
3. 参考文档: https://developer.qiniu.com/aitokenapi/12882/ai-inference-api
4. 设置环境变量:
   ```bash
   export AI_PROVIDER="openai"
   export OPENAI_API_KEY="your-qiniu-api-key"
   export OPENAI_BASE_URL="https://api.qiniu.com/v1"
   export OPENAI_MODEL="gpt-3.5-turbo"
   ```

#### 选项3: 其他OpenAI兼容服务

设置相应的环境变量:
```bash
export AI_PROVIDER="openai"
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://your-service-url/v1"
export OPENAI_MODEL="your-model-name"
```

### 高德地图MCP服务器

**方式1: 使用官方MCP服务器(推荐)**

1. 访问高德地图MCP文档: https://lbs.amap.com/api/mcp-server/gettingstarted
2. 按照文档安装高德MCP服务器
3. 设置环境变量: `export AMAP_MCP_SERVER_PATH="/path/to/amap-mcp-server"`

**方式2: 使用Mock客户端(开发测试)**

如果不设置MCP服务器路径，程序将自动使用内置Mock客户端，支持以下城市坐标:
- 北京、上海、广州、深圳、杭州、成都、西安、重庆、南京、武汉

## 示例

### 使用Anthropic Claude

```bash
$ export AI_PROVIDER="anthropic"
$ export ANTHROPIC_API_KEY="sk-ant-..."
$ python main.py
=== AI Map Navigator (MCP Architecture) ===

Using AI provider: anthropic
Enter your navigation request (e.g., '从北京到上海', '我要从广州去深圳'):
> 从北京到上海

[1/5] Connecting to Amap MCP server...
Note: Using mock Amap MCP client. Set AMAP_MCP_SERVER_PATH or AMAP_API_KEY to use real server.
✓ Connected to Amap MCP server

[2/5] Parsing request with AI...
✓ Parsed: 北京 → 上海

[3/5] Getting coordinates for start location via MCP...
✓ Start: 北京 (116.397128, 39.916527)

[4/5] Getting coordinates for end location via MCP...
✓ End: 上海 (121.473701, 31.230416)

[5/5] Opening navigation in browser...
✓ Navigation opened from 北京 to 上海

Navigation URL: https://uri.amap.com/navigation?from=116.397128,39.916527&to=121.473701,31.230416&mode=car&policy=1&src=ai-navigator&coordinate=gaode&callnative=0

=== Navigation request completed successfully! ===
```

### 使用七牛AI Token API

```bash
$ export AI_PROVIDER="openai"
$ export OPENAI_API_KEY="your-qiniu-key"
$ export OPENAI_BASE_URL="https://api.qiniu.com/v1"
$ python main.py
=== AI Map Navigator (MCP Architecture) ===

Using AI provider: openai
Enter your navigation request (e.g., '从北京到上海', '我要从广州去深圳'):
> 我想去深圳

[1/5] Connecting to Amap MCP server...
Note: Using mock Amap MCP client. Set AMAP_MCP_SERVER_PATH or AMAP_API_KEY to use real server.
✓ Connected to Amap MCP server

[2/5] Parsing request with AI...
✓ Parsed: 当前位置 → 深圳

[3/5] Getting coordinates for start location via MCP...
✓ Start: 当前位置 (116.397128, 39.916527)

[4/5] Getting coordinates for end location via MCP...
✓ End: 深圳 (114.057868, 22.543099)

[5/5] Opening navigation in browser...
✓ Navigation opened from 当前位置 to 深圳

=== Navigation request completed successfully! ===
```

## 扩展功能(后续版本)

- [x] 集成高德地图MCP Server(已通过MCP协议调用)
- [ ] 支持语音输入MCP Server
- [ ] 支持多种地图服务(百度地图等)
- [ ] 桌面应用版本(Electron)
- [ ] 路线偏好设置(避开高速、最短时间等)
- [ ] POI搜索功能
- [ ] 路径规划和路况信息

## 故障排除

**问题**: 浏览器未打开
- 检查系统是否有默认浏览器
- 尝试手动复制URL到浏览器

**问题**: AI解析失败
- 检查AI_PROVIDER环境变量是否正确设置
- 对于Anthropic: 检查ANTHROPIC_API_KEY是否正确设置
- 对于OpenAI兼容API: 检查OPENAI_API_KEY和OPENAI_BASE_URL是否正确设置
- 确保网络连接正常
- 检查API配额是否充足

**问题**: 坐标获取失败
- 检查AMAP_API_KEY是否正确
- 确认高德API配额未超限

**问题**: 如何切换AI提供商
- 设置AI_PROVIDER环境变量为"anthropic"或"openai"
- 确保相应的API密钥已设置

## License

MIT

## Contributing

欢迎提交Issue和Pull Request!
