"""
FlowTTS - OpenAI-style TTS SDK for Tencent Cloud.

A lightweight, elegant Text-to-Speech SDK that wraps Tencent Cloud's
TRTC TTS API with an OpenAI-compatible interface.

Example:
    >>> from flow_tts import FlowTTS
    >>> client = FlowTTS({
    ...     "secret_id": "your-secret-id",
    ...     "secret_key": "your-secret-key",
    ...     "sdk_app_id": 1234567890
    ... })
    >>> response = client.synthesize({"text": "Hello, world!"})
    >>> with open("output.wav", "wb") as f:
    ...     f.write(response["audio"])
"""

__version__ = "0.1.0"

from .client import FlowTTS
from .types import (
    AudioFormat,
    FlowTTSConfig,
    Language,
    StreamChunk,
    SynthesizeOptions,
    SynthesizeResponse,
    TTSError,
    Voice,
    VoiceLibrary,
)
from .utils import detect_language, voice_resolver

__all__ = [
    "FlowTTS",
    "AudioFormat",
    "FlowTTSConfig",
    "Language",
    "StreamChunk",
    "SynthesizeOptions",
    "SynthesizeResponse",
    "TTSError",
    "Voice",
    "VoiceLibrary",
    "detect_language",
    "voice_resolver",
]
