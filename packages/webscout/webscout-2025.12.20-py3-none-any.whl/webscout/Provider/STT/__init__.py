# This file marks the directory as a Python package.
# Static imports for all STT (Speech-to-Text) provider modules

# Base classes
from webscout.Provider.STT.base import (
    STTCompatibleProvider,
    BaseSTTTranscriptions,
    BaseSTTAudio,
    BaseSTTChat,
    TranscriptionResponse,
    STTModels,
)

# Provider implementations
from webscout.Provider.STT.elevenlabs import ElevenLabsSTT

# List of all exported names
__all__ = [
    # Base classes
    "STTCompatibleProvider",
    "BaseSTTTranscriptions",
    "BaseSTTAudio",
    "BaseSTTChat",
    "TranscriptionResponse",
    "STTModels",
    # Providers
    "ElevenLabsSTT",
]
