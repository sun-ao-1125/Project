#!/usr/bin/env python3
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from ai_navigator.voice_recognizer import VoiceRecognizer, get_voice_input
import speech_recognition as sr


class TestVoiceRecognizer:
    
    def test_init_with_local_recognition(self):
        with patch('ai_navigator.voice_recognizer.vosk'):
            recognizer = VoiceRecognizer(language='zh-CN', use_local=True)
            
            assert recognizer.language == 'zh-CN'
            assert recognizer.use_local is True
    
    def test_init_without_local_recognition(self):
        recognizer = VoiceRecognizer(language='en-US', use_local=False)
        
        assert recognizer.language == 'en-US'
        assert recognizer.use_local is False
        assert recognizer.vosk_available is False
    
    def test_init_vosk_not_available(self):
        with patch('voice_recognizer.vosk', side_effect=ImportError):
            with patch('builtins.print'):
                recognizer = VoiceRecognizer(use_local=True)
                
                assert recognizer.vosk_available is False
    
    def test_adjust_for_noise(self):
        recognizer = VoiceRecognizer()
        
        with patch.object(recognizer.recognizer, 'adjust_for_ambient_noise') as mock_adjust:
            with patch('builtins.print'):
                recognizer._adjust_for_noise()
                
                mock_adjust.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_recognize_speech_timeout(self):
        recognizer = VoiceRecognizer(use_local=False)
        
        with patch.object(recognizer, '_adjust_for_noise'):
            with patch.object(recognizer.recognizer, 'listen', side_effect=sr.WaitTimeoutError):
                with patch('builtins.print'):
                    result = await recognizer.recognize_speech(timeout=1)
                    
                    assert result is None
    
    @pytest.mark.asyncio
    async def test_recognize_speech_online_success(self):
        recognizer = VoiceRecognizer(use_local=False)
        mock_audio = Mock()
        
        with patch.object(recognizer, '_adjust_for_noise'):
            with patch.object(recognizer.recognizer, 'listen', return_value=mock_audio):
                with patch.object(recognizer.recognizer, 'recognize_google', return_value="从北京到上海"):
                    with patch('builtins.print'):
                        result = await recognizer.recognize_speech(timeout=5)
                        
                        assert result == "从北京到上海"
    
    @pytest.mark.asyncio
    async def test_recognize_speech_online_unknown_value_error(self):
        recognizer = VoiceRecognizer(use_local=False)
        mock_audio = Mock()
        
        with patch.object(recognizer, '_adjust_for_noise'):
            with patch.object(recognizer.recognizer, 'listen', return_value=mock_audio):
                with patch.object(recognizer.recognizer, 'recognize_google', side_effect=sr.UnknownValueError):
                    with patch('builtins.print'):
                        result = await recognizer.recognize_speech(timeout=5)
                        
                        assert result is None
    
    @pytest.mark.asyncio
    async def test_recognize_speech_online_request_error(self):
        recognizer = VoiceRecognizer(use_local=False)
        mock_audio = Mock()
        
        with patch.object(recognizer, '_adjust_for_noise'):
            with patch.object(recognizer.recognizer, 'listen', return_value=mock_audio):
                with patch.object(recognizer.recognizer, 'recognize_google', side_effect=sr.RequestError("Network error")):
                    with patch('builtins.print'):
                        result = await recognizer.recognize_speech(timeout=5)
                        
                        assert result is None
    
    @pytest.mark.asyncio
    async def test_recognize_speech_general_exception(self):
        recognizer = VoiceRecognizer(use_local=False)
        
        with patch.object(recognizer, '_adjust_for_noise', side_effect=Exception("Test error")):
            with patch('builtins.print'):
                result = await recognizer.recognize_speech(timeout=1)
                
                assert result is None
    
    def test_recognize_vosk_success(self):
        recognizer = VoiceRecognizer(use_local=True)
        mock_audio = Mock()
        mock_audio.get_raw_data = Mock(return_value=b"audio_data")
        
        mock_vosk = MagicMock()
        mock_model = Mock()
        mock_recognizer_obj = Mock()
        mock_recognizer_obj.AcceptWaveform = Mock()
        mock_recognizer_obj.FinalResult = Mock(return_value='{"text": "从北京到上海"}')
        mock_vosk.Model.return_value = mock_model
        mock_vosk.KaldiRecognizer.return_value = mock_recognizer_obj
        
        with patch('voice_recognizer.vosk', mock_vosk):
            with patch('os.path.exists', return_value=True):
                with patch('builtins.print'):
                    result = recognizer._recognize_vosk(mock_audio)
                    
                    assert result == "从北京到上海"
    
    def test_recognize_vosk_no_text_result(self):
        recognizer = VoiceRecognizer(use_local=True)
        mock_audio = Mock()
        mock_audio.get_raw_data = Mock(return_value=b"audio_data")
        
        mock_vosk = MagicMock()
        mock_model = Mock()
        mock_recognizer_obj = Mock()
        mock_recognizer_obj.AcceptWaveform = Mock()
        mock_recognizer_obj.FinalResult = Mock(return_value='{"text": ""}')
        mock_vosk.Model.return_value = mock_model
        mock_vosk.KaldiRecognizer.return_value = mock_recognizer_obj
        
        with patch('voice_recognizer.vosk', mock_vosk):
            with patch('os.path.exists', return_value=True):
                with patch('builtins.print'):
                    result = recognizer._recognize_vosk(mock_audio)
                    
                    assert result is None
    
    def test_recognize_vosk_exception_returns_none(self):
        recognizer = VoiceRecognizer(use_local=True)
        mock_audio = Mock()
        
        with patch('voice_recognizer.vosk', side_effect=Exception("Vosk error")):
            with patch('builtins.print'):
                result = recognizer._recognize_vosk(mock_audio)
                
                assert result is None
    
    @pytest.mark.asyncio
    async def test_recognize_online_success(self):
        recognizer = VoiceRecognizer()
        loop = asyncio.get_event_loop()
        mock_audio = Mock()
        
        with patch.object(recognizer.recognizer, 'recognize_google', return_value="测试文本"):
            with patch('builtins.print'):
                result = await recognizer._recognize_online(loop, mock_audio, timeout=5)
                
                assert result == "测试文本"
    
    @pytest.mark.asyncio
    async def test_recognize_online_timeout_error(self):
        recognizer = VoiceRecognizer()
        loop = asyncio.get_event_loop()
        mock_audio = Mock()
        
        async def slow_recognize():
            await asyncio.sleep(10)
            return "result"
        
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
            with patch('builtins.print'):
                result = await recognizer._recognize_online(loop, mock_audio, timeout=1)
                
                assert result is None


class TestGetVoiceInput:
    
    @pytest.mark.asyncio
    async def test_get_voice_input_success(self):
        with patch('ai_navigator.voice_recognizer.VoiceRecognizer') as mock_class:
            mock_instance = Mock()
            mock_instance.recognize_speech = AsyncMock(return_value="从上海到杭州")
            mock_class.return_value = mock_instance
            
            result = await get_voice_input()
            
            assert result == "从上海到杭州"
            mock_class.assert_called_once_with(use_local=True)
    
    @pytest.mark.asyncio
    async def test_get_voice_input_returns_none(self):
        with patch('ai_navigator.voice_recognizer.VoiceRecognizer') as mock_class:
            mock_instance = Mock()
            mock_instance.recognize_speech = AsyncMock(return_value=None)
            mock_class.return_value = mock_instance
            
            result = await get_voice_input()
            
            assert result is None
