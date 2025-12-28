from dotenv import load_dotenv

from tts_clients.minmax.client import MiniMaxT2AClient
from tts_clients.minmax.models import TextToAudioRequest, VoiceSetting


load_dotenv()


client = MiniMaxT2AClient()
r = client.text_to_audio(TextToAudioRequest(text="こんにちは！", voice_setting=VoiceSetting(emotion="angry")))
r.data.save_mp3("test.mp3")
