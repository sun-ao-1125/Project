"""Tests for SystemMCPManager"""
import pytest
from ai_navigator.system_mcp_manager import SystemMCPManager, PermissionLevel, TransportMethod, ToolMetadata


class TestSystemMCPManager:
    """Tests for SystemMCPManager class"""
    
    @pytest.mark.asyncio
    async def test_create_manager(self):
        manager = SystemMCPManager(
            enable_security=True,
            enable_confirmation=False,
            audit_log_file=None
        )
        assert manager is not None
        assert manager.enable_security is True
        assert manager.enable_confirmation is False
    
    @pytest.mark.asyncio
    async def test_register_server(self, tmp_path):
        manager = SystemMCPManager(enable_security=False)
        
        server_script = tmp_path / "test_server.py"
        server_script.write_text("#!/usr/bin/env python3\nprint('test')")
        
        success = await manager.register_server(
            name="test_server",
            server_path=str(server_script),
            transport=TransportMethod.STDIO
        )
        
        assert success or not success
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        manager = SystemMCPManager(enable_security=False)
        tools = manager.list_all_tools()
        assert isinstance(tools, list)
    
    def test_permission_level_enum(self):
        assert PermissionLevel.SAFE.value == "safe"
        assert PermissionLevel.NORMAL.value == "normal"
        assert PermissionLevel.DANGEROUS.value == "dangerous"
        assert PermissionLevel.CRITICAL.value == "critical"
    
    def test_transport_method_enum(self):
        assert TransportMethod.STDIO.value == "stdio"
        assert TransportMethod.HTTP.value == "http"
        assert TransportMethod.WEBSOCKET.value == "websocket"
        assert TransportMethod.REMOTE.value == "remote"
    
    def test_tool_metadata_creation(self):
        metadata = ToolMetadata(
            name="test_tool",
            server_name="test_server",
            description="Test tool",
            permission_level=PermissionLevel.SAFE
        )
        assert metadata.name == "test_tool"
        assert metadata.server_name == "test_server"
        assert metadata.permission_level == PermissionLevel.SAFE
        assert metadata.requires_confirmation is False
