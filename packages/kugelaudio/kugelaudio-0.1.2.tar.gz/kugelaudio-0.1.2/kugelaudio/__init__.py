"""
KugelAudio Python SDK - Official client for KugelAudio TTS API.

Example usage:
    from kugelaudio import KugelAudio

    client = KugelAudio(api_key="your_api_key")

    # List available models
    models = client.models.list()

    # List available voices
    voices = client.voices.list()

    # Generate audio (non-streaming)
    audio = client.tts.generate(
        text="Hello, world!",
        model="kugel-1-turbo",
        voice_id=123,
    )
    audio.save("output.wav")

    # Generate audio (streaming via WebSocket)
    for chunk in client.tts.stream(
        text="Hello, world!",
        model="kugel-1-turbo",
        voice_id=123,
    ):
        # Process audio chunk
        pass
"""

from kugelaudio.client import KugelAudio
from kugelaudio.exceptions import (
    AuthenticationError,
    InsufficientCreditsError,
    KugelAudioError,
    RateLimitError,
    ValidationError,
)
from kugelaudio.models import (
    AudioChunk,
    AudioResponse,
    GenerateRequest,
    Model,
    StreamConfig,
    Voice,
)
from kugelaudio.streaming import StreamingSession, StreamingSessionSync

__version__ = "0.1.2"
__all__ = [
    "KugelAudio",
    "AudioChunk",
    "AudioResponse",
    "GenerateRequest",
    "Model",
    "StreamConfig",
    "Voice",
    "StreamingSession",
    "StreamingSessionSync",
    "KugelAudioError",
    "AuthenticationError",
    "RateLimitError",
    "InsufficientCreditsError",
    "ValidationError",
]

