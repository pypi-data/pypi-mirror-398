#!/usr/bin/env python
# coding: utf-8

import os
from io import BytesIO
from typing import Optional, List, Dict, Any
import pickle
import tempfile
import shutil

from basedir import basedir
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
import chromadb
from chromadb.config import Settings

from cachetools import cached, TTLCache

from google.cloud.storage.bucket import Bucket
from athenah_ai.libs.google.storage import GCPStorageClient
from athenah_ai.logger import logger
from athenah_ai.config import config

load_dotenv()

cache = TTLCache(maxsize=100, ttl=3600)


class VectorStore(object):
    storage_type: str = "local"  # local or gcs
    _client: Optional[chromadb.ClientAPI] = None
    _collection: Optional[chromadb.Collection] = None
    _embedder: Optional[OpenAIEmbeddings] = None
    _collection_name: str = ""

    def __init__(cls, storage_type: str) -> None:
        cls.storage_type = storage_type
        cls._embedder = OpenAIEmbeddings(
            openai_api_key=config.llm.openai_api_key,
            model=config.indexer.embedding_model,
            chunk_size=config.text_processing.indexer_chunk_size,
        )

    def load(cls, name: str, dir: str = "dist", version: str = "v1") -> chromadb.ClientAPI:
        """Load ChromaDB client and return it."""
        cls._collection_name = f"{name}_{version}".replace("-", "_")

        if cls.storage_type == "local":
            logger.debug("LOADING LOCAL CHROMADB")
            cls._client = cls.load_local(dir, name, version)
            return cls._client

        if cls.storage_type == "gcs":
            logger.debug("LOADING GCS CHROMADB")
            try:
                cls._client = cls.load_local(dir, name, version)
                return cls._client
            except Exception:
                cls.storage_client: GCPStorageClient = GCPStorageClient().add_client()
                cls.bucket: Bucket = cls.storage_client.init_bucket(
                    config.indexer.gcp_index_bucket
                )
                cls._client = cls.load_gcs(name, version, dir)
                return cls._client

    def load_local(cls, dir: str, name: str, version: str) -> chromadb.ClientAPI:
        """Load local ChromaDB collection."""
        cls.base_path: str = os.path.join(basedir, dir)
        cls.name_version_path: str = os.path.join(cls.base_path, f"{name}-{version}")

        # Initialize ChromaDB client with local persistence
        cls._client = chromadb.PersistentClient(
            path=cls.name_version_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )

        try:
            # Check if collection exists
            cls._collection = cls._client.get_collection(name=cls._collection_name)
            count = cls._collection.count()
            logger.info(
                f"Loaded collection {cls._collection_name} with {count} documents"
            )
        except Exception:
            logger.warning(f"Collection {cls._collection_name} not found in local storage")

        return cls._client

    @cached(cache)
    def load_gcs(cls, name: str, version: str, dir: str = "dist") -> chromadb.ClientAPI:
        """Load ChromaDB collection from GCS."""
        import tarfile

        # Download tarball from GCS
        blob = cls.bucket.blob(f"{name}/{version}/chroma.tar.gz")
        temp_dir = tempfile.mkdtemp()

        try:
            tarball_path = os.path.join(temp_dir, "chroma.tar.gz")
            blob.download_to_filename(tarball_path)

            # Extract tarball
            with tarfile.open(tarball_path, "r:gz") as tar:
                tar.extractall(temp_dir)

            # Create local persistent client from extracted data
            cls.base_path: str = os.path.join(basedir, dir)
            cls.name_version_path: str = os.path.join(cls.base_path, f"{name}-{version}")

            # Copy extracted chroma directory to permanent location
            import shutil
            extracted_chroma_path = os.path.join(temp_dir, "chroma")
            if os.path.exists(cls.name_version_path):
                shutil.rmtree(cls.name_version_path)
            shutil.copytree(extracted_chroma_path, cls.name_version_path)

            # Initialize client with permanent location
            cls._client = chromadb.PersistentClient(
                path=cls.name_version_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )

            # Get collection
            cls._collection = cls._client.get_collection(name=cls._collection_name)
            count = cls._collection.count()

            logger.info(
                f"Loaded collection {cls._collection_name} from GCS with {count} documents"
            )

            return cls._client
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def save_to_gcs(cls, name: str, version: str) -> bool:
        """Save ChromaDB collection to GCS."""
        import tarfile

        try:
            cls.storage_client: GCPStorageClient = GCPStorageClient().add_client()
            cls.bucket: Bucket = cls.storage_client.init_bucket(
                config.indexer.gcp_index_bucket
            )

            if not cls._client or not cls.name_version_path:
                logger.error("No ChromaDB client or path to save")
                return False

            # Create tarball of ChromaDB directory
            temp_dir = tempfile.mkdtemp()
            try:
                tarball_path = os.path.join(temp_dir, "chroma.tar.gz")
                with tarfile.open(tarball_path, "w:gz") as tar:
                    tar.add(cls.name_version_path, arcname="chroma")

                # Upload tarball to GCS
                blob = cls.bucket.blob(f"{name}/{version}/chroma.tar.gz")
                blob.upload_from_filename(tarball_path)

                count = cls._collection.count() if cls._collection else 0
                logger.info(
                    f"Saved collection {cls._collection_name} to GCS with {count} documents"
                )
                return True
            finally:
                # Clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            logger.error(f"Failed to save ChromaDB collection: {e}")
            return False

    def get_collection_info(cls) -> Dict[str, Any]:
        """Get collection statistics."""
        if not cls._client:
            return {"exists": False}

        try:
            if not cls._collection:
                cls._collection = cls._client.get_collection(name=cls._collection_name)

            count = cls._collection.count()
            return {
                "exists": True,
                "points_count": count,
                "vectors_count": count,  # In ChromaDB, points_count == vectors_count
                "collection_name": cls._collection_name,
            }
        except Exception:
            return {"exists": False}
