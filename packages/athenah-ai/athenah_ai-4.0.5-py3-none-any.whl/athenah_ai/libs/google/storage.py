#!/usr/bin/env python
# coding: utf-8

from typing import Any

from google.cloud.storage.client import Client
from google.cloud.storage.bucket import Bucket


class GCPStorageClient(object):
    client: Client = None
    bucket: Bucket = None
    public_base: str = None
    project_id: str = None
    parent: str = None

    def __init__(cls, project_id: str = None):
        """
        :param project_id:
        """
        cls.public_base = "https://storage.googleapis.com"
        cls.project_id = project_id
        cls.parent = f"projects/{cls.project_id}"

    def add_client(cls) -> Any:
        """
        :return:
        """
        cls.client = Client()
        return cls

    def init_bucket(cls, name: str = None) -> Any:
        """
        :param name:
        :return:
        """
        cls.bucket = cls.client.get_bucket(name if name else cls.project_id)
        return cls.bucket

    def get(cls, path):
        blob = cls.bucket.get_blob(path)
        blob.download_to_filename("/local/path/to/file.txt")
        return cls.bucket
