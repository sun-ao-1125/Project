# Generic MCP Client

A flexible and extensible Python client for interacting with Model Context Protocol (MCP) servers following the official MCP specification.

## Features

### ✨ Core Features

- **Multiple Transport Methods**: HTTP+SSE, stdio, WebSocket
- **Capability Discovery**: Automatic discovery of server tools, resources, and prompts
- **Tool Invocation**: Execute server-side tools with typed arguments
- **Resource Access**: Read and manage server resources
- **Prompt Management**: Retrieve and use server-defined prompts
- **Authentication**: Support for Bearer tokens, OAuth2, and API keys
- **Error Handling**: Comprehensive error handling with automatic retry logic
- **Async/Await**: Fully asynchronous API using asyncio

### 🔒 Security Features

- Token-based authentication (Bearer, OAuth2, API Key)
- Secure credential management
- Resource indicators support
- Server metadata verification

### 🔄 Reliability Features

- Automatic reconnection with exponential backoff
- Configurable retry policies
- Connection timeout management
- Graceful error recovery

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
import asyncio
from mcp_client import create_mcp_client, TransportType

async def main():
    client = await create_mcp_client(
        server_url="http://localhost:3000",
        transport_type=TransportType.HTTP_SSE
    )
    
    tools = client.list_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")
    
    await client.disconnect()

asyncio.run(main())
```

### Advanced Configuration

```python
from mcp_client import MCPClient, MCPConfig, TransportType, AuthType

config = MCPConfig(
    server_url="https://api.example.com/mcp",
    transport_type=TransportType.HTTP_SSE,
    auth_type=AuthType.BEARER,
    auth_token="your-api-key",
    timeout=60,
    max_retries=5,
    retry_delay=2.0,
    client_info={
        "name": "my-app",
        "version": "1.0.0"
    }
)

client = MCPClient(config)
await client.connect()
```

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                     MCP Client                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Config    │  │  Connection  │  │ Capability   │  │
│  │   Module    │  │   Manager    │  │  Discovery   │  │
│  └─────────────┘  └──────────────┘  └──────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Tool     │  │   Resource   │  │    Prompt    │  │
│  │  Invocation │  │    Access    │  │  Management  │  │
│  └─────────────┘  └──────────────┘  └──────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Error    │  │  Reconnect   │  │   Security   │  │
│  │   Handler   │  │   Manager    │  │    Module    │  │
│  └─────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
    ┌────────┐        ┌────────┐        ┌────────┐
    │HTTP+SSE│        │ stdio  │        │WebSocket│
    └────────┘        └────────┘        └────────┘
```

### Module Descriptions

#### 1. Configuration Module (`MCPConfig`)
- Server URL and transport type specification
- Authentication configuration
- Client metadata
- Timeout and retry policies

#### 2. Connection Module (`MCPTransport`)
- Establish connections to MCP servers
- Protocol handshake and version negotiation
- Transport-specific implementations (HTTP+SSE, stdio, WebSocket)

#### 3. Capability Discovery
- Automatic discovery of server capabilities
- Tool enumeration and metadata
- Resource listing
- Prompt template discovery

#### 4. Tool Invocation
- Execute server-side tools
- Parameter validation
- Result processing
- Error handling

#### 5. Resource Access
- Read server resources by URI
- Resource metadata retrieval
- MIME type handling

#### 6. Prompt Management
- Retrieve prompt templates
- Dynamic prompt generation with arguments
- Prompt metadata access

#### 7. Error Handling & Reconnection
- Automatic retry with exponential backoff
- Connection recovery
- Graceful degradation
- Configurable retry policies

#### 8. Security Module
- Multiple authentication methods
- Token management
- Secure credential storage
- OAuth2 flow support

## API Reference

### MCPClient

#### Connection Methods

```python
async def connect() -> bool
```
Establish connection to MCP server and perform handshake.

```python
async def disconnect() -> None
```
Close connection to MCP server.

```python
def is_connected() -> bool
```
Check if client is currently connected.

#### Capability Methods

```python
def list_tools() -> List[Tool]
```
Get list of available tools from server.

```python
def list_resources() -> List[Resource]
```
Get list of available resources from server.

```python
def list_prompts() -> List[Prompt]
```
Get list of available prompts from server.

```python
def get_tool_info(tool_name: str) -> Optional[Tool]
```
Get detailed information about a specific tool.

```python
def get_resource_info(uri: str) -> Optional[Resource]
```
Get detailed information about a specific resource.

```python
def get_prompt_info(name: str) -> Optional[Prompt]
```
Get detailed information about a specific prompt.

#### Invocation Methods

```python
async def call_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]
```
Invoke a server tool with specified arguments.

```python
async def get_resource(uri: str) -> Dict[str, Any]
```
Retrieve a resource from the server.

```python
async def get_prompt(name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]
```
Get a prompt template with optional arguments.

#### Authentication Methods

```python
def set_auth_token(token: str, auth_type: AuthType = AuthType.BEARER) -> None
```
Update authentication token and type.

#### Information Methods

```python
def get_server_info() -> Dict[str, Any]
```
Get server information from handshake.

```python
def get_capabilities() -> Dict[str, Any]
```
Get server capabilities.

### Configuration Classes

#### MCPConfig

```python
@dataclass
class MCPConfig:
    server_url: Optional[str] = None
    transport_type: TransportType = TransportType.HTTP_SSE
    auth_type: AuthType = AuthType.NONE
    auth_token: Optional[str] = None
    client_info: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
```

#### TransportType

```python
class TransportType(Enum):
    STDIO = "stdio"
    HTTP_SSE = "http_sse"
    WEBSOCKET = "websocket"
```

#### AuthType

```python
class AuthType(Enum):
    NONE = "none"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
```

### Data Classes

#### Tool

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
```

#### Resource

```python
@dataclass
class Resource:
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

#### Prompt

```python
@dataclass
class Prompt:
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None
```

## Usage Examples

### Example 1: Basic Tool Invocation

```python
import asyncio
from mcp_client import create_mcp_client

async def main():
    client = await create_mcp_client(
        server_url="http://localhost:3000"
    )
    
    try:
        result = await client.call_tool(
            tool_name="search",
            arguments={"query": "Python", "limit": 10}
        )
        print(f"Search results: {result}")
    finally:
        await client.disconnect()

asyncio.run(main())
```

### Example 2: Resource Access

```python
async def access_resources():
    client = await create_mcp_client(
        server_url="http://localhost:3000"
    )
    
    resources = client.list_resources()
    for resource in resources:
        print(f"Resource: {resource.name} ({resource.uri})")
        
        content = await client.get_resource(resource.uri)
        print(f"Content: {content}")
    
    await client.disconnect()
```

### Example 3: With Authentication

```python
from mcp_client import MCPClient, MCPConfig, AuthType, TransportType

async def authenticated_access():
    config = MCPConfig(
        server_url="https://api.example.com/mcp",
        transport_type=TransportType.HTTP_SSE,
        auth_type=AuthType.BEARER,
        auth_token="your-secret-token"
    )
    
    client = MCPClient(config)
    await client.connect()
    
    tools = client.list_tools()
    print(f"Authenticated access granted. Tools: {len(tools)}")
    
    await client.disconnect()
```

### Example 4: Error Handling

```python
async def with_error_handling():
    config = MCPConfig(
        server_url="http://localhost:3000",
        max_retries=5,
        retry_delay=2.0
    )
    
    client = MCPClient(config)
    
    try:
        if await client.connect():
            result = await client.call_tool("analyze", {"text": "sample"})
            print(f"Result: {result}")
        else:
            print("Failed to connect after retries")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()
```

### Example 5: Using Prompts

```python
async def use_prompts():
    client = await create_mcp_client(
        server_url="http://localhost:3000"
    )
    
    prompts = client.list_prompts()
    print(f"Available prompts: {[p.name for p in prompts]}")
    
    prompt = await client.get_prompt(
        name="code_review",
        arguments={"language": "python"}
    )
    print(f"Generated prompt: {prompt}")
    
    await client.disconnect()
```

## Transport Types

### HTTP + SSE (Server-Sent Events)

Best for: Web-based integrations, cloud services

```python
config = MCPConfig(
    server_url="https://api.example.com/mcp",
    transport_type=TransportType.HTTP_SSE
)
```

### stdio (Standard Input/Output)

Best for: Local processes, command-line tools

```python
config = MCPConfig(
    transport_type=TransportType.STDIO
)
```

### WebSocket

Best for: Real-time bidirectional communication

```python
config = MCPConfig(
    server_url="ws://localhost:8080/mcp",
    transport_type=TransportType.WEBSOCKET
)
```

## Best Practices

1. **Always close connections**: Use `try/finally` or async context managers
2. **Handle errors gracefully**: Wrap calls in try/except blocks
3. **Configure retries**: Set appropriate `max_retries` and `retry_delay`
4. **Secure credentials**: Never hardcode API keys, use environment variables
5. **Validate tool arguments**: Check parameters before calling tools
6. **Monitor connections**: Use `is_connected()` to verify connection state

## Error Handling

The client provides comprehensive error handling:

- `ConnectionError`: Raised when not connected to server
- `ValueError`: Raised for invalid parameters or missing capabilities
- Transport-specific exceptions for network errors
- Automatic retry for transient failures

## Contributing

Contributions are welcome! Please ensure:

1. Code follows the existing style
2. All methods are properly documented
3. Error handling is comprehensive
4. Examples are provided for new features

## License

This implementation is based on the official MCP specification.

## References

- [MCP Official Documentation](https://modelcontextprotocol.io)
- [MCP Specification](https://spec.modelcontextprotocol.io)
- [MCP GitHub Repository](https://github.com/modelcontextprotocol)
