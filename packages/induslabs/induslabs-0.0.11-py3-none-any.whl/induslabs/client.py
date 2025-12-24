"""
IndusLabs Voice API SDK
A Python client for text-to-speech and speech-to-text services.
"""

import os
import json
import asyncio
import warnings
import aiohttp
import requests
import numpy as np
import soundfile as sf
from typing import Optional, Union, AsyncIterator, Iterator, BinaryIO, List, Callable
from pathlib import Path
from dataclasses import dataclass
import io


__version__ = "0.0.11"


class Voice:
    """Represents a single voice."""

    def __init__(self, name: str, voice_id: str, gender: str, language: str):
        self.name = name
        self.voice_id = voice_id
        self.gender = gender
        self.language = language

    def __repr__(self) -> str:
        return (
            f"Voice(name='{self.name}', voice_id='{self.voice_id}', "
            f"gender='{self.gender}', language='{self.language}')"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "voice_id": self.voice_id,
            "gender": self.gender,
            "language": self.language,
        }


class VoiceResponse:
    """Response object for voice listing requests."""

    def __init__(self, data: dict):
        self.status_code = data.get("status_code")
        self.message = data.get("message")
        self.error = data.get("error")
        self._raw_data = data.get("data", {})
        self.voices = self._parse_voices()

    def _parse_voices(self) -> List[Voice]:
        """Parse voice data into Voice objects."""
        voices = []
        for language, voice_list in self._raw_data.items():
            for voice_data in voice_list:
                voices.append(
                    Voice(
                        name=voice_data["name"],
                        voice_id=voice_data["voice_id"],
                        gender=voice_data["gender"],
                        language=language,
                    )
                )
        return voices

    def get_voices_by_language(self, language: str) -> List[Voice]:
        """Get all voices for a specific language."""
        return [v for v in self.voices if v.language == language]

    def get_voices_by_gender(self, gender: str) -> List[Voice]:
        """Get all voices for a specific gender."""
        return [v for v in self.voices if v.gender == gender]

    def get_voice_by_id(self, voice_id: str) -> Optional[Voice]:
        """Get a specific voice by ID."""
        for v in self.voices:
            if v.voice_id == voice_id:
                return v
        return None

    def list_voice_ids(self) -> List[str]:
        """Get list of all voice IDs."""
        return [v.voice_id for v in self.voices]

    def to_dict(self) -> dict:
        """Return raw response data as dictionary."""
        return {
            "status_code": self.status_code,
            "message": self.message,
            "error": self.error,
            "data": self._raw_data,
        }

    def __repr__(self) -> str:
        return f"VoiceResponse(voices={len(self.voices)})"


class TTSResponse:
    """Response object for TTS requests."""

    def __init__(self, content: bytes, headers: dict, request_id: str):
        self.content = content
        self.headers = headers
        self.request_id = request_id
        self.sample_rate = int(headers.get("x-sample-rate", 24000))
        self.channels = int(headers.get("x-channels", 1))
        self.bit_depth = int(headers.get("x-bit-depth", 16))
        self.format = headers.get("x-format", "wav")

    def save(self, filepath: Union[str, Path]) -> None:
        """Save audio to file."""
        with open(filepath, "wb") as f:
            f.write(self.content)

    def stream_to_file(self, filepath: Union[str, Path]) -> None:
        """Alias for save() for consistency."""
        self.save(filepath)

    def get_audio_data(self) -> bytes:
        """Get raw audio bytes."""
        return self.content

    def to_file_object(self) -> BinaryIO:
        """Return audio as a file-like object."""
        return io.BytesIO(self.content)


