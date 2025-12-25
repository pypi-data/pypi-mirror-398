"""Main client for KugelAudio SDK."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union
from urllib.parse import urljoin, urlparse

import httpx
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

logger = logging.getLogger(__name__)

# Default API endpoints
# By default, TTS WebSocket connects to the same URL as the API
# (the backend proxies WebSocket requests to the TTS server)
DEFAULT_API_URL = "https://api.kugelaudio.com"
DEFAULT_TTS_URL = None  # If None, uses api_url


class ModelsResource:
    """Resource for listing available TTS models."""

    def __init__(self, client: KugelAudio):
        self._client = client

    def list(self) -> List[Model]:
        """List available TTS models.

        Returns:
            List of available models
        """
        response = self._client._request("GET", "/v1/models")
        return [Model.from_dict(m) for m in response.get("models", [])]


class VoicesResource:
    """Resource for managing voices."""

    def __init__(self, client: KugelAudio):
        self._client = client

    def list(
        self,
        language: Optional[str] = None,
        include_public: bool = True,
        limit: int = 100,
    ) -> List[Voice]:
        """List available voices.

        Args:
            language: Filter by language code (e.g., 'en', 'de')
            include_public: Include public voices
            limit: Maximum number of voices to return

        Returns:
            List of available voices
        """
        params: Dict[str, Any] = {"limit": limit}
        if language:
            params["language"] = language
        if include_public:
            params["include_public"] = "true"

        response = self._client._request("GET", "/v1/voices", params=params)
        return [Voice.from_dict(v) for v in response.get("voices", [])]

    def get(self, voice_id: int) -> Voice:
        """Get a specific voice by ID.

        Args:
            voice_id: Voice ID

        Returns:
            Voice details
        """
        response = self._client._request("GET", f"/v1/voices/{voice_id}")
        return Voice.from_dict(response)


class TTSResource:
    """Resource for text-to-speech generation."""

    def __init__(self, client: KugelAudio):
        self._client = client
        self._ws_connection = None
        self._ws_lock = asyncio.Lock()
        self._ws_url: Optional[str] = None

    def generate(
        self,
        text: str,
        model: str = "kugel-1-turbo",
        voice_id: Optional[int] = None,
        cfg_scale: float = 2.0,
        max_new_tokens: int = 2048,
        sample_rate: int = 24000,
        speaker_prefix: bool = True,
    ) -> AudioResponse:
        """Generate audio from text (non-streaming).

        This method collects all audio chunks internally and returns
        the complete audio response.

        Args:
            text: Text to synthesize
            model: Model to use ('kugel-1-turbo' for 1.5B or 'kugel-1' for 7B)
            voice_id: Voice ID to use
            cfg_scale: CFG scale for generation
            max_new_tokens: Maximum tokens to generate
            sample_rate: Output sample rate (24000)
            speaker_prefix: Whether to add speaker prefix

        Returns:
            Complete audio response
        """
        request = GenerateRequest(
            text=text,
            model=model,
            voice_id=voice_id,
            cfg_scale=cfg_scale,
            max_new_tokens=max_new_tokens,
            sample_rate=sample_rate,
            speaker_prefix=speaker_prefix,
        )

        # Use sync wrapper for async streaming
        chunks: List[AudioChunk] = []
        final_stats: Dict[str, Any] = {}

        for item in self.stream(
            text=text,
            model=model,
            voice_id=voice_id,
            cfg_scale=cfg_scale,
            max_new_tokens=max_new_tokens,
            sample_rate=sample_rate,
            speaker_prefix=speaker_prefix,
        ):
            if isinstance(item, AudioChunk):
                chunks.append(item)
            elif isinstance(item, dict) and item.get("final"):
                final_stats = item

        return AudioResponse.from_chunks(chunks, final_stats)

    def stream(
        self,
        text: str,
        model: str = "kugel-1-turbo",
        voice_id: Optional[int] = None,
        cfg_scale: float = 2.0,
        max_new_tokens: int = 2048,
        sample_rate: int = 24000,
        speaker_prefix: bool = True,
    ) -> Iterator[Union[AudioChunk, Dict[str, Any]]]:
        """Stream audio from text via WebSocket.

        Yields audio chunks as they are generated. The final message
        contains stats about the generation.

        Args:
            text: Text to synthesize
            model: Model to use ('kugel-1-turbo' for 1.5B or 'kugel-1' for 7B)
            voice_id: Voice ID to use
            cfg_scale: CFG scale for generation
            max_new_tokens: Maximum tokens to generate
            sample_rate: Output sample rate
            speaker_prefix: Whether to add speaker prefix

        Yields:
            AudioChunk for audio data, dict for final stats
        """
        import queue
        import threading

        # Use a thread-safe queue for true streaming
        result_queue: queue.Queue = queue.Queue()
        exception_holder: List[Exception] = []
        done_sentinel = object()

        async def collect():
            try:
                async for item in self.stream_async(
                    text=text,
                    model=model,
                    voice_id=voice_id,
                    cfg_scale=cfg_scale,
                    max_new_tokens=max_new_tokens,
                    sample_rate=sample_rate,
                    speaker_prefix=speaker_prefix,
                ):
                    result_queue.put(item)
            except Exception as e:
                exception_holder.append(e)
            finally:
                result_queue.put(done_sentinel)

        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(collect())
            finally:
                loop.close()

        # Start async collection in background thread
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

        # Yield items as they arrive (true streaming)
        while True:
            item = result_queue.get()
            if item is done_sentinel:
                break
            yield item

        # Check for exceptions after streaming completes
        if exception_holder:
            raise exception_holder[0]

    async def _get_ws_connection(self, model: str):
        """Get or create a WebSocket connection for the given model.
        
        This implements connection pooling to avoid the ~220ms connect
        overhead on each request.
        """
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets is required for streaming. Install with: pip install websockets"
            )

        # Build WebSocket URL
        ws_url = self._client._tts_url.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        ws_url = f"{ws_url}/ws/tts?api_key={self._client._api_key}"
        if model:
            ws_url += f"&model={model}"

        async with self._ws_lock:
            # Check if we have a valid connection for this URL
            # websockets uses .state (OPEN = 1) or .closed property
            if self._ws_connection is not None and self._ws_url == ws_url:
                try:
                    # Check if connection is still open
                    is_open = (
                        hasattr(self._ws_connection, 'open') and self._ws_connection.open
                    ) or (
                        hasattr(self._ws_connection, 'state') 
                        and self._ws_connection.state.name == 'OPEN'
                    ) or (
                        hasattr(self._ws_connection, 'closed') 
                        and not self._ws_connection.closed
                    )
                    if is_open:
                        return self._ws_connection
                except Exception:
                    pass

            # Close old connection if URL changed
            if self._ws_connection is not None:
                try:
                    await self._ws_connection.close()
                except Exception:
                    pass
                self._ws_connection = None

            # Create new connection
            self._ws_connection = await websockets.connect(
                ws_url, compression=None
            )
            self._ws_url = ws_url
            return self._ws_connection

    async def _close_ws_connection(self):
        """Close the pooled WebSocket connection."""
        async with self._ws_lock:
            if self._ws_connection is not None:
                try:
                    await self._ws_connection.close()
                except Exception:
                    pass
                self._ws_connection = None
                self._ws_url = None

    async def stream_async(
        self,
        text: str,
        model: str = "kugel-1-turbo",
        voice_id: Optional[int] = None,
        cfg_scale: float = 2.0,
        max_new_tokens: int = 2048,
        sample_rate: int = 24000,
        speaker_prefix: bool = True,
        reuse_connection: bool = True,
    ) -> AsyncIterator[Union[AudioChunk, Dict[str, Any]]]:
        """Stream audio asynchronously via WebSocket.

        Args:
            text: Text to synthesize
            model: Model to use ('kugel-1-turbo' for 1.5B or 'kugel-1' for 7B)
            voice_id: Voice ID to use
            cfg_scale: CFG scale for generation
            max_new_tokens: Maximum tokens to generate
            sample_rate: Output sample rate
            speaker_prefix: Whether to add speaker prefix
            reuse_connection: If True (default), reuse WebSocket connection
                for faster TTFA (~175ms vs ~390ms). Set to False to always
                create a new connection.

        Yields:
            AudioChunk for audio data, dict for final stats
        """
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets is required for streaming. Install with: pip install websockets"
            )

        request_data = {
            "text": text,
            "model": model,
            "cfg_scale": cfg_scale,
            "max_new_tokens": max_new_tokens,
            "sample_rate": sample_rate,
            "speaker_prefix": speaker_prefix,
        }
        if voice_id is not None:
            request_data["voice_id"] = voice_id

        if reuse_connection:
            # Use connection pooling for faster TTFA
            ws = await self._get_ws_connection(model)
            try:
                await ws.send(json.dumps(request_data))

                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)

                        if data.get("error"):
                            error_msg = data["error"]
                            if (
                                "auth" in error_msg.lower()
                                or "unauthorized" in error_msg.lower()
                            ):
                                raise AuthenticationError(error_msg)
                            elif "credit" in error_msg.lower():
                                raise InsufficientCreditsError(error_msg)
                            else:
                                raise KugelAudioError(error_msg)

                        if data.get("final"):
                            yield data
                            break

                        if data.get("audio"):
                            yield AudioChunk.from_dict(data)

                    except websockets.exceptions.ConnectionClosed as e:
                        # Connection was closed, clear pool and retry once
                        await self._close_ws_connection()
                        if e.code == 4001:
                            raise AuthenticationError("WebSocket authentication failed")
                        elif e.code == 4003:
                            raise InsufficientCreditsError("Insufficient credits")
                        raise KugelAudioError(f"WebSocket connection closed: {e}")

            except websockets.exceptions.ConnectionClosed:
                # Connection died, clear it from pool
                await self._close_ws_connection()
                raise

        else:
            # Original behavior: new connection per request
            ws_url = self._client._tts_url.replace("https://", "wss://").replace(
                "http://", "ws://"
            )
            ws_url = f"{ws_url}/ws/tts?api_key={self._client._api_key}"
            if model:
                ws_url += f"&model={model}"

            try:
                async with websockets.connect(ws_url) as ws:
                    await ws.send(json.dumps(request_data))

                    while True:
                        try:
                            msg = await ws.recv()
                            data = json.loads(msg)

                            if data.get("error"):
                                error_msg = data["error"]
                                if (
                                    "auth" in error_msg.lower()
                                    or "unauthorized" in error_msg.lower()
                                ):
                                    raise AuthenticationError(error_msg)
                                elif "credit" in error_msg.lower():
                                    raise InsufficientCreditsError(error_msg)
                                else:
                                    raise KugelAudioError(error_msg)

                            if data.get("final"):
                                yield data
                                break

                            if data.get("audio"):
                                yield AudioChunk.from_dict(data)

                        except websockets.exceptions.ConnectionClosed as e:
                            if e.code == 4001:
                                raise AuthenticationError("WebSocket authentication failed")
                            elif e.code == 4003:
                                raise InsufficientCreditsError("Insufficient credits")
                            raise KugelAudioError(f"WebSocket connection closed: {e}")

            except websockets.exceptions.InvalidStatusCode as e:
                if e.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif e.status_code == 403:
                    raise InsufficientCreditsError("Insufficient credits")
                elif e.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                raise KugelAudioError(f"Connection failed: {e}")

    def streaming_session(
        self,
        voice_id: Optional[int] = None,
        cfg_scale: float = 2.0,
        max_new_tokens: int = 2048,
        sample_rate: int = 24000,
        speaker_prefix: bool = True,
        flush_timeout_ms: int = 500,
    ):
        """Create a streaming session for text-in/audio-out streaming.

        Use this when streaming text from an LLM and want audio as soon
        as complete sentences are available.

        Example:
            async with client.tts.streaming_session(voice_id=123) as session:
                async for token in llm_stream:
                    async for chunk in session.send(token):
                        play_audio(chunk)

                async for chunk in session.flush():
                    play_audio(chunk)

        Args:
            voice_id: Voice ID to use
            cfg_scale: CFG scale for generation
            max_new_tokens: Maximum tokens per generation
            sample_rate: Output sample rate
            speaker_prefix: Whether to add speaker prefix
            flush_timeout_ms: Auto-flush timeout in milliseconds

        Returns:
            StreamingSession for async use
        """
        from kugelaudio.models import StreamConfig
        from kugelaudio.streaming import StreamingSession

        config = StreamConfig(
            voice_id=voice_id,
            cfg_scale=cfg_scale,
            max_new_tokens=max_new_tokens,
            sample_rate=sample_rate,
            speaker_prefix=speaker_prefix,
            flush_timeout_ms=flush_timeout_ms,
        )

        return StreamingSession(
            api_key=self._client._api_key,
            tts_url=self._client._tts_url,
            config=config,
        )

    def streaming_session_sync(
        self,
        voice_id: Optional[int] = None,
        cfg_scale: float = 2.0,
        max_new_tokens: int = 2048,
        sample_rate: int = 24000,
        speaker_prefix: bool = True,
        flush_timeout_ms: int = 500,
    ):
        """Create a synchronous streaming session.

        Example:
            with client.tts.streaming_session_sync(voice_id=123) as session:
                for token in llm_stream:
                    for chunk in session.send(token):
                        play_audio(chunk)

                for chunk in session.flush():
                    play_audio(chunk)

        Returns:
            StreamingSessionSync for sync use
        """
        from kugelaudio.streaming import StreamingSessionSync

        async_session = self.streaming_session(
            voice_id=voice_id,
            cfg_scale=cfg_scale,
            max_new_tokens=max_new_tokens,
            sample_rate=sample_rate,
            speaker_prefix=speaker_prefix,
            flush_timeout_ms=flush_timeout_ms,
        )

        return StreamingSessionSync(async_session)

    async def generate_async(
        self,
        text: str,
        model: str = "kugel-1-turbo",
        voice_id: Optional[int] = None,
        cfg_scale: float = 2.0,
        max_new_tokens: int = 2048,
        sample_rate: int = 24000,
        speaker_prefix: bool = True,
    ) -> AudioResponse:
        """Generate audio asynchronously.

        Args:
            text: Text to synthesize
            model: Model to use ('kugel-1-turbo' for 1.5B or 'kugel-1' for 7B)
            voice_id: Voice ID to use
            cfg_scale: CFG scale for generation
            max_new_tokens: Maximum tokens to generate
            sample_rate: Output sample rate
            speaker_prefix: Whether to add speaker prefix

        Returns:
            Complete audio response
        """
        chunks: List[AudioChunk] = []
        final_stats: Dict[str, Any] = {}

        async for item in self.stream_async(
            text=text,
            model=model,
            voice_id=voice_id,
            cfg_scale=cfg_scale,
            max_new_tokens=max_new_tokens,
            sample_rate=sample_rate,
            speaker_prefix=speaker_prefix,
        ):
            if isinstance(item, AudioChunk):
                chunks.append(item)
            elif isinstance(item, dict) and item.get("final"):
                final_stats = item

        return AudioResponse.from_chunks(chunks, final_stats)


class KugelAudio:
    """KugelAudio API client.

    Example:
        client = KugelAudio(api_key="your_api_key")

        # List models
        models = client.models.list()

        # List voices
        voices = client.voices.list()

        # Generate audio with fast model (1.5B params)
        audio = client.tts.generate(
            text="Hello, world!",
            model="kugel-1-turbo",
        )
        audio.save("output.wav")

        # Generate audio with premium model (7B params)
        audio = client.tts.generate(
            text="Hello, world!",
            model="kugel-1",
        )
    """

    def __init__(
        self,
        api_key: str,
        api_url: Optional[str] = None,
        tts_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        """Initialize KugelAudio client.

        Args:
            api_key: Your KugelAudio API key
            api_url: API base URL (default: https://api.kugelaudio.com)
            tts_url: TTS server URL (default: same as api_url, the backend proxies WebSocket)
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValidationError("API key is required")

        self._api_key = api_key
        self._api_url = (api_url or DEFAULT_API_URL).rstrip("/")
        # If tts_url not specified, use api_url (backend proxies to TTS server)
        self._tts_url = (tts_url or self._api_url).rstrip("/")
        self._timeout = timeout

        # Initialize resources
        self.models = ModelsResource(self)
        self.voices = VoicesResource(self)
        self.tts = TTSResource(self)

        # HTTP client
        self._http_client = httpx.Client(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-API-Key": api_key,
                "User-Agent": "kugelaudio-python/0.1.0",
            },
        )

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to API.

        Args:
            method: HTTP method
            path: API path
            params: Query parameters
            json_data: JSON body

        Returns:
            Response data

        Raises:
            KugelAudioError: On API error
        """
        url = urljoin(self._api_url + "/", path.lstrip("/"))

        try:
            response = self._http_client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )

            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 403:
                raise InsufficientCreditsError("Access denied or insufficient credits")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    message = (
                        error_data.get("detail")
                        or error_data.get("error")
                        or str(error_data)
                    )
                except Exception:
                    message = response.text or f"HTTP {response.status_code}"
                raise KugelAudioError(message, status_code=response.status_code)

            return response.json()

        except httpx.TimeoutException:
            raise KugelAudioError("Request timed out")
        except httpx.RequestError as e:
            raise KugelAudioError(f"Request failed: {e}")

    def close(self) -> None:
        """Close the client and release resources."""
        self._http_client.close()
        # Close WebSocket pool if any
        if hasattr(self.tts, '_ws_connection') and self.tts._ws_connection is not None:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.tts._close_ws_connection())
                else:
                    loop.run_until_complete(self.tts._close_ws_connection())
            except Exception:
                pass

    async def aclose(self) -> None:
        """Close the client asynchronously."""
        self._http_client.close()
        if hasattr(self.tts, '_close_ws_connection'):
            await self.tts._close_ws_connection()

    def __enter__(self) -> KugelAudio:
        return self

    def __exit__(self, *args) -> None:
        self.close()

