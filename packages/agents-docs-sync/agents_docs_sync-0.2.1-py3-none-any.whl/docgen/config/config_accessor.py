"""
Configuration Accessor Module

Type-safe configuration accessor for docgen.
"""

from typing import Any


class ConfigKeys:
    """Configuration key constants to avoid hardcoding."""

    GENERATION = "generation"
    LLM = "llm"
    OUTPUT = "output"
    RAG = "rag"
    CACHE = "cache"
    DEBUG = "debug"
    AGENTS = "agents"
    ARCHITECTURE = "architecture"
    EXCLUDE = "exclude"
    HOOKS = "hooks"
    LANGUAGES = "languages"


class ConfigAccessor:
    """
    Type-safe configuration accessor.
    Wraps the raw configuration dictionary and provides typed properties.
    """

    def __init__(self, config: dict[str, Any]):
        self._config = config

    @property
    def raw_config(self) -> dict[str, Any]:
        """Get raw configuration dictionary"""
        return self._config

    # ─────────────────────────────────────────────────────────────────
    # Generation Settings
    # ─────────────────────────────────────────────────────────────────
    @property
    def generation(self) -> dict[str, Any]:
        return self._config.get(ConfigKeys.GENERATION, {})

    @property
    def generate_api_doc(self) -> bool:
        return self.generation.get("generate_api_doc", True)

    @property
    def update_readme(self) -> bool:
        return self.generation.get("update_readme", True)

    @property
    def generate_agents_doc(self) -> bool:
        return self.generation.get("generate_agents_doc", True)

    @property
    def preserve_manual_sections(self) -> bool:
        return self.generation.get("preserve_manual_sections", True)

    # ─────────────────────────────────────────────────────────────────
    # LLM Settings
    # ─────────────────────────────────────────────────────────────────
    @property
    def llm(self) -> dict[str, Any]:
        return self._config.get(ConfigKeys.LLM, {})

    @property
    def llm_provider(self) -> str:
        return self.llm.get("provider", "openai")

    @property
    def llm_model(self) -> str:
        return self.llm.get("model", "gpt-4")

    @property
    def llm_temperature(self) -> float:
        return self.llm.get("temperature", 0.0)

    # ─────────────────────────────────────────────────────────────────
    # Output Settings
    # ─────────────────────────────────────────────────────────────────
    @property
    def output(self) -> dict[str, Any]:
        return self._config.get(ConfigKeys.OUTPUT, {})

    @property
    def output_dir(self) -> str:
        return self.output.get("dir", "docs")

    @property
    def api_doc_dir(self) -> str:
        return self.output.get("api_doc_dir", "api")

    @property
    def readme_path(self) -> str:
        return self.output.get("readme", "README.md")

    @property
    def agents_doc_path(self) -> str:
        return self.output.get("agents_doc", "AGENTS.md")

    # ─────────────────────────────────────────────────────────────────
    # RAG Settings
    # ─────────────────────────────────────────────────────────────────
    @property
    def rag(self) -> dict[str, Any]:
        return self._config.get(ConfigKeys.RAG, {})

    @property
    def rag_enabled(self) -> bool:
        return self.rag.get("enabled", False)

    @property
    def rag_auto_build_index(self) -> bool:
        return self.rag.get("auto_build_index", False)

    @property
    def rag_embedding(self) -> dict[str, Any]:
        return self.rag.get("embedding", {})

    @property
    def rag_retrieval(self) -> dict[str, Any]:
        return self.rag.get("retrieval", {})

    # ─────────────────────────────────────────────────────────────────
    # Cache Settings
    # ─────────────────────────────────────────────────────────────────
    @property
    def cache(self) -> dict[str, Any]:
        return self._config.get(ConfigKeys.CACHE, {})

    @property
    def cache_enabled(self) -> bool:
        return self.cache.get("enabled", True)

    # ─────────────────────────────────────────────────────────────────
    # Debug Settings
    # ─────────────────────────────────────────────────────────────────
    @property
    def debug(self) -> dict[str, Any]:
        return self._config.get(ConfigKeys.DEBUG, {})

    @property
    def debug_enabled(self) -> bool:
        return self.debug.get("enabled", False)

    # ─────────────────────────────────────────────────────────────────
    # Agents Settings
    # ─────────────────────────────────────────────────────────────────
    @property
    def agents(self) -> dict[str, Any]:
        return self._config.get(ConfigKeys.AGENTS, {})

    @property
    def agents_llm_mode(self) -> str:
        return self.agents.get("llm_mode", "api")

    @property
    def agents_generation(self) -> dict[str, Any]:
        return self.agents.get("generation", {})

    # ─────────────────────────────────────────────────────────────────
    # Architecture Settings
    # ─────────────────────────────────────────────────────────────────
    @property
    def architecture(self) -> dict[str, Any]:
        return self._config.get(ConfigKeys.ARCHITECTURE, {})

    @property
    def architecture_enabled(self) -> bool:
        return self.architecture.get("enabled", False)

    @property
    def architecture_output_dir(self) -> str:
        return self.architecture.get("output_dir", "docs/architecture")

    @property
    def architecture_generator(self) -> str:
        return self.architecture.get("generator", "mermaid")

    # ─────────────────────────────────────────────────────────────────
    # Exclude Settings
    # ─────────────────────────────────────────────────────────────────
    @property
    def exclude(self) -> dict[str, Any]:
        return self._config.get(ConfigKeys.EXCLUDE, {})

    @property
    def exclude_directories(self) -> list[str]:
        return self.exclude.get("directories", [])

    @property
    def exclude_patterns(self) -> list[str]:
        return self.exclude.get("patterns", [])

    @property
    def use_gitignore(self) -> bool:
        """`.gitignore`を適用するかどうか"""
        return self.exclude.get("use_gitignore", True)

    # ─────────────────────────────────────────────────────────────────
    # Hooks Settings
    # ─────────────────────────────────────────────────────────────────
    @property
    def hooks(self) -> dict[str, Any]:
        return self._config.get(ConfigKeys.HOOKS, {})

    @property
    def hooks_enabled(self) -> bool:
        return self.hooks.get("enabled", True)

    # ─────────────────────────────────────────────────────────────────
    # Languages Settings
    # ─────────────────────────────────────────────────────────────────
    @property
    def languages(self) -> dict[str, Any]:
        return self._config.get(ConfigKeys.LANGUAGES, {})

    @property
    def languages_auto_detect(self) -> bool:
        return self.languages.get("auto_detect", True)

    @property
    def languages_preferred(self) -> list[str]:
        return self.languages.get("preferred", [])

    @property
    def languages_ignored(self) -> list[str]:
        return self.languages.get("ignored", [])
