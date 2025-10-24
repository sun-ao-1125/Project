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
高德地图API/MCP Server → 获取坐标
   ↓
浏览器控制MCP Server → 打开导航
```

### MCP组件

1. **Browser Control MCP Server** (`mcp_browser_server.py`)
   - 提供浏览器控制能力
   - 工具: `open_url`, `open_map_navigation`
   - 遵循MCP协议标准

2. **主应用程序** (`main.py`)
   - AI指令解析(Claude)
   - 地理编码(高德地图API)
   - 协调各MCP服务器

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export AMAP_API_KEY="your-amap-api-key"  # 可选，不设置将使用模拟数据
```

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

- **AI模型**: Claude 3.5 Sonnet (Anthropic)
- **MCP协议**: Model Context Protocol
- **地图服务**: 高德地图API
- **编程语言**: Python 3.8+

## 项目结构

```
.
├── main.py                 # 主应用程序
├── mcp_browser_server.py   # 浏览器控制MCP服务器
├── requirements.txt        # Python依赖
└── README.md              # 项目文档
```

## 配置说明

### 高德地图API Key

1. 注册账号: https://console.amap.com/
2. 创建应用获取API Key
3. 设置环境变量 `AMAP_API_KEY`

如果不设置API Key，程序将使用内置的模拟坐标数据(仅支持北京、上海、广州、深圳、杭州)。

### Anthropic API Key

1. 注册账号: https://console.anthropic.com/
2. 创建API Key
3. 设置环境变量 `ANTHROPIC_API_KEY`

## 示例

```bash
$ python main.py
=== AI Map Navigator (MCP Architecture) ===

Enter your navigation request (e.g., '从北京到上海', '我要从广州去深圳'):
> 从北京到上海

[1/4] Parsing request with AI...
✓ Parsed: 北京 → 上海

[2/4] Getting coordinates for start location...
✓ Start: 北京 (116.397128, 39.916527)

[3/4] Getting coordinates for end location...
✓ End: 上海 (121.473701, 31.230416)

[4/4] Opening navigation in browser...
✓ Navigation opened from 北京 to 上海

Navigation URL: https://uri.amap.com/navigation?from=116.397128,39.916527&to=121.473701,31.230416&mode=car&policy=1&src=ai-navigator&coordinate=gaode&callnative=0

=== Navigation request completed successfully! ===
```

## 扩展功能(后续版本)

- [ ] 集成高德地图MCP Server(替代直接API调用)
- [ ] 支持语音输入
- [ ] 支持多种地图服务(百度地图等)
- [ ] 桌面应用版本(Electron)
- [ ] 路线偏好设置(避开高速、最短时间等)

## 故障排除

**问题**: 浏览器未打开
- 检查系统是否有默认浏览器
- 尝试手动复制URL到浏览器

**问题**: AI解析失败
- 检查ANTHROPIC_API_KEY是否正确设置
- 确保网络连接正常

**问题**: 坐标获取失败
- 检查AMAP_API_KEY是否正确
- 确认高德API配额未超限

## License

MIT

## Contributing

欢迎提交Issue和Pull Request!
