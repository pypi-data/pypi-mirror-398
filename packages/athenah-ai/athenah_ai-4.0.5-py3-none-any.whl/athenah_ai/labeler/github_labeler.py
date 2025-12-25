"""
GitHub-integrated AI Code Labeler.

Provides high-level interface for labeling GitHub repositories with
support for incremental updates and change detection.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from athenah_ai.labeler.labeler import AICodeLabeler
from athenah_ai.labeler.github import GitHubRepoManager, FileChange, FileChangeType

logger = logging.getLogger("app")


class GitHubLabeler:
    """
    High-level interface for labeling GitHub repositories.

    Handles:
    - Initial repository cloning and labeling
    - Incremental updates when repository changes
    - Documentation generation for labeled files
    - Integration with indexer for RAG
    """

    def __init__(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        workspace_root: str = "workflow",
        storage_type: str = "local",
        labeler_id: str = "github",
        version: str = "v1",
        indexer=None,
        use_rag_context: bool = False
    ):
        """
        Initialize GitHub labeler.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch to process
            workspace_root: Root directory for workspaces (default: "workflow")
            storage_type: Storage type (local or gcs)
            labeler_id: Identifier for labeler
            version: Version string
            indexer: Optional indexer for RAG context (BaseIndexClient)
            use_rag_context: Whether to use RAG context when labeling
        """
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.workspace_root = workspace_root
        self.storage_type = storage_type
        self.labeler_id = labeler_id
        self.version = version
        self.indexer = indexer
        self.use_rag_context = use_rag_context

        # Initialize GitHub manager
        self.github_manager = GitHubRepoManager(
            workspace_root=workspace_root,
            storage_type=storage_type
        )

        # Get paths
        self.workspace = self.github_manager.get_repo_workspace(owner, repo, branch)
        self.source_path = None
        self.labeler_workspace = None
        self.current_commit = None

        # Initialize labeler (will be created after we have source path)
        self.labeler: Optional[AICodeLabeler] = None

    def _initialize_labeler(self) -> None:
        """Initialize the AICodeLabeler once we have the source path."""
        if not self.source_path:
            raise RuntimeError("Source path not set. Call setup() first.")

        # Labeler workspace is where .ai.json files are stored
        # This should be the same as the source path (labeler adds .txt to files)
        self.labeler_workspace = self.source_path

        # Initialize labeler pointing to the source directory
        labeler_name = f"{self.owner}-{self.repo}"
        self.labeler = AICodeLabeler(
            storage_type=self.storage_type,
            id=self.labeler_id,
            dir=self.workspace,  # Base workspace directory
            name=labeler_name,
            version=self.version,
            indexer=self.indexer,
            use_rag_context=self.use_rag_context
        )

        # Override the source_path to match the actual GitHub repository location
        self.labeler.source_path = self.source_path
        self.labeler.processor.source_path = self.source_path
        self.labeler.documenter.source_path = self.source_path

    def _cleanup_index_for_changes(self, changes: List[FileChange]) -> None:
        """
        Remove deleted and renamed files from the index.
        Critical for incremental updates to keep index in sync.

        Args:
            changes: List of file changes
        """
        if not self.labeler or not self.labeler.indexer:
            return

        indexer = self.labeler.indexer
        removed_count = 0

        for change in changes:
            try:
                if change.change_type == FileChangeType.DELETED:
                    # Remove deleted file from index
                    if hasattr(indexer, 'remove_document'):
                        indexer.remove_document(metadata_filter={'source': change.file_path})
                        removed_count += 1
                        logger.debug(f"Removed deleted file from index: {change.file_path}")

                elif change.change_type == FileChangeType.RENAMED and hasattr(change, 'old_file_path'):
                    # Remove old path from index (new one will be added during labeling)
                    if hasattr(indexer, 'remove_document'):
                        indexer.remove_document(metadata_filter={'source': change.old_file_path})
                        removed_count += 1
                        logger.debug(f"Removed renamed file from index: {change.old_file_path}")

            except Exception as e:
                logger.warning(f"Failed to remove {change.file_path} from index: {e}")

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} entries from index")

    def setup(
        self,
        commit_sha: Optional[str] = None,
        force_reclone: bool = False
    ) -> str:
        """
        Setup: clone or update repository.

        Args:
            commit_sha: Specific commit to checkout (optional)
            force_reclone: Force re-clone even if repo exists

        Returns:
            Path to source directory
        """
        logger.info(f"Setting up {self.owner}/{self.repo} branch {self.branch}")

        # Clone or update repository
        self.source_path, self.current_commit = self.github_manager.clone_or_update_repo(
            owner=self.owner,
            repo=self.repo,
            branch=self.branch,
            commit_sha=commit_sha,
            force_reclone=force_reclone
        )

        # Initialize labeler
        self._initialize_labeler()

        logger.info(f"Setup complete. Source at: {self.source_path}")
        logger.info(f"Current commit: {self.current_commit[:7]}")

        return self.source_path

    def label_all(
        self,
        directories: Optional[List[str]] = None,
        generate_summaries: bool = True,
        generate_documentation: bool = True
    ) -> Dict[str, Any]:
        """
        Label all files in specified directories (full labeling).

        Args:
            directories: List of directories to process (relative to repo root)
            generate_summaries: Generate directory.ai.json files
            generate_documentation: Generate .ai.md documentation files

        Returns:
            Dict with processing results
        """
        if not self.labeler:
            raise RuntimeError("Labeler not initialized. Call setup() first.")

        logger.info("Starting full repository labeling...")

        # Use default directories if not specified
        if not directories:
            directories = ["."]  # Label everything

        # Process all directories
        result = self.labeler.process_directories(
            directories=directories,
            generate_summaries=generate_summaries,
            skip_complete=False,  # Don't skip, process all
            process_stale=True
        )

        # Generate documentation if requested
        if generate_documentation and result['processed']:
            logger.info(f"Generating documentation for {len(result['processed'])} files...")
            doc_result = self.labeler.generate_file_documentation(
                file_paths=result['processed'],
                use_ai_json=True,
                force_regenerate=False
            )
            result['documentation'] = doc_result

            # Generate directory documentation
            if generate_summaries:
                dir_result = self.labeler.generate_directory_documentation(
                    directories=directories,
                    force_regenerate=False
                )
                result['directory_docs'] = dir_result

        # Save metadata
        self.github_manager.save_labeling_metadata(
            repo_path=self.source_path,
            labeler_workspace=self.labeler_workspace,
            commit_sha=self.current_commit
        )

        logger.info(f"Full labeling complete: {len(result['processed'])} files processed")

        return result

    def label_changes(
        self,
        old_commit: Optional[str] = None,
        generate_documentation: bool = True
    ) -> Dict[str, Any]:
        """
        Label only files that changed since last labeling or specified commit.

        Args:
            old_commit: Old commit SHA (if None, uses last labeled commit from metadata)
            generate_documentation: Generate .ai.md documentation for changed files

        Returns:
            Dict with processing results
        """
        if not self.labeler:
            raise RuntimeError("Labeler not initialized. Call setup() first.")

        logger.info("Detecting changed files...")

        # Get changed files
        if old_commit:
            changes = self.github_manager.get_changed_files_between_commits(
                repo_path=self.source_path,
                old_commit=old_commit,
                new_commit=self.current_commit
            )
        else:
            changes = self.github_manager.get_changed_files_since_last_label(
                repo_path=self.source_path,
                labeler_workspace=self.labeler_workspace
            )

        if not changes:
            logger.info("No changes detected")
            return {
                'processed': [],
                'failed': [],
                'skipped': [],
                'changes': []
            }

        logger.info(f"Found {len(changes)} changed files")

        # Handle file operations (delete, rename)
        file_ops = self.github_manager.handle_file_changes(
            changes=changes,
            source_path=self.source_path,
            labeler_workspace=self.labeler_workspace
        )

        # Update index for deleted and renamed files (if RAG mode enabled)
        self._cleanup_index_for_changes(changes)

        # Process changed files (added, modified, renamed)
        files_to_process = file_ops['process']

        if not files_to_process:
            logger.info("No files to process after handling changes")
            return {
                'processed': [],
                'failed': [],
                'skipped': [],
                'changes': changes,
                'deleted': file_ops['delete'],
                'renamed': file_ops['rename']
            }

        logger.info(f"Processing {len(files_to_process)} files...")

        # Convert to absolute paths with .txt extension for labeler
        absolute_paths = [
            os.path.join(self.source_path, f) + ".txt"
            for f in files_to_process
        ]

        # Process files
        result = self.labeler.process_files(
            file_paths=absolute_paths,
            max_retries=3,
            use_checkpoint=False,
            generate_documentation=False  # We'll do this separately
        )

        # Generate documentation if requested
        if generate_documentation and result['processed']:
            logger.info(f"Generating documentation for {len(result['processed'])} changed files...")
            doc_result = self.labeler.generate_file_documentation(
                file_paths=result['processed'],
                use_ai_json=True,
                force_regenerate=True  # Force regenerate for changed files
            )
            result['documentation'] = doc_result

        # Add change information to result
        result['changes'] = changes
        result['deleted'] = file_ops['delete']
        result['renamed'] = file_ops['rename']

        # Save metadata
        self.github_manager.save_labeling_metadata(
            repo_path=self.source_path,
            labeler_workspace=self.labeler_workspace,
            commit_sha=self.current_commit
        )

        logger.info(f"Incremental labeling complete: {len(result['processed'])} files processed")

        return result

    def update_and_label(
        self,
        commit_sha: Optional[str] = None,
        directories: Optional[List[str]] = None,
        generate_documentation: bool = True
    ) -> Dict[str, Any]:
        """
        Update repository and label only changed files (incremental workflow).

        Args:
            commit_sha: Specific commit to checkout (optional, uses latest if None)
            directories: Directories to process (optional, only for initial labeling)
            generate_documentation: Generate .ai.md documentation

        Returns:
            Dict with processing results
        """
        logger.info("=" * 80)
        logger.info(f"UPDATE AND LABEL: {self.owner}/{self.repo} branch {self.branch}")
        logger.info("=" * 80)

        # Update repository
        old_commit = self.current_commit
        self.setup(commit_sha=commit_sha, force_reclone=False)

        # Check if this is initial labeling (no metadata exists)
        metadata_path = os.path.join(self.labeler_workspace, ".labeler_metadata.json")
        is_initial = not os.path.exists(metadata_path)

        if is_initial:
            logger.info("Initial labeling detected, processing all files...")
            return self.label_all(
                directories=directories,
                generate_summaries=True,
                generate_documentation=generate_documentation
            )
        else:
            logger.info("Incremental update detected, processing only changes...")
            return self.label_changes(
                old_commit=old_commit,
                generate_documentation=generate_documentation
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get current labeling status.

        Returns:
            Dict with status information
        """
        if not self.labeler:
            return {'error': 'Labeler not initialized'}

        # Get status for all directories
        status = {
            'owner': self.owner,
            'repo': self.repo,
            'branch': self.branch,
            'current_commit': self.current_commit,
            'source_path': self.source_path,
            'workspace': self.workspace
        }

        # Get labeling metadata
        metadata_path = os.path.join(self.labeler_workspace, ".labeler_metadata.json")
        if os.path.exists(metadata_path):
            import json
            with open(metadata_path, 'r') as f:
                status['last_labeled'] = json.load(f)

        return status
