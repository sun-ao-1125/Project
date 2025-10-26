# MCP 架构 - 通信抽象与安全控制

本文档介绍新增的通信抽象层和安全控制层功能。

## 概述

### 一、通信抽象层

**目标**: 让 MCP Manager 与各个 MCP Server 的交互完全解耦传输方式（无论是本地、远程、WebSocket、HTTP、Stdio 都一样调用）。

**优势**:
- ✅ 彻底消除协议依赖
- ✅ 支持远程或容器化 Server
- ✅ AI 可以统一访问所有功能

### 二、安全控制层

**目标**: 
- 防止 AI 误操作系统（例如删除文件、关闭窗口）
- 提供权限分级、安全确认、可审计性

**核心机制**:
1. ✅ 权限等级（Permission Level）
2. ✅ 调用时权限验证
3. ✅ 可选安全确认机制
4. ✅ 操作日志 / 审计记录

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                  AI Application Layer                    │
│                     (main.py)                            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              SystemMCPManager                            │
│  ┌────────────────────────────────────────────────┐    │
│  │  Security Control Layer                        │    │
│  │  - Permission Validation                       │    │
│  │  - Confirmation Mechanism                      │    │
│  │  - Audit Logging                               │    │
│  └────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────┐    │
│  │  Communication Abstraction Layer               │    │
│  │  - Transport Method Decoupling                 │    │
│  │  - Stdio / HTTP / WebSocket / Remote           │    │
│  └────────────────────────────────────────────────┘    │
└─────┬──────┬──────┬──────┬──────┬──────┬──────────────┘
      │      │      │      │      │      │
      ▼      ▼      ▼      ▼      ▼      ▼
   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
   │Browser│File │Window│Network│Map  │Voice│
   │MCP   │MCP  │MCP   │MCP   │MCP  │MCP  │
   │Server│Server│Server│Server│Server│Server│
   └────┘ └────┘ └────┘ └────┘ └────┘ └────┘
```

## 权限等级系统

### Permission Levels

| 等级 | 说明 | 示例操作 | 需要确认 |
|------|------|---------|----------|
| **SAFE** | 安全操作，不会修改系统状态 | `open_url`, `read_file`, `list_directory` | ❌ |
| **NORMAL** | 普通操作，有限的系统影响 | `write_file`, `create_directory` | ❌ |
| **DANGEROUS** | 危险操作，可能影响系统 | `delete_file`, `close_window`, `kill_process` | ⚠️ 可选 |
| **CRITICAL** | 关键操作，严重影响系统 | `format_disk`, `shutdown_system`, `delete_system_file` | ✅ 必需 |

### 自动权限推断

系统会根据工具名称自动推断权限等级:

```python
# 关键词映射
CRITICAL: ["format", "wipe", "destroy", "shutdown", "reboot"]
DANGEROUS: ["delete", "remove", "close", "kill", "terminate"]
SAFE: ["get", "read", "list", "search", "find", "open_url", "open_map"]
NORMAL: 其他所有工具
```

## 安全确认机制

### 配置选项

```python
mcp_manager = SystemMCPManager(
    enable_security=True,          # 启用安全控制
    enable_confirmation=True,      # 启用用户确认
    audit_log_file="mcp_audit.log" # 审计日志文件
)
```

### 确认流程

当调用 DANGEROUS 或 CRITICAL 级别的工具时:

```
⚠️  WARNING: DANGEROUS OPERATION
Server: file
Tool: delete_file
Description: Delete a file from the filesystem
Arguments: {
  "path": "/home/user/important.txt"
}

Allow this operation? (yes/no/always): 
```

用户选项:
- `yes` / `y` - 允许本次操作
- `no` / `n` - 拒绝本次操作
- `always` - 永久允许此工具（本次会话内）

## 审计日志

### 日志格式

所有工具调用都会记录到审计日志 (`mcp_audit.log`):

```json
{
  "timestamp": "2025-10-25T08:00:00.123456",
  "server_name": "browser",
  "tool_name": "open_map_navigation",
  "permission_level": "safe",
  "arguments": {
    "start_lng": 116.397128,
    "start_lat": 39.916527,
    "end_lng": 121.473701,
    "end_lat": 31.230416,
    "start_name": "北京",
    "end_name": "上海"
  },
  "result_status": "success",
  "result_message": "Tool call completed",
  "user_confirmed": false
}
```

### 查看审计日志

```python
# 获取最近 10 条日志
recent_logs = mcp_manager.get_audit_logs(count=10)