class TTSStreamResponse:
    """Streaming response object for TTS requests."""

    def __init__(self, response, headers: dict, request_id: str):
        self._response = response
        self.headers = headers
        self.request_id = request_id
        self.sample_rate = int(headers.get("x-sample-rate", 24000))
        self.channels = int(headers.get("x-channels", 1))
        self.bit_depth = int(headers.get("x-bit-depth", 16))
        self.format = headers.get("x-format", "wav")

    def iter_bytes(self, chunk_size: int = 8192) -> Iterator[bytes]:
        """Iterate over audio bytes as they arrive."""
        for chunk in self._response.iter_content(chunk_size=chunk_size):
            if chunk:
                yield chunk

    def save(self, filepath: Union[str, Path], chunk_size: int = 8192) -> None:
        """Save streamed audio to file."""
        with open(filepath, "wb") as f:
            for chunk in self.iter_bytes(chunk_size=chunk_size):
                f.write(chunk)

    def to_file_object(self, chunk_size: int = 8192) -> BinaryIO:
        """Convert stream to file-like object by reading all chunks."""
        buffer = io.BytesIO()
        for chunk in self.iter_bytes(chunk_size=chunk_size):
            buffer.write(chunk)
        buffer.seek(0)
        return buffer


class AsyncTTSStreamResponse:
    """Async streaming response object for TTS requests."""

    def __init__(self, response: aiohttp.ClientResponse, headers: dict, request_id: str):
        self._response = response
        self.headers = headers
        self.request_id = request_id
        self.sample_rate = int(headers.get("x-sample-rate", 24000))
        self.channels = int(headers.get("x-channels", 1))
        self.bit_depth = int(headers.get("x-bit-depth", 16))
        self.format = headers.get("x-format", "wav")

    async def iter_bytes(self, chunk_size: int = 8192) -> AsyncIterator[bytes]:
        """Async iterate over audio bytes as they arrive."""
        async for chunk in self._response.content.iter_chunked(chunk_size):
            if chunk:
                yield chunk

    async def save(self, filepath: Union[str, Path], chunk_size: int = 8192) -> None:
        """Save streamed audio to file asynchronously."""
        with open(filepath, "wb") as f:
            async for chunk in self.iter_bytes(chunk_size=chunk_size):
                f.write(chunk)

    async def to_file_object(self, chunk_size: int = 8192) -> BinaryIO:
        """Convert stream to file-like object by reading all chunks."""
        buffer = io.BytesIO()
        async for chunk in self.iter_bytes(chunk_size=chunk_size):
            buffer.write(chunk)
        buffer.seek(0)
        return buffer


@dataclass
class STTSegment:
    """Represents a segment of transcribed text."""

    text: str
    start: Optional[float] = None
    end: Optional[float] = None


@dataclass
class STTMetrics:
    """Performance metrics for STT transcription."""

    buffer_duration: float
    transcription_time: float
    total_time: float
    rtf: Optional[float]  # Real-time factor
    request_id: str


class STTResponse:
    """Response object for STT requests."""

    def __init__(self):
        self.segments: List[STTSegment] = []
        self.text: str = ""
        self.request_id: Optional[str] = None
        self.language_detected: Optional[str] = None
        self.audio_duration_seconds: Optional[float] = None
        self.processing_time_seconds: Optional[float] = None
        self.first_token_time_seconds: Optional[float] = None
        self.credits_used: Optional[float] = None
        self.metrics: Optional[STTMetrics] = None
        self._error: Optional[str] = None
        self._completed: bool = False

    def add_segment(self, text: str, start: Optional[float] = None, end: Optional[float] = None):
        """Add a transcription segment."""
        self.segments.append(STTSegment(text=text, start=start, end=end))

    def set_final(self, text: str, request_id: str):
        """Set final transcription text."""
        self.text = text
        self.request_id = request_id

    def set_metrics(
        self,
        buffer: float,
        transcription: float,
        total: float,
        rtf: Optional[float],
        request_id: str,
    ):
        """Set performance metrics."""
        self.metrics = STTMetrics(
            buffer_duration=buffer,
            transcription_time=transcription,
            total_time=total,
            rtf=rtf,
            request_id=request_id,
        )
        self.processing_time_seconds = transcription
        self.audio_duration_seconds = buffer

    def set_error(self, error: str):
        """Set error message."""
        self._error = error
        self._completed = True

    def complete(self):
        """Mark the response as completed."""
        self._completed = True

    @property
    def is_completed(self) -> bool:
        """Check if the response is completed."""
        return self._completed

    @property
    def has_error(self) -> bool:
        """Check if there was an error."""
        return self._error is not None

    @property
    def error(self) -> Optional[str]:
        """Get error message if any."""
        return self._error

    def to_dict(self) -> dict:
        """Return response data as dictionary."""
        return {
            "request_id": self.request_id,
            "text": self.text,
            "language_detected": self.language_detected,
            "audio_duration_seconds": self.audio_duration_seconds,
            "processing_time_seconds": self.processing_time_seconds,
            "first_token_time_seconds": self.first_token_time_seconds,
            "credits_used": self.credits_used,
            "segments": [{"text": s.text, "start": s.start, "end": s.end} for s in self.segments],
            "metrics": (
                {
                    "buffer_duration": self.metrics.buffer_duration,
                    "transcription_time": self.metrics.transcription_time,
                    "total_time": self.metrics.total_time,
                    "rtf": self.metrics.rtf,
                    "request_id": self.metrics.request_id,
                }
                if self.metrics
                else None
            ),
        }

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"STTResponse(text='{self.text[:50]}...', language='{self.language_detected}')"


