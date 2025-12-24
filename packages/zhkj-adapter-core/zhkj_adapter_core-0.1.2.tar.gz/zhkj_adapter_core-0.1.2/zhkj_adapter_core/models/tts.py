from pydantic import BaseModel
from typing import Optional
from dataclasses import dataclass

#通用请求体
class TTSRequest(BaseModel):
    text: str
    model: str = "cosyvoice-300"  # 模型类型参数
    room_token: Optional[str] = None #校验码
    prompt_audio_id: Optional[str] = None #提示音id
    prompt_audio: Optional[str] = None #提示音url
    prompt_audio_text: Optional[str] = None #提示音文本
    volume: Optional[float] = 1.0
    speed: Optional[float] = 1.0
    pitch: Optional[float] = None

    def to_dict(self):
        return {
            'text': self.text,
            'prompt_audio_id': self.prompt_audio_id,  # 提示音id,可以读取到音频文件地址和提示文本
            'prompt_audio': self.prompt_audio, # 提示音url
            'prompt_audio_text': self.prompt_audio_text,
            'volume': self.volume,  # 带默认值的可选参数
            'speed': self.speed,
            'model': self.model,
            'pitch': self.pitch,
        }


@dataclass
#通用响应内容
class TTSResponse:
    audio_url: str
    duration: float
    inference_time: float
    model: str
    def to_dict(self):
        return {
            'audio_url': self.audio_url,  # 转换二进制数据为十六进制
            'duration': self.duration,
            'inference_time': self.inference_time,
            'model': self.model,
        }

