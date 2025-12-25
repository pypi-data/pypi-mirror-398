"""FlowTTS Client - OpenAI-compatible TTS client for Tencent Cloud."""

import base64
import json
from typing import Iterator, List, Optional

from .core import generate_headers, make_request, make_stream_request
from .types import (
    AudioFormat,
    FlowTTSConfig,
    StreamChunk,
    SynthesizeOptions,
    SynthesizeResponse,
    TTSError,
    Voice,
    VoiceLibrary,
)
from .utils import detect_language, voice_resolver


class FlowTTS:
    """
    FlowTTS Client - OpenAI-compatible TTS SDK for Tencent Cloud.

    Example:
        >>> client = FlowTTS({
        ...     "secret_id": "your-secret-id",
        ...     "secret_key": "your-secret-key",
        ...     "sdk_app_id": 1234567890
        ... })
        >>> response = client.synthesize({"text": "你好，世界"})
        >>> with open("output.wav", "wb") as f:
        ...     f.write(response["audio"])
    """

    def __init__(self, config: FlowTTSConfig) -> None:
        """
        Initialize FlowTTS client.

        Args:
            config: Client configuration

        Raises:
            ValueError: If configuration is invalid
        """
        if not config.get("secret_id"):
            raise ValueError("secret_id is required")
        if not config.get("secret_key"):
            raise ValueError("secret_key is required")
        if not config.get("sdk_app_id"):
            raise ValueError("sdk_app_id is required")

        sdk_app_id = config.get("sdk_app_id", 0)
        if sdk_app_id <= 0:
            raise ValueError("Invalid sdk_app_id")

        self._secret_id = config["secret_id"]
        self._secret_key = config["secret_key"]
        self._sdk_app_id = sdk_app_id
        self._region = config.get("region", "ap-beijing")

        # OpenAI-compatible API
        self.audio = AudioAPI(self)

    def synthesize(self, options: SynthesizeOptions) -> SynthesizeResponse:
        """
        Synthesize text to speech.

        Args:
            options: Synthesis options

        Returns:
            Synthesis response with audio data

        Raises:
            TTSError: If synthesis fails
        """
        text = options.get("text", "")
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Validate parameters
        speed = options.get("speed", 1.0)
        volume = options.get("volume", 1.0)
        pitch = options.get("pitch", 0)

        if not (0.5 <= speed <= 2.0):
            raise ValueError("Speed must be between 0.5 and 2.0")
        if not (0.5 <= volume <= 2.0):
            raise ValueError("Volume must be between 0.5 and 2.0")
        if not (-12 <= pitch <= 12):
            raise ValueError("Pitch must be between -12 and 12 semitones")

        # Detect language if not provided
        language = options.get("language")
        auto_detected = False
        if not language:
            language = detect_language(text)
            auto_detected = True

        # Get voice ID
        voice_id = options.get("voice")
        if not voice_id:
            # Use fallback voice
            fallback = voice_resolver.get_fallback_voice()
            voice_id = fallback["id"]

        # Get model for voice
        model = voice_resolver.get_model_for_voice(voice_id)

        # Get audio format
        audio_format = options.get("format", "wav")

        # Build request payload (must match Tencent API structure)
        payload_dict = {
            "SdkAppId": self._sdk_app_id,
            "Text": text,
            "Model": model,
            "Voice": {
                "VoiceId": voice_id,
                "Speed": speed,
                "Volume": volume,
                "Pitch": pitch,
            },
            "AudioFormat": {
                "Format": audio_format,
                "SampleRate": 24000,
            },
        }

        payload = json.dumps(payload_dict)

        # Generate headers
        headers = generate_headers(
            self._secret_id,
            self._secret_key,
            payload,
            stream=False,
        )

        # Make request
        response = make_request(headers, payload)

        # Extract audio data
        response_data = response.get("Response", {})
        audio_base64 = response_data.get("Audio", "")

        if not audio_base64:
            raise TTSError(
                message="No audio data in response",
                request_id=response_data.get("RequestId"),
            )

        audio_bytes = base64.b64decode(audio_base64)

        return SynthesizeResponse(
            audio=audio_bytes,
            format=audio_format,
            detected_language=language if auto_detected else None,
            auto_detected=auto_detected,
            request_id=response_data.get("RequestId", ""),
        )

    def synthesize_stream(
        self, options: SynthesizeOptions
    ) -> Iterator[StreamChunk]:
        """
        Synthesize text to speech with streaming.

        Args:
            options: Synthesis options

        Yields:
            Stream chunks with audio data

        Raises:
            TTSError: If synthesis fails
        """
        text = options.get("text", "")
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Validate parameters
        speed = options.get("speed", 1.0)
        volume = options.get("volume", 1.0)

        if not (0.5 <= speed <= 2.0):
            raise ValueError("Speed must be between 0.5 and 2.0")
        if not (0.5 <= volume <= 2.0):
            raise ValueError("Volume must be between 0.5 and 2.0")

        # Detect language if not provided
        language = options.get("language")
        if not language:
            language = detect_language(text)

        # Get voice ID
        voice_id = options.get("voice")
        if not voice_id:
            fallback = voice_resolver.get_fallback_voice()
            voice_id = fallback["id"]

        # Get model for voice
        model = voice_resolver.get_model_for_voice(voice_id)

        # Build request payload (streaming format is PCM)
        payload_dict = {
            "SdkAppId": self._sdk_app_id,
            "Text": text,
            "Model": model,
            "Voice": {
                "VoiceId": voice_id,
                "Speed": speed,
                "Volume": volume,
            },
            "AudioFormat": {
                "Format": "pcm",
                "SampleRate": 24000,
            },
        }

        payload = json.dumps(payload_dict)

        # Generate headers
        headers = generate_headers(
            self._secret_id,
            self._secret_key,
            payload,
            stream=True,
        )

        # Collect chunks
        chunks: List[StreamChunk] = []

        def on_chunk(chunk_data: dict) -> None:
            chunk_type = chunk_data.get("Type")

            if chunk_type == "audio":
                audio_b64 = chunk_data.get("Audio")
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    chunks.append(
                        StreamChunk(
                            type="audio",
                            data=audio_bytes,
                            sequence=len(chunks),
                        )
                    )

            # Check for end of stream (either Type=="end" or IsEnd==True)
            if chunk_type == "end" or chunk_data.get("IsEnd"):
                chunks.append(
                    StreamChunk(
                        type="end",
                        total_chunks=len(chunks),
                        request_id=chunk_data.get("RequestId"),
                    )
                )

        # Make streaming request
        make_stream_request(headers, payload, on_chunk)

        # Yield all collected chunks
        for chunk in chunks:
            yield chunk

    # Voice management methods
    def get_voices(self, include_extended: bool = True) -> VoiceLibrary:
        """
        Get all available voices.

        Args:
            include_extended: Whether to include extended voices

        Returns:
            Voice library
        """
        return voice_resolver.get_voices(include_extended)

    def search_voices(self, query: str) -> List[Voice]:
        """
        Search voices by name, description, or language.

        Args:
            query: Search query

        Returns:
            List of matching voices
        """
        return voice_resolver.search_voices(query)

    def get_voice(self, voice_id: str) -> Optional[Voice]:
        """
        Get voice metadata by ID.

        Args:
            voice_id: Voice ID

        Returns:
            Voice metadata or None if not found
        """
        return voice_resolver.get_voice(voice_id)


class AudioAPI:
    """OpenAI-compatible audio API."""

    def __init__(self, client: FlowTTS) -> None:
        """Initialize audio API."""
        self._client = client
        self.speech = SpeechAPI(client)


class SpeechAPI:
    """OpenAI-compatible speech API."""

    def __init__(self, client: FlowTTS) -> None:
        """Initialize speech API."""
        self._client = client

    def create(self, options: SynthesizeOptions) -> SynthesizeResponse:
        """
        Create speech from text (OpenAI-compatible).

        Args:
            options: Synthesis options

        Returns:
            Synthesis response
        """
        return self._client.synthesize(options)