# ============================================================================
# Voices Interface
# ============================================================================


class Voices:
    """Voice management interface."""

    def __init__(self, api_key: str, voices_base_url: str = "https://api.indusai.app"):
        self.api_key = api_key
        self.voices_base_url = voices_base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    def list(self) -> VoiceResponse:
        """Get all available voices (synchronous)."""
        url = f"{self.voices_base_url}/api/voice/get-voices"
        response = requests.post(url, headers={"accept": "application/json"})
        response.raise_for_status()
        return VoiceResponse(response.json())

    async def list_async(self) -> VoiceResponse:
        """Get all available voices (asynchronous)."""
        url = f"{self.voices_base_url}/api/voice/get-voices"

        if self._session is None:
            self._session = aiohttp.ClientSession()

        async with self._session.post(url, headers={"accept": "application/json"}) as response:
            response.raise_for_status()
            data = await response.json()
            return VoiceResponse(data)

    async def close(self):
        """Close async session."""
        if self._session:
            await self._session.close()
            self._session = None


class TTS:
    """Text-to-Speech interface."""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None

    def speak(
        self,
        text: str,
        voice: str = "Indus-hi-Urvashi",
        language: Optional[str] = None,
        output_format: str = "wav",
        stream: bool = False,
        model: str = "orpheus-3b",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        sample_rate: int = 24000,
        speed: float = 1.0,
        pitch_shift: float = 0.0,
        loudness_db: float = 0.0,
    ) -> Union[TTSResponse, TTSStreamResponse]:
        """Synchronous text-to-speech conversion."""
        if output_format not in ["wav", "mp3", "pcm"]:
            raise ValueError("output_format must be 'wav', 'mp3', or 'pcm'")

        url = f"{self.base_url}/v1/audio/speech"

        payload = {
            "text": text,
            "voice": voice,
            "output_format": output_format,
            "stream": stream,
            "model": model,
            "api_key": self.api_key,
            "normalize": True,
            "read_urls_as": "verbatim",
            "sample_rate": sample_rate,
            "speed": speed,
            "pitch_shift": pitch_shift,
            "loudness_db": loudness_db,
        }

        if language:
            payload["language"] = language
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        response = requests.post(url, json=payload, stream=stream)
        response.raise_for_status()

        request_id = response.headers.get("x-request-id", "")

        if stream:
            return TTSStreamResponse(response, dict(response.headers), request_id)
        else:
            return TTSResponse(response.content, dict(response.headers), request_id)

    async def speak_async(
        self,
        text: str,
        voice: str = "Indus-hi-Urvashi",
        language: Optional[str] = None,
        output_format: str = "wav",
        stream: bool = False,
        model: str = "orpheus-3b",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        sample_rate: int = 24000,
        speed: float = 1.0,
        pitch_shift: float = 0.0,
        loudness_db: float = 0.0,
    ) -> Union[TTSResponse, AsyncTTSStreamResponse]:
        """Asynchronous text-to-speech conversion."""
        if output_format not in ["wav", "mp3", "pcm"]:
            raise ValueError("output_format must be 'wav', 'mp3', or 'pcm'")

        url = f"{self.base_url}/v1/audio/speech"

        payload = {
            "text": text,
            "voice": voice,
            "output_format": output_format,
            "stream": stream,
            "model": model,
            "api_key": self.api_key,
            "normalize": True,
            "read_urls_as": "verbatim",
            "sample_rate": sample_rate,
            "speed": speed,
            "pitch_shift": pitch_shift,
            "loudness_db": loudness_db,
        }

        if language:
            payload["language"] = language
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if self._session is None:
            self._session = aiohttp.ClientSession()

        async with self._session.post(url, json=payload) as response:
            response.raise_for_status()
            request_id = response.headers.get("x-request-id", "")

            if stream:
                return AsyncTTSStreamResponse(response, dict(response.headers), request_id)
            else:
                content = await response.read()
                return TTSResponse(content, dict(response.headers), request_id)

    async def close(self):
        """Close async session."""
        if self._session:
            await self._session.close()
            self._session = None


