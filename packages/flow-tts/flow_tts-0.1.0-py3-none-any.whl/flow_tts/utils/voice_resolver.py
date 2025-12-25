"""Voice library resolver."""

import json
import os
from typing import Dict, List, Optional

from ..types import Voice, VoiceLibrary


class VoiceResolver:
    """Voice library resolver with O(1) lookups."""

    def __init__(self) -> None:
        """Initialize voice resolver."""
        self._turbo_voices: List[Voice] = []
        self._ex_voices: List[Voice] = []
        self._turbo_voice_map: Dict[str, Voice] = {}
        self._ex_voice_map: Dict[str, Voice] = {}
        self._initialized = False

    def _init(self) -> None:
        """Initialize voice library (lazy loading)."""
        if self._initialized:
            return

        try:
            # Find data directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(current_dir), "data")

            # Load Turbo voices
            turbo_path = os.path.join(data_dir, "voices-flow_01_turbo.json")
            with open(turbo_path, "r", encoding="utf-8") as f:
                turbo_data = json.load(f)
                self._turbo_voices = turbo_data["voices"]
                self._turbo_voice_map = {v["id"]: v for v in self._turbo_voices}

            # Load Ex voices
            ex_path = os.path.join(data_dir, "voices-flow_01_ex.json")
            with open(ex_path, "r", encoding="utf-8") as f:
                ex_data = json.load(f)
                self._ex_voices = ex_data["voices"]
                self._ex_voice_map = {v["id"]: v for v in self._ex_voices}

            self._initialized = True
        except Exception as e:
            raise RuntimeError(
                f"Failed to load voice library: {e}. "
                f"Expected location: {data_dir}"
            )

    def get_model_for_voice(self, voice_id: str) -> str:
        """
        Get model name for a voice ID (O(1) lookup).

        Args:
            voice_id: Voice ID to look up

        Returns:
            Model name ('flow_01_turbo' or 'flow_01_ex')

        Raises:
            ValueError: If voice ID is not found
        """
        self._init()

        if voice_id in self._turbo_voice_map:
            return "flow_01_turbo"
        if voice_id in self._ex_voice_map:
            return "flow_01_ex"

        raise ValueError(
            f"Unknown voice ID: {voice_id}. "
            "Use get_voices() to see available voices."
        )

    def get_voice(self, voice_id: str) -> Optional[Voice]:
        """
        Get voice metadata by ID.

        Args:
            voice_id: Voice ID to look up

        Returns:
            Voice metadata or None if not found
        """
        self._init()
        return self._turbo_voice_map.get(voice_id) or self._ex_voice_map.get(voice_id)

    def get_voices(self, include_extended: bool = True) -> VoiceLibrary:
        """
        Get all available voices.

        Args:
            include_extended: Whether to include extended voices

        Returns:
            Voice library with preset voices
        """
        self._init()
        preset = self._turbo_voices.copy()
        if include_extended:
            preset.extend(self._ex_voices)
        return {"preset": preset}

    def search_voices(self, query: str) -> List[Voice]:
        """
        Search voices by name, description, or language.

        Args:
            query: Search query

        Returns:
            List of matching voices
        """
        self._init()
        query_lower = query.lower()
        all_voices = self._turbo_voices + self._ex_voices

        results = []
        for voice in all_voices:
            if (
                query_lower in voice.get("name", "").lower()
                or query_lower in voice.get("description", "").lower()
                or query_lower in voice.get("language", "").lower()
            ):
                results.append(voice)

        return results

    def get_fallback_voice(self) -> Voice:
        """
        Get fallback voice.

        Returns:
            Default voice for fallback
        """
        self._init()
        return self._turbo_voices[0]


# Singleton instance
voice_resolver = VoiceResolver()
