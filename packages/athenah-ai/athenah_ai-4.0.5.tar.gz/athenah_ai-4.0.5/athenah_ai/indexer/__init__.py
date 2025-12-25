#!/usr/bin/env python
# coding: utf-8

import os
from typing import List

from basedir import basedir
from dotenv import load_dotenv

from athenah_ai.indexer.index_client import IndexClient
from athenah_ai.logger import logger

load_dotenv()


class AthenahIndexer(IndexClient):
    storage_type: str = "local"  # local or gcs
    id: str = ""
    dir: str = ""
    name: str = ""
    version: str = ""

    def __init__(
        cls,
        storage_type: str,
        id: str,
        dir: str,
        name: str,
        version: str,
    ):
        cls.storage_type = storage_type
        cls.id = id
        cls.dir = dir
        cls.name = name
        cls.version = version
        super().__init__(cls.storage_type, cls.id, cls.dir, cls.name, cls.version)
        pass

    def index_dir(
        cls,
        source: str,
        dirs: List[str],
        include_root: bool = False,
        clean_dir: bool = False,
    ):
        cls.build_from_dirs(source, dirs, include_root, clean_dir)

    def index_dirs(
        cls,
        source: str,
        dirs: List[str],
        include_root: bool = False,
        clean_dirs: bool = False,
    ):
        if dirs == ["."]:
            cls.build_from_dir(source, clean_dirs)
            return

        cls.build_from_dirs(source, dirs, include_root, clean_dirs)

    def index_files(
        cls,
        file_paths: List[str],
    ):
        cls.build_from_files(file_paths)

    def index_file(cls, file_path: str):
        cls.build_from_file(file_path)