class STT:
    """Speech-to-Text interface."""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self._ws_session: Optional[aiohttp.ClientSession] = None

    def _convert_audio_to_pcm16(self, audio_data: bytes) -> bytes:
        """Convert audio to PCM16 format at 16kHz."""
        try:
            # Read audio using soundfile
            audio_buffer = io.BytesIO(audio_data)
            audio_np, sample_rate = sf.read(audio_buffer, dtype="float32")

            # Resample to 16kHz if needed
            if sample_rate != 16000:
                # Simple resampling using numpy
                duration = len(audio_np) / sample_rate
                target_length = int(duration * 16000)
                audio_np = np.interp(
                    np.linspace(0, len(audio_np), target_length), np.arange(len(audio_np)), audio_np
                )

            # Convert to mono if stereo
            if len(audio_np.shape) > 1:
                audio_np = np.mean(audio_np, axis=1)

            # Convert to int16 PCM
            audio_int16 = (audio_np * 32767).astype(np.int16)
            return audio_int16.tobytes()
        except Exception as e:
            raise ValueError(f"Failed to convert audio to PCM16: {e}")

    def transcribe(
        self,
        file: Union[str, Path, BinaryIO],
        model: str = "indus-stt-v1",
        streaming: bool = False,  # Changed to bool
        noise_cancellation: bool = False,
        language: Optional[str] = None,
        on_segment: Optional[Callable[[STTSegment], None]] = None,
        chunk_size: int = 8192,
    ) -> STTResponse:
        """
        Synchronous speech-to-text transcription using WebSocket.

        This method streams audio to the server via WebSocket and receives
        transcription segments in real-time.

        Args:
            file: Audio file path or file-like object
            model: Model type - 'indus-stt-v1' or 'indus-stt-hi-en' (default: 'indus-stt-v1')
            streaming: Enable streaming (default: False)
            noise_cancellation: Enable noise suppression for non-streaming mode (default: False)
            language: Optional language code (e.g., 'hindi', 'english')
            on_segment: Optional callback function called for each transcription segment
            chunk_size: Size of audio chunks to send (default: 8192 bytes)

        Returns:
            STTResponse object containing transcription text, segments, and metrics
        """
        try:
            import websocket
        except ImportError:
            raise ImportError(
                "websocket-client is required for STT. "
                "Install it with: pip install websocket-client"
            )

        # --- UPDATED VALIDATION LOGIC ---
        if streaming and model == "indus-stt-v1":
            raise ValueError(
                "When 'streaming' is set to True, the 'model' cannot be 'indus-stt-v1'. "
                "Please use 'indus-stt-hi-en' for streaming transcription."
            )

        if model not in ["indus-stt-v1", "indus-stt-hi-en"]:
            raise ValueError("model must be 'indus-stt-v1' or 'indus-stt-hi-en'")
        # --- END UPDATED VALIDATION LOGIC ---

        if streaming and noise_cancellation:
            warnings.warn(
                "Noise cancellation is only supported in non-streaming mode right now.",
                UserWarning,
            )

        # Convert bool to required string "true" or "false"
        streaming_str = "true" if streaming else "false"
        noise_cancellation_str = "true" if noise_cancellation else "false"

        if isinstance(file, (str, Path)):
            with open(file, "rb") as f:
                audio_data = f.read()
        else:
            audio_data = file.read()

        pcm_data = self._convert_audio_to_pcm16(audio_data)

        ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = (
            f"{ws_url}/v1/audio/transcribe_ws?api_key={self.api_key}&model={model}"
            f"&streaming={streaming_str}&noise_cancellation={noise_cancellation_str}"
        )

        if language:
            ws_url += f"&language={language}"

        response = STTResponse()

        ws = websocket.WebSocket()
        try:
            ws.connect(ws_url)

            for i in range(0, len(pcm_data), chunk_size):
                chunk = pcm_data[i : i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)

            ws.send(b"__END__", opcode=websocket.ABNF.OPCODE_BINARY)

            while True:
                try:
                    message = ws.recv()
                    if not message:
                        break

                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "chunk_interim":
                        # Handle interim results (streaming mode)
                        pass

                    elif msg_type == "chunk_final":
                        segment = STTSegment(
                            text=data.get("text", ""), start=data.get("start"), end=data.get("end")
                        )
                        response.add_segment(segment.text, segment.start, segment.end)
                        if on_segment:
                            on_segment(segment)

                    elif msg_type == "final":
                        response.set_final(data.get("text", ""), data.get("request_id", ""))

                    elif msg_type == "metrics":
                        response.set_metrics(
                            buffer=data.get("buffer", 0),
                            transcription=data.get("transcription", 0),
                            total=data.get("total", 0),
                            rtf=data.get("RTF"),
                            request_id=data.get("request_id", ""),
                        )
                        response.complete()
                        break

                    elif msg_type == "error":
                        response.set_error(data.get("message", "Unknown error"))
                        break

                except Exception as e:
                    response.set_error(f"Error receiving message: {e}")
                    break

        except Exception as e:
            response.set_error(f"Connection error: {e}")
        finally:
            ws.close()

        return response

    async def transcribe_async(
        self,
        file: Union[str, Path, BinaryIO],
        model: str = "indus-stt-v1",
        streaming: bool = False,  # Changed to bool
        noise_cancellation: bool = False,
        language: Optional[str] = None,
        on_segment: Optional[Callable[[STTSegment], None]] = None,
        chunk_size: int = 8192,
    ) -> STTResponse:
        """
        Asynchronous speech-to-text transcription using WebSocket.

        This method streams audio to the server via WebSocket and receives
        transcription segments in real-time.

        Args:
            file: Audio file path or file-like object
            model: Model type - 'indus-stt-v1' or 'indus-stt-hi-en' (default: 'indus-stt-v1')
            streaming: Enable streaming (default: False)
            noise_cancellation: Enable noise suppression for non-streaming mode (default: False)
            language: Optional language code (e.g., 'hindi', 'english')
            on_segment: Optional callback function called for each transcription segment
            chunk_size: Size of audio chunks to send (default: 8192 bytes)

        Returns:
            STTResponse object containing transcription text, segments, and metrics
        """
        # --- UPDATED VALIDATION LOGIC ---
        if streaming and model == "indus-stt-v1":
            raise ValueError(
                "When 'streaming' is set to True, the 'model' cannot be 'indus-stt-v1'. "
                "Please use 'indus-stt-hi-en' for streaming transcription."
            )

        if model not in ["indus-stt-v1", "indus-stt-hi-en"]:
            raise ValueError("model must be 'indus-stt-v1' or 'indus-stt-hi-en'")
        # --- END UPDATED VALIDATION LOGIC ---

        if streaming and noise_cancellation:
            warnings.warn(
                "Noise cancellation is only supported in non-streaming mode right now.",
                UserWarning,
            )

        # Convert bool to required string "true" or "false"
        streaming_str = "true" if streaming else "false"
        noise_cancellation_str = "true" if noise_cancellation else "false"

        # Read audio file
        if isinstance(file, (str, Path)):
            with open(file, "rb") as f:
                audio_data = f.read()
        else:
            audio_data = file.read()

        # Convert to PCM16
        pcm_data = self._convert_audio_to_pcm16(audio_data)

        # Build WebSocket URL
        ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = (
            f"{ws_url}/v1/audio/transcribe_ws?api_key={self.api_key}&model={model}"
            f"&streaming={streaming_str}&noise_cancellation={noise_cancellation_str}"
        )

        if language:
            ws_url += f"&language={language}"

        response = STTResponse()

        if self._ws_session is None:
            self._ws_session = aiohttp.ClientSession()

        try:
            async with self._ws_session.ws_connect(ws_url) as ws:
                # Send audio in chunks
                for i in range(0, len(pcm_data), chunk_size):
                    chunk = pcm_data[i : i + chunk_size]
                    await ws.send_bytes(chunk)

                # Send END marker
                await ws.send_bytes(b"__END__")

                # Receive responses
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        msg_type = data.get("type")

                        if msg_type == "chunk_interim":
                            # Handle interim results (streaming mode)
                            pass

                        elif msg_type == "chunk_final":
                            segment = STTSegment(
                                text=data.get("text", ""),
                                start=data.get("start"),
                                end=data.get("end"),
                            )
                            response.add_segment(segment.text, segment.start, segment.end)
                            if on_segment:
                                if asyncio.iscoroutinefunction(on_segment):
                                    await on_segment(segment)
                                else:
                                    on_segment(segment)

                        elif msg_type == "final":
                            response.set_final(data.get("text", ""), data.get("request_id", ""))

                        elif msg_type == "metrics":
                            response.set_metrics(
                                buffer=data.get("buffer", 0),
                                transcription=data.get("transcription", 0),
                                total=data.get("total", 0),
                                rtf=data.get("RTF"),
                                request_id=data.get("request_id", ""),
                            )
                            response.complete()
                            break

                        elif msg_type == "error":
                            response.set_error(data.get("message", "Unknown error"))
                            break

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        response.set_error(f"WebSocket error: {ws.exception()}")
                        break

        except Exception as e:
            response.set_error(f"Connection error: {e}")

        return response

    async def close(self):
        """Close async sessions."""
        if self._ws_session:
            await self._ws_session.close()
            self._ws_session = None


