from pathlib import Path
from typing import Any

from pydantic import BaseModel


class TextToAudioRequest(BaseModel):
    text: str
    instructions: str
    voice_name: str
    speed: float = 1.0


class TextToAudioResponse(BaseModel):
    audio_stream: Any

    def save_mp3(self, path: str | Path):
        if not isinstance(path, Path):
            path = Path(path)
        if not path.suffix == ".mp3":
            raise ValueError("path must end with .mp3")
        self.audio_stream.stream_to_file(path)
