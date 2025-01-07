"""
Text-to-Speech and Audio Mixing Module

This module provides functionality for converting text to speech using ElevenLabs API
and mixing the generated speech with background music. It includes capabilities for
audio processing such as volume adjustment and timing synchronization.

Required Environment Variables:
    - ELEVENLABS_API_KEY: API key for accessing ElevenLabs text-to-speech service

Dependencies:
    - elevenlabs: For text-to-speech conversion
    - pydub: For audio processing and mixing
"""

import os
import elevenlabs
from pydub import AudioSegment
from io import BytesIO

def mix_audio(music_bytes, audio_bytes):
    """
    Mix two audio streams together, with the second audio stream overlaid on the first.
    
    Args:
        music_bytes (bytes): Background music audio data in bytes
        audio_bytes (bytes): Voice/speech audio data in bytes to overlay
        
    Returns:
        bytes: Mixed audio data in WAV format
        
    Notes:
        - Reduces the volume of the overlay audio by 10dB
        - Adds 1 second of silence at the beginning of the overlay
        - Trims the overlay to match the length of the background music
    """
    # Create file-like objects from bytes
    music_io = BytesIO(music_bytes)
    audio_io = BytesIO(audio_bytes)
    
    # Load audio segments from BytesIO objects
    music = AudioSegment.from_file(music_io)
    audio = AudioSegment.from_file(audio_io)
    
    # Reduce the volume of the audio
    audio = audio - 10

    # Add 2 seconds of silence at the beginning
    audio = AudioSegment.silent(duration=1000) + audio
    
    # Trim the audio to the length of the music
    audio = audio[:music.duration_seconds * 1000]
    
    mixed = music.overlay(audio)
    return mixed.export(format="wav").read()

def text_to_speech_mixed(text, music_bytes):
    """
    Convert text to speech and mix it with background music.
    
    Args:
        text (str): The text to convert to speech
        music_bytes (bytes): Background music audio data in bytes
        
    Returns:
        bytes: Mixed audio containing both the speech and background music
        
    Note:
        Uses the 'Adam' voice from ElevenLabs for speech generation
    """
    client = elevenlabs.ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    
    bytes = b""
    for chunk in client.generate(text=text, voice="Adam"):
        bytes += chunk
        
    return mix_audio(music_bytes, bytes)



