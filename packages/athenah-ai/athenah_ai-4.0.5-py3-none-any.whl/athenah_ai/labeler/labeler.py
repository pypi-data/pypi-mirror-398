import os
import logging
import time
from typing import Dict, Any, List, Optional, Callable

from athenah_ai.client import AthenahClient
from athenah_ai.client.llm_adapters import LLMProvider
from athenah_ai.config import config

from basedir import basedir

# Import refactored modules
from athenah_ai.labeler.models import ProcessingProgress
from athenah_ai.labeler.documenter import DocumentationGenerator
from athenah_ai.labeler.processor import FileProcessor

logger = logging.getLogger("app")


class AICodeLabeler:
    """
    AI Code Labeler - Orchestrates file processing and documentation generation.

    This is the main entry point for the labeling system. It delegates actual
    processing to specialized components (DocumentationGenerator and FileProcessor).
    """

    language_extensions = {
        ".py": "python",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".ipp": "cpp",  # C++ implementation file (inline/template implementations)
        ".c": "c",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".h": "c header",
        ".hpp": "cpp header",
        ".hh": "cpp header",
        # Add more as needed
    }

    def __init__(
        self,
        storage_type: str,
        id: str,
        dir: str,
        name: str,
        version: str,
        progress_callback: Optional[Callable[[ProcessingProgress], None]] = None,
        rate_limit_delay: float = None,
        max_concurrent: int = None,
        checkpoint_interval: int = None,
        indexer=None,
        use_rag_context: bool = None
    ):
        """
        Initialize AICodeLabeler.

        Args:
            storage_type: Storage type for data
            id: Unique identifier
            dir: Base directory
            name: Project name
            version: Version string
            progress_callback: Optional callback for progress updates
            rate_limit_delay: Delay between API calls in seconds
            max_concurrent: Maximum concurrent operations
            checkpoint_interval: Number of files between checkpoint saves
            indexer: Optional indexer for RAG context (BaseIndexClient)
            use_rag_context: Whether to use RAG context when labeling
        """
        self.storage_type = storage_type
        self.id = id
        self.dir = dir
        self.name = name
        self.version = version
        self.base_path = os.path.join(basedir, dir)
        self.name_path = os.path.join(self.base_path, name)
        self.source_path = os.path.join(self.name_path, f"{name}-source")
        self.client = AthenahClient(self.id, LLMProvider.OPENAI, self.dir)

        # Production features
        self.progress_callback = progress_callback
        self.rate_limit_delay = rate_limit_delay if rate_limit_delay is not None else config.retry.rate_limit_delay
        self.max_concurrent = max_concurrent if max_concurrent is not None else config.retry.max_concurrent
        self.checkpoint_interval = checkpoint_interval if checkpoint_interval is not None else config.file_processing.checkpoint_interval
        self.checkpoint_path = os.path.join(self.name_path, ".labeler_checkpoint.json")
        self.indexer = indexer
        self.use_rag_context = use_rag_context if use_rag_context is not None else config.rag.use_rag_context

        # Rate limiting
        self.last_api_call = 0.0

        # Initialize sub-components
        self.documenter = DocumentationGenerator(
            client=self.client,
            language_extensions=self.language_extensions,
            source_path=self.source_path,
            retry_with_backoff=self._retry_with_backoff
        )

        self.processor = FileProcessor(
            client=self.client,
            language_extensions=self.language_extensions,
            source_path=self.source_path,
            checkpoint_path=self.checkpoint_path,
            checkpoint_interval=self.checkpoint_interval,
            retry_with_backoff=self._retry_with_backoff,
            report_progress=self._report_progress,
            indexer=indexer,
            use_rag_context=use_rag_context
        )

    # ========== Helper Methods ==========

    def _report_progress(self, progress: ProcessingProgress) -> None:
        """Report progress via callback if configured"""
        if self.progress_callback:
            try:
                self.progress_callback(progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    def _rate_limit(self) -> None:
        """Enforce rate limiting between API calls"""
        if self.rate_limit_delay > 0:
            elapsed = time.time() - self.last_api_call
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self.last_api_call = time.time()

    def _retry_with_backoff(
        self, func: Callable, max_retries: int = None, initial_delay: float = None
    ) -> Any:
        """Retry a function with exponential backoff"""
        max_retries = max_retries if max_retries is not None else config.retry.max_retries
        initial_delay = initial_delay if initial_delay is not None else config.retry.initial_delay
        delay = initial_delay
        last_exception = None

        for attempt in range(max_retries):
            try:
                self._rate_limit()
                return func()
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= config.retry.exponential_backoff_multiplier  # Exponential backoff

        logger.error(f"All {max_retries} attempts failed")
        raise last_exception

    # ========== File Processing API (delegates to FileProcessor) ==========

    def process_files(
        self,
        file_paths: List[str],
        max_retries: int = 3,
        use_checkpoint: bool = True,
        generate_documentation: bool = False
    ) -> Dict[str, List[str]]:
        """
        Process a specific list of file paths (e.g., changed files from a git diff).
        Includes progress callbacks, checkpoint support, and handles large files via chunking.

        Args:
            file_paths: List of relative or absolute file paths to process
            max_retries: Number of times to retry processing if verification fails
            use_checkpoint: Whether to use checkpoint for resumable processing
            generate_documentation: Whether to generate .ai.md documentation after labeling

        Returns:
            Dict with 'processed', 'failed', 'skipped' file lists, and optionally 'documentation' results
        """
        # Process files using FileProcessor
        result = self.processor.process_files(
            file_paths=file_paths,
            max_retries=max_retries,
            use_checkpoint=use_checkpoint,
            generate_documentation=False  # We'll handle doc generation separately
        )

        # Generate documentation if requested
        if generate_documentation and result.get('processed'):
            logger.info(f"Generating documentation for {len(result['processed'])} processed files...")
            doc_results = self.documenter.generate_file_documentation(
                file_paths=result['processed'],
                use_ai_json=True,
                force_regenerate=False,
                max_retries=max_retries
            )
            result['documentation'] = doc_results

        return result

    def process_directories(
        self,
        directories: List[str],
        max_retries: int = 3,
        generate_summaries: bool = True,
        skip_complete: bool = True,
        process_stale: bool = True,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Process all files in the specified directories and optionally generate directory summaries.
        Intelligently skips already-complete directories unless forced.

        Args:
            directories: List of directory paths to process
            max_retries: Number of times to retry processing if verification fails
            generate_summaries: Whether to generate directory.ai.json files after processing
            skip_complete: Skip directories where all files are already labeled
            process_stale: Process files where source is newer than .ai.json
            force: Force reprocessing even if directory is complete

        Returns:
            Dict with processing results and summary generation results
        """
        return self.processor.process_directories(
            directories=directories,
            max_retries=max_retries,
            generate_summaries=generate_summaries,
            skip_complete=skip_complete,
            process_stale=process_stale,
            force=force
        )

    def check_directory_status(self, directory: str) -> Dict[str, Any]:
        """
        Check the processing status of a directory.

        Args:
            directory: Directory path to check

        Returns:
            Dict with status information
        """
        return self.processor.check_directory_status(directory)

    def get_files_needing_processing(
        self, directories: List[str], include_stale: bool = True
    ) -> Dict[str, List[str]]:
        """
        Get lists of files that need processing across multiple directories.

        Args:
            directories: List of directory paths to check
            include_stale: Include files where source is newer than .ai.json

        Returns:
            Dict with 'unlabeled' and 'stale' file lists
        """
        return self.processor.get_files_needing_processing(directories, include_stale)

    def remove_labels(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Remove .ai.json files for deleted source files.

        Args:
            file_paths: List of deleted file paths

        Returns:
            Dict with 'removed' and 'not_found' lists
        """
        return self.processor.remove_labels(file_paths)

    def clear_directory_labels(
        self, directories: List[str], include_directory_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Remove all .ai.json files from specified directories.

        Args:
            directories: List of directory paths to clear
            include_directory_summary: Whether to also remove directory.ai.json files

        Returns:
            Dict with 'cleared' count per directory and 'failed' list
        """
        return self.processor.clear_directory_labels(directories, include_directory_summary)

    def generate_directory_summaries(
        self, directories: List[str]
    ) -> Dict[str, List[str]]:
        """
        Generate directory.ai.json files that summarize the functionality
        of each directory based on the .ai.json files within it.

        Args:
            directories: List of directory paths to summarize

        Returns:
            Dict with 'generated' and 'failed' lists
        """
        return self.processor.generate_directory_summaries(directories)

    # ========== Documentation Generation API (delegates to DocumentationGenerator) ==========

    def generate_file_documentation(
        self,
        file_paths: List[str],
        use_ai_json: bool = True,
        force_regenerate: bool = False,
        max_retries: int = 3
    ) -> Dict[str, List[str]]:
        """
        Generate .ai.md documentation for individual files.

        Args:
            file_paths: List of source file paths to document
            use_ai_json: If True, use existing .ai.json as input (faster, cheaper)
            force_regenerate: Regenerate even if .ai.md exists and is fresh
            max_retries: Number of retries for failed generations

        Returns:
            Dict with 'generated', 'failed', and 'skipped' lists
        """
        return self.documenter.generate_file_documentation(
            file_paths=file_paths,
            use_ai_json=use_ai_json,
            force_regenerate=force_regenerate,
            max_retries=max_retries
        )

    def generate_directory_documentation(
        self,
        directories: List[str],
        force_regenerate: bool = False
    ) -> Dict[str, List[str]]:
        """
        Generate directory.ai.md overview files for directories.

        Args:
            directories: List of directory paths to document
            force_regenerate: Regenerate even if directory.ai.md exists and is fresh

        Returns:
            Dict with 'generated' and 'failed' lists
        """
        return self.documenter.generate_directory_documentation(
            directories=directories,
            force_regenerate=force_regenerate
        )

    def check_documentation_status(self, directory: str) -> Dict[str, Any]:
        """
        Check the documentation status of a directory.

        Args:
            directory: Directory path to check

        Returns:
            Dict with status information
        """
        return self.documenter.check_documentation_status(directory)