for log in recent_logs:
    print(f"{log.timestamp}: {log.server_name}.{log.tool_name} - {log.result_status}")
```

## 通信抽象层

### 支持的传输方式

```python
from system_mcp_manager import TransportMethod

# 1. Stdio 传输 (本地进程)
await mcp_manager.register_server(
    name="browser",
    server_path="/path/to/mcp_browser_server.py",
    transport=TransportMethod.STDIO
)

# 2. HTTP 传输 (远程服务器)
await mcp_manager.register_server(
    name="remote_service",
    server_path="",  # 不需要本地路径
    transport=TransportMethod.HTTP,
    server_url="http://remote-server:8000/mcp"
)

# 3. WebSocket 传输 (实时通信)
await mcp_manager.register_server(
    name="realtime_service",
    server_path="",
    transport=TransportMethod.WEBSOCKET,
    server_url="ws://remote-server:8001/mcp"
)

# 4. Remote 传输 (容器化服务)
await mcp_manager.register_server(
    name="container_service",
    server_path="",
    transport=TransportMethod.REMOTE,
    server_url="http://container:3000"
)
```

### 统一调用接口

无论使用哪种传输方式，调用接口完全一致:

```python
# 调用本地 stdio server
result = await mcp_manager.call_tool(
    server_name="browser",
    tool_name="open_url",
    arguments={"url": "https://example.com"}
)

# 调用远程 HTTP server
result = await mcp_manager.call_tool(
    server_name="remote_service",
    tool_name="process_data",
    arguments={"data": [1, 2, 3]}
)
```

## 使用示例

### 完整示例

```python
import asyncio
from system_mcp_manager import SystemMCPManager, TransportMethod

async def main():
    # 创建 MCP Manager
    async with SystemMCPManager(
        enable_security=True,
        enable_confirmation=True,
        audit_log_file="mcp_audit.log"
    ) as manager:
        
        # 注册浏览器控制 Server
        await manager.register_server(
            name="browser",
            server_path="mcp_browser_server.py",
            transport=TransportMethod.STDIO
        )
        
        # 查看可用工具
        tools = manager.list_all_tools()
        print(f"Available tools: {tools}")
        
        # 调用工具
        result = await manager.call_tool(
            server_name="browser",
            tool_name="open_url",
            arguments={"url": "https://github.com"}
        )
        
        # 查看审计日志
        logs = manager.get_audit_logs(count=5)
        for log in logs:
            print(f"{log.timestamp}: {log.tool_name} - {log.result_status}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 在 main.py 中的使用

已集成到 `main.py`:

```python
# 初始化 MCP Manager (默认关闭用户确认以避免交互干扰)
mcp_manager = SystemMCPManager(
    enable_security=True,
    enable_confirmation=False,  # 在 AI 导航应用中关闭确认
    audit_log_file="mcp_audit.log"
)

# 注册浏览器控制 Server
await mcp_manager.register_server(
    name="browser",
    server_path="mcp_browser_server.py",
    transport=TransportMethod.STDIO
)

# 通过 MCP 协议打开导航
result = await mcp_manager.call_tool(
    server_name="browser",
    tool_name="open_map_navigation",
    arguments={
        "start_lng": start_coords['longitude'],
        "start_lat": start_coords['latitude'],
        "end_lng": end_coords['longitude'],
        "end_lat": end_coords['latitude'],
        "start_name": start_coords['name'],
        "end_name": end_coords['name']
    }
)
```

## API 参考

### SystemMCPManager

#### 构造函数

```python
SystemMCPManager(
    enable_security: bool = True,          # 启用安全控制
    enable_confirmation: bool = True,      # 启用用户确认
    audit_log_file: str = "mcp_audit.log" # 审计日志文件路径
)
```

#### 主要方法

```python
# 注册 MCP Server
async def register_server(
    name: str,                           # Server 唯一名称
    server_path: str,                    # Server 路径（stdio模式）
    transport: TransportMethod = STDIO,  # 传输方式
    server_url: Optional[str] = None,    # 远程 Server URL
    auto_connect: bool = True,           # 自动连接
    **kwargs                             # 其他配置
) -> bool

# 调用工具
async def call_tool(
    server_name: str,                    # Server 名称
    tool_name: str,                      # 工具名称
    arguments: Dict[str, Any],           # 工具参数
    skip_confirmation: bool = False      # 跳过确认（自动化场景）
) -> Any

# 列出所有工具
def list_all_tools() -> Dict[str, List[ToolMetadata]]

# 获取 Server 能力
def get_server_capabilities(server_name: str) -> List[ToolMetadata]

# 获取审计日志
def get_audit_logs(count: int = 10) -> List[AuditLogEntry]

# 断开所有连接
async def disconnect_all()
```

## 扩展指南

### 添加新的 MCP Server

1. 创建 MCP Server（遵循 MCP 协议）
2. 在 SystemMCPManager 中注册

```python
await mcp_manager.register_server(
    name="my_service",
    server_path="/path/to/my_mcp_server.py",
    transport=TransportMethod.STDIO
)
```

3. 调用工具

```python
result = await mcp_manager.call_tool(
    server_name="my_service",
    tool_name="my_tool",
    arguments={"param": "value"}
)
```

### 自定义权限等级

修改 `MCPServerConnection._infer_permission_level()` 方法来自定义权限推断逻辑。

### 自定义安全验证

继承 `SecurityValidator` 类并重写 `validate_permission()` 方法:

```python
class CustomSecurityValidator(SecurityValidator):
    def validate_permission(self, tool_meta: ToolMetadata, arguments: Dict[str, Any]) -> tuple[bool, str]:
        # 自定义验证逻辑
        return True, "Custom validation passed"
```

## 最佳实践

1. **生产环境**: 启用安全控制和审计日志
   ```python
   SystemMCPManager(enable_security=True, enable_confirmation=True)
   ```

2. **自动化场景**: 关闭用户确认
   ```python
   SystemMCPManager(enable_security=True, enable_confirmation=False)
   ```

3. **开发测试**: 可以完全关闭安全控制
   ```python
   SystemMCPManager(enable_security=False)
   ```

4. **定期审查日志**: 
   ```bash
   tail -f mcp_audit.log
   ```

5. **远程 Server**: 使用 HTTP/WebSocket 传输
   ```python
   await manager.register_server(
       name="remote",
       server_path="",
       transport=TransportMethod.HTTP,
       server_url="https://api.example.com/mcp"
   )
   ```

## 故障排除

### 问题: Server 注册失败

**解决方案**:
1. 检查 server_path 是否正确
2. 确认 Python 环境中安装了必要依赖
3. 查看日志输出获取详细错误信息

### 问题: 工具调用被拒绝

**解决方案**:
1. 检查权限等级设置
2. 如果启用了确认机制，确保正确响应确认提示
3. 查看审计日志了解拒绝原因

### 问题: 远程 Server 连接失败

**解决方案**:
1. 检查 server_url 是否正确
2. 确认网络连接正常
3. 验证远程 Server 是否正在运行

## 未来扩展

计划中的功能:

- [ ] HTTP 传输完整实现
- [ ] WebSocket 传输完整实现
- [ ] 远程/容器化 Server 支持
- [ ] 更细粒度的权限控制（基于参数）
- [ ] 审计日志的查询和分析工具
- [ ] Web UI 管理界面

## 总结

通过通信抽象层和安全控制层，MCP 架构实现了:

✅ **统一接口** - 所有工具调用通过标准接口  
✅ **传输解耦** - 支持多种传输方式  
✅ **安全防护** - 权限分级和确认机制  
✅ **可审计性** - 完整的操作日志记录  
✅ **易扩展性** - 轻松添加新的 MCP Server  

真正实现了 "AI 驱动系统操作" 的安全、灵活架构！
