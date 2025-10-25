import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
BAIDU_SPEECH_API_KEY = os.getenv('BAIDU_SPEECH_API_KEY', '')
BAIDU_SPEECH_SECRET_KEY = os.getenv('BAIDU_SPEECH_SECRET_KEY', '')
DEFAULT_MAP_SERVICE = os.getenv('DEFAULT_MAP_SERVICE', 'baidu')

MCP_SERVER_CONFIG = {
    'transport': 'stdio',
    'command': 'npx',
    'args': ['-y', '@modelcontextprotocol/server-memory']
}
