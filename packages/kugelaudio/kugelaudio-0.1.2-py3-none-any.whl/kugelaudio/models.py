"""Data models for KugelAudio SDK."""

from __future__ import annotations

import base64
import io
import struct
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional


class VoiceCategory(str, Enum):
    """Voice category types."""

    PREMADE = "premade"
    CLONED = "cloned"
    DESIGNED = "designed"
    CONVERSATIONAL = "conversational"
    NARRATIVE = "narrative"
    CHARACTERS = "characters"


class VoiceSex(str, Enum):
    """Voice sex types."""

    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VoiceAge(str, Enum):
    """Voice age types."""

    YOUNG = "young"
    MIDDLE_AGED = "middle_aged"
    MIDDLE_AGE = "middle_age"  # Alternative spelling
    OLD = "old"


@dataclass
class Model:
    """TTS model information."""

    id: str
    name: str
    description: str
    parameters: str  # e.g., "1.5B", "7B"
    max_input_length: int = 5000
    sample_rate: int = 24000

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Model:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            parameters=data.get("parameters", ""),
            max_input_length=data.get("max_input_length", 5000),
            sample_rate=data.get("sample_rate", 24000),
        )


@dataclass
class Voice:
    """Voice information."""

    id: int
    name: str
    description: Optional[str] = None
    category: Optional[VoiceCategory] = None
    sex: Optional[VoiceSex] = None
    age: Optional[VoiceAge] = None
    supported_languages: List[str] = field(default_factory=list)
    sample_text: Optional[str] = None
    avatar_url: Optional[str] = None
    sample_url: Optional[str] = None
    is_public: bool = False
    verified: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Voice:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            category=VoiceCategory(data["category"]) if data.get("category") else None,
            sex=VoiceSex(data["sex"]) if data.get("sex") else None,
            age=VoiceAge(data["age"]) if data.get("age") else None,
            supported_languages=data.get("supported_languages") or [],
            sample_text=data.get("sample_text"),
            avatar_url=data.get("avatar_url"),
            sample_url=data.get("sample_url"),
            is_public=data.get("is_public", False),
            verified=data.get("verified", False),
        )


@dataclass
class GenerateRequest:
    """Request for TTS generation."""

    text: str
    model: str = "kugel-1-turbo"
    voice_id: Optional[int] = None
    cfg_scale: float = 2.0
    max_new_tokens: int = 2048
    sample_rate: int = 24000
    speaker_prefix: bool = True

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "text": self.text,
            "model": self.model,
            "cfg_scale": self.cfg_scale,
            "max_new_tokens": self.max_new_tokens,
            "sample_rate": self.sample_rate,
            "speaker_prefix": self.speaker_prefix,
        }
        if self.voice_id is not None:
            result["voice_id"] = self.voice_id
        return result


@dataclass
class StreamConfig:
    """Configuration for streaming TTS sessions."""

    voice_id: Optional[int] = None
    cfg_scale: float = 2.0
    max_new_tokens: int = 2048
    sample_rate: int = 24000
    speaker_prefix: bool = True
    flush_timeout_ms: int = 500
    max_buffer_length: int = 1000

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "cfg_scale": self.cfg_scale,
            "max_new_tokens": self.max_new_tokens,
            "sample_rate": self.sample_rate,
            "speaker_prefix": self.speaker_prefix,
            "flush_timeout_ms": self.flush_timeout_ms,
            "max_buffer_length": self.max_buffer_length,
        }
        if self.voice_id is not None:
            result["voice_id"] = self.voice_id
        return result


@dataclass
class AudioChunk:
    """Audio chunk from streaming TTS."""

    audio: bytes  # Raw PCM16 audio bytes
    index: int
    sample_rate: int
    samples: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AudioChunk:
        """Create from WebSocket message."""
        audio_b64 = data["audio"]
        audio_bytes = base64.b64decode(audio_b64)
        return cls(
            audio=audio_bytes,
            index=data["idx"],
            sample_rate=data["sr"],
            samples=data["samples"],
        )

    def to_float32(self) -> List[float]:
        """Convert PCM16 to float32 samples (-1.0 to 1.0)."""
        int16_samples = struct.unpack(f"<{len(self.audio) // 2}h", self.audio)
        return [s / 32768.0 for s in int16_samples]

    @property
    def duration_seconds(self) -> float:
        """Duration of this chunk in seconds."""
        return self.samples / self.sample_rate


@dataclass
class AudioResponse:
    """Complete audio response from TTS generation."""

    audio: bytes  # Raw PCM16 audio bytes
    sample_rate: int
    samples: int
    duration_ms: float
    generation_ms: float
    rtf: float  # Real-time factor

    @classmethod
    def from_chunks(
        cls, chunks: List[AudioChunk], final_stats: Dict[str, Any]
    ) -> AudioResponse:
        """Create from collected chunks and final stats."""
        all_audio = b"".join(c.audio for c in chunks)
        sample_rate = chunks[0].sample_rate if chunks else 24000
        return cls(
            audio=all_audio,
            sample_rate=sample_rate,
            samples=final_stats.get("total_samples", len(all_audio) // 2),
            duration_ms=final_stats.get("dur_ms", 0.0),
            generation_ms=final_stats.get("gen_ms", 0.0),
            rtf=final_stats.get("rtf", 0.0),
        )

    def to_float32(self) -> List[float]:
        """Convert PCM16 to float32 samples (-1.0 to 1.0)."""
        int16_samples = struct.unpack(f"<{len(self.audio) // 2}h", self.audio)
        return [s / 32768.0 for s in int16_samples]

    @property
    def duration_seconds(self) -> float:
        """Duration in seconds."""
        return self.samples / self.sample_rate

    def save(self, path: str, format: str = "wav") -> None:
        """Save audio to file.

        Args:
            path: Output file path
            format: Output format ('wav' or 'raw')
        """
        if format == "wav":
            self._save_wav(path)
        elif format == "raw":
            with open(path, "wb") as f:
                f.write(self.audio)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _save_wav(self, path: str) -> None:
        """Save as WAV file."""
        with open(path, "wb") as f:
            # WAV header
            f.write(b"RIFF")
            data_size = len(self.audio)
            f.write(struct.pack("<I", 36 + data_size))  # File size - 8
            f.write(b"WAVEfmt ")
            f.write(
                struct.pack(
                    "<IHHIIHH",
                    16,  # Subchunk1Size (16 for PCM)
                    1,  # AudioFormat (1 for PCM)
                    1,  # NumChannels (mono)
                    self.sample_rate,  # SampleRate
                    self.sample_rate * 2,  # ByteRate
                    2,  # BlockAlign
                    16,  # BitsPerSample
                )
            )
            f.write(b"data")
            f.write(struct.pack("<I", data_size))
            f.write(self.audio)

    def to_wav_bytes(self) -> bytes:
        """Get WAV file as bytes."""
        buffer = io.BytesIO()
        # WAV header
        buffer.write(b"RIFF")
        data_size = len(self.audio)
        buffer.write(struct.pack("<I", 36 + data_size))
        buffer.write(b"WAVEfmt ")
        buffer.write(
            struct.pack(
                "<IHHIIHH", 16, 1, 1, self.sample_rate, self.sample_rate * 2, 2, 16
            )
        )
        buffer.write(b"data")
        buffer.write(struct.pack("<I", data_size))
        buffer.write(self.audio)
        return buffer.getvalue()

