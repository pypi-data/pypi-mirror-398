"""Models package."""

from .agents import (
    AgentsConfig,
    AgentsConfigSection,
    AgentsDocument,
    AgentsGenerationConfig,
    BuildTestInstructions,
    CodingStandards,
    LLMConfig,
    LLMSetup,
    PRGuidelines,
    ProjectOverview,
    SetupInstructions,
)
from .api import APIInfo, APIParameter
from .base import DocgenBaseModel
from .cache import CacheEntry, CacheMetadata
from .config import (
    CacheConfig,
    DebugConfig,
    DocgenConfig,
    ExcludeConfig,
    GenerationConfig,
    LanguagesConfig,
    OutputConfig,
)
from .detected_language import DetectedLanguage
from .detector import LanguageConfig, PackageManagerRule
from .llm import LLMClientConfig
from .project import ProjectInfo
from .readme import Dependencies, ReadmeConfig, ReadmeDocument, ReadmeSetupInstructions

__all__ = [
    # Base
    "DocgenBaseModel",
    # Agents
    "ProjectOverview",
    "LLMSetup",
    "SetupInstructions",
    "BuildTestInstructions",
    "CodingStandards",
    "PRGuidelines",
    "AgentsConfig",
    "AgentsDocument",
    "AgentsConfigSection",
    "AgentsGenerationConfig",
    "LLMConfig",
    # Readme
    "Dependencies",
    "ReadmeSetupInstructions",
    "ReadmeConfig",
    "ReadmeDocument",
    # Config
    "LanguagesConfig",
    "OutputConfig",
    "GenerationConfig",
    "ExcludeConfig",
    "CacheConfig",
    "DebugConfig",
    "DocgenConfig",
    # API
    "APIParameter",
    "APIInfo",
    # LLM
    "LLMClientConfig",
    # Cache
    "CacheEntry",
    "CacheMetadata",
    # Project
    "ProjectInfo",
    # Detector
    "LanguageConfig",
    "PackageManagerRule",
    "DetectedLanguage",
]
