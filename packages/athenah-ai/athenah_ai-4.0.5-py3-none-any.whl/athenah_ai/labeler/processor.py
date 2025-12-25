"""
File processing logic for AI Code Labeler.
Handles extraction of classes, functions, namespaces, and metadata from source files.
"""

import os
import json
import logging
from typing import Dict, Any, List, Set, Optional, Callable

from athenah_ai.utils.tokens import get_token_total
from athenah_ai.labeler.models import ProcessingStatus, ProcessingProgress
from athenah_ai.labeler.utils import safe_json_loads
from athenah_ai.config import config

logger = logging.getLogger("app")

# JSON Templates for AI responses - defined outside to avoid bracket issues
FUNCTION_JSON_TEMPLATE = """{
    "name": "function_name",
    "args": ["list of arguments"],
    "lineno": starting_line_number
}"""

NAMESPACE_JSON_TEMPLATE = """{
    "name": "namespace_name",
    "lineno": starting_line_number
}"""

CLASS_JSON_TEMPLATE = """{
    "name": "class_name",
    "args": ["list of arguments"],
    "lineno": starting_line_number
}"""

ARG_JSON_TEMPLATE = """{
    "name": "arg_name",
    "lineno": starting_line_number
}"""

DESCRIPTION_JSON_TEMPLATE = """{
    "description": "brief description of what the file does"
}"""


