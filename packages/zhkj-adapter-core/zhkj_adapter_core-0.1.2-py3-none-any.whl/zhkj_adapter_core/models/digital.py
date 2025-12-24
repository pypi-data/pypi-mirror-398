from pydantic import BaseModel


class DigitalRequest(BaseModel):
    code: str
    audio_url: str
    video_url: str
    model: str

    def to_dict(self):
        return {
            "code": self.code,
            "model": self.model,
            "audio_url": self.audio_url,
            "video_url": self.video_url,
        }


class DigitalResponse(BaseModel):
    url: str
    duration: float
    inference_time: float
    model: str