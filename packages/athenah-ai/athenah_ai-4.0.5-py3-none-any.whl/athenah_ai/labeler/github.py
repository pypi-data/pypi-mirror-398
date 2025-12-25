"""
GitHub integration for AI Code Labeler.

Handles repository cloning, incremental updates, and file change detection.
"""

import os
import json
import logging
import subprocess
import shutil
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("app")


class FileChangeType(Enum):
    """Type of change to a file"""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class FileChange:
    """Represents a file change in a commit"""
    path: str
    change_type: FileChangeType
    old_path: Optional[str] = None  # For renames
    additions: int = 0
    deletions: int = 0


class GitHubRepoManager:
    """
    Manages GitHub repository cloning and incremental updates for the labeler.

    Handles:
    - Cloning repositories at specific branches/commits
    - Detecting changed files between commits
    - Merging old labeling data with new source files
    - Git-based staleness detection
    """

    def __init__(
        self,
        workspace_root: str = "workflow",
        storage_type: str = "local"
    ):
        """
        Initialize the GitHub repository manager.

        Args:
            workspace_root: Root directory for workspaces (default: "workflow")
            storage_type: Storage type (local or gcs)
        """
        self.workspace_root = workspace_root
        self.storage_type = storage_type
        os.makedirs(workspace_root, exist_ok=True)

    def get_repo_workspace(self, owner: str, repo: str, branch: str = "main") -> str:
        """
        Get the workspace path for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name

        Returns:
            Path to workspace directory
        """
        workspace_name = f"{owner}-{repo}-{branch}"
        return os.path.join(self.workspace_root, workspace_name)

    def clone_or_update_repo(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        commit_sha: Optional[str] = None,
        force_reclone: bool = False
    ) -> Tuple[str, str]:
        """
        Clone repository or update if it already exists.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch to clone (default: main)
            commit_sha: Specific commit to checkout (optional)
            force_reclone: Force re-clone even if repo exists

        Returns:
            Tuple of (source_path, current_commit_sha)
        """
        workspace = self.get_repo_workspace(owner, repo, branch)
        source_path = os.path.join(workspace, "source")

        try:
            # Remove existing if force_reclone
            if force_reclone and os.path.exists(source_path):
                logger.info(f"Force re-cloning: removing {source_path}")
                shutil.rmtree(source_path)

            # Clone if doesn't exist
            if not os.path.exists(source_path):
                logger.info(f"Cloning {owner}/{repo} branch {branch}...")
                os.makedirs(workspace, exist_ok=True)

                clone_url = f"https://github.com/{owner}/{repo}.git"
                result = subprocess.run(
                    ["git", "clone", "--branch", branch, "--single-branch", clone_url, "source"],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    check=True
                )

                logger.info(f"Cloned repository to {source_path}")
            else:
                # Update existing repository
                logger.info(f"Updating existing repository at {source_path}")

                # Fetch latest changes
                subprocess.run(
                    ["git", "fetch", "origin", branch],
                    cwd=source_path,
                    capture_output=True,
                    check=True
                )

                # Reset to latest
                subprocess.run(
                    ["git", "reset", "--hard", f"origin/{branch}"],
                    cwd=source_path,
                    capture_output=True,
                    check=True
                )

                logger.info("Repository updated to latest")

            # Checkout specific commit if requested
            if commit_sha:
                logger.info(f"Checking out commit {commit_sha}")
                subprocess.run(
                    ["git", "checkout", commit_sha],
                    cwd=source_path,
                    capture_output=True,
                    check=True
                )

            # Get current commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=source_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_sha = result.stdout.strip()

            logger.info(f"Repository at commit {current_sha[:7]}")

            return source_path, current_sha

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            raise RuntimeError(f"Failed to clone/update repository: {e}")
        except Exception as e:
            logger.error(f"Error managing repository: {e}")
            raise

    def get_changed_files_between_commits(
        self,
        repo_path: str,
        old_commit: str,
        new_commit: str
    ) -> List[FileChange]:
        """
        Get list of files changed between two commits using git diff.

        Args:
            repo_path: Path to git repository
            old_commit: Old commit SHA
            new_commit: New commit SHA

        Returns:
            List of FileChange objects
        """
        try:
            # Get diff with name-status to see what changed
            result = subprocess.run(
                ["git", "diff", "--name-status", "--numstat", f"{old_commit}..{new_commit}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            changes = []

            # Parse name-status output
            status_result = subprocess.run(
                ["git", "diff", "--name-status", f"{old_commit}..{new_commit}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            for line in status_result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) < 2:
                    continue

                status = parts[0]

                if status.startswith('A'):  # Added
                    changes.append(FileChange(
                        path=parts[1],
                        change_type=FileChangeType.ADDED
                    ))
                elif status.startswith('M'):  # Modified
                    changes.append(FileChange(
                        path=parts[1],
                        change_type=FileChangeType.MODIFIED
                    ))
                elif status.startswith('D'):  # Deleted
                    changes.append(FileChange(
                        path=parts[1],
                        change_type=FileChangeType.DELETED
                    ))
                elif status.startswith('R'):  # Renamed
                    if len(parts) >= 3:
                        changes.append(FileChange(
                            path=parts[2],  # New path
                            change_type=FileChangeType.RENAMED,
                            old_path=parts[1]  # Old path
                        ))

            # Get additions/deletions using numstat
            numstat_result = subprocess.run(
                ["git", "diff", "--numstat", f"{old_commit}..{new_commit}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            numstat_map = {}
            for line in numstat_result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) >= 3:
                    additions = int(parts[0]) if parts[0] != '-' else 0
                    deletions = int(parts[1]) if parts[1] != '-' else 0
                    filename = parts[2]
                    numstat_map[filename] = (additions, deletions)

            # Merge numstat data with changes
            for change in changes:
                if change.path in numstat_map:
                    change.additions, change.deletions = numstat_map[change.path]

            logger.info(f"Found {len(changes)} changed files between {old_commit[:7]} and {new_commit[:7]}")

            return changes

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get git diff: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"Error getting changed files: {e}")
            return []

    def get_changed_files_since_last_label(
        self,
        repo_path: str,
        labeler_workspace: str
    ) -> List[FileChange]:
        """
        Get files changed since last labeling operation.

        Uses a metadata file to track the last commit that was labeled.

        Args:
            repo_path: Path to git repository
            labeler_workspace: Path to labeler workspace with .ai.json files

        Returns:
            List of FileChange objects
        """
        metadata_path = os.path.join(labeler_workspace, ".labeler_metadata.json")

        try:
            # Get current commit
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_commit = result.stdout.strip()

            # Load last labeled commit
            last_commit = None
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    last_commit = metadata.get('last_labeled_commit')

            if not last_commit:
                logger.info("No previous labeling found, all files will be labeled")
                return []  # Will be handled as initial labeling

            if last_commit == current_commit:
                logger.info("Repository unchanged since last labeling")
                return []

            # Get changes
            changes = self.get_changed_files_between_commits(
                repo_path,
                last_commit,
                current_commit
            )

            return changes

        except Exception as e:
            logger.error(f"Error checking for changes: {e}")
            return []

    def save_labeling_metadata(
        self,
        repo_path: str,
        labeler_workspace: str,
        commit_sha: Optional[str] = None
    ) -> None:
        """
        Save metadata about the current labeling operation.

        Args:
            repo_path: Path to git repository
            labeler_workspace: Path to labeler workspace
            commit_sha: Commit SHA (will be detected if not provided)
        """
        try:
            if not commit_sha:
                # Get current commit
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                commit_sha = result.stdout.strip()

            metadata = {
                'last_labeled_commit': commit_sha,
                'labeled_at': str(subprocess.run(
                    ["git", "log", "-1", "--format=%ci", commit_sha],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                ).stdout.strip()),
                'repo_path': repo_path
            }

            metadata_path = os.path.join(labeler_workspace, ".labeler_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Saved labeling metadata for commit {commit_sha[:7]}")

        except Exception as e:
            logger.error(f"Failed to save labeling metadata: {e}")

    def handle_file_changes(
        self,
        changes: List[FileChange],
        source_path: str,
        labeler_workspace: str
    ) -> Dict[str, List[str]]:
        """
        Handle file changes by updating labeling data accordingly.

        Args:
            changes: List of file changes
            source_path: Path to source repository
            labeler_workspace: Path to labeler workspace with .ai.json files

        Returns:
            Dict with lists of files to process, delete, and rename
        """
        files_to_process = []
        files_to_delete = []
        files_to_rename = []

        for change in changes:
            if change.change_type == FileChangeType.DELETED:
                # Delete .ai.json and .ai.md files
                files_to_delete.append(change.path)

            elif change.change_type == FileChangeType.RENAMED:
                # Rename .ai.json and .ai.md files
                files_to_rename.append((change.old_path, change.path))
                # Also process the renamed file to update content if changed
                files_to_process.append(change.path)

            elif change.change_type in (FileChangeType.ADDED, FileChangeType.MODIFIED):
                # Process these files
                files_to_process.append(change.path)

        # Delete old labeling files
        for file_path in files_to_delete:
            self._delete_labeling_files(file_path, labeler_workspace)

        # Rename labeling files
        for old_path, new_path in files_to_rename:
            self._rename_labeling_files(old_path, new_path, labeler_workspace)

        logger.info(f"Will process {len(files_to_process)} files")
        logger.info(f"Deleted labeling for {len(files_to_delete)} files")
        logger.info(f"Renamed labeling for {len(files_to_rename)} files")

        return {
            'process': files_to_process,
            'delete': files_to_delete,
            'rename': files_to_rename
        }

    def _delete_labeling_files(self, file_path: str, workspace: str) -> None:
        """Delete .ai.json and .ai.md files for a source file."""
        # Convert source path to workspace path
        base_path = os.path.join(workspace, file_path + ".txt")
        ai_json_path = base_path.replace('.txt', '') + '.ai.json'
        ai_md_path = base_path.replace('.txt', '') + '.ai.md'

        for path in [base_path, ai_json_path, ai_md_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logger.debug(f"Deleted {path}")
                except Exception as e:
                    logger.warning(f"Failed to delete {path}: {e}")

    def _rename_labeling_files(self, old_path: str, new_path: str, workspace: str) -> None:
        """Rename .ai.json and .ai.md files when source file is renamed."""
        old_base = os.path.join(workspace, old_path + ".txt")
        new_base = os.path.join(workspace, new_path + ".txt")

        # Ensure destination directory exists
        os.makedirs(os.path.dirname(new_base), exist_ok=True)

        # Rename .txt, .ai.json, and .ai.md
        for suffix in ['', '.ai.json', '.ai.md']:
            old_file = old_base.replace('.txt', '') + suffix if suffix else old_base
            new_file = new_base.replace('.txt', '') + suffix if suffix else new_base

            if os.path.exists(old_file):
                try:
                    shutil.move(old_file, new_file)
                    logger.debug(f"Renamed {old_file} -> {new_file}")
                except Exception as e:
                    logger.warning(f"Failed to rename {old_file}: {e}")
