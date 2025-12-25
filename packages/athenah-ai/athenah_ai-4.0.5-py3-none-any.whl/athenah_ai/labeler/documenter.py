"""
Documentation generation for AI Code Labeler.

Handles .ai.md file generation for individual files and directories.
"""

import os
import json
import logging
from typing import Dict, Any, List, Callable

from athenah_ai.labeler.prompts import (
    FILE_DOC_FROM_JSON_TEMPLATE,
    FILE_DOC_FROM_SOURCE_TEMPLATE,
    DIRECTORY_DOC_TEMPLATE,
    CHUNK_MERGE_TEMPLATE
)
from athenah_ai.config import config

logger = logging.getLogger("app")


class DocumentationGenerator:
    """Handles all .ai.md documentation generation."""

    def __init__(
        self,
        client,
        language_extensions: Dict[str, str],
        source_path: str,
        retry_with_backoff: Callable
    ):
        """
        Initialize documentation generator.

        Args:
            client: AthenahClient instance for AI calls
            language_extensions: Mapping of file extensions to languages
            source_path: Base path to source files
            retry_with_backoff: Function to retry AI calls with backoff
        """
        self.client = client
        self.language_extensions = language_extensions
        self.source_path = source_path
        self._retry_with_backoff = retry_with_backoff

    def _check_md_staleness(self, source_path: str, md_path: str) -> bool:
        """
        Check if .ai.md file needs regeneration based on source file mtime.

        Args:
            source_path: Path to source file (.txt)
            md_path: Path to .ai.md file

        Returns:
            True if .ai.md is stale or doesn't exist, False otherwise
        """
        if not os.path.exists(md_path):
            return True

        if not os.path.exists(source_path):
            return False

        source_mtime = os.path.getmtime(source_path)
        md_mtime = os.path.getmtime(md_path)

        # Check if .ai.json exists and is newer than .ai.md
        ai_json_path = source_path.replace('.txt', '') + '.ai.json'
        if os.path.exists(ai_json_path):
            ai_json_mtime = os.path.getmtime(ai_json_path)
            if ai_json_mtime > md_mtime:
                return True

        return source_mtime > md_mtime

    def _check_if_truncated(self, documentation: str) -> bool:
        """
        Use AI to check if documentation appears truncated/incomplete.

        Args:
            documentation: The generated documentation text

        Returns:
            True if documentation appears truncated, False if complete
        """
        try:
            # Quick heuristic checks first
            if len(documentation) < 100:
                return True  # Definitely too short

            # Check if ends mid-sentence
            last_chars = documentation.strip()[-50:]
            if not any(last_chars.endswith(end) for end in ['.', '!', '?', '```', '`']):
                logger.debug("Documentation may be truncated (no proper ending)")
                return True

            # Use AI for more sophisticated check
            check_prompt = f"""You are checking if this documentation appears complete or was cut off mid-sentence.

DOCUMENTATION:
{documentation[-1000:]}

Analyze the ENDING of the documentation above. Is it:
A) Complete - ends naturally with a proper conclusion
B) Truncated - appears to be cut off mid-sentence or mid-thought

Respond with ONLY "COMPLETE" or "TRUNCATED" (one word).
"""

            def call_ai():
                return self.client.base_prompt(None, check_prompt)

            response = self._retry_with_backoff(call_ai, max_retries=2)
            response = response.strip().upper()

            is_truncated = "TRUNCATED" in response
            if is_truncated:
                logger.warning("AI detected documentation is truncated")
            else:
                logger.debug("AI confirmed documentation is complete")

            return is_truncated

        except Exception as e:
            logger.error(f"Error checking if truncated: {e}")
            # If we can't check, assume it's not truncated
            return False

    def _verify_documentation(self, file_path: str, md_path: str, min_length: int = None) -> bool:
        """
        Verify generated documentation meets quality standards.
        Uses lightweight heuristics (no expensive AI verification).

        Args:
            file_path: Path to source file
            md_path: Path to .ai.md file
            min_length: Minimum length in characters (default: MIN_DOC_LENGTH)

        Returns:
            True if documentation passes verification, False otherwise
        """
        if min_length is None:
            min_length = config.documentation.min_doc_length

        try:
            if not os.path.exists(md_path):
                logger.warning(f"Documentation file does not exist: {md_path}")
                return False

            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check minimum length
            if len(content) < min_length:
                logger.warning(f"Documentation too short ({len(content)} chars): {md_path}")
                return False

            # Check if it's valid markdown (basic check)
            if not content.strip():
                logger.warning(f"Documentation is empty: {md_path}")
                return False

            # Check if it references code elements (basic sanity check)
            # Look for inline code markers or code blocks
            has_code_refs = '`' in content or '```' in content
            if not has_code_refs:
                logger.debug(f"Documentation has no code references: {md_path}")

            logger.debug(f"Documentation verified: {md_path} ({len(content)} chars)")
            return True

        except Exception as e:
            logger.error(f"Error verifying documentation {md_path}: {e}")
            return False

    def _generate_file_documentation(
        self,
        file_path: str,
        source_code: str = None,
        ai_json_data: Dict[str, Any] = None
    ) -> bool:
        """
        Generate detailed narrative .ai.md documentation for a single file.
        Uses either source code directly or existing .ai.json metadata.
        Automatically retries with higher max_tokens if response is truncated.

        Args:
            file_path: Path to source file (.txt)
            source_code: Optional source code content (if not provided, will read from file)
            ai_json_data: Optional .ai.json metadata (if not provided, will try to load)

        Returns:
            True if documentation was generated successfully, False otherwise
        """
        try:
            file_name = os.path.basename(file_path)
            md_path = file_path.replace('.txt', '') + '.ai.md'

            # Determine which mode to use
            use_json_mode = ai_json_data is not None or (source_code is None and os.path.exists(file_path.replace('.txt', '') + '.ai.json'))

            if use_json_mode:
                # Mode 1: Use .ai.json metadata (faster, cheaper)
                if ai_json_data is None:
                    ai_json_path = file_path.replace('.txt', '') + '.ai.json'
                    if not os.path.exists(ai_json_path):
                        logger.warning(f"No .ai.json found for {file_path}, falling back to source code")
                        use_json_mode = False
                    else:
                        with open(ai_json_path, 'r', encoding='utf-8') as f:
                            ai_json_data = json.load(f)

                if use_json_mode:
                    # Format classes info
                    classes_info = []
                    for cls in ai_json_data.get('classes', []):
                        cls_str = f"- `{cls.get('name', 'Unknown')}` (line {cls.get('lineno', '?')})"
                        if cls.get('constructors'):
                            cls_str += f"\n  Constructors: {', '.join(cls['constructors'])}"
                        classes_info.append(cls_str)
                    classes_text = '\n'.join(classes_info) if classes_info else "None"

                    # Format functions info
                    functions_info = []
                    for func in ai_json_data.get('functions', []):
                        func_args = ', '.join(func.get('args', []))
                        functions_info.append(f"- `{func.get('name', 'Unknown')}({func_args})` (line {func.get('lineno', '?')})")
                    functions_text = '\n'.join(functions_info) if functions_info else "None"

                    # Format namespaces info
                    namespaces = ai_json_data.get('namespaces', [])
                    namespaces_text = ', '.join([ns.get('name', '') for ns in namespaces]) if namespaces else "None"

                    # Generate prompt from template
                    prompt = FILE_DOC_FROM_JSON_TEMPLATE.format(
                        file_name=file_name,
                        language=ai_json_data.get('language', 'unknown'),
                        description=ai_json_data.get('description', 'No description available'),
                        classes_info=classes_text,
                        functions_info=functions_text,
                        namespaces_info=namespaces_text
                    )

            if not use_json_mode:
                # Mode 2: Use source code directly (more detailed but expensive)
                if source_code is None:
                    if not os.path.exists(file_path):
                        logger.error(f"Source file does not exist: {file_path}")
                        return False
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source_code = f.read()

                # Determine language
                file_ext = os.path.splitext(file_name)[-2]
                _file_ext = ".".join([s for s in file_ext.split(".") if s != "txt"])
                _file_ext = _file_ext.split(".")[-1]
                language = self.language_extensions.get(f".{_file_ext}", "unknown")

                # Generate prompt from template
                prompt = FILE_DOC_FROM_SOURCE_TEMPLATE.format(
                    file_name=file_name,
                    language=language,
                    source_code=source_code
                )

            # Try generating documentation with increasing max_tokens if truncated
            max_tokens = config.documentation.initial_max_tokens
            ai_response = None

            while max_tokens <= config.documentation.max_tokens_limit:
                logger.debug(f"Generating documentation with max_tokens={max_tokens}")

                # Temporarily set max_tokens for this call
                original_max_tokens = self.client.max_tokens
                self.client.max_tokens = max_tokens

                try:
                    def call_ai():
                        return self.client.base_prompt(None, prompt)

                    ai_response = self._retry_with_backoff(call_ai, max_retries=3)

                    # Check if response is truncated
                    if self._check_if_truncated(ai_response):
                        logger.warning(f"Documentation truncated with max_tokens={max_tokens}, retrying with more tokens")
                        max_tokens += 1000  # Increase by 1000 tokens
                        continue
                    else:
                        # Response is complete, break out of loop
                        logger.debug(f"Documentation complete with max_tokens={max_tokens}")
                        break

                finally:
                    # Restore original max_tokens
                    self.client.max_tokens = original_max_tokens

            if ai_response is None:
                logger.error(f"Failed to generate complete documentation after trying up to {config.documentation.max_tokens_limit} tokens")
                return False

            # Save documentation to .ai.md file
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(ai_response)

            logger.info(f"Generated documentation: {md_path} ({len(ai_response)} chars, max_tokens={max_tokens})")
            return True

        except Exception as e:
            logger.error(f"Error generating documentation for {file_path}: {e}")
            return False

    def _merge_chunked_documentation(
        self,
        chunk_docs: List[str],
        file_path: str
    ) -> str:
        """
        Merge per-chunk documentation into cohesive narrative.
        Used for large files processed in chunks.

        Args:
            chunk_docs: List of documentation strings for each chunk
            file_path: Path to the file being documented

        Returns:
            Merged documentation string
        """
        try:
            file_name = os.path.basename(file_path)

            # Format chunk docs with separators
            formatted_chunks = []
            for i, doc in enumerate(chunk_docs, 1):
                formatted_chunks.append(f"--- CHUNK {i} ---\n{doc}\n")
            chunk_docs_text = '\n'.join(formatted_chunks)

            # Generate merge prompt
            prompt = CHUNK_MERGE_TEMPLATE.format(
                file_name=file_name,
                num_chunks=len(chunk_docs),
                chunk_docs=chunk_docs_text
            )

            # Call AI to merge documentation
            def call_ai():
                return self.client.base_prompt(None, prompt)

            merged_doc = self._retry_with_backoff(call_ai, max_retries=3)

            logger.info(f"Merged {len(chunk_docs)} documentation chunks for {file_path}")
            return merged_doc

        except Exception as e:
            logger.error(f"Error merging chunked documentation for {file_path}: {e}")
            # Return concatenated docs as fallback
            return '\n\n---\n\n'.join(chunk_docs)

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
            file_paths: List of source file paths to document (relative or absolute)
            use_ai_json: If True, use existing .ai.json as input (faster, cheaper)
            force_regenerate: Regenerate even if .ai.md exists and is fresh
            max_retries: Number of retries for failed generations

        Returns:
            Dict with 'generated', 'failed', and 'skipped' lists
        """
        generated: List[str] = []
        failed: List[str] = []
        skipped: List[str] = []

        logger.info(f"Generating documentation for {len(file_paths)} files...")

        for idx, file_path in enumerate(file_paths, 1):
            # Convert to absolute path if relative
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.source_path, file_path)

            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                skipped.append(file_path)
                continue

            # Skip if file is not a supported type
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[-2]
            _file_ext = ".".join([s for s in file_ext.split(".") if s != "txt"])
            _file_ext = _file_ext.split(".")[-1]
            language = self.language_extensions.get(f".{_file_ext}")

            if not language:
                logger.debug(f"Skipping unsupported file type: {file_path}")
                skipped.append(file_path)
                continue

            md_path = file_path.replace('.txt', '') + '.ai.md'

            # Check if documentation needs regeneration
            if not force_regenerate:
                if os.path.exists(md_path):
                    if not self._check_md_staleness(file_path, md_path):
                        logger.debug(f"Documentation up-to-date, skipping: {file_path}")
                        skipped.append(file_path)
                        continue

            # Check if file is chunked (large file)
            ai_json_path = file_path.replace('.txt', '') + '.ai.json'
            is_chunked = False
            ai_json_data = None
            if use_ai_json and os.path.exists(ai_json_path):
                with open(ai_json_path, 'r', encoding='utf-8') as f:
                    ai_json_data = json.load(f)
                    is_chunked = ai_json_data.get('chunked', False)

            # Generate documentation
            logger.info(f"[{idx}/{len(file_paths)}] Generating documentation for: {file_path}")

            retries = 0
            success = False
            while retries < max_retries:
                try:
                    if is_chunked:
                        # For chunked files, use the merged .ai.json data
                        success = self._generate_file_documentation(
                            file_path,
                            ai_json_data=ai_json_data if use_ai_json else None
                        )
                    else:
                        # Normal file
                        success = self._generate_file_documentation(
                            file_path,
                            ai_json_data=ai_json_data if use_ai_json and os.path.exists(ai_json_path) else None
                        )

                    if success:
                        # Verify documentation
                        if self._verify_documentation(file_path, md_path):
                            generated.append(file_path)
                            break
                        else:
                            logger.warning(f"Documentation verification failed, retrying ({retries+1}/{max_retries})")
                            retries += 1
                    else:
                        retries += 1

                except Exception as e:
                    logger.error(f"Error generating documentation for {file_path}: {e}")
                    retries += 1

            if not success or retries == max_retries:
                failed.append(file_path)
                logger.error(f"Failed to generate documentation after {max_retries} retries: {file_path}")

        logger.info(f"Documentation generation complete: {len(generated)} generated, {len(failed)} failed, {len(skipped)} skipped")

        return {
            'generated': generated,
            'failed': failed,
            'skipped': skipped
        }

    def _generate_directory_documentation_md(self, dir_path: str) -> bool:
        """
        Generate human-readable directory.ai.md overview.
        Uses existing .ai.json files and directory.ai.json as input.

        Args:
            dir_path: Directory path (absolute)

        Returns:
            True if documentation was generated successfully, False otherwise
        """
        try:
            # Check if directory.ai.json exists
            dir_summary_path = os.path.join(dir_path, 'directory.ai.json')
            if not os.path.exists(dir_summary_path):
                logger.warning(f"No directory.ai.json found for {dir_path}, cannot generate directory documentation")
                return False

            # Load directory summary
            with open(dir_summary_path, 'r', encoding='utf-8') as f:
                dir_summary = json.load(f)

            # Collect file information from .ai.json files
            files_info = []
            for file_name in os.listdir(dir_path):
                if file_name.endswith('.ai.json') and file_name != 'directory.ai.json':
                    file_path = os.path.join(dir_path, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            ai_data = json.load(f)
                            files_info.append({
                                'file_name': file_name.replace('.ai.json', ''),
                                'description': ai_data.get('description', ''),
                                'language': ai_data.get('language', ''),
                                'num_classes': len(ai_data.get('classes', [])),
                                'num_functions': len(ai_data.get('functions', [])),
                            })
                    except Exception as e:
                        logger.warning(f"Error reading {file_path}: {e}")

            if not files_info:
                logger.warning(f"No .ai.json files found in {dir_path}")
                return False

            # Format files list for prompt
            files_list_text = '\n'.join([
                f"- `{f['file_name']}` ({f['language']}): {f['description'][:100]}..."
                if len(f['description']) > 100 else
                f"- `{f['file_name']}` ({f['language']}): {f['description']}"
                for f in files_info[:20]  # Limit to prevent token overflow
            ])

            # Get directory name and relative path
            dir_name = os.path.basename(dir_path)
            try:
                relative_path = os.path.relpath(dir_path, self.source_path)
            except:
                relative_path = dir_name

            # Format directory summary data
            purpose = dir_summary.get('purpose', 'No purpose description available')
            functionalities = ', '.join(dir_summary.get('functionality', []))
            main_files = ', '.join(dir_summary.get('main_files', []))
            dependencies = ', '.join(dir_summary.get('dependencies', []))

            # Generate prompt from template
            prompt = DIRECTORY_DOC_TEMPLATE.format(
                dir_name=dir_name,
                relative_path=relative_path,
                purpose=purpose,
                functionalities=functionalities if functionalities else 'Not specified',
                main_files=main_files if main_files else 'Not specified',
                dependencies=dependencies if dependencies else 'None',
                files_list=files_list_text
            )

            # Call AI to generate directory documentation
            def call_ai():
                return self.client.base_prompt(None, prompt)

            ai_response = self._retry_with_backoff(call_ai, max_retries=3)

            # Save documentation to directory.ai.md file
            md_path = os.path.join(dir_path, 'directory.ai.md')
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(ai_response)

            logger.info(f"Generated directory documentation: {md_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating directory documentation for {dir_path}: {e}")
            return False

    def generate_directory_documentation(
        self,
        directories: List[str],
        force_regenerate: bool = False
    ) -> Dict[str, List[str]]:
        """
        Generate directory.ai.md overview files for directories.

        Args:
            directories: List of directory paths (relative or absolute) to document
            force_regenerate: Regenerate even if directory.ai.md exists and is fresh

        Returns:
            Dict with 'generated' and 'failed' lists
        """
        generated: List[str] = []
        failed: List[str] = []

        logger.info(f"Generating directory documentation for {len(directories)} directories...")

        for dir_path in directories:
            # Convert to absolute path if relative
            if not os.path.isabs(dir_path):
                dir_path = os.path.join(self.source_path, dir_path)

            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                logger.warning(f"Directory does not exist: {dir_path}")
                failed.append(dir_path)
                continue

            md_path = os.path.join(dir_path, 'directory.ai.md')
            dir_summary_path = os.path.join(dir_path, 'directory.ai.json')

            # Check if documentation needs regeneration
            if not force_regenerate and os.path.exists(md_path):
                # Check if any .ai.json or directory.ai.json is newer than directory.ai.md
                md_mtime = os.path.getmtime(md_path)
                needs_update = False

                # Check directory.ai.json
                if os.path.exists(dir_summary_path):
                    if os.path.getmtime(dir_summary_path) > md_mtime:
                        needs_update = True

                # Check individual .ai.json files
                if not needs_update:
                    for file_name in os.listdir(dir_path):
                        if file_name.endswith('.ai.json') and file_name != 'directory.ai.json':
                            file_path = os.path.join(dir_path, file_name)
                            if os.path.getmtime(file_path) > md_mtime:
                                needs_update = True
                                break

                if not needs_update:
                    logger.debug(f"Directory documentation up-to-date, skipping: {dir_path}")
                    continue

            # Generate documentation
            logger.info(f"Generating directory documentation for: {dir_path}")
            success = self._generate_directory_documentation_md(dir_path)

            if success:
                generated.append(dir_path)
            else:
                failed.append(dir_path)

        logger.info(f"Directory documentation generation complete: {len(generated)} generated, {len(failed)} failed")

        return {
            'generated': generated,
            'failed': failed
        }

    def check_documentation_status(self, directory: str) -> Dict[str, Any]:
        """
        Check the documentation status of a directory.

        Args:
            directory: Directory path to check (relative or absolute)

        Returns:
            Dict with status information including:
            - total_files: Total supported source files
            - documented_files: Files with .ai.md
            - missing_docs: Files with .ai.json but no .ai.md
            - stale_docs: Files where source or .ai.json is newer than .ai.md
            - directory_doc_exists: Whether directory.ai.md exists
            - directory_doc_stale: Whether directory.ai.md needs update
        """
        # Convert to absolute path if relative
        if not os.path.isabs(directory):
            directory = os.path.join(self.source_path, directory)

        if not os.path.exists(directory) or not os.path.isdir(directory):
            return {'error': 'Directory does not exist'}

        total_files = 0
        documented_files = []
        missing_docs = []
        stale_docs = []

        try:
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)

                # Skip directories and .ai files
                if not os.path.isfile(file_path) or file_name.endswith('.ai.json') or file_name.endswith('.ai.md'):
                    continue

                # Check if it's a supported file type
                file_ext = os.path.splitext(file_name)[-2]
                _file_ext = ".".join([s for s in file_ext.split(".") if s != "txt"])
                _file_ext = _file_ext.split(".")[-1]
                language = self.language_extensions.get(f".{_file_ext}")

                if not language:
                    continue

                total_files += 1

                # Check for corresponding .ai.md
                md_path = file_path.replace('.txt', '') + '.ai.md'

                if os.path.exists(md_path):
                    documented_files.append(file_path)

                    # Check if stale
                    if self._check_md_staleness(file_path, md_path):
                        stale_docs.append(file_path)
                else:
                    # Check if .ai.json exists (has been labeled but not documented)
                    ai_json_path = file_path.replace('.txt', '') + '.ai.json'
                    if os.path.exists(ai_json_path):
                        missing_docs.append(file_path)

            # Check directory documentation
            dir_md_path = os.path.join(directory, 'directory.ai.md')
            dir_summary_path = os.path.join(directory, 'directory.ai.json')
            directory_doc_exists = os.path.exists(dir_md_path)

            # Check if directory doc is stale
            directory_doc_stale = False
            if directory_doc_exists:
                dir_md_mtime = os.path.getmtime(dir_md_path)

                # Check if directory.ai.json is newer
                if os.path.exists(dir_summary_path):
                    if os.path.getmtime(dir_summary_path) > dir_md_mtime:
                        directory_doc_stale = True

                # Check if any .ai.json or .ai.md is newer
                if not directory_doc_stale:
                    for file_name in os.listdir(directory):
                        if file_name.endswith('.ai.json') or file_name.endswith('.ai.md'):
                            if file_name == 'directory.ai.md':
                                continue
                            file_path = os.path.join(directory, file_name)
                            if os.path.getmtime(file_path) > dir_md_mtime:
                                directory_doc_stale = True
                                break

            return {
                'directory': directory,
                'total_files': total_files,
                'documented_files': len(documented_files),
                'missing_docs': len(missing_docs),
                'stale_docs': len(stale_docs),
                'directory_doc_exists': directory_doc_exists,
                'directory_doc_stale': directory_doc_stale,
                'missing_docs_list': missing_docs,
                'stale_docs_list': stale_docs,
            }

        except Exception as e:
            logger.error(f"Error checking documentation status: {e}")
            return {'error': str(e)}
