# KugelAudio Python SDK

Official Python SDK for the KugelAudio Text-to-Speech API.

## Installation

```bash
pip install kugelaudio
```

Or with `uv`:

```bash
uv add kugelaudio
```

## Quick Start

```python
from kugelaudio import KugelAudio

# Initialize the client - just needs an API key!
client = KugelAudio(api_key="your_api_key")

# Generate speech
audio = client.tts.generate(
    text="Hello, world!",
    model="kugel-1-turbo",
)

# Save to file
audio.save("output.wav")
```

## Client Configuration

```python
from kugelaudio import KugelAudio

# Simple setup - single URL handles everything
client = KugelAudio(api_key="your_api_key")

# Or with custom options
client = KugelAudio(
    api_key="your_api_key",           # Required: Your API key
    api_url="https://api.kugelaudio.com",  # Optional: API base URL (default)
    timeout=60.0,                      # Optional: Request timeout in seconds
)
```

### Single URL Architecture

The SDK uses a **single URL** for both REST API and WebSocket streaming. The TTS server provides both REST endpoints (`/v1/models`, `/v1/voices`) and WebSocket (`/ws/tts`) - no proxy needed, minimal latency.

### Local Development

For local development, point directly to your TTS server:

```python
client = KugelAudio(
    api_key="your_api_key",
    api_url="http://localhost:8000",   # TTS server handles everything
)
```

Or if you have separate backend and TTS servers:

```python
client = KugelAudio(
    api_key="your_api_key",
    api_url="http://localhost:8001",   # Backend for REST API
    tts_url="http://localhost:8000",   # TTS server for WebSocket streaming
)
```

## Available Models

| Model ID | Name | Parameters | Description |
|----------|------|------------|-------------|
| `kugel-1-turbo` | Kugel 1 Turbo | 1.5B | Fast, low-latency model for real-time applications |
| `kugel-1` | Kugel 1 | 7B | Premium quality model for pre-recorded content |

### List Available Models

```python
models = client.models.list()

for model in models:
    print(f"{model.id}: {model.name}")
    print(f"  Description: {model.description}")
    print(f"  Parameters: {model.parameters}")
    print(f"  Max Input: {model.max_input_length} characters")
    print(f"  Sample Rate: {model.sample_rate} Hz")
```

## Voices

### List Available Voices

```python
# List all available voices
voices = client.voices.list()

for voice in voices:
    print(f"{voice.id}: {voice.name}")
    print(f"  Category: {voice.category}")
    print(f"  Languages: {', '.join(voice.supported_languages)}")

# Filter by language
german_voices = client.voices.list(language="de")

# Get only public voices
public_voices = client.voices.list(include_public=True)

# Limit results
first_10 = client.voices.list(limit=10)
```

### Get a Specific Voice

```python
voice = client.voices.get(voice_id=123)
print(f"Voice: {voice.name}")
print(f"Sample text: {voice.sample_text}")
```

## Text-to-Speech Generation

### Basic Generation (Non-Streaming)

Generate complete audio and receive it all at once:

```python
audio = client.tts.generate(
    text="Hello, this is a test of the KugelAudio text-to-speech system.",
    model="kugel-1-turbo",  # 'kugel-1-turbo' (fast) or 'kugel-1' (quality)
    voice_id=123,              # Optional: specific voice ID
    cfg_scale=2.0,             # Guidance scale (1.0-5.0)
    max_new_tokens=2048,       # Maximum tokens to generate
    sample_rate=24000,         # Output sample rate
    speaker_prefix=True,       # Add speaker prefix for better quality
)

# Audio properties
print(f"Duration: {audio.duration_seconds:.2f}s")
print(f"Samples: {audio.samples}")
print(f"Sample rate: {audio.sample_rate} Hz")
print(f"Generation time: {audio.generation_ms:.0f}ms")
print(f"RTF: {audio.rtf:.2f}")  # Real-time factor

# Save to WAV file
audio.save("output.wav")

# Get raw PCM bytes
pcm_data = audio.audio

# Get WAV bytes (with header)
wav_bytes = audio.to_wav_bytes()
```

### Streaming Audio Output

Receive audio chunks as they are generated for lower latency:

```python
# Synchronous streaming
for item in client.tts.stream(
    text="Hello, this is streaming audio.",
    model="kugel-1-turbo",
):
    if hasattr(item, 'audio'):  # AudioChunk
        # Process audio chunk immediately
        print(f"Chunk {item.index}: {len(item.audio)} bytes, {item.samples} samples")
        # play_audio(item.audio)
    elif isinstance(item, dict) and item.get('final'):
        # Final stats
        print(f"Total duration: {item.get('dur_ms', 0):.0f}ms")
        print(f"Time to first audio: {item.get('ttfa_ms', 0):.0f}ms")
```

### Async Streaming

For async applications:

```python
import asyncio

async def generate_speech():
    async for item in client.tts.stream_async(
        text="Async streaming example.",
        model="kugel-1-turbo",
    ):
        if hasattr(item, 'audio'):
            # Process chunk
            pass

asyncio.run(generate_speech())
```

