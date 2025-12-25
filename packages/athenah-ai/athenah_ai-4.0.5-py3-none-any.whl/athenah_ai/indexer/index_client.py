#!/usr/bin/env python
# coding: utf-8

import os
from typing import List, Union
import shutil
from shutil import ignore_patterns

from basedir import basedir

from athenah_ai.indexer.cleaner import AthenahCleaner
from athenah_ai.indexer.base_index_client import BaseIndexClient
from athenah_ai.logger import logger

import nltk

nltk.download("punkt_tab")
nltk.download("averaged_perceptron_tagger_eng")


class IndexClient(BaseIndexClient):
    storage_type: str = "local"  # local or gcs
    id: str = ""
    dir: str = ""
    name: str = ""
    version: str = ""

    def __init__(
        cls, storage_type: str, id: str, dir: str, name: str, version: str = "v1"
    ) -> None:
        cls.storage_type = storage_type
        cls.id = id
        cls.dir = dir
        cls.name = name
        cls.version = version
        cls.dist_path: str = os.path.join(basedir, "dist")
        cls.base_path: str = os.path.join(basedir, dir)
        cls.name_path: str = os.path.join(cls.base_path, cls.name)
        cls.name_version_path: str = os.path.join(
            cls.base_path, f"{cls.name}-{cls.version}"
        )
        os.makedirs(cls.base_path, exist_ok=True)
        os.makedirs(cls.name_path, exist_ok=True)
        super().__init__(cls.storage_type, cls.id, cls.dir, cls.name, cls.version)

    def remove(cls, dest: str, is_dir: bool = False):
        if is_dir:
            shutil.rmtree(dest, ignore_errors=True)
        else:
            shutil.rmtree(dest, ignore_errors=True)

    def copy_dir(cls, source: str, dest: str):
        shutil.copytree(
            source,
            dest,
            dirs_exist_ok=True,
            ignore=ignore_patterns(
                "node_modules*",
                "dist*",
                "build*",
                ".git*",
                ".venv*",
                ".vscode*",
                "__pycache__*",
                "poetry.lock",
            ),
        )

    def copy_file(cls, source: str, dest: str):
        shutil.copyfile(source, dest)

    def prepare_dir(cls, source: str, dest_filepath: str):
        logger.debug(f"DEST PATH: {dest_filepath}")
        cls.remove(dest_filepath, True)
        cls.copy_dir(source, dest_filepath)

    def prepare_file(cls, source: str, dest_filepath: str):
        logger.debug(f"DEST PATH: {dest_filepath}")
        cls.remove(dest_filepath, False)
        cls.copy_file(source, dest_filepath)

    def build_from_dir(
        cls,
        source: str,
        clean_dir: bool = False,
    ) -> bool:
        """Build Qdrant collection from a directory."""
        source_name: str = f"{cls.name}-source"
        build_paths: List[str] = [f"{cls.name_path}/{source_name}"]

        if clean_dir:
            dest_filepath: str = os.path.join(cls.name_path, source_name)
            cls.prepare_dir(
                source,
                dest_filepath,
            )
            _ = [AthenahCleaner().clean_dir(filepath, True) for filepath in build_paths]

        _docs, _metadata = cls._build_from_dirs(source, build_paths, False)
        success = cls.store_from_docs(_docs, _metadata)
        if success:
            cls.save()
        return success

    def build_from_dirs(
        cls,
        source: str,
        folders: Union[List[str], str] = None,
        include_root: bool = False,
        clean_dirs: bool = False,
    ) -> bool:
        """Build Qdrant collection from multiple directories."""
        source_name: str = f"{cls.name}-source"
        build_paths: List[str] = [f"{cls.name_path}/{source_name}/{f}" for f in folders]
        if clean_dirs:
            dest_filepath: str = os.path.join(cls.name_path, source_name)
            cls.prepare_dir(
                source,
                dest_filepath,
            )

            [AthenahCleaner().clean_dir(filepath, True) for filepath in build_paths]
            if include_root:
                AthenahCleaner().clean_dir(f"{cls.name_path}/{source_name}", False)

        _docs, _metadata = cls._build_from_dirs(source, build_paths, include_root)
        success = cls.store_from_docs(_docs, _metadata)
        if success:
            cls.save()
        return success

    def build_from_files(cls, file_paths: List[str]) -> bool:
        """Build Qdrant collection from multiple files."""
        source_name: str = f"{cls.name}-source"
        dest_source: str = os.path.join(cls.name_path, source_name)
        shutil.rmtree(dest_source, ignore_errors=True)
        os.makedirs(dest_source, exist_ok=True)

        def copy_files_preserving_structure(
            file_paths: List[str],
            dest_root: str,
            root_path: str = None,
            prepare_file_fn=None,
        ):
            """
            Copies files to dest_root, preserving their relative directory structure from root_path.
            Optionally uses a custom prepare_file_fn for copying.
            """
            for file_path in file_paths:
                try:
                    rel_path = (
                        os.path.relpath(file_path, root_path)
                        if root_path
                        else os.path.basename(file_path)
                    )
                    dest_file_path = os.path.join(dest_root, rel_path)
                    os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                    if prepare_file_fn:
                        prepare_file_fn(file_path, dest_file_path)
                    else:
                        shutil.copy2(file_path, dest_file_path)
                except Exception as e:
                    print(f"Error copying {file_path}: {e}")

        copy_files_preserving_structure(
            file_paths, dest_source, root_path="", prepare_file_fn=cls.prepare_file
        )

        try:
            AthenahCleaner().clean_dir(dest_source, True)
            _docs, _metadata = cls._build_from_dirs(dest_source, [dest_source], True)
            success = cls.store_from_docs(_docs, _metadata)
            if success:
                cls.save()
            return success
        except Exception as e:
            print(f"Error building index: {e}")
            return False

    def build_from_file(cls, file_path: str) -> bool:
        """Build Qdrant collection from a single file."""
        source_name: str = f"{cls.name}-source"
        dest_source: str = os.path.join(cls.name_path, source_name)
        shutil.rmtree(dest_source, ignore_errors=True)
        os.makedirs(dest_source, exist_ok=True)
        cls.prepare_file(
            file_path,
            os.path.join(dest_source, file_path.split("/")[-1]),
        )
        AthenahCleaner().clean_dir(dest_source, True)
        _docs, _metadata = cls._build_from_dirs(dest_source, [dest_source], True)
        success = cls.store_from_docs(_docs, _metadata)
        if success:
            cls.save()
        return success
