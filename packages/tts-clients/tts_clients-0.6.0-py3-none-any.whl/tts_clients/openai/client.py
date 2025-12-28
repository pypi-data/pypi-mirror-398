from openai import OpenAI

from .models import TextToAudioRequest, TextToAudioResponse


class OpenAITTSClient:
    def __init__(self):
        self.client = OpenAI()

    def text_to_audio(self, req: TextToAudioRequest) -> TextToAudioResponse:
        response = self.client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=req.voice_name,
            input=req.text,
            instructions=req.instructions,
            speed=req.speed,
        )
        return TextToAudioResponse(audio_stream=response)
