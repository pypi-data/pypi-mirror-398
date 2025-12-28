from dotenv import load_dotenv

from tts_clients.elevenlabs.client import ElevenLabsClient
from tts_clients.elevenlabs.models import TextToAudioRequest


load_dotenv()

client = ElevenLabsClient()
request = TextToAudioRequest(text="こんにちは！", voice_name="kuon")
response = client.text_to_audio(request)
response.save_mp3("test.mp3")
