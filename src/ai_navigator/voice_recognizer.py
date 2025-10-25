#!/usr/bin/env python3
"""
Voice Recognition Module
Provides voice input capability for the AI Map Navigator
"""

import asyncio
import speech_recognition as sr
from typing import Optional
import os

class VoiceRecognizer:
    def __init__(self, language: str = 'zh-CN', use_local: bool = True):
        self.recognizer = sr.Recognizer()
        self.language = language
        self.microphone = sr.Microphone()
        self.use_local = use_local  # 是否使用本地识别
        self.vosk_model = None
        
        # 初始化Vosk（如果使用本地识别）
        if self.use_local:
            try:
                import vosk
                self.vosk_available = True
                print("本地语音识别引擎(Vosk)已初始化。")
            except ImportError:
                self.vosk_available = False
                print("警告：Vosk库未安装，将使用在线识别服务。")
        else:
            self.vosk_available = False
            
    def _adjust_for_noise(self):
        """调整识别器以适应环境噪音"""
        with self.microphone as source:
            print("正在调整麦克风以适应环境噪音，请稍候...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("麦克风调整完成!")
    
    async def recognize_speech(self, timeout: int = 10) -> Optional[str]:
        """
        异步识别语音输入
        
        Args:
            timeout: 识别超时时间（秒）
        
        Returns:
            识别出的文本，识别失败则返回None
        """
        # 因为SpeechRecognition是同步的，我们使用线程池来避免阻塞事件循环
        loop = asyncio.get_event_loop()
        
        try:
            # 首先调整噪音水平
            await loop.run_in_executor(None, self._adjust_for_noise)
            
            print(f"\n请说出您的导航请求（例如：'从北京到上海'，'{timeout}秒内无输入将超时）...")
            
            # 定义一个同步函数来捕获语音
            def capture_speech():
                with self.microphone as source:
                    try:
                        audio = self.recognizer.listen(source, timeout=timeout)
                        return audio
                    except sr.WaitTimeoutError:
                        print("语音输入超时，请重试。")
                        return None
            
            # 异步执行语音捕获
            audio_data = await asyncio.wait_for(
                loop.run_in_executor(None, capture_speech),
                timeout=timeout + 2  # 额外添加2秒以避免超时问题
            )
            
            if not audio_data:
                return None
            
            print("正在识别语音...")
            
            # 根据是否使用本地识别选择不同的识别方法
            if self.use_local and self.vosk_available:
                return await loop.run_in_executor(None, self._recognize_vosk, audio_data)
            else:
                # 使用在线识别（备用方案）
                return await self._recognize_online(loop, audio_data, timeout)
            
        except asyncio.TimeoutError:
            print("语音识别过程超时。")
            return None
        except Exception as e:
            print(f"语音识别过程中发生错误: {e}")
            return None
    
    def _recognize_vosk(self, audio_data) -> Optional[str]:
        """使用Vosk本地识别引擎识别语音"""
        try:
            import vosk
            
            # 下载中文模型（如果尚未下载）
            model_path = "model-small-cn"
            if not os.path.exists(model_path):
                print("首次使用，正在下载中文语音识别模型（约40MB）...")
                import requests
                import zipfile
                import shutil
                
                # 下载小体积的中文模型
                url = "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip"
                zip_path = "model.zip"
                
                # 获取文件总大小
                response = requests.head(url)
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                print(f"首次使用，正在下载中文语音识别模型（约{total_size/1024/1024:.1f}MB）...")
                
                # 下载模型文件
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(zip_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            # 计算下载进度百分比
                            progress = (downloaded_size / total_size) * 100 if total_size > 0 else 0
                            # 显示进度条
                            bar_length = 30
                            filled_length = int(bar_length * downloaded_size // total_size)
                            bar = '█' * filled_length + '-' * (bar_length - filled_length)
                            print(f"\r下载进度: |{bar}| {progress:.1f}%", end="")
                print()  # 换行
                
                # 解压模型
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall()
                
                # 重命名模型文件夹
                os.rename("vosk-model-small-cn-0.22", model_path)
                os.remove(zip_path)
                print("模型下载完成!")
            
            # 初始化模型
            if self.vosk_model is None:
                self.vosk_model = vosk.Model(model_path)
            
            # 转换音频数据格式
            audio_data_bytes = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
            
            # 进行识别
            rec = vosk.KaldiRecognizer(self.vosk_model, 16000)
            rec.AcceptWaveform(audio_data_bytes)
            result = rec.FinalResult()
            
            # 解析识别结果
            import json
            text = json.loads(result).get("text", "")
            
            if text:
                print(f"本地识别结果: {text}")
            else:
                print("本地识别未能识别出有效内容。")
            
            return text if text else None
            
        except Exception as e:
            print(f"本地语音识别过程中发生错误: {e}")
            # 发生错误时，回退到在线识别
            print("正在尝试使用在线识别服务...")
            return None
    
    async def _recognize_online(self, loop, audio_data, timeout) -> Optional[str]:
        """使用在线语音识别服务"""
        print("正在连接到语音识别服务...")

        # 定义一个同步函数来识别语音
        def recognize_audio():
            try:
                # 使用Google的语音识别API
                print("正在发送语音数据进行识别...")
                text = self.recognizer.recognize_google(
                    audio_data, 
                    language=self.language
                )
                print("语音识别服务返回结果")
                return text
            except sr.UnknownValueError:
                print("无法识别您的语音，请尝试更清晰地说话。")
                return None
            except sr.RequestError as e:
                print(f"无法连接到语音识别服务: {e}")
                print("提示：可能是网络连接问题或API不可用。")
                return None

        # 异步执行语音识别，增加超时时间
        try:
            text = await asyncio.wait_for(
                loop.run_in_executor(None, recognize_audio),
                timeout=timeout + 5  # 额外增加5秒超时时间
            )
        except asyncio.TimeoutError:
            print("语音识别API调用超时。")
            return None

        if text:
            print(f"识别结果: {text}")
        else:
            print("未能识别出有效内容。")

        return text

# 简单的工厂函数，便于使用
async def get_voice_input() -> Optional[str]:
    """获取语音输入的便捷函数"""
    recognizer = VoiceRecognizer(use_local=True)  # 默认使用本地识别
    return await recognizer.recognize_speech()