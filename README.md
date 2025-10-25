# AI 驱动的地图导航系统

一个基于 MCP (Model Context Protocol) 的智能导航系统，支持文本和语音输入，自动打开百度地图或高德地图并进入导航状态。

## 功能特性

- 🎤 **多种输入方式**: 支持文本和语音输入
- 🤖 **AI 智能解析**: 基于 Claude AI (MCP) 理解用户意图，提取起点和终点
- 🗺️ **多地图支持**: 支持百度地图和高德地图
- 🚀 **自动化导航**: 自动打开浏览器并设置导航路线
- 🔧 **灵活配置**: 支持环境变量配置

## 系统架构

```
用户输入 (文字/语音)
    ↓
输入处理层 (语音转文字)
    ↓
MCP 客户端 (AI 理解与决策)
    ↓
浏览器自动化层 (Playwright)
    ↓
地图服务 (百度地图/高德地图)
```

## 三人开发分工

### Developer 1: 输入处理与 MCP 客户端 (`developer1_input_handler.py`)
- ✅ 语音识别模块 (使用 Google Speech Recognition)
- ✅ 文本输入接口
- ✅ MCP 客户端实现 (基于 Anthropic Claude API)
- ✅ 智能提取导航起点和终点信息
- ✅ 回退解析机制（当 API 调用失败时）

### Developer 2: 地图服务集成与浏览器自动化 (`developer2_map_automation.py`)
- ✅ 浏览器自动化框架 (Playwright)
- ✅ 百度地图自动化逻辑
- ✅ 高德地图自动化逻辑
- ✅ 地图服务工厂模式
- ✅ URL 参数编码和路由导航

### Developer 3: 系统协调与主控逻辑 (`developer3_main_coordinator.py`)
- ✅ 主程序入口和命令行接口
- ✅ 模块间协调
- ✅ 错误处理与日志系统
- ✅ 配置管理 (`config.py`)
- ✅ 用户友好的 CLI 交互

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/bjcq666/Project.git
cd Project
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入必要的 API 密钥：

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEFAULT_MAP_SERVICE=baidu
```

## 使用方法

### 文本输入模式（推荐）

```bash
python developer3_main_coordinator.py --text
```

然后输入导航指令，例如：
- "从北京到上海"
- "去天安门"
- "用高德地图从杭州到苏州"

### 语音输入模式

```bash
python developer3_main_coordinator.py --voice
```

听到提示后，说出导航指令。

### 查看帮助

```bash
python developer3_main_coordinator.py --help
```

## 技术栈

- **Python 3.8+**: 主要开发语言
- **Playwright**: 浏览器自动化
- **Anthropic Claude API**: AI 理解与解析 (MCP 基础)
- **SpeechRecognition**: 语音识别
- **python-dotenv**: 环境配置管理

## 项目结构

```
Project/
├── developer1_input_handler.py    # 输入处理与 MCP 客户端
├── developer2_map_automation.py   # 地图自动化
├── developer3_main_coordinator.py # 主协调器
├── config.py                      # 配置管理
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量示例
└── README.md                      # 项目文档
```

## 示例演示

### 示例 1: 文本输入

```bash
$ python developer3_main_coordinator.py --text
请输入导航指令 (例如: 从北京到上海): 从杭州西湖到上海外滩
正在使用百度地图导航...
导航已启动，浏览器将保持打开状态
```

### 示例 2: 语音输入

```bash
$ python developer3_main_coordinator.py --voice
正在调整环境噪音...
请说话...
识别结果: 用高德地图从广州到深圳
正在使用高德地图导航...
导航已启动，浏览器将保持打开状态
```

## MCP 实现说明

本项目基于 **Model Context Protocol (MCP)** 理念实现：

1. **解耦设计**: 输入、AI 处理、自动化三层分离
2. **AI 驱动**: 使用 Claude AI 理解自然语言，而非硬编码规则
3. **灵活扩展**: 可轻松添加新的地图服务或输入方式
4. **协议标准**: 遵循 MCP 的客户端-服务端模式

## 开发说明

### 添加新的地图服务

在 `developer2_map_automation.py` 中：

```python
class NewMapAutomation(MapAutomation):
    BASE_URL = "https://newmap.com"
    
    def navigate(self, origin: str, destination: str):
        # 实现导航逻辑
        pass
```

然后在 `MapServiceFactory` 中注册。

### 添加新的输入方式

在 `developer1_input_handler.py` 的 `InputHandler` 类中添加新方法。

## 常见问题

**Q: 为什么需要 ANTHROPIC_API_KEY?**  
A: 项目使用 Claude AI 进行智能语言理解，需要 API 密钥。可在 https://console.anthropic.com/ 获取。

**Q: 语音识别不工作怎么办?**  
A: 确保已安装 PyAudio，并且系统有麦克风权限。可以使用文本模式作为替代。

**Q: 浏览器自动关闭怎么办?**  
A: 导航启动后，程序会等待用户按回车。保持终端窗口打开即可。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT License

## 联系方式

如有问题，请提交 Issue 或联系开发团队。
