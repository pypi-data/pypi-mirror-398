"""Streaming TTS session for text-in/audio-out streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Callable, Dict, Optional, Union

from kugelaudio.exceptions import (
    AuthenticationError,
    InsufficientCreditsError,
    KugelAudioError,
)
from kugelaudio.models import AudioChunk, StreamConfig

logger = logging.getLogger(__name__)


class StreamingSession:
    """WebSocket session for streaming text input and audio output.

    This allows streaming text (e.g., from an LLM) and receiving audio
    as it's generated. Text is buffered and processed when sentence
    boundaries are detected or when explicitly flushed.

    Example:
        async with client.tts.streaming_session(voice_id=123) as session:
            async for token in llm_stream:
                async for chunk in session.send(token):
                    play_audio(chunk)

            # Flush remaining text
            async for chunk in session.flush():
                play_audio(chunk)
    """

    def __init__(
        self,
        api_key: str,
        tts_url: str,
        config: Optional[StreamConfig] = None,
    ):
        self._api_key = api_key
        self._tts_url = tts_url
        self._config = config or StreamConfig()
        self._ws = None
        self._session_id: Optional[str] = None
        self._is_started = False

    async def __aenter__(self) -> StreamingSession:
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def connect(self) -> None:
        """Connect to the streaming WebSocket endpoint."""
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets required. Install with: pip install websockets"
            )

        ws_url = self._tts_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/ws/tts/stream?api_key={self._api_key}"

        try:
            self._ws = await websockets.connect(ws_url)
        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif e.status_code == 403:
                raise InsufficientCreditsError("Insufficient credits")
            raise KugelAudioError(f"Connection failed: {e}")

    async def start(self) -> None:
        """Start the streaming session with initial config."""
        if self._is_started:
            return

        if not self._ws:
            await self.connect()

        # Send initial config
        await self._ws.send(json.dumps(self._config.to_dict()))

        # Wait for session confirmation
        msg = await self._ws.recv()
        data = json.loads(msg)

        if data.get("error"):
            raise KugelAudioError(data["error"])

        if data.get("session_started"):
            self._session_id = data.get("session_id")
            self._is_started = True
            logger.debug("Streaming session started: %s", self._session_id)

    async def send(
        self,
        text: str,
        flush: bool = False,
    ) -> AsyncIterator[AudioChunk]:
        """Send text and yield any generated audio chunks.

        Args:
            text: Text to add to buffer
            flush: Force flush the buffer

        Yields:
            AudioChunk as audio is generated
        """
        if not self._is_started:
            await self.start()

        # Send text
        await self._ws.send(json.dumps({"text": text, "flush": flush}))

        # Collect any generated audio
        async for chunk in self._receive_until_idle():
            yield chunk

    async def flush(self) -> AsyncIterator[AudioChunk]:
        """Flush the text buffer and yield remaining audio.

        Yields:
            AudioChunk as remaining audio is generated
        """
        if not self._is_started:
            return

        await self._ws.send(json.dumps({"flush": True}))

        async for chunk in self._receive_until_idle():
            yield chunk

    async def _receive_until_idle(self) -> AsyncIterator[AudioChunk]:
        """Receive messages until we get a final message."""
        while True:
            try:
                msg = await asyncio.wait_for(self._ws.recv(), timeout=0.1)
                data = json.loads(msg)

                if data.get("error"):
                    raise KugelAudioError(data["error"])

                if data.get("audio"):
                    yield AudioChunk.from_dict(data)

                if data.get("final"):
                    # Generation complete for this chunk
                    break

            except asyncio.TimeoutError:
                # No more messages waiting
                break
            except Exception as e:
                if "ConnectionClosed" in str(type(e)):
                    break
                raise

    async def close(self) -> Dict[str, Any]:
        """Close the session and return stats.

        Returns:
            Session statistics
        """
        stats = {}

        if self._ws:
            try:
                # Send close command
                await self._ws.send(json.dumps({"close": True}))

                # Wait for session stats
                msg = await asyncio.wait_for(self._ws.recv(), timeout=5.0)
                data = json.loads(msg)

                if data.get("session_closed"):
                    stats = data

            except Exception:
                pass
            finally:
                await self._ws.close()
                self._ws = None
                self._is_started = False

        return stats


class StreamingSessionSync:
    """Synchronous wrapper for StreamingSession."""

    def __init__(self, session: StreamingSession):
        self._session = session
        self._loop = asyncio.new_event_loop()

    def __enter__(self) -> StreamingSessionSync:
        self._loop.run_until_complete(self._session.connect())
        return self

    def __exit__(self, *args) -> None:
        self._loop.run_until_complete(self._session.close())
        self._loop.close()

    def send(self, text: str, flush: bool = False):
        """Send text and return generated audio chunks."""

        async def collect():
            chunks = []
            async for chunk in self._session.send(text, flush=flush):
                chunks.append(chunk)
            return chunks

        return self._loop.run_until_complete(collect())

    def flush(self):
        """Flush buffer and return remaining audio chunks."""

        async def collect():
            chunks = []
            async for chunk in self._session.flush():
                chunks.append(chunk)
            return chunks

        return self._loop.run_until_complete(collect())

    def close(self) -> Dict[str, Any]:
        """Close the session."""
        return self._loop.run_until_complete(self._session.close())

