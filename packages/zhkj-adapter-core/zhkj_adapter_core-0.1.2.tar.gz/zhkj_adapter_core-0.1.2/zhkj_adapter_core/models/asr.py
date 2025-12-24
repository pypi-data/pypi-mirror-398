from typing import Any, Dict, List

from pydantic import BaseModel
from dataclasses import dataclass


# 通用请求体
class AsrRequest(BaseModel):
    model: str = "funasr"  # 模型类型参数
    audio_url: str = None  # 音频url

    def to_dict(self):
        return {
            'model': self.model,
            'audio_url': self.audio_url,
        }


@dataclass
# 通用响应内容
class AsrResponse:
    data: List[Dict[str, Any]]
    duration: float
    inference_time: float
    model: str

    def to_dict(self):
        return {
            'data': self.data,  # 识别的文本
            'duration': self.duration,
            'inference_time': self.inference_time,
            'model': self.model,
        }
