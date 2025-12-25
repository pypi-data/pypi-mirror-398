#!/usr/bin/env python
# config.py - Centralized configuration for Athena AI

import os
from dataclasses import dataclass, field
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


# Language extension mappings used across the codebase
LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".ipp": "cpp",  # C++ implementation file (inline/template implementations)
    ".c": "c",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
    ".kt": "kotlin",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".scala": "scala",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".h": "c header",
    ".hpp": "cpp header",
    ".hh": "cpp header",
    ".hxx": "cpp header",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".md": "markdown",
    ".txt": "text",
}


@dataclass
class LLMConfig:
    """Configuration for LLM providers and models."""

    # API Keys
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    xai_api_key: str = os.environ.get("XAI_API_KEY", "")
    odinai_api_key: str = os.environ.get("ODINAI_API_KEY", "")

    # OpenAI Model Map (max output tokens)
    openai_model_map: Dict[str, int] = field(default_factory=lambda: {
        "gpt-4o-mini": 16383,
        "gpt-4o": 4095,
        "gpt-4-turbo": 4095,
        "gpt-4": 8191,
        "gpt-4.1": 32768,
        "o3-mini": 100000,
        "o4": 200000,
        "gpt-5-nano": 128000,
    })

    # Anthropic Model Map (max output tokens)
    anthropic_model_map: Dict[str, int] = field(default_factory=lambda: {
        "claude-4-sonnet-20250514": 40000,
        "claude-3-5-sonnet-20241022": 8192,
        "claude-3-5-haiku-20241022": 8192,
        "claude-3-opus-20240229": 4096,
        "claude-3-sonnet-20240229": 4096,
        "claude-3-haiku-20240307": 4096,
    })

    # xAI Model Map (max output tokens)
    xai_model_map: Dict[str, int] = field(default_factory=lambda: {
        "grok-4": 256000,
        "grok-3": 131072,
        "grok-3-mini": 131072,
        "grok-2-vision": 32768,
    })

    # OdinAI Model Map (max output tokens)
    odinai_model_map: Dict[str, int] = field(default_factory=lambda: {
        "glm-4": 32768,
        "owen-coder": 131072,
    })

    # Default Models
    default_openai_model: str = "gpt-4.1"
    default_anthropic_model: str = "claude-4-sonnet-20250514"
    default_xai_model: str = "grok-4"
    default_odinai_model: str = "glm-4"

    # Default LLM Parameters
    default_temperature: float = 0.0
    default_max_tokens: int = 8000
    default_n_completions: int = 3  # Number of completions to generate

    # Token counting model (used in utils/tokens.py)
    token_counter_model: str = "gpt-4o"


@dataclass
class RetryConfig:
    """Configuration for retry and backoff logic."""

    # Rate limiting
    rate_limit_delay: float = 0.5  # Delay between API calls in seconds
    max_concurrent: int = 5  # Maximum concurrent operations

    # Retry parameters
    max_retries: int = 3  # Number of retry attempts
    initial_delay: float = 1.0  # Initial backoff delay in seconds
    exponential_backoff_multiplier: int = 2  # Multiplier for exponential backoff

    # Verification
    verification_score_threshold: int = 80  # Minimum acceptable verification score (0-100)


@dataclass
class TextProcessingConfig:
    """Configuration for text processing and chunking."""

    # Chunk sizes (characters/tokens)
    default_chunk_size: int = 1000  # General text splitting
    indexer_chunk_size: int = 200  # Embedding optimization (smaller for better granularity)

    # Chunk overlap
    default_chunk_overlap: int = 20  # Overlap between chunks in characters
    indexer_chunk_overlap: int = 0  # No overlap for embeddings

    # Token estimation
    avg_chars_per_token: int = 4  # Average characters per token ratio
    safety_margin: float = 0.9  # Use 90% of max tokens as safe limit

    # Max tokens per operation
    max_tokens_per_chunk: int = 2048  # Maximum tokens for indexing chunks
    large_file_token_limit: int = 32768  # Triggers chunked processing for large files


@dataclass
class RAGConfig:
    """Configuration for RAG (Retrieval-Augmented Generation)."""

    # Search parameters
    search_limit: int = 5  # Number of related files to retrieve
    search_multiplier: int = 10  # Fetch more results for filtering
    max_related_files: int = 5  # Maximum related files to include in context

    # Context parameters
    context_preview_length: int = 500  # Characters to show in context preview

    # Feature flags
    use_rag_context: bool = False  # Whether to use RAG context by default


@dataclass
class DocumentationConfig:
    """Configuration for documentation generation."""

    # Quality thresholds
    min_doc_length: int = 200  # Minimum documentation length in characters

    # Checkpoints
    checkpoint_interval: int = 5  # Files between checkpoint saves

    # Token limits for documentation generation
    initial_max_tokens: int = 2000  # Start with 2000 tokens
    max_tokens_limit: int = 4000  # Maximum tokens to try
    token_increment: int = 1000  # Increase by 1000 tokens when truncated