### Async Generation

```python
import asyncio

async def main():
    audio = await client.tts.generate_async(
        text="Async generation example.",
        model="kugel-1-turbo",
    )
    audio.save("async_output.wav")

asyncio.run(main())
```

## LLM Integration: Streaming Text Input

For real-time TTS when streaming text from an LLM (like GPT-4, Claude, etc.):

### Async Streaming Session

```python
import asyncio

async def stream_from_llm():
    # Simulate LLM token stream
    llm_tokens = ["Hello, ", "this ", "is ", "a ", "streamed ", "response."]
    
    async with client.tts.streaming_session(
        voice_id=123,
        cfg_scale=2.0,
        flush_timeout_ms=500,  # Auto-flush after 500ms of no input
    ) as session:
        # Send tokens as they arrive from LLM
        for token in llm_tokens:
            async for chunk in session.send(token):
                # Play audio chunk immediately
                play_audio(chunk.audio)
        
        # Flush any remaining text
        async for chunk in session.flush():
            play_audio(chunk.audio)

asyncio.run(stream_from_llm())
```

### Synchronous Streaming Session

```python
with client.tts.streaming_session_sync(voice_id=123) as session:
    for token in llm_tokens:
        for chunk in session.send(token):
            play_audio(chunk.audio)
    
    for chunk in session.flush():
        play_audio(chunk.audio)
```

## Error Handling

```python
from kugelaudio import KugelAudio
from kugelaudio.exceptions import (
    KugelAudioError,
    AuthenticationError,
    RateLimitError,
    InsufficientCreditsError,
    ValidationError,
    ConnectionError,
)

try:
    audio = client.tts.generate(text="Hello!")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded, please wait")
except InsufficientCreditsError:
    print("Not enough credits, please top up")
except ValidationError as e:
    print(f"Invalid request: {e}")
except ConnectionError:
    print("Failed to connect to server")
except KugelAudioError as e:
    print(f"API error: {e}")
```

## Data Models

### AudioChunk

Represents a single audio chunk from streaming:

```python
class AudioChunk:
    audio: bytes          # Raw PCM16 audio data
    encoding: str         # 'pcm_s16le'
    index: int           # Chunk index (0-based)
    sample_rate: int     # Sample rate (24000)
    samples: int         # Number of samples in chunk
    
    @property
    def duration_seconds(self) -> float:
        """Duration of this chunk in seconds."""
```

### AudioResponse

Complete audio response from generation:

```python
class AudioResponse:
    audio: bytes              # Complete PCM16 audio
    sample_rate: int          # Sample rate (24000)
    samples: int              # Total samples
    duration_ms: float        # Duration in milliseconds
    generation_ms: float      # Generation time in milliseconds
    rtf: float               # Real-time factor
    
    @property
    def duration_seconds(self) -> float:
        """Duration in seconds."""
    
    def save(self, path: str) -> None:
        """Save as WAV file."""
    
    def to_wav_bytes(self) -> bytes:
        """Get WAV file as bytes."""
```

### Model

TTS model information:

```python
class Model:
    id: str                   # 'kugel-1-turbo' or 'kugel-1'
    name: str                 # Human-readable name
    description: str          # Model description
    parameters: str           # Parameter count ('1.5B', '7B')
    max_input_length: int     # Maximum input characters
    sample_rate: int          # Output sample rate
```

### Voice

Voice information:

```python
class Voice:
    id: int                          # Voice ID
    name: str                        # Voice name
    description: Optional[str]       # Description
    category: Optional[VoiceCategory]  # 'premade', 'cloned', 'generated'
    sex: Optional[VoiceSex]          # 'male', 'female', 'neutral'
    age: Optional[VoiceAge]          # 'young', 'middle_aged', 'old'
    supported_languages: List[str]   # ['en', 'de', ...]
    sample_text: Optional[str]       # Sample text for preview
    avatar_url: Optional[str]        # Avatar image URL
    sample_url: Optional[str]        # Sample audio URL
    is_public: bool                  # Whether voice is public
    verified: bool                   # Whether voice is verified
```

## Complete Example

```python
from kugelaudio import KugelAudio

# Initialize client
client = KugelAudio(api_key="your_api_key")

# List available models
print("Available Models:")
for model in client.models.list():
    print(f"  - {model.id}: {model.name} ({model.parameters})")

# List available voices
print("\nAvailable Voices:")
for voice in client.voices.list(limit=5):
    print(f"  - {voice.id}: {voice.name}")

# Generate audio
print("\nGenerating audio...")
audio = client.tts.generate(
    text="Welcome to KugelAudio. This is an example of high-quality text-to-speech synthesis.",
    model="kugel-1-turbo",
)

print(f"Generated {audio.duration_seconds:.2f}s of audio in {audio.generation_ms:.0f}ms")
print(f"Real-time factor: {audio.rtf:.2f}x")

# Save to file
audio.save("example.wav")
print("Saved to example.wav")

# Close client
client.close()
```

## License

MIT

