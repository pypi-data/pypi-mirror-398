import os

from elevenlabs import ElevenLabs

from .models import TextToAudioRequest, TextToAudioResponse, VoiceIdMap


class ElevenLabsClient:
    def __init__(self, model_id: str = "eleven_v3"):
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"),)
        self.model_id = model_id

    def text_to_audio(self, request: TextToAudioRequest) -> TextToAudioResponse:
        audio = self.client.text_to_speech.convert(
            text=request.text,
            voice_id=VoiceIdMap[request.voice_name],
            model_id=self.model_id,
            output_format="mp3_44100_128",
        )
        audio = b"".join(audio)
        return TextToAudioResponse(audio=audio)
