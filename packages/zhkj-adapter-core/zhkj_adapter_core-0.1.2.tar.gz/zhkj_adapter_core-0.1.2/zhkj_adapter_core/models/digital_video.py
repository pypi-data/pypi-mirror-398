from typing import Optional

from pydantic import BaseModel


class DigitalVideoTTSModel(BaseModel):
    text: Optional[str] = None  # tts是必填的，但是接口可以不必填，允许后续传入
    prompt_audio: str
    prompt_audio_text: str
    model: str

    def to_dict(self):
        return {
            "text": self.text,
            "prompt_audio": self.prompt_audio,
            "prompt_audio_text": self.prompt_audio_text,
            "model": self.model,
        }


class DigitalVideoAsrModel(BaseModel):
    model: str
    audio_url: Optional[str] = None  # asr是必填的，但是接口可以不必填，允许后续传入
    auto_stop: bool = False

    def to_dict(self):
        return {
            "auto_stop": self.auto_stop,
            "audio_url": self.audio_url,
            "model": self.model,
        }


class DigitalVideoDigitalModel(BaseModel):
    code: Optional[str] = None
    video_url: str
    model: str

    def to_dict(self):
        return {
            "code": self.code,
            "video_url": self.video_url,
            "model": self.model,
        }


class DigitalVideoRequest(BaseModel):
    tts_model: Optional[DigitalVideoTTSModel] = None
    digital_model: DigitalVideoDigitalModel
    asr_model: Optional[DigitalVideoAsrModel] = None  # 混剪视频
    pending_editing_video_url: Optional[str]
    model: str

    def to_dict(self):
        return {
            "tts_model": self.tts_model.to_dict(),
            "digital_model": self.digital_model.to_dict(),
            "asr_model": self.asr_model.to_dict(),
            "model": self.model,
            "pending_editing_video_url": self.pending_editing_video_url
        }


class DigitalVideoResponse(BaseModel):
    data: str
    url: str
    duration: float
    inference_time: float
    model: str
