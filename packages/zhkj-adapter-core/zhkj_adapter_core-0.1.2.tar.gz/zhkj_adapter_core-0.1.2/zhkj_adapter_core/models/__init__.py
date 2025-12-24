"""
数据模型模块
包含TTS相关的数据模型定义
"""

from .tts import TTSRequest, TTSResponse
from .digital import DigitalRequest, DigitalResponse
from .asr import AsrResponse, AsrRequest
from .digital_video import DigitalVideoRequest, DigitalVideoResponse, DigitalVideoTTSModel, DigitalVideoDigitalModel, DigitalVideoAsrModel

__all__ = [
    "TTSRequest", "TTSResponse",
    "DigitalRequest", "DigitalResponse",
    "AsrResponse", "AsrRequest",
    "DigitalVideoRequest", "DigitalVideoResponse", "DigitalVideoTTSModel", "DigitalVideoDigitalModel", "DigitalVideoAsrModel"
]
