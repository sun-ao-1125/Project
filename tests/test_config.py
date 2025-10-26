"""
Unit tests for configuration loading module.
"""

import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from ai_navigator.config import load_config, get_config_summary


class TestLoadConfig:
    """Test configuration loading functionality."""
    
    def test_load_config_with_existing_env_file(self, tmp_path):
        """Test loading configuration from an existing .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "AI_PROVIDER=anthropic\n"
            "ANTHROPIC_API_KEY=test-key-123\n"
            "AMAP_API_KEY=amap-key-456\n"
        )
        
        os.environ.pop("AI_PROVIDER", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("AMAP_API_KEY", None)
        
        load_config(str(env_file))
        
        assert os.getenv("AI_PROVIDER") == "anthropic"
        assert os.getenv("ANTHROPIC_API_KEY") == "test-key-123"
        assert os.getenv("AMAP_API_KEY") == "amap-key-456"
    
    def test_load_config_with_nonexistent_env_file(self, capsys):
        """Test behavior when .env file doesn't exist."""
        load_config("/nonexistent/path/.env")
        
        captured = capsys.readouterr()
        assert "No .env file found" in captured.out
    
    def test_load_config_respects_existing_env_vars(self, tmp_path):
        """Test that system environment variables take precedence."""
        env_file = tmp_path / ".env"
        env_file.write_text("AI_PROVIDER=openai\n")
        
        os.environ["AI_PROVIDER"] = "anthropic"
        
        load_config(str(env_file))
        
        assert os.getenv("AI_PROVIDER") == "anthropic"
        
        os.environ.pop("AI_PROVIDER", None)
    
    def test_load_config_without_dotenv_installed(self, capsys, monkeypatch):
        """Test graceful handling when python-dotenv is not installed."""
        import sys
        
        original_import = __builtins__.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == "dotenv":
                raise ImportError("No module named 'dotenv'")
            return original_import(name, *args, **kwargs)
        
        with patch("builtins.__import__", side_effect=mock_import):
            load_config()
            
            captured = capsys.readouterr()
            assert "python-dotenv not installed" in captured.out
    
    def test_load_config_default_path(self, tmp_path, monkeypatch):
        """Test loading from default .env path in project root."""
        monkeypatch.chdir(tmp_path)
        
        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_MODEL=gpt-4\n")
        
        os.environ.pop("OPENAI_MODEL", None)
        
        with patch("ai_navigator.config.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            mock_path.return_value.__truediv__ = lambda self, other: tmp_path / other
            
            project_root_mock = MagicMock()
            project_root_mock.parent.parent.parent = tmp_path
            mock_path.return_value = project_root_mock
            
            load_config(str(env_file))
        
        assert os.getenv("OPENAI_MODEL") == "gpt-4"
        
        os.environ.pop("OPENAI_MODEL", None)


class TestGetConfigSummary:
    """Test configuration summary functionality."""
    
    def test_get_config_summary_with_values(self):
        """Test getting config summary with actual values."""
        os.environ["AI_PROVIDER"] = "anthropic"
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test123456789"
        os.environ["OPENAI_BASE_URL"] = "https://api.example.com"
        
        summary = get_config_summary()
        
        assert summary["AI_PROVIDER"] == "anthropic"
        assert summary["ANTHROPIC_API_KEY"] == "sk-a...6789"
        assert summary["OPENAI_BASE_URL"] == "https://api.example.com"
        
        os.environ.pop("AI_PROVIDER", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("OPENAI_BASE_URL", None)
    
    def test_get_config_summary_masks_short_keys(self):
        """Test that short API keys are fully masked."""
        os.environ["AMAP_API_KEY"] = "short"
        
        summary = get_config_summary()
        
        assert summary["AMAP_API_KEY"] == "***"
        
        os.environ.pop("AMAP_API_KEY", None)
    
    def test_get_config_summary_with_missing_values(self):
        """Test getting config summary when values are not set."""
        os.environ.pop("AI_PROVIDER", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        
        summary = get_config_summary()
        
        assert summary["AI_PROVIDER"] == "Not set"
        assert summary["ANTHROPIC_API_KEY"] == "Not set"
    
    def test_get_config_summary_all_fields_present(self):
        """Test that summary includes all expected configuration fields."""
        summary = get_config_summary()
        
        expected_fields = [
            "AI_PROVIDER",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "OPENAI_MODEL",
            "AMAP_MCP_SERVER_URL",
            "AMAP_MCP_SERVER_PATH",
            "AMAP_API_KEY",
        ]
        
        for field in expected_fields:
            assert field in summary
