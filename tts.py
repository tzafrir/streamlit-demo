import os
import elevenlabs
from pydub import AudioSegment
from io import BytesIO

def mix_audio(music_bytes, audio_bytes):
    # Create file-like objects from bytes
    music_io = BytesIO(music_bytes)
    audio_io = BytesIO(audio_bytes)
    
    # Load audio segments from BytesIO objects
    music = AudioSegment.from_file(music_io)
    audio = AudioSegment.from_file(audio_io)
    
    # Reduce the volume of the audio
    audio = audio - 16

    # Add 2 seconds of silence at the beginning
    audio = AudioSegment.silent(duration=2000) + audio
    
    # Trim the audio to the length of the music
    audio = audio[:music.duration_seconds * 1000]
    
    mixed = music.overlay(audio)
    return mixed.export(format="wav").read()

def text_to_speech_mixed(text, music_bytes):
    client = elevenlabs.ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    
    bytes = b""
    for chunk in client.generate(text=text, voice="Adam"):
        bytes += chunk
        
    return mix_audio(music_bytes, bytes)



