import os
from pathlib import Path
from typing import Optional


def load_config(env_file: Optional[str] = None) -> None:
    """
    Load environment variables from .env file if it exists.
    
    This function attempts to load environment variables from a .env file
    in the project root directory. If the file exists, variables are loaded
    into the environment. If not, the function silently continues, allowing
    the application to use system environment variables.
    
    Args:
        env_file: Optional path to .env file. If not provided, looks for
                 .env in the project root directory.
    
    Environment variables loaded:
        AI_PROVIDER: AI provider type ('anthropic' or 'openai')
        ANTHROPIC_API_KEY: Anthropic API key
        OPENAI_API_KEY: OpenAI-compatible API key
        OPENAI_BASE_URL: OpenAI API base URL
        OPENAI_MODEL: OpenAI model name
        AMAP_MCP_SERVER_URL: Amap MCP server URL
        AMAP_MCP_SERVER_PATH: Amap MCP server path
        AMAP_API_KEY: Amap API key
    
    Note:
        - Environment variables already set in the system take precedence
        - This function should be called before any os.getenv() calls
        - The .env file is excluded from version control via .gitignore
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("⚠️  python-dotenv not installed. Run: pip install python-dotenv")
        return
    
    if env_file is None:
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
    else:
        env_file = Path(env_file)
    
    if env_file.exists():
        load_dotenv(env_file, override=False)
        print(f"✓ Loaded configuration from {env_file}")
    else:
        print("ℹ️  No .env file found, using system environment variables")


def get_config_summary() -> dict:
    """
    Get a summary of current configuration (without exposing sensitive values).
    
    Returns:
        dict: Configuration summary with masked sensitive values
    """
    def mask_value(value: Optional[str]) -> str:
        if not value:
            return "Not set"
        if len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"
    
    return {
        "AI_PROVIDER": os.getenv("AI_PROVIDER", "Not set"),
        "ANTHROPIC_API_KEY": mask_value(os.getenv("ANTHROPIC_API_KEY")),
        "OPENAI_API_KEY": mask_value(os.getenv("OPENAI_API_KEY")),
        "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", "Not set"),
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "Not set"),
        "AMAP_MCP_SERVER_URL": os.getenv("AMAP_MCP_SERVER_URL", "Not set"),
        "AMAP_MCP_SERVER_PATH": os.getenv("AMAP_MCP_SERVER_PATH", "Not set"),
        "AMAP_API_KEY": mask_value(os.getenv("AMAP_API_KEY")),
    }