class FileProcessor:
    """Handles file processing, metadata extraction, and directory operations."""

    def __init__(
        self,
        client,
        language_extensions: Dict[str, str],
        source_path: str,
        checkpoint_path: str,
        checkpoint_interval: int,
        retry_with_backoff: Callable,
        report_progress: Callable[[ProcessingProgress], None],
        indexer=None,
        use_rag_context: bool = False,
    ):
        """
        Initialize FileProcessor.

        Args:
            client: AthenahClient for AI calls
            language_extensions: Mapping of file extensions to language names
            source_path: Root path for source files
            checkpoint_path: Path to checkpoint file
            checkpoint_interval: Number of files between checkpoint saves
            retry_with_backoff: Function to retry operations with exponential backoff
            report_progress: Function to report progress updates
            indexer: Optional indexer for RAG context (BaseIndexClient)
            use_rag_context: Whether to use RAG context when labeling
        """
        self.client = client
        self.language_extensions = language_extensions
        self.source_path = source_path
        self.checkpoint_path = checkpoint_path
        self.checkpoint_interval = checkpoint_interval
        self._retry_with_backoff = retry_with_backoff
        self._report_progress = report_progress
        self.indexer = indexer
        self.use_rag_context = use_rag_context

        # Validate indexer has required methods if RAG is enabled
        if self.use_rag_context and self.indexer:
            if not hasattr(self.indexer, "search"):
                raise AttributeError(
                    f"Indexer {type(self.indexer).__name__} is missing required 'search' method. "
                    f"Cannot use RAG context without a properly configured indexer."
                )

    # ========== Checkpoint Management ==========

    def _save_checkpoint(self, data: Dict[str, Any]) -> None:
        """Save processing checkpoint"""
        try:
            with open(self.checkpoint_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Checkpoint saved: {self.checkpoint_path}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def _load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load processing checkpoint"""
        try:
            if os.path.exists(self.checkpoint_path):
                with open(self.checkpoint_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
        return None

    def _clear_checkpoint(self) -> None:
        """Clear checkpoint file"""
        try:
            if os.path.exists(self.checkpoint_path):
                os.remove(self.checkpoint_path)
                logger.debug("Checkpoint cleared")
        except Exception as e:
            logger.error(f"Failed to clear checkpoint: {e}")

    # ========== RAG Context Building ==========

    def _load_directory_context(self, file_path: str) -> Optional[str]:
        """
        Load directory context from directory.ai.json if it exists.

        Args:
            file_path: Path to the file being processed

        Returns:
            Formatted directory context string or None
        """
        try:
            dir_path = os.path.dirname(file_path)
            dir_summary_path = os.path.join(dir_path, "directory.ai.json")

            if not os.path.exists(dir_summary_path):
                return None

            with open(dir_summary_path, "r", encoding="utf-8") as f:
                dir_data = json.load(f)

            # Format directory context
            context = f"""
DIRECTORY CONTEXT: {dir_data.get('directory_name', 'Unknown')}
Purpose: {dir_data.get('purpose', 'No description')}
Key Functionalities: {', '.join(dir_data.get('functionality', []))}
Main Files: {', '.join(dir_data.get('main_files', []))}
"""
            return context.strip()

        except Exception as e:
            logger.debug(f"Could not load directory context for {file_path}: {e}")
            return None

    def _query_related_files(
        self, file_path: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query indexer for files related to the current file.

        Args:
            file_path: Path to the file being processed
            limit: Maximum number of related files to retrieve

        Returns:
            List of related file documents with their content
        """
        if not self.indexer:
            return []

        try:
            file_name = os.path.basename(file_path)
            dir_name = os.path.basename(os.path.dirname(file_path))

            # Query for related files in the same directory and similar names
            query = f"files in {dir_name} directory similar to {file_name}"

            # Search the index
            results = self.indexer.search(
                query=query,
                limit=limit,
                filter_metadata={"directory": os.path.dirname(file_path)},
            )

            return results if results else []

        except AttributeError as e:
            # Fatal error: indexer missing required method
            error_msg = f"Indexer missing required method for {file_path}: {e}"
            logger.error(error_msg)
            raise AttributeError(error_msg) from e
        except Exception as e:
            logger.debug(f"Could not query related files for {file_path}: {e}")
            return []

    def _build_context_from_related_files(
        self, related_docs: List[Dict[str, Any]]
    ) -> str:
        """
        Build formatted context string from related file documents.

        Args:
            related_docs: List of documents from indexer

        Returns:
            Formatted context string
        """
        if not related_docs:
            return ""

        context_parts = ["RELATED FILES IN CODEBASE:"]

        for doc in related_docs[:5]:  # Limit to top 5 for token efficiency
            metadata = doc.get("metadata", {})
            content = doc.get("page_content", "")

            file_name = metadata.get("source", "Unknown")
            # Truncate content to avoid token overflow
            preview_len = config.rag.context_preview_length
            content_preview = content[:preview_len] + "..." if len(content) > preview_len else content

            context_parts.append(f"\nFile: {file_name}")
            context_parts.append(f"Preview: {content_preview}")

        return "\n".join(context_parts)

    def _build_full_context(self, file_path: str) -> Optional[str]:
        """
        Build complete context for a file (directory context + RAG context).

        Args:
            file_path: Path to the file being processed

        Returns:
            Combined context string or None if no context available
        """
        if not self.use_rag_context:
            return None

        context_parts = []

        # Add directory context
        dir_context = self._load_directory_context(file_path)
        if dir_context:
            context_parts.append(dir_context)
            logger.debug(f"Added directory context for {file_path}")

        # Add RAG context from related files
        if self.indexer:
            related_docs = self._query_related_files(file_path, limit=config.rag.search_limit)
            if related_docs:
                rag_context = self._build_context_from_related_files(related_docs)
                context_parts.append(rag_context)
                logger.debug(
                    f"Added RAG context from {len(related_docs)} related files"
                )

        if not context_parts:
            return None

        return "\n\n".join(context_parts)

    def _index_labeled_file(self, file_path: str, ai_json_path: str) -> bool:
        """
        Index a labeled file immediately after processing.

        Args:
            file_path: Path to source file
            ai_json_path: Path to generated .ai.json file

        Returns:
            True if indexed successfully, False otherwise
        """
        if not self.indexer:
            return False

        try:
            # Read the generated metadata
            with open(ai_json_path, "r", encoding="utf-8") as f:
                ai_data = json.load(f)

            # Read source content
            with open(file_path, "r", encoding="utf-8") as f:
                source_content = f.read()

            # Create metadata for indexing
            metadata = {
                "source": file_path,
                "directory": os.path.dirname(file_path),
                "language": ai_data.get("language", "unknown"),
                "description": ai_data.get("description", ""),
                "classes": [c.get("name", "") for c in ai_data.get("classes", [])],
                "functions": [f.get("name", "") for f in ai_data.get("functions", [])],
            }

            # Index the file
            self.indexer.add_document(content=source_content, metadata=metadata)

            logger.debug(f"Indexed file: {file_path}")
            return True

        except Exception as e:
            logger.warning(f"Failed to index file {file_path}: {e}")
            return False

    # ========== File Chunking ==========

    def _chunk_file_content(
        self, content: str, max_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        Split file content into logical chunks for processing.
        Tries to split by classes/functions to maintain context.
        """
        chunks = []
        lines = content.split("\n")
        current_chunk = []
        current_tokens = 0
        chunk_start_line = 1

        for i, line in enumerate(lines, 1):
            line_tokens = get_token_total(line)

            # Check if adding this line would exceed the limit
            if current_tokens + line_tokens > max_tokens and current_chunk:
                # Save current chunk
                chunk_content = "\n".join(current_chunk)
                chunks.append(
                    {
                        "content": chunk_content,
                        "start_line": chunk_start_line,
                        "end_line": i - 1,
                        "tokens": current_tokens,
                    }
                )
                current_chunk = []
                current_tokens = 0
                chunk_start_line = i

            current_chunk.append(line)
            current_tokens += line_tokens

        # Add remaining chunk
        if current_chunk:
            chunk_content = "\n".join(current_chunk)
            chunks.append(
                {
                    "content": chunk_content,
                    "start_line": chunk_start_line,
                    "end_line": len(lines),
                    "tokens": current_tokens,
                }
            )

        return chunks

    # ========== Code Element Extraction ==========

    def _extract_functions(
        self, content: str, context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        context_section = f"\n{context}\n" if context else ""
        prompt = f"""{context_section}
List all functions in the source code below.

[CODE]
{content}
[/CODE]

**CRITICAL OUTPUT REQUIREMENT: You MUST respond with ONLY valid JSON. No explanations, no markdown, no text outside the JSON.**

Return a JSON array where each object has these fields:
{FUNCTION_JSON_TEMPLATE}

Your response must be a valid JSON array (starting with [ and ending with ]). If no functions, return an empty array [].
OUTPUT ONLY JSON, nothing else."""

        ai_response = self.client.base_prompt(None, prompt)
        json_data = safe_json_loads(ai_response)
        if not json_data or not isinstance(json_data, list):
            json_data = []
        return json_data

    def _extract_namespaces(
        self, content: str, context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        context_section = f"\n{context}\n" if context else ""
        prompt = f"""{context_section}
List all namespaces in the source code below.

[CODE]
{content}
[/CODE]

**CRITICAL OUTPUT REQUIREMENT: You MUST respond with ONLY valid JSON. No explanations, no markdown, no text outside the JSON.**

Return a JSON array where each object has these fields:
{NAMESPACE_JSON_TEMPLATE}

Your response must be a valid JSON array (starting with [ and ending with ]). If no namespaces, return an empty array [].
OUTPUT ONLY JSON, nothing else."""

        ai_response = self.client.base_prompt(None, prompt)
        json_data = safe_json_loads(ai_response)
        if not json_data or not isinstance(json_data, list):
            json_data = []
        return json_data

    def _extract_classes(
        self, content: str, context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        context_section = f"\n{context}\n" if context else ""
        prompt = f"""{context_section}
List all classes in the source code below.

[CODE]
{content}
[/CODE]

**CRITICAL OUTPUT REQUIREMENT: You MUST respond with ONLY valid JSON. No explanations, no markdown, no text outside the JSON.**

Return a JSON array where each object has these fields:
{CLASS_JSON_TEMPLATE}

Your response must be a valid JSON array (starting with [ and ending with ]). If no classes, return an empty array [].
OUTPUT ONLY JSON, nothing else."""

        ai_response = self.client.base_prompt(None, prompt)
        json_data = safe_json_loads(ai_response)
        if not json_data or not isinstance(json_data, list):
            json_data = []
        return json_data

    def _extract_args(
        self, content: str, context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        context_section = f"\n{context}\n" if context else ""
        prompt = f"""{context_section}
List all arguments and variables used in the source code below.

[CODE]
{content}
[/CODE]

**CRITICAL OUTPUT REQUIREMENT: You MUST respond with ONLY valid JSON. No explanations, no markdown, no text outside the JSON.**

Return a JSON array where each object has these fields:
{ARG_JSON_TEMPLATE}

Your response must be a valid JSON array (starting with [ and ending with ]). If no args/variables, return an empty array [].
OUTPUT ONLY JSON, nothing else."""

        ai_response = self.client.base_prompt(None, prompt)
        json_data = safe_json_loads(ai_response)
        if not json_data or not isinstance(json_data, list):
            json_data = []
        return json_data

    def _summarize_file(
        self,
        file_name: str,
        content: str,
        classes: dict,
        functions: dict,
        args: dict,
        context: Optional[str] = None,
    ) -> str:
        context_section = f"\n{context}\n" if context else ""
        prompt = f"""{context_section}
Summarize the {file_name} file below.

[CODE]
{content}
[/CODE]

FileName: {file_name}
Classes: {classes}
Functions: {functions}
Arguments: {args}

**CRITICAL OUTPUT REQUIREMENT: You MUST respond with ONLY valid JSON. No explanations, no markdown, no text outside the JSON.**

Return a JSON object with this structure:
{DESCRIPTION_JSON_TEMPLATE}

Your response must be a valid JSON object (starting with {{ and ending with }}).
OUTPUT ONLY JSON, nothing else."""

        ai_response = self.client.base_prompt(None, prompt)
        json_data = safe_json_loads(ai_response)
        if not json_data or not isinstance(json_data, dict):
            json_data = {"description": ""}
        return json_data.get("description", "")

    def _count_lines(self, file_path: str) -> int:
        """Count lines in a text file. Returns -1 if file is binary or unreadable."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except UnicodeDecodeError:
            return -1  # Binary file
        except Exception as e:
            logger.warning(f"Could not count lines in {file_path}: {e}")
            return -1

    def _is_binary_file(self, file_path: str, sample_size: int = None) -> bool:
        """
        Check if a file is binary by reading a sample and looking for null bytes.

        Args:
            file_path: Path to file
            sample_size: Number of bytes to sample

        Returns:
            True if file appears to be binary, False if text
        """
        if sample_size is None:
            sample_size = config.file_processing.binary_detection_sample_size
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(sample_size)
                # Check for null bytes (common in binary files)
                if b"\x00" in chunk:
                    return True
                # Try to decode as UTF-8
                try:
                    chunk.decode("utf-8")
                    return False
                except UnicodeDecodeError:
                    return True
        except Exception as e:
            logger.warning(f"Error checking if file is binary {file_path}: {e}")
            return True  # Assume binary if we can't read it

    # ========== Single File Processing ==========

    def _process_file(
        self, file_path: str, file_name: str, context: Optional[str] = None
    ) -> str:
        """
        Process a single file and generate .ai.json metadata.

        Args:
            file_path: Path to source file
            file_name: Name of file
            context: Optional context string (directory context + RAG context)

        Returns:
            Path to generated .ai.json file, or empty string on failure
        """
        try:
            # Get file extension correctly - splitext returns (name, .ext)
            file_ext = os.path.splitext(file_name)[1]  # Gets ".h", ".cpp", etc.
            # Remove .txt suffix if present (from cleaner)
            _file_ext = file_ext.replace(".txt", "")
            language = self.language_extensions.get(_file_ext)

            if not language:
                # Skip unsupported file types (like .md, .txt, etc.) - not code files
                logger.info(
                    f"Skipping non-code file {file_name} (extension '{file_ext}' not supported)"
                )
                return ""

            logger.debug(f"Processing {file_name} as {language}")
        except Exception as e:
            logger.error(f"Error parsing file extension for {file_name}: {e}")
            return ""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
                classes = self._extract_classes(source_code, context)
                args = self._extract_args(source_code, context)
                functions = self._extract_functions(source_code, context)
                namespaces = self._extract_namespaces(source_code, context)
                description = self._summarize_file(
                    file_path, source_code, classes, functions, args, context
                )
                config = {
                    "file_path": file_path,
                    "description": description,
                    "namespaces": namespaces,
                    "language": language,
                    "functions": functions,
                    "args": args,
                    "classes": classes,
                }
                file_path_no_txt = file_path.replace(".txt", "")
                dest_file_path = f"{file_path_no_txt}.ai.json"
                with open(dest_file_path, "w") as f:
                    json.dump(config, f, indent=2, sort_keys=True)

                # Index immediately after labeling if RAG mode is enabled
                if self.use_rag_context and self.indexer:
                    self._index_labeled_file(file_path, dest_file_path)

                logger.info(f"Successfully labeled {file_name} -> {dest_file_path}")
                return dest_file_path

        except FileNotFoundError as e:
            logger.error(f"File not found while processing {file_name}: {e}")
            return ""
        except json.JSONDecodeError as e:
            logger.error(f"JSON encoding error for {file_name}: {e}")
            return ""
        except Exception as e:
            logger.error(
                f"Unexpected error processing {file_name}: {type(e).__name__}: {e}",
                exc_info=True,
            )
            return ""

    def _verify_file(
        self, file_path: str, result_path: str, max_attempts: int = 3
    ) -> bool:
        """
        Verify generated .ai.json metadata meets quality standards.

        Args:
            file_path: Path to source file
            result_path: Path to .ai.json file
            max_attempts: Maximum verification attempts

        Returns:
            True if verification passes (score >= 80), False otherwise
        """
        if not os.path.exists(file_path) or not os.path.exists(result_path):
            logger.error(
                f"Source or result file does not exist: {file_path}, {result_path}"
            )
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        with open(result_path, "r", encoding="utf-8") as f:
            result_json = json.load(f)

        prompt_template = """
        You are an expert code reviewer. Given the following source code and its AI-generated summary/result,
        rate the accuracy of the result on a scale from 0 to 100, where 100 means perfect accuracy.
        ONLY Return a JSON response in the following format:
        {{
            "score": <integer 0-100>,
            "reason": "<short explanation>"
        }}

        Source code:
        [CODE]
        {source}
        [/CODE]

        AI Result:
        {result}
        """

        for attempt in range(1, max_attempts + 1):
            prompt = prompt_template.format(
                source=source_code, result=json.dumps(result_json, indent=2)
            )
            ai_response = self.client.base_prompt(None, prompt)
            response_json = safe_json_loads(ai_response)
            if not response_json or not isinstance(response_json, dict):
                logger.error(
                    f"Verification AI response error: Invalid format | {ai_response}"
                )
                return False
            score = response_json.get("score", 0)
            if score >= config.retry.verification_score_threshold:
                return True

        return False

    # ========== Large File Processing ==========

    def _process_large_file(
        self,
        file_path: str,
        file_name: str,
        source_code: str,
        max_tokens: int,
        max_retries: int,
    ) -> bool:
        """
        Process a large file by splitting it into chunks.
        Merges results from all chunks into a single .ai.json file.
        """
        try:
            chunks = self._chunk_file_content(source_code, max_tokens)
            logger.info(f"Split {file_path} into {len(chunks)} chunks")

            all_classes = []
            all_functions = []
            all_args = []
            all_namespaces = []
            descriptions = []

            # Process each chunk
            for i, chunk in enumerate(chunks):
                logger.debug(
                    f"Processing chunk {i+1}/{len(chunks)} "
                    f"(lines {chunk['start_line']}-{chunk['end_line']})"
                )

                def process_chunk():
                    classes = self._extract_classes(chunk["content"])
                    functions = self._extract_functions(chunk["content"])
                    args = self._extract_args(chunk["content"])
                    namespaces = self._extract_namespaces(chunk["content"])
                    return classes, functions, args, namespaces

                # Use retry logic for each chunk
                try:
                    classes, functions, args, namespaces = self._retry_with_backoff(
                        process_chunk, max_retries=max_retries
                    )

                    # Adjust line numbers based on chunk start
                    for item in classes + functions + args:
                        if "lineno" in item:
                            item["lineno"] += chunk["start_line"] - 1

                    all_classes.extend(classes)
                    all_functions.extend(functions)
                    all_args.extend(args)
                    all_namespaces.extend(namespaces)

                    # Generate chunk description
                    chunk_desc = self._summarize_file(
                        f"{file_name} (lines {chunk['start_line']}-{chunk['end_line']})",
                        chunk["content"],
                        classes,
                        functions,
                        args,
                    )
                    if chunk_desc:
                        descriptions.append(chunk_desc)

                except Exception as e:
                    logger.error(f"Failed to process chunk {i+1}: {e}")
                    return False

            # Merge results
            try:
                # Get file extension correctly - splitext returns (name, .ext)
                file_ext = os.path.splitext(file_name)[1]  # Gets ".h", ".cpp", etc.
                # Remove .txt suffix if present (from cleaner)
                _file_ext = file_ext.replace(".txt", "")
                language = self.language_extensions.get(_file_ext)

                if not language:
                    # Skip unsupported file types (like .md, .txt, etc.) - not code files
                    logger.info(
                        f"Skipping non-code file {file_name} (extension '{file_ext}' not supported)"
                    )
                    return False

                logger.debug(f"Processing large file {file_name} as {language}")
            except Exception as e:
                logger.error(f"Error parsing file extension for {file_name}: {e}")
                return False

            merged_config = {
                "file_path": file_path,
                "description": " ".join(descriptions),
                "namespaces": all_namespaces,
                "language": language,
                "functions": all_functions,
                "args": all_args,
                "classes": all_classes,
                "chunked": True,
                "num_chunks": len(chunks),
            }

            file_path_no_txt = file_path.replace(".txt", "")
            dest_file_path = f"{file_path_no_txt}.ai.json"
            with open(dest_file_path, "w") as f:
                json.dump(merged_config, f, indent=2, sort_keys=True)

            logger.info(f"Successfully processed large file: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error processing large file {file_path}: {e}")
            return False

    # ========== Batch File Processing ==========

    def process_files(
        self,
        file_paths: List[str],
        max_retries: int = 3,
        use_checkpoint: bool = True,
        generate_documentation: bool = False,
    ) -> Dict[str, List[str]]:
        """
        Process a specific list of file paths (e.g., changed files from a git diff).
        Includes progress callbacks, checkpoint support, and handles large files via chunking.

        Args:
            file_paths: List of relative or absolute file paths to process
            max_retries: Number of times to retry processing if verification fails
            use_checkpoint: Whether to use checkpoint for resumable processing
            generate_documentation: Whether to generate .ai.md documentation after labeling (default: False)

        Returns:
            Dict with 'processed', 'failed', 'skipped' file lists, and optionally 'documentation' results
        """
        processed_files: Set[str] = set()
        failed_files: Set[str] = set()
        skipped_files: Set[str] = set()

        # Load checkpoint if enabled
        if use_checkpoint:
            checkpoint = self._load_checkpoint()
            if checkpoint:
                processed_files = set(checkpoint.get("processed", []))
                failed_files = set(checkpoint.get("failed", []))
                skipped_files = set(checkpoint.get("skipped", []))
                logger.info(
                    f"Resumed from checkpoint: {len(processed_files)} processed, "
                    f"{len(failed_files)} failed, {len(skipped_files)} skipped"
                )

        MAX_TOKENS = 32768
        total_files = len(file_paths)
        processed_count = 0

        for idx, file_path in enumerate(file_paths, 1):
            # Convert to absolute path if relative
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.source_path, file_path)

            # Skip if already processed in checkpoint
            if (
                file_path in processed_files
                or file_path in failed_files
                or file_path in skipped_files
            ):
                continue

            # Report progress
            self._report_progress(
                ProcessingProgress(
                    file_path=file_path,
                    status=ProcessingStatus.PROCESSING,
                    current=idx,
                    total=total_files,
                    message=f"Processing file {idx}/{total_files}",
                )
            )

            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                skipped_files.add(file_path)
                self._report_progress(
                    ProcessingProgress(
                        file_path=file_path,
                        status=ProcessingStatus.SKIPPED,
                        current=idx,
                        total=total_files,
                        message="File does not exist",
                    )
                )
                continue

            # Skip if already an AI file
            if file_path.endswith(".ai.json"):
                logger.debug(f"Skipping AI file: {file_path}")
                skipped_files.add(file_path)
                self._report_progress(
                    ProcessingProgress(
                        file_path=file_path,
                        status=ProcessingStatus.SKIPPED,
                        current=idx,
                        total=total_files,
                        message="AI file",
                    )
                )
                continue

            # Get file extension and check if we support it
            file_name = os.path.basename(file_path)
            try:
                # Get file extension correctly - splitext returns (name, .ext)
                file_ext = os.path.splitext(file_name)[1]  # Gets ".h", ".cpp", etc.
                # Remove .txt suffix if present (from cleaner)
                _file_ext = file_ext.replace(".txt", "")
                language = self.language_extensions.get(_file_ext)
            except Exception as e:
                logger.error(f"Error parsing file extension for {file_name}: {e}")
                failed_files.add(file_path)
                self._report_progress(
                    ProcessingProgress(
                        file_path=file_path,
                        status=ProcessingStatus.FAILED,
                        current=idx,
                        total=total_files,
                        message=f"Extension parsing error: {e}",
                    )
                )
                continue

            if not language:
                logger.debug(f"Skipping unsupported file type: {file_path}")
                skipped_files.add(file_path)
                self._report_progress(
                    ProcessingProgress(
                        file_path=file_path,
                        status=ProcessingStatus.SKIPPED,
                        current=idx,
                        total=total_files,
                        message="Unsupported file type",
                    )
                )
                continue

            # Skip binary files
            if self._is_binary_file(file_path):
                logger.debug(f"Skipping binary file: {file_path}")
                skipped_files.add(file_path)
                self._report_progress(
                    ProcessingProgress(
                        file_path=file_path,
                        status=ProcessingStatus.SKIPPED,
                        current=idx,
                        total=total_files,
                        message="Binary file",
                    )
                )
                continue

            # Read and check token count
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source_code = f.read()
                    total_tokens = get_token_total(source_code)

                    # Handle large files with chunking
                    if total_tokens > MAX_TOKENS:
                        logger.info(
                            f"File {file_path} has {total_tokens} tokens, processing in chunks"
                        )
                        success = self._process_large_file(
                            file_path, file_name, source_code, MAX_TOKENS, max_retries
                        )
                        if success:
                            processed_files.add(file_path)
                            self._report_progress(
                                ProcessingProgress(
                                    file_path=file_path,
                                    status=ProcessingStatus.COMPLETED,
                                    current=idx,
                                    total=total_files,
                                    message="Processed (chunked)",
                                )
                            )
                        else:
                            failed_files.add(file_path)
                            self._report_progress(
                                ProcessingProgress(
                                    file_path=file_path,
                                    status=ProcessingStatus.FAILED,
                                    current=idx,
                                    total=total_files,
                                    message="Failed to process chunked file",
                                )
                            )
                        processed_count += 1
                        # Save checkpoint periodically
                        if (
                            use_checkpoint
                            and processed_count % self.checkpoint_interval == 0
                        ):
                            self._save_checkpoint(
                                {
                                    "processed": list(processed_files),
                                    "failed": list(failed_files),
                                    "skipped": list(skipped_files),
                                }
                            )
                        continue

            except UnicodeDecodeError:
                logger.warning(f"Skipping file with encoding issues: {file_path}")
                skipped_files.add(file_path)
                self._report_progress(
                    ProcessingProgress(
                        file_path=file_path,
                        status=ProcessingStatus.SKIPPED,
                        current=idx,
                        total=total_files,
                        message="Encoding error",
                    )
                )
                continue
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                failed_files.add(file_path)
                self._report_progress(
                    ProcessingProgress(
                        file_path=file_path,
                        status=ProcessingStatus.FAILED,
                        current=idx,
                        total=total_files,
                        error=str(e),
                    )
                )
                continue

            # Build context if RAG mode is enabled
            context = (
                self._build_full_context(file_path) if self.use_rag_context else None
            )

            # Process the file with retries
            retries = 0
            success = False
            while retries < max_retries:
                try:
                    result_path = self._process_file(file_path, file_name, context)
                    if not result_path:
                        break

                    verified = self._verify_file(file_path, result_path, max_attempts=3)
                    if verified:
                        processed_files.add(file_path)
                        logger.info(f"Successfully processed: {file_path}")
                        self._report_progress(
                            ProcessingProgress(
                                file_path=file_path,
                                status=ProcessingStatus.COMPLETED,
                                current=idx,
                                total=total_files,
                                message="Completed",
                            )
                        )
                        success = True
                        break
                    else:
                        logger.warning(
                            f"Verification failed for {file_path}, retrying ({retries+1}/{max_retries})"
                        )
                        retries += 1
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    retries += 1

            if not success:
                failed_files.add(file_path)
                self._report_progress(
                    ProcessingProgress(
                        file_path=file_path,
                        status=ProcessingStatus.FAILED,
                        current=idx,
                        total=total_files,
                        message=f"Failed after {max_retries} retries",
                    )
                )

            processed_count += 1

            # Save checkpoint periodically
            if use_checkpoint and processed_count % self.checkpoint_interval == 0:
                self._save_checkpoint(
                    {
                        "processed": list(processed_files),
                        "failed": list(failed_files),
                        "skipped": list(skipped_files),
                    }
                )

        # Clear checkpoint on successful completion
        if use_checkpoint:
            self._clear_checkpoint()

        result = {
            "processed": list(processed_files),
            "failed": list(failed_files),
            "skipped": list(skipped_files),
        }

        # Note: documentation generation will be handled by DocumentationGenerator
        # This is just a placeholder for backward compatibility
        if generate_documentation:
            logger.info(
                "Documentation generation flag set - will be handled by DocumentationGenerator"
            )

        return result

    # ========== Directory Processing ==========

    def _process_directory(
        self,
        dir_path: str,
        processed_files: Set[str],
        failed_files: Set[str],
        max_retries: int = 1,
    ) -> None:
        """
        Process all supported files in a directory.

        Args:
            dir_path: Directory path
            processed_files: Set to add successfully processed files
            failed_files: Set to add failed files
            max_retries: Number of retries per file
        """
        MAX_TOKENS = config.text_processing.large_file_token_limit
        oversized_files: List[str] = []
        for root, _, files in os.walk(dir_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if file_path.endswith(".ai.json"):
                    logger.debug(f"Skipping AI file: {file_path}")
                    continue

                if file_path in processed_files or file_path in failed_files:
                    continue

                ai_file_path = f"{file_path.replace('.txt', '')}.ai.json"
                if os.path.exists(ai_file_path):
                    logger.debug(f"Skipping existing AI file: {ai_file_path}")
                    continue

                # Skip binary files
                if self._is_binary_file(file_path):
                    logger.debug(f"Skipping binary file: {file_path}")
                    continue

                total_lines = self._count_lines(file_path)
                if total_lines == -1:
                    logger.debug(f"Skipping unreadable file: {file_path}")
                    continue

                logger.debug(f"File {file_name} has: {total_lines} lines")

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        source_code = f.read()
                        total_tokens = get_token_total(source_code)
                        if total_tokens > MAX_TOKENS:
                            logger.warning(
                                f"File {file_path} has {total_tokens} tokens, which exceeds the limit of {MAX_TOKENS} tokens."
                            )
                            oversized_files.append(file_path)
                            continue
                except UnicodeDecodeError:
                    logger.warning(f"Skipping file with encoding issues: {file_path}")
                    continue
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")
                    failed_files.add(file_path)
                    continue

                # Build context if RAG mode is enabled
                context = (
                    self._build_full_context(file_path)
                    if self.use_rag_context
                    else None
                )

                retries = 0
                while retries < max_retries:
                    result_path = self._process_file(file_path, file_name, context)
                    if not result_path:
                        failed_files.add(file_path)
                        break
                    verified = self._verify_file(file_path, result_path, max_attempts=3)
                    if verified:
                        processed_files.add(file_path)
                        break
                    else:
                        logger.warning(
                            f"Verification failed for {file_path}, retrying ({retries+1}/{max_retries})"
                        )
                        retries += 1
                if retries == max_retries:
                    failed_files.add(file_path)
        if oversized_files:
            print(f"Oversized files: {oversized_files}")

    # ========== Directory Status & Operations ==========

    def check_directory_status(self, directory: str) -> Dict[str, Any]:
        """
        Check the processing status of a directory.

        Args:
            directory: Directory path to check

        Returns:
            Dict with status information including:
            - total_files: Total supported source files
            - labeled_files: Files with .ai.json
            - unlabeled_files: Files without .ai.json
            - stale_files: Files where source is newer than .ai.json
            - is_complete: Whether all files are labeled
            - has_directory_summary: Whether directory.ai.json exists
        """
        # Convert to absolute path if relative
        if not os.path.isabs(directory):
            directory = os.path.join(self.source_path, directory)

        if not os.path.exists(directory) or not os.path.isdir(directory):
            return {"error": "Directory does not exist", "is_complete": False}

        source_files = []
        labeled_files = []
        unlabeled_files = []
        stale_files = []

        try:
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)

                # Skip directories and .ai.json files
                if not os.path.isfile(file_path) or file_name.endswith(".ai.json"):
                    continue

                # Check if it's a supported file type
                try:
                    # Get file extension correctly - splitext returns (name, .ext)
                    file_ext = os.path.splitext(file_name)[1]  # Gets ".h", ".cpp", etc.
                    # Remove .txt suffix if present (from cleaner)
                    _file_ext = file_ext.replace(".txt", "")
                    language = self.language_extensions.get(_file_ext)

                    if not language:
                        continue
                except Exception as e:
                    logger.debug(f"Error parsing file extension for {file_name}: {e}")
                    continue

                source_files.append(file_path)

                # Check for corresponding .ai.json
                ai_file_path = f"{file_path.replace('.txt', '')}.ai.json"

                if os.path.exists(ai_file_path):
                    labeled_files.append(file_path)

                    # Check if stale (source modified after .ai.json)
                    source_mtime = os.path.getmtime(file_path)
                    ai_mtime = os.path.getmtime(ai_file_path)

                    if source_mtime > ai_mtime:
                        stale_files.append(file_path)
                else:
                    unlabeled_files.append(file_path)

            # Check for directory.ai.json
            dir_summary_path = os.path.join(directory, "directory.ai.json")
            has_directory_summary = os.path.exists(dir_summary_path)

            # Check if directory summary is stale
            dir_summary_stale = False
            if has_directory_summary:
                dir_summary_mtime = os.path.getmtime(dir_summary_path)
                # Directory summary is stale if any .ai.json file is newer
                for file_name in os.listdir(directory):
                    if (
                        file_name.endswith(".ai.json")
                        and file_name != "directory.ai.json"
                    ):
                        ai_file_path = os.path.join(directory, file_name)
                        if os.path.getmtime(ai_file_path) > dir_summary_mtime:
                            dir_summary_stale = True
                            break

            is_complete = len(unlabeled_files) == 0 and len(stale_files) == 0

            return {
                "directory": directory,
                "total_files": len(source_files),
                "labeled_files": len(labeled_files),
                "unlabeled_files": len(unlabeled_files),
                "stale_files": len(stale_files),
                "is_complete": is_complete,
                "has_directory_summary": has_directory_summary,
                "directory_summary_stale": dir_summary_stale,
                "unlabeled_file_list": unlabeled_files,
                "stale_file_list": stale_files,
            }

        except Exception as e:
            logger.error(f"Error checking directory status: {e}")
            return {"error": str(e), "is_complete": False}

    def get_files_needing_processing(
        self, directories: List[str], include_stale: bool = True
    ) -> Dict[str, List[str]]:
        """
        Get lists of files that need processing across multiple directories.
        Useful for planning and reporting before actual processing.

        Args:
            directories: List of directory paths to check
            include_stale: Include files where source is newer than .ai.json

        Returns:
            Dict with 'unlabeled' and 'stale' file lists
        """
        all_unlabeled = []
        all_stale = []

        for dir_path in directories:
            status = self.check_directory_status(dir_path)
            if "error" not in status:
                all_unlabeled.extend(status.get("unlabeled_file_list", []))
                if include_stale:
                    all_stale.extend(status.get("stale_file_list", []))

        return {
            "unlabeled": all_unlabeled,
            "stale": all_stale,
            "total_needing_processing": len(all_unlabeled)
            + (len(all_stale) if include_stale else 0),
        }

    def remove_labels(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Remove .ai.json files for deleted source files.

        Args:
            file_paths: List of deleted file paths (relative or absolute)

        Returns:
            Dict with 'removed' and 'not_found' lists
        """
        removed_files: List[str] = []
        not_found_files: List[str] = []

        for file_path in file_paths:
            # Convert to absolute path if relative
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.source_path, file_path)

            # Calculate .ai.json path
            ai_file_path = f"{file_path.replace('.txt', '')}.ai.json"

            if os.path.exists(ai_file_path):
                os.remove(ai_file_path)
                removed_files.append(ai_file_path)
                logger.info(f"Removed label file: {ai_file_path}")
            else:
                not_found_files.append(ai_file_path)
                logger.debug(f"Label file not found: {ai_file_path}")

        return {"removed": removed_files, "not_found": not_found_files}

    def clear_directory_labels(
        self, directories: List[str], include_directory_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Remove all .ai.json files from specified directories (non-recursive).
        Useful for invalidating/making directories stale.

        Args:
            directories: List of directory paths to clear
            include_directory_summary: Whether to also remove directory.ai.json files

        Returns:
            Dict with 'cleared' count per directory and 'failed' list
        """
        results = {}
        failed = []

        for dir_path in directories:
            # Convert to absolute path if relative
            if not os.path.isabs(dir_path):
                dir_path = os.path.join(self.source_path, dir_path)

            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                logger.warning(f"Directory does not exist: {dir_path}")
                failed.append(dir_path)
                continue

            try:
                removed_count = 0
                for file_name in os.listdir(dir_path):
                    # Skip directory.ai.json unless explicitly requested
                    if (
                        file_name == "directory.ai.json"
                        and not include_directory_summary
                    ):
                        continue

                    if file_name.endswith(".ai.json"):
                        file_path = os.path.join(dir_path, file_name)
                        try:
                            os.remove(file_path)
                            removed_count += 1
                            logger.debug(f"Removed: {file_path}")
                        except Exception as e:
                            logger.error(f"Failed to remove {file_path}: {e}")

                results[dir_path] = removed_count
                logger.info(f"Cleared {removed_count} label files from {dir_path}")

            except Exception as e:
                logger.error(f"Error clearing directory {dir_path}: {e}")
                failed.append(dir_path)

        return {"cleared": results, "failed": failed}

    # ========== Directory Summary Generation ==========

    def _create_directory_summary_with_ai(
        self, dir_name: str, ai_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use AI to create a summary of the directory's purpose and functionality"""
        files_summary = "\n".join(
            [
                f"- {f['file_name']} ({f['language']}): {f['description']}\n"
                f"  Classes: {', '.join(f['classes'][:5])}\n"
                f"  Functions: {', '.join(f['functions'][:5])}"
                for f in ai_files[:20]  # Limit to prevent token overflow
            ]
        )

        response_template = """{
            "purpose": "high-level purpose of this directory",
            "functionality": ["list", "of", "key", "functionalities"],
            "main_files": ["list", "of", "most", "important", "files"],
            "dependencies": ["external", "dependencies", "or", "imports"]
        }"""

        prompt = f"""
        Analyze the following directory "{dir_name}" and its files to provide a comprehensive summary.

        Files in this directory:
        {files_summary}

        Total files: {len(ai_files)}

        Response Template:
        {response_template}

        Instructions:
        - Provide a clear, concise summary of the directory's purpose
        - List 3-5 key functionalities
        - Identify the 3-5 most important files
        - Note any apparent external dependencies
        - Do not include code blocks or markdown
        - Return valid JSON only, no extra text
        """

        try:

            def call_ai():
                return self.client.base_prompt(None, prompt)

            ai_response = self._retry_with_backoff(call_ai, max_retries=3)
            json_data = safe_json_loads(ai_response)

            if not json_data or not isinstance(json_data, dict):
                json_data = {
                    "purpose": f"Directory containing {len(ai_files)} files",
                    "functionality": [],
                    "main_files": [f["file_name"] for f in ai_files[:5]],
                    "dependencies": [],
                }

            # Add metadata
            json_data["directory_name"] = dir_name
            json_data["file_count"] = len(ai_files)
            json_data["files"] = [
                {
                    "name": f["file_name"],
                    "language": f["language"],
                    "num_classes": f["num_classes"],
                    "num_functions": f["num_functions"],
                }
                for f in ai_files
            ]

            return json_data

        except Exception as e:
            logger.error(f"Error creating AI summary: {e}")
            return {
                "directory_name": dir_name,
                "purpose": f"Directory containing {len(ai_files)} files",
                "functionality": [],
                "main_files": [f["file_name"] for f in ai_files[:5]],
                "dependencies": [],
                "file_count": len(ai_files),
                "files": [
                    {
                        "name": f["file_name"],
                        "language": f["language"],
                        "num_classes": f["num_classes"],
                        "num_functions": f["num_functions"],
                    }
                    for f in ai_files
                ],
                "error": str(e),
            }

    def _generate_directory_summary(self, dir_path: str) -> bool:
        """Generate a directory.ai.json summary file for a specific directory"""
        try:
            # Collect all .ai.json files in this directory (non-recursive)
            ai_files = []
            for file_name in os.listdir(dir_path):
                if file_name.endswith(".ai.json") and file_name != "directory.ai.json":
                    file_path = os.path.join(dir_path, file_name)
                    try:
                        with open(file_path, "r") as f:
                            ai_data = json.load(f)
                            ai_files.append(
                                {
                                    "file_name": file_name.replace(".ai.json", ""),
                                    "description": ai_data.get("description", ""),
                                    "language": ai_data.get("language", ""),
                                    "num_classes": len(ai_data.get("classes", [])),
                                    "num_functions": len(ai_data.get("functions", [])),
                                    "classes": [
                                        c.get("name", "")
                                        for c in ai_data.get("classes", [])
                                    ],
                                    "functions": [
                                        f.get("name", "")
                                        for f in ai_data.get("functions", [])
                                    ],
                                }
                            )
                    except Exception as e:
                        logger.warning(f"Error reading {file_path}: {e}")

            if not ai_files:
                logger.debug(f"No .ai.json files found in {dir_path}")
                return False

            # Generate summary using AI
            dir_name = os.path.basename(dir_path)
            summary_data = self._create_directory_summary_with_ai(dir_name, ai_files)

            # Save directory.ai.json
            output_path = os.path.join(dir_path, "directory.ai.json")
            with open(output_path, "w") as f:
                json.dump(summary_data, f, indent=2, sort_keys=True)

            logger.info(f"Generated directory summary: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating directory summary for {dir_path}: {e}")
            return False

    def generate_directory_summaries(
        self, directories: List[str]
    ) -> Dict[str, List[str]]:
        """
        Generate directory.ai.json files that summarize the functionality
        of each directory based on the .ai.json files within it.

        Args:
            directories: List of directory paths (relative or absolute) to summarize

        Returns:
            Dict with 'generated' and 'failed' lists of directory paths
        """
        generated: List[str] = []
        failed: List[str] = []

        for dir_path in directories:
            # Convert to absolute path if relative
            if not os.path.isabs(dir_path):
                dir_path = os.path.join(self.source_path, dir_path)

            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                logger.warning(f"Directory does not exist: {dir_path}")
                failed.append(dir_path)
                continue

            try:
                logger.info(f"Generating directory summary for: {dir_path}")
                success = self._generate_directory_summary(dir_path)
                if success:
                    generated.append(dir_path)
                else:
                    failed.append(dir_path)
            except Exception as e:
                logger.error(f"Failed to generate summary for {dir_path}: {e}")
                failed.append(dir_path)

        return {"generated": generated, "failed": failed}

    # ========== High-level Processing Methods ==========

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
            skip_complete: Skip directories where all files are already labeled (default: True)
            process_stale: Process files where source is newer than .ai.json (default: True)
            force: Force reprocessing even if directory is complete (default: False)

        Returns:
            Dict with processing results and summary generation results
        """
        processed_files: Set[str] = set()
        failed_files: Set[str] = set()
        skipped_dirs: List[str] = []
        stale_files_processed: Set[str] = set()

        # Process all files in directories
        for rel_dir in directories:
            abs_dir = os.path.join(self.source_path, rel_dir)

            # Check directory status if not forcing
            if not force and skip_complete:
                status = self.check_directory_status(abs_dir)

                # Skip if complete and no stale files
                if status.get("is_complete", False):
                    logger.info(f"Skipping complete directory: {abs_dir}")
                    skipped_dirs.append(abs_dir)
                    continue

                # If processing stale files only
                if process_stale and status.get("stale_files", 0) > 0:
                    logger.info(
                        f"Processing {status['stale_files']} stale files in {abs_dir}"
                    )
                    stale_file_list = status.get("stale_file_list", [])
                    for file_path in stale_file_list:
                        file_name = os.path.basename(file_path)

                        # Build context if RAG mode is enabled
                        context = (
                            self._build_full_context(file_path)
                            if self.use_rag_context
                            else None
                        )

                        retries = 0
                        success = False
                        while retries < max_retries:
                            result_path = self._process_file(
                                file_path, file_name, context
                            )
                            if not result_path:
                                break
                            verified = self._verify_file(
                                file_path, result_path, max_attempts=3
                            )
                            if verified:
                                processed_files.add(file_path)
                                stale_files_processed.add(file_path)
                                logger.info(
                                    f"Successfully processed stale file: {file_path}"
                                )
                                success = True
                                break
                            else:
                                retries += 1
                        if not success:
                            failed_files.add(file_path)

                    # Continue to next directory after processing stale files
                    if status.get("unlabeled_files", 0) == 0:
                        continue

            # Process entire directory if not complete or forced
            self._process_directory(abs_dir, processed_files, failed_files, max_retries)

        results = {
            "processed": list(processed_files),
            "failed": list(failed_files),
            "skipped_directories": skipped_dirs,
            "stale_files_updated": list(stale_files_processed),
        }

        # Generate directory summaries if requested
        if generate_summaries:
            logger.info("Generating directory summaries...")
            # Only generate summaries for directories that were processed or had stale files
            dirs_to_summarize = [
                d
                for d in directories
                if os.path.join(self.source_path, d) not in skipped_dirs
            ]
            if dirs_to_summarize:
                summary_results = self.generate_directory_summaries(dirs_to_summarize)
                results["summaries"] = summary_results
            else:
                results["summaries"] = {"generated": [], "failed": []}

        return results