class Client:
    """
    Main client for IndusLabs Voice API.

    Example:
        >>> from induslabs import Client
        >>> client = Client(api_key="your_api_key")
        >>>
        >>> # List available voices
        >>> voices_response = client.voices.list()
        >>> for voice in voices_response.voices:
        ...     print(f"{voice.name}: {voice.voice_id}")
        >>>
        >>> # Text-to-Speech
        >>> response = client.tts.speak(
        ...     text="Hello world",
        ...     voice="Indus-hi-Urvashi",
        ...     language="hi-IN"
        ... )
        >>> response.save("output.wav")
        >>>
        >>> # Speech-to-Text (WebSocket)
        >>> result = client.stt.transcribe("audio.wav")
        >>> print(result.text)
        >>>
        >>> # With segment callback
        >>> def on_segment(segment):
        ...     print(f"Segment: {segment.text}")
        >>> result = client.stt.transcribe("audio.wav", on_segment=on_segment)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://voice.induslabs.io",
        voices_base_url: str = "https://api.indusai.app",
    ):
        """
        Initialize IndusLabs client.

        Args:
            api_key: API key (can also be set via INDUSLABS_API_KEY env variable)
            base_url: Base URL for TTS/STT API (default: https://voice.induslabs.io)
            voices_base_url: Base URL for voices API (default: https://api.indusai.app)
        """
        self.api_key = api_key or os.environ.get("INDUSLABS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided either as argument or via "
                "INDUSLABS_API_KEY environment variable"
            )

        self.base_url = base_url.rstrip("/")
        self.voices_base_url = voices_base_url.rstrip("/")

        self.tts = TTS(self.api_key, self.base_url)
        self.stt = STT(self.api_key, self.base_url)
        self.voices = Voices(self.api_key, self.voices_base_url)

    async def close(self):
        """Close all async sessions."""
        await self.tts.close()
        await self.stt.close()
        await self.voices.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
