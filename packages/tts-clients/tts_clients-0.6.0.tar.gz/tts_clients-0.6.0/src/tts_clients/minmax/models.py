from typing import Any, Literal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


MinimaxModels = Literal["speech-02-turbo", "speech-02-hd", "speech-01-turbo", "speech-01-hd"]
MinimaxVoiceIds = Literal[
    "Wise_Woman",
    "Friendly_Person",
    "Inspirational_girl",
    "Deep_Voice_Man",
    "Calm_Woman",
    "Casual_Guy",
    "Lively_Girl",
    "Patient_Man",
    "Young_Knight",
    "Determined_Man",
    "Lovely_Girl",
    "Decent_Boy",
    "Imposing_Manner",
    "Elegant_Man",
    "Abbess",
    "Sweet_Girl_2",
    "Exuberant_Girl",
    "Japanese_GentleButler",
    "Japanese_LoyalKnight",
]

MiniMaxEmotions = Literal[
    "happy",
    "sad",
    "angry",
    "fearful",
    "disgusted",
    "surprised",
    "neutral",
]


class BaseResp(BaseModel):
    status_code: int
    status_msg: str


class VoiceSetting(BaseModel):
    voice_id: MinimaxVoiceIds | str = "Japanese_LoyalKnight"
    speed: float = Field(1.0, ge=0.5, le=2.0)
    vol: float = Field(1.0, ge=0, le=2.0)
    pitch: int = Field(0, ge=-12, le=12)
    emotion: MiniMaxEmotions | None = None
    english_normalization: bool = False


class AudioSetting(BaseModel):
    audio_sample_rate: Literal[24000, 32000, 48000] = 32000
    bitrate: Literal[32000, 64000, 128000] = 128000
    format: Literal["mp3", "pcm", "flac"] = "mp3"
    channel: Literal[1, 2] = 1


class TextToAudioRequest(BaseModel):
    """
    T2A v2 Request Model
    """
    text: str
    model: MinimaxModels = "speech-02-turbo"
    stream: bool = False
    voice_setting: VoiceSetting = VoiceSetting()
    audio_setting: AudioSetting = AudioSetting()
    pronunciation_dict: dict[str, str] | None = None

    model_config = ConfigDict(extra="allow")

    @field_validator("text")
    def _trim_length(cls, v):
        if len(v) > 5000:
            raise ValueError("text length exceeds 5000 characters (T2A v2 hard limit)")
        return v


class AudioData(BaseModel):
    audio: str
    status: int

    def to_bytes(self) -> bytes:
        return bytes.fromhex(self.audio)

    def save_mp3(self, path: str | Path):
        if not isinstance(path, Path):
            path = Path(path)
        if not path.suffix == ".mp3":
            raise ValueError("path must end with .mp3")
        with open(path, "wb") as f:
            f.write(self.to_bytes())


class TextToAudioResponse(BaseModel):
    data: AudioData | None = None
    trace_id: str | None = None
    subtitle_file: str | None = None
    base_resp: BaseResp
    extra_info: dict[str, Any] | None = None
