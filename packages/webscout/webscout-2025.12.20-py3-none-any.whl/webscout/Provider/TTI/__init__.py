# This file marks the directory as a Python package.
# Static imports for all TTI (Text-to-Image) provider modules

# Base classes
from webscout.Provider.TTI.base import (
    TTICompatibleProvider,
    BaseImages,
)

# Utility classes
from webscout.Provider.TTI.utils import (
    ImageData,
    ImageResponse,
)

# Provider implementations
from webscout.Provider.TTI.claudeonline import ClaudeOnlineTTI
from webscout.Provider.TTI.magicstudio import MagicStudioAI
from webscout.Provider.TTI.pollinations import PollinationsAI
from webscout.Provider.TTI.together import TogetherImage
from webscout.Provider.TTI.venice import VeniceAI
from webscout.Provider.TTI.miragic import MiragicAI

# List of all exported names
__all__ = [
    # Base classes
    "TTICompatibleProvider",
    "BaseImages",
    # Utilities
    "ImageData",
    "ImageResponse",
    # Providers
    "ClaudeOnlineTTI",
    "MagicStudioAI",
    "PollinationsAI",
    "TogetherImage",
    "VeniceAI",
    "MiragicAI",

]