"""Type definitions for FlowTTS."""

from typing import Any, Dict, List, Literal, Optional, TypedDict

# Audio format types
AudioFormat = Literal["wav", "pcm"]

# Language codes
Language = Literal["zh", "en", "ja", "ko"]


class FlowTTSConfig(TypedDict, total=False):
    """Configuration for FlowTTS client."""

    secret_id: str
    secret_key: str
    sdk_app_id: int
    region: Optional[str]


class SynthesizeOptions(TypedDict, total=False):
    """Options for text synthesis."""

    text: str
    voice: Optional[str]
    language: Optional[str]
    format: Optional[AudioFormat]
    speed: Optional[float]
    volume: Optional[float]
    pitch: Optional[int]


class SynthesizeResponse(TypedDict):
    """Response from synthesis."""

    audio: bytes
    format: AudioFormat
    detected_language: Optional[str]
    auto_detected: Optional[bool]
    request_id: str


class Voice(TypedDict, total=False):
    """Voice metadata."""

    id: str
    name: str
    name_en: Optional[str]
    language: str
    description: Optional[str]
    sample_text: Optional[str]
    preview_url: Optional[str]
    gender: Optional[str]
    tone: Optional[str]
    style: Optional[str]
    scenarios: Optional[str]


class VoiceLibrary(TypedDict):
    """Voice library structure."""

    preset: List[Voice]


class StreamChunk(TypedDict, total=False):
    """Stream chunk data."""

    type: str
    data: Optional[bytes]
    sequence: Optional[int]
    total_chunks: Optional[int]
    request_id: Optional[str]


class TTSError(Exception):
    """TTS API error."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Initialize error."""
        super().__init__(message)
        self.code = code
        self.request_id = request_id