@dataclass
class FileProcessingConfig:
    """Configuration for file processing operations."""

    # Checkpoints
    checkpoint_interval: int = 10  # Files between checkpoint saves

    # Binary file detection
    binary_detection_sample_size: int = 8192  # Bytes to sample for binary detection

    # Preview sizes
    file_preview_length: int = 2000  # Characters to preview for dynamic chunk sizing

    # Language extensions
    language_extensions: Dict[str, str] = field(default_factory=lambda: LANGUAGE_EXTENSIONS.copy())


@dataclass
class HTTPConfig:
    """Configuration for HTTP requests and timeouts."""

    # Request timeouts (in seconds)
    default_timeout: int = 10  # Standard HTTP request timeout
    extended_timeout: int = 15  # Extended timeout for external APIs
    download_timeout: int = 300  # Shell command/download timeout (5 minutes)


@dataclass
class IndexerConfig:
    """Configuration for indexing and embeddings."""

    # Embedding model
    embedding_model: str = "text-embedding-3-large"

    # Storage
    gcp_index_bucket: str = os.environ.get("GCP_INDEX_BUCKET", "athenah-ai-indexes")

    # Token estimation model
    token_estimation_model: str = "gpt-3.5-turbo-16k"


@dataclass
class DirectoryConfig:
    """Configuration for directories and storage."""

    # Base directory (can be overridden)
    base_dir: Optional[str] = None

    # Default storage type
    default_storage_type: str = "local"  # "local" or "gcs"


@dataclass
class AthenaConfig:
    """Main configuration class for Athena AI."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    text_processing: TextProcessingConfig = field(default_factory=TextProcessingConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    documentation: DocumentationConfig = field(default_factory=DocumentationConfig)
    file_processing: FileProcessingConfig = field(default_factory=FileProcessingConfig)
    http: HTTPConfig = field(default_factory=HTTPConfig)
    indexer: IndexerConfig = field(default_factory=IndexerConfig)
    directory: DirectoryConfig = field(default_factory=DirectoryConfig)

    def __post_init__(self):
        """Apply environment variable overrides after initialization."""
        self._apply_env_overrides()

    def _apply_env_overrides(self):
        """
        Apply environment variable overrides using the pattern:
        ATHENA_<SECTION>_<PARAMETER>

        Examples:
            ATHENA_LLM_MAX_TOKENS=16000
            ATHENA_RETRY_RATE_LIMIT_DELAY=1.0
            ATHENA_RAG_SEARCH_LIMIT=10
        """
        prefix = "ATHENA_"

        for env_key, env_value in os.environ.items():
            if not env_key.startswith(prefix):
                continue

            # Parse the environment variable name
            parts = env_key[len(prefix):].lower().split("_", 1)
            if len(parts) != 2:
                continue

            section_name, param_name = parts

            # Get the appropriate config section
            section = None
            if section_name == "llm":
                section = self.llm
            elif section_name == "retry":
                section = self.retry
            elif section_name == "textprocessing":
                section = self.text_processing
                param_name = param_name.replace("_", "")  # Handle camelCase conversion
            elif section_name == "rag":
                section = self.rag
            elif section_name == "documentation":
                section = self.documentation
            elif section_name == "fileprocessing":
                section = self.file_processing
                param_name = param_name.replace("_", "")  # Handle camelCase conversion
            elif section_name == "http":
                section = self.http
            elif section_name == "indexer":
                section = self.indexer
            elif section_name == "directory":
                section = self.directory

            if section is None:
                continue

            # Check if the parameter exists in the section
            if not hasattr(section, param_name):
                continue

            # Get the current value to determine type
            current_value = getattr(section, param_name)

            # Convert the environment variable value to the appropriate type
            try:
                if isinstance(current_value, bool):
                    # Handle boolean conversion
                    converted_value = env_value.lower() in ("true", "1", "yes", "on")
                elif isinstance(current_value, int):
                    converted_value = int(env_value)
                elif isinstance(current_value, float):
                    converted_value = float(env_value)
                elif isinstance(current_value, str):
                    converted_value = env_value
                else:
                    # Skip complex types (dicts, etc.)
                    continue

                # Apply the override
                setattr(section, param_name, converted_value)
            except (ValueError, TypeError):
                # Skip invalid conversions
                continue


# Global configuration instance
config = AthenaConfig()


# Backward compatibility helper functions

def get_max_tokens(model_name: str) -> int:
    """
    Get the maximum number of output tokens for a given model.

    Args:
        model_name (str): The name of the model.

    Returns:
        int: The maximum number of tokens for the model.
    """
    # Check OpenAI models first
    if model_name in config.llm.openai_model_map:
        return config.llm.openai_model_map[model_name]
    # Check Anthropic models
    elif model_name in config.llm.anthropic_model_map:
        return config.llm.anthropic_model_map[model_name]
    # Check xAI models
    elif model_name in config.llm.xai_model_map:
        return config.llm.xai_model_map[model_name]
    # Check OdinAI models
    elif model_name in config.llm.odinai_model_map:
        return config.llm.odinai_model_map[model_name]
    else:
        return 4096  # Default fallback
