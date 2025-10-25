import speech_recognition as sr
from typing import Optional, Dict
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InputHandler:
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    def get_text_input(self, prompt: str = "请输入导航指令 (例如: 从北京到上海): ") -> str:
        return input(prompt).strip()
    
    def get_voice_input(self) -> Optional[str]:
        try:
            with sr.Microphone() as source:
                logger.info("正在调整环境噪音...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("请说话...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            logger.info("正在识别...")
            text = self.recognizer.recognize_google(audio, language='zh-CN')
            logger.info(f"识别结果: {text}")
            return text
            
        except sr.WaitTimeoutError:
            logger.error("超时: 未检测到语音")
            return None
        except sr.UnknownValueError:
            logger.error("无法识别语音")
            return None
        except sr.RequestError as e:
            logger.error(f"语音识别服务错误: {e}")
            return None
        except Exception as e:
            logger.error(f"语音输入错误: {e}")
            return None


class MCPClient:
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.system_prompt = """你是一个导航助手。用户会给你描述导航需求，你需要提取出起点(origin)和终点(destination)。

请以JSON格式返回:
{
    "origin": "起点地址",
    "destination": "目的地地址",
    "map_service": "baidu" 或 "gaode"
}

如果用户没有指定地图服务，默认使用 "baidu"。"""
    
    def parse_navigation_request(self, user_input: str) -> Dict[str, str]:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": user_input}
                ]
            )
            
            response_text = message.content[0].text
            logger.info(f"AI 解析结果: {response_text}")
            
            result = json.loads(response_text)
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误: {e}")
            return self._fallback_parse(user_input)
        except Exception as e:
            logger.error(f"MCP 客户端错误: {e}")
            return self._fallback_parse(user_input)
    
    def _fallback_parse(self, user_input: str) -> Dict[str, str]:
        keywords = ['从', '到', '去']
        origin = ""
        destination = ""
        
        if '从' in user_input and '到' in user_input:
            parts = user_input.split('从', 1)[1].split('到', 1)
            origin = parts[0].strip()
            destination = parts[1].strip()
        elif '去' in user_input:
            destination = user_input.split('去', 1)[1].strip()
            origin = "当前位置"
        
        return {
            "origin": origin,
            "destination": destination,
            "map_service": "baidu"
        }


def process_input(input_type: str = "text", api_key: str = "") -> Optional[Dict[str, str]]:
    handler = InputHandler()
    mcp_client = MCPClient(api_key)
    
    if input_type == "voice":
        user_input = handler.get_voice_input()
    else:
        user_input = handler.get_text_input()
    
    if not user_input:
        logger.error("未获取到有效输入")
        return None
    
    navigation_info = mcp_client.parse_navigation_request(user_input)
    return navigation_info
