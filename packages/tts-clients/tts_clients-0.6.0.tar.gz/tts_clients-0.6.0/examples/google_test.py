from dotenv import load_dotenv

from tts_clients.google.client import GoogleTTSClient
from tts_clients.google.models import MultiSpeakerTextToAudioRequest, SpeakerTextToAudioRequest


load_dotenv()

client = GoogleTTSClient()
r = client.multi_speaker_text_to_audio(MultiSpeakerTextToAudioRequest(
    speakers=[
        SpeakerTextToAudioRequest(speaker_name="speaker1", text="こんにちは！", voice_name="Kore"),
        SpeakerTextToAudioRequest(speaker_name="speaker2", text="こんばんは！", voice_name="Orus"),
        SpeakerTextToAudioRequest(speaker_name="speaker1", text="今日は晴れですね", voice_name="Kore"),
    ],
    instructions="Say cheerfully",
))
r.save_mp3("test.mp3")
