from pathlib import Path
from typing import Literal

from pydantic import BaseModel


VoiceIdMap = {
    "kuon": "B8gJV1IhpuegLxdpXFOE",
    "Ishibashi": "Mv8AjrYZCBkdsmDHNwcB",
    "Satoshi": "V3XiX7JWJpn959SS60pv",
    "Morioki": "8EkOjt4xTPGMclNlh1pk"
}


VoiceNameTypes = Literal["kuon", "Ishibashi", "Satoshi", "Morioki"]


class TextToAudioRequest(BaseModel):
    text: str
    voice_name: VoiceNameTypes


class TextToAudioResponse(BaseModel):
    audio: bytes

    def save_mp3(self, path: str | Path):
        if not isinstance(path, Path):
            path = Path(path)
        if not path.suffix == ".mp3":
            raise ValueError("path must end with .mp3")
        with open(path, "wb") as f:
            f.write(self.audio)
