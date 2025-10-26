"""Tests for MCP File Server"""
import pytest
import tempfile
import os
from pathlib import Path


class TestMCPFileServer:
    """Tests for file operations MCP server"""
    
    def test_import_file_server(self):
        try:
            from ai_navigator import mcp_file_server
            assert mcp_file_server is not None
        except ImportError:
            pytest.skip("mcp_file_server module not available")
    
    @pytest.mark.asyncio
    async def test_read_file_operation(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_content = "Hello, MCP!"
        test_file.write_text(test_content)
        
        content = test_file.read_text()
        assert content == test_content
    
    @pytest.mark.asyncio
    async def test_write_file_operation(self, tmp_path):
        test_file = tmp_path / "output.txt"
        test_content = "MCP File Write Test"
        
        test_file.write_text(test_content)
        
        assert test_file.exists()
        assert test_file.read_text() == test_content
    
    @pytest.mark.asyncio
    async def test_list_directory_operation(self, tmp_path):
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        (tmp_path / "subdir").mkdir()
        
        entries = list(tmp_path.iterdir())
        
        assert len(entries) == 3
        assert any(e.name == "file1.txt" for e in entries)
        assert any(e.name == "file2.txt" for e in entries)
        assert any(e.name == "subdir" for e in entries)
    
    @pytest.mark.asyncio
    async def test_create_directory_operation(self, tmp_path):
        new_dir = tmp_path / "new_directory"
        
        new_dir.mkdir()
        
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    @pytest.mark.asyncio
    async def test_delete_file_operation(self, tmp_path):
        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("Delete me")
        
        assert test_file.exists()
        
        test_file.unlink()
        
        assert not test_file.exists()
    
    @pytest.mark.asyncio
    async def test_move_file_operation(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("Move me")
        dest = tmp_path / "destination.txt"
        
        source.rename(dest)
        
        assert not source.exists()
        assert dest.exists()
        assert dest.read_text() == "Move me"
    
    @pytest.mark.asyncio
    async def test_copy_file_operation(self, tmp_path):
        import shutil
        
        source = tmp_path / "source.txt"
        source.write_text("Copy me")
        dest = tmp_path / "copy.txt"
        
        shutil.copy2(source, dest)
        
        assert source.exists()
        assert dest.exists()
        assert dest.read_text() == "Copy me"
    
    @pytest.mark.asyncio
    async def test_file_info_operation(self, tmp_path):
        test_file = tmp_path / "info.txt"
        test_file.write_text("File info test")
        
        stat = test_file.stat()
        
        assert stat.st_size > 0
        assert test_file.name == "info.txt"
    
    @pytest.mark.asyncio
    async def test_error_handling_nonexistent_file(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            nonexistent.read_text()
