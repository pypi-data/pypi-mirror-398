from google import genai
from google.genai import types

from .models import MultiSpeakerTextToAudioRequest, TextToAudioRequest, TextToAudioResponse


class GoogleTTSClient:
    def __init__(self, model: str = "gemini-2.5-pro-preview-tts"):
        self.client = genai.Client()
        self.model = model

    def text_to_audio(self, req: TextToAudioRequest) -> TextToAudioResponse:
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{req.instructions}: {req.text}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=req.voice_name,
                        )
                    ),
                ),
            ),
        )
        data = response.candidates[0].content.parts[0].inline_data.data
        return TextToAudioResponse.from_bytes(data)

    def multi_speaker_text_to_audio(self, req: MultiSpeakerTextToAudioRequest) -> TextToAudioResponse:
        prompt_text = "\n".join([
            f"{speaker.speaker_name}: {speaker.text}"
            for speaker in req.speakers
        ])
        speakers_set = set([(speaker.speaker_name, speaker.voice_name) for speaker in req.speakers])
        speech_config=types.SpeechConfig(
           multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
              speaker_voice_configs=[
                 types.SpeakerVoiceConfig(
                    speaker=speaker[0],
                    voice_config=types.VoiceConfig(
                       prebuilt_voice_config=types.PrebuiltVoiceConfig(
                          voice_name=speaker[1],
                       )
                    )
                 )
                 for speaker in speakers_set
              ]
           )
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{req.instructions}:\n{prompt_text}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=speech_config,
            ),
        )
        data = response.candidates[0].content.parts[0].inline_data.data
        return TextToAudioResponse.from_bytes(data)
