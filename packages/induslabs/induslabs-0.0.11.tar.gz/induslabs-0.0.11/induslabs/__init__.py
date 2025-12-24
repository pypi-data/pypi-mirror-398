"""IndusLabs Voice API SDK."""

from .client import (
    Client,
    TTS,
    STT,
    Voices,
    Voice,
    TTSResponse,
    TTSStreamResponse,
    AsyncTTSStreamResponse,
    STTResponse,
    STTSegment,
    STTMetrics,
    VoiceResponse,
)

__version__ = "0.0.11"
__all__ = [
    "Client",
    "TTS",
    "STT",
    "Voices",
    "Voice",
    "TTSResponse",
    "TTSStreamResponse",
    "AsyncTTSStreamResponse",
    "STTResponse",
    "STTSegment",
    "STTMetrics",
    "VoiceResponse",
]
