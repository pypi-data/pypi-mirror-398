# Changelog

All notable changes to the KugelAudio Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-17

### Added
- Initial release of the KugelAudio Python SDK
- **Models API**: List available TTS models (`client.models.list()`)
- **Voices API**: List voices (`client.voices.list()`) and get voice details (`client.voices.get()`)
- **TTS Generation**: Generate complete audio (`client.tts.generate()`)
- **Streaming**: Real-time audio streaming via WebSocket (`client.tts.stream()`)
- **Async Support**: Full async/await support (`stream_async()`, `generate_async()`)
- **Streaming Sessions**: LLM integration for real-time TTS (`client.tts.streaming_session()`)
- **Audio Utilities**: Save to WAV, get duration, RTF calculation
- **Error Handling**: Typed exceptions for auth, rate limits, validation errors
- **Single URL Architecture**: Connect to TTS server directly for minimal latency
