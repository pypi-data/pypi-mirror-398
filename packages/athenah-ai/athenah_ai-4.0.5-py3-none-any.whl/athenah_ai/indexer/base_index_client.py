import os
import math
from typing import Dict, Any, List, Tuple, Optional, Union
import shutil
import pickle
import tiktoken
import tempfile
import uuid

from basedir import basedir
from dotenv import load_dotenv

from unstructured.file_utils.filetype import FileType, detect_filetype
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import Language
from langchain_openai import OpenAIEmbeddings

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from google.cloud.storage.bucket import Bucket, Blob
from athenah_ai.libs.google.storage import GCPStorageClient

from athenah_ai.client import AthenahClient
from athenah_ai.indexer.splitters import code_splitter, text_splitter
from athenah_ai.logger import logger
from athenah_ai.config import config

load_dotenv()

# --- Utility Functions ---


def estimate_tokens(text: str, model: str = "gpt-3.5-turbo-16k") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except Exception as e:
        logger.error(f"Token estimation failed: {e}")
        return len(text) // 4  # fallback: rough estimate


def estimate_chunk_size(
    model: str,
    max_tokens: int,
    avg_chars_per_token: int = 4,
    safety_margin: float = 0.9,
) -> int:
    try:
        # Use tiktoken to get a more accurate chars/token if needed
        # For now, use avg_chars_per_token as a fallback
        return int(max_tokens * avg_chars_per_token * safety_margin)
    except Exception as e:
        logger.error(f"Chunk size estimation failed: {e}")
        return int(max_tokens * avg_chars_per_token * safety_margin)


def get_dynamic_chunk_size(
    model: str,
    max_tokens: int,
    sample_text: Optional[str] = None,
    safety_margin: float = 0.9,
) -> int:
    if sample_text:
        try:
            tokens = estimate_tokens(sample_text, model)
            chars_per_token = len(sample_text) / max(tokens, 1)
            return int(max_tokens * chars_per_token * safety_margin)
        except Exception as e:
            logger.error(f"Dynamic chunk size estimation failed: {e}")
    return estimate_chunk_size(model, max_tokens, safety_margin=safety_margin)


# --- Summarization ---


def summarize_file(content: str) -> str:
    try:
        client = AthenahClient(id="id", model_name="gpt-3.5-turbo-16k")
        response = client.base_prompt(
            (
                "Describe and summarize what this document says. "
                "Be very specific. Everything must be documented. "
                "Keep it very short and concise, this will be used for labeling a vector search."
            ),
            content,
        )
        return response
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return ""


# --- Directory/File Preparation ---


def load_ai_json_metadata(root: str) -> Dict[str, Any]:
    ai_metadata = {}
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".ai.json"):
                path = os.path.join(dirpath, filename)
                try:
                    with open(path, "r") as f:
                        import json

                        data = json.load(f)
                    real_file = data.get("file_path")
                    if real_file:
                        ai_metadata[os.path.abspath(real_file)] = data
                except Exception as e:
                    logger.error(f"Failed to load metadata {path}: {e}")
    return ai_metadata


def prepare_dir(
    root: str,
    save_path: Optional[str] = None,
    recursive: bool = False,
    chunk_size: Optional[int] = None,
    chunk_overlap: int = config.text_processing.indexer_chunk_overlap,
    model: str = config.indexer.embedding_model,
    max_tokens: int = 2048,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    splited_docs: List[str] = []
    splited_metadatas: List[Dict[str, Any]] = []

    try:
        loader = DirectoryLoader(
            root,
            silent_errors=True,
            recursive=recursive,
            exclude=["**/node_modules/**", "**/*.ai.json"],
        )
        docs = loader.load()
    except Exception as e:
        logger.error(f"Directory loading failed: {e}")
        return [], []

    ai_metadata = load_ai_json_metadata(root)

    for doc in docs:
        real_path = os.path.abspath(
            doc.metadata.get("source", doc.metadata.get("file_path", ""))
        )
        if real_path in ai_metadata:
            doc.metadata.update(ai_metadata[real_path])
        doc.metadata["source"] = doc.metadata["source"].strip(".txt")

    for doc in docs:
        file_name: str = doc.metadata["source"]
        language = None
        file_type = "text"
        if ".cpp" in file_name or ".h" in file_name:
            file_type = "cpp"
            language = Language.CPP
        elif ".js" in file_name:
            file_type = "js"
            language = Language.JS
        elif ".ts" in file_name:
            file_type = "ts"
            language = Language.TS
        elif ".py" in file_name:
            file_type = "py"
            language = Language.PYTHON

        # Dynamic chunk size
        _chunk_size = chunk_size or get_dynamic_chunk_size(
            model, max_tokens, doc.page_content[:2000]
        )

        splitter = (
            code_splitter(language, chunk_size=_chunk_size, chunk_overlap=chunk_overlap)
            if language
            else text_splitter(chunk_size=_chunk_size, chunk_overlap=chunk_overlap)
        )

        try:
            splits = splitter.split_text(doc.page_content)
        except Exception as e:
            logger.error(f"Text splitting failed for {file_name}: {e}")
            continue

        for index, split in enumerate(splits):
            if not split.strip():
                continue
            chunk_metadata = {
                "file_path": file_name,
                "file_name": os.path.basename(file_name),
                "file_type": file_type,
                "chunk_index": index,
                "total_chunks": len(splits),
            }
            splited_docs.append(split)
            splited_metadatas.append(chunk_metadata)
            if save_path:
                try:
                    split_file_path = os.path.join(save_path, f"split_{index}.txt")
                    with open(split_file_path, "w") as split_file:
                        split_file.write(split)
                except Exception as e:
                    logger.error(f"Failed to save split: {e}")

    return splited_docs, splited_metadatas


def prepare_file(
    file: str,
    save_path: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: int = config.text_processing.indexer_chunk_overlap,
    model: str = config.indexer.embedding_model,
    max_tokens: int = 2048,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    splited_docs: List[str] = []
    splited_metadatas: List[Dict[str, Any]] = []
    file_name: str = os.path.basename(file)
    language = None
    file_type = "text"
    if ".h" in file_name or ".cpp" in file_name:
        file_type = "cpp"
        language = Language.CPP
    elif ".js" in file_name:
        file_type = "js"
        language = Language.JS
    elif ".ts" in file_name:
        file_type = "ts"
        language = Language.TS
    elif ".py" in file_name:
        file_type = "py"
        language = Language.PYTHON

    try:
        with open(file, "r") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file}: {e}")
        return [], []

    _chunk_size = chunk_size or get_dynamic_chunk_size(
        model, max_tokens, content[:2000]
    )

    splitter = (
        code_splitter(language, chunk_size=_chunk_size, chunk_overlap=chunk_overlap)
        if language
        else text_splitter(chunk_size=_chunk_size, chunk_overlap=chunk_overlap)
    )

    try:
        splits = splitter.split_text(content)
    except Exception as e:
        logger.error(f"Text splitting failed for {file_name}: {e}")
        return [], []

    for index, split in enumerate(splits):
        if not split.strip():
            continue
        chunk_metadata = {
            "file_name": file_name,
            "file_path": file,
            "file_type": file_type,
            "chunk_index": index,
            "total_chunks": len(splits),
        }
        splited_docs.append(split)
        splited_metadatas.append(chunk_metadata)
        if save_path:
            try:
                split_file_path = os.path.join(save_path, f"split_{index}.txt")
                with open(split_file_path, "w") as split_file:
                    split_file.write(split)
            except Exception as e:
                logger.error(f"Failed to save split: {e}")

    return splited_docs, splited_metadatas


# --- BaseIndexClient ---


class BaseIndexClient:
    storage_type: str = "local"
    id: str = ""
    name: str = ""
    version: str = ""
    splited_docs: List[str] = []
    splited_metadatas: List[Dict[str, Any]] = []
    _chroma_client: Optional[chromadb.ClientAPI] = None
    _collection: Optional[chromadb.Collection] = None
    _embedder: Optional[OpenAIEmbeddings] = None
    _collection_name: str = ""

    def __init__(
        self,
        storage_type: str,
        id: str,
        dir: str,
        name: str,
        version: str = "v1",
    ) -> None:
        self.storage_type = storage_type
        self.id = id
        self.name = name
        self.version = version
        self.base_path: str = os.path.join(basedir, dir)
        self.name_path: str = os.path.join(self.base_path, self.name)
        self.name_source_path: str = os.path.join(self.name_path, f"{self.name}-source")
        self.name_version_path: str = os.path.join(
            self.base_path, f"{self.name}-{self.version}"
        )
        os.makedirs(self.name_version_path, exist_ok=True)
        self.splited_docs: List[str] = []
        self.splited_metadatas: List[Dict[str, Any]] = []
        self._collection_name = f"{self.name}_{self.version}".replace("-", "_")

        # Initialize embedder
        self._embedder = OpenAIEmbeddings(
            openai_api_key=config.llm.openai_api_key,
            model=config.indexer.embedding_model,
            chunk_size=config.text_processing.indexer_chunk_size,
        )

        if self.storage_type == "gcs":
            self.storage_client: GCPStorageClient = GCPStorageClient().add_client()
            self.bucket: Bucket = self.storage_client.init_bucket(config.indexer.gcp_index_bucket)
            # For GCS, use ephemeral client initially (in-memory)
            self._chroma_client = chromadb.EphemeralClient()
        else:
            # For local, persist to disk - ChromaDB handles concurrent access properly
            self._chroma_client = chromadb.PersistentClient(
                path=self.name_version_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )

    def copy(self, source: str, destination: str, is_dir: bool = False):
        try:
            if is_dir:
                shutil.copytree(source, destination, dirs_exist_ok=True)
            else:
                shutil.copyfile(source, destination)
        except Exception as e:
            logger.error(f"Copy failed: {e}")

    def _build_from_dirs(
        self,
        source: str,
        dirs: List[str],
        include_root: bool,
        chunk_size: Optional[int] = None,
        chunk_overlap: int = config.text_processing.indexer_chunk_overlap,
        model: str = config.indexer.embedding_model,
        max_tokens: int = 2048,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        _splitted_docs: List[str] = []
        _splited_metadatas: List[Dict[str, Any]] = []
        for dir in dirs:
            splited_docs, splited_metadatas = prepare_dir(
                dir,
                self.name_version_path,
                True,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                model=model,
                max_tokens=max_tokens,
            )
            _splitted_docs.extend(splited_docs)
            _splited_metadatas.extend(splited_metadatas)
        return _splitted_docs, _splited_metadatas

    def _build_from_files(
        self,
        file_paths: List[str],
        chunk_size: Optional[int] = None,
        chunk_overlap: int = config.text_processing.indexer_chunk_overlap,
        model: str = config.indexer.embedding_model,
        max_tokens: int = 2048,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        _splitted_docs: List[str] = []
        _splited_metadatas: List[Dict[str, Any]] = []
        for file_path in file_paths:
            splited_docs, splited_metadatas = prepare_file(
                file_path,
                self.name_version_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                model=model,
                max_tokens=max_tokens,
            )
            _splitted_docs.extend(splited_docs)
            _splited_metadatas.extend(splited_metadatas)
        return _splitted_docs, _splited_metadatas

    def store_from_docs(
        self,
        splited_docs: List[str],
        splited_metadatas: List[Dict[str, Any]],
        model: str = config.indexer.embedding_model,
        chunk_size: Optional[int] = None,
    ) -> bool:
        """
        Create or update ChromaDB collection from documents.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not splited_docs:
                logger.warning("No documents to store")
                return False

            # Get or create collection
            try:
                self._collection = self._chroma_client.get_or_create_collection(
                    name=self._collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.debug(f"Using collection {self._collection_name}")
            except Exception as e:
                logger.error(f"Failed to get/create collection: {e}")
                return False

            # Generate embeddings for all documents
            logger.debug(f"Generating embeddings for {len(splited_docs)} documents")
            embeddings = self._embedder.embed_documents(splited_docs)

            # Prepare data for ChromaDB
            ids = [str(uuid.uuid4()) for _ in range(len(splited_docs))]

            # ChromaDB requires metadata to be Dict[str, Union[str, int, float, bool]]
            # Add page_content to metadata since ChromaDB stores documents separately
            metadatas = []
            for doc, metadata in zip(splited_docs, splited_metadatas):
                # Ensure all metadata values are JSON-serializable primitives
                clean_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        clean_metadata[key] = value
                    else:
                        clean_metadata[key] = str(value)
                metadatas.append(clean_metadata)

            # Batch add documents
            batch_size = 100
            for i in range(0, len(splited_docs), batch_size):
                batch_end = min(i + batch_size, len(splited_docs))
                self._collection.add(
                    ids=ids[i:batch_end],
                    embeddings=embeddings[i:batch_end],
                    documents=splited_docs[i:batch_end],
                    metadatas=metadatas[i:batch_end]
                )
                logger.debug(
                    f"Added batch {i // batch_size + 1}/{(len(splited_docs) + batch_size - 1) // batch_size}"
                )

            logger.info(
                f"Successfully stored {len(splited_docs)} documents in collection {self._collection_name}"
            )
            return True

        except Exception as e:
            logger.error(f"ChromaDB store creation failed: {e}")
            return False

    def save(self) -> bool:
        """
        Save ChromaDB collection.
        For local: Already persisted to disk automatically by ChromaDB
        For GCS: Create tarball and upload to GCS
        """
        try:
            if self.storage_type == "local":
                # ChromaDB PersistentClient automatically persists
                logger.debug(f"Collection {self._collection_name} persisted locally at {self.name_version_path}")
                return True

            elif self.storage_type == "gcs":
                # For GCS, we need to persist to a temp directory, tar it, and upload
                temp_dir = tempfile.mkdtemp()
                temp_chroma_path = os.path.join(temp_dir, "chroma")

                try:
                    # Create a persistent client to save data
                    temp_client = chromadb.PersistentClient(
                        path=temp_chroma_path,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=False
                        )
                    )

                    # Get collection data from ephemeral client
                    collection_data = self._collection.get(
                        include=["embeddings", "documents", "metadatas"]
                    )

                    # Create collection in temp persistent client
                    temp_collection = temp_client.get_or_create_collection(
                        name=self._collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )

                    # Add all data to temp collection
                    if collection_data["ids"]:
                        temp_collection.add(
                            ids=collection_data["ids"],
                            embeddings=collection_data["embeddings"],
                            documents=collection_data["documents"],
                            metadatas=collection_data["metadatas"]
                        )

                    # Create tarball of ChromaDB directory
                    import tarfile
                    tarball_path = os.path.join(temp_dir, "chroma.tar.gz")
                    with tarfile.open(tarball_path, "w:gz") as tar:
                        tar.add(temp_chroma_path, arcname="chroma")

                    # Upload tarball to GCS
                    blob: Blob = self.bucket.blob(
                        f"{self.name}/{self.version}/chroma.tar.gz"
                    )
                    blob.upload_from_filename(tarball_path)

                    logger.info(
                        f"Uploaded collection {self._collection_name} to GCS with {len(collection_data['ids'])} documents"
                    )
                    return True
                finally:
                    # Clean up temp directory
                    shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            logger.error(f"Failed to save ChromaDB collection: {e}")
            return False

    def load(self) -> bool:
        """
        Load ChromaDB collection from storage.
        For local: Check if collection exists (already loaded by persistent client)
        For GCS: Download tarball and restore collection data

        Returns:
            True if collection exists and is loaded, False otherwise
        """
        try:
            if self.storage_type == "local":
                # Check if collection exists
                try:
                    self._collection = self._chroma_client.get_collection(
                        name=self._collection_name
                    )
                    count = self._collection.count()
                    logger.info(
                        f"Loaded existing collection {self._collection_name} with {count} documents"
                    )
                    return True
                except Exception:
                    # Collection doesn't exist yet - fresh start
                    logger.info(
                        f"Starting fresh collection {self._collection_name} at {self.name_version_path} (Progressive RAG)"
                    )
                    return False

            elif self.storage_type == "gcs":
                # Download from GCS
                blob: Blob = self.bucket.blob(f"{self.name}/{self.version}/chroma.tar.gz")

                try:
                    # Download tarball to temp directory
                    temp_dir = tempfile.mkdtemp()
                    tarball_path = os.path.join(temp_dir, "chroma.tar.gz")
                    blob.download_to_filename(tarball_path)

                    # Extract tarball
                    import tarfile
                    with tarfile.open(tarball_path, "r:gz") as tar:
                        tar.extractall(temp_dir)

                    # Load from extracted directory
                    chroma_path = os.path.join(temp_dir, "chroma")
                    temp_client = chromadb.PersistentClient(
                        path=chroma_path,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=False
                        )
                    )

                    # Get collection from downloaded data
                    temp_collection = temp_client.get_collection(name=self._collection_name)
                    collection_data = temp_collection.get(
                        include=["embeddings", "documents", "metadatas"]
                    )

                    # Load into ephemeral client
                    self._collection = self._chroma_client.get_or_create_collection(
                        name=self._collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )

                    if collection_data["ids"]:
                        self._collection.add(
                            ids=collection_data["ids"],
                            embeddings=collection_data["embeddings"],
                            documents=collection_data["documents"],
                            metadatas=collection_data["metadatas"]
                        )

                    logger.info(
                        f"Loaded collection {self._collection_name} from GCS with {len(collection_data['ids'])} documents"
                    )

                    # Clean up temp directory
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return True

                except Exception as e:
                    # Collection doesn't exist in GCS yet
                    logger.info(
                        f"Starting fresh collection {self._collection_name} in GCS (Progressive RAG): {e}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to load ChromaDB collection: {e}")
            return False

    def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: Optional[int] = None,
        chunk_overlap: int = config.text_processing.indexer_chunk_overlap,
        model: str = config.indexer.embedding_model,
        max_tokens: int = 2048,
    ) -> bool:
        """
        Add a single document to the Qdrant collection (progressive indexing).

        Args:
            content: Document content
            metadata: Document metadata
            chunk_size: Optional chunk size for splitting
            chunk_overlap: Overlap between chunks
            model: Embedding model to use
            max_tokens: Maximum tokens per chunk

        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine file type from metadata
            file_path = metadata.get("source", "")
            language = metadata.get("language", "unknown")
            file_type = "text"
            language_enum = None

            # Map language to LangChain Language enum
            if language in ["cpp", "c"]:
                file_type = "cpp"
                language_enum = Language.CPP
            elif language == "javascript":
                file_type = "js"
                language_enum = Language.JS
            elif language == "typescript":
                file_type = "ts"
                language_enum = Language.TS
            elif language == "python":
                file_type = "py"
                language_enum = Language.PYTHON

            # Get dynamic chunk size
            _chunk_size = chunk_size or get_dynamic_chunk_size(
                model, max_tokens, content[:2000] if len(content) > 2000 else content
            )

            # Choose splitter based on language
            splitter = (
                code_splitter(
                    language_enum, chunk_size=_chunk_size, chunk_overlap=chunk_overlap
                )
                if language_enum
                else text_splitter(chunk_size=_chunk_size, chunk_overlap=chunk_overlap)
            )

            # Split content into chunks
            splits = splitter.split_text(content)

            # Create chunk metadata
            splited_docs = []
            splited_metadatas = []
            for index, split in enumerate(splits):
                if not split.strip():
                    continue

                chunk_metadata = {
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "file_type": file_type,
                    "chunk_index": index,
                    "total_chunks": len(splits),
                }
                # Merge with original metadata
                chunk_metadata.update(metadata)

                splited_docs.append(split)
                splited_metadatas.append(chunk_metadata)

            # Ensure collection exists
            collection_exists = self.load()

            if not collection_exists:
                # Create collection first
                self._collection = self._chroma_client.get_or_create_collection(
                    name=self._collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new collection {self._collection_name}")

            # Generate embeddings
            embeddings = self._embedder.embed_documents(splited_docs)

            # Prepare metadata for ChromaDB
            ids = [str(uuid.uuid4()) for _ in range(len(splited_docs))]
            clean_metadatas = []
            for metadata_dict in splited_metadatas:
                clean_metadata = {}
                for key, value in metadata_dict.items():
                    if isinstance(value, (str, int, float, bool)):
                        clean_metadata[key] = value
                    else:
                        clean_metadata[key] = str(value)
                clean_metadatas.append(clean_metadata)

            # Add to collection
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=splited_docs,
                metadatas=clean_metadatas
            )

            logger.debug(f"Added {len(splited_docs)} chunks to collection {self._collection_name}")

            # Save if using GCS
            if self.storage_type == "gcs":
                self.save()

            return True

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False

    def search(
        self,
        query: str,
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search the ChromaDB collection for similar documents with native metadata filtering.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            filter_metadata: Optional metadata filters (e.g., {"file_type": "py", "directory": "/path/to/dir"})
                           ChromaDB natively filters BEFORE similarity search - efficient!

        Returns:
            List of documents with metadata and scores
        """
        try:
            # Check if collection exists
            collection_exists = self.load()
            if not collection_exists:
                # No collection available - return empty results (normal during progressive RAG)
                logger.debug(
                    "No collection available for search yet (returning empty results)"
                )
                return []

            # Generate query embedding
            query_embedding = self._embedder.embed_query(query)

            # Build ChromaDB where filter from metadata
            where_filter = None
            if filter_metadata:
                # ChromaDB uses simple dict filters: {"field": "value"} or {"$and": [{...}, {...}]}
                if len(filter_metadata) == 1:
                    where_filter = filter_metadata
                else:
                    # Multiple conditions - use $and
                    where_filter = {
                        "$and": [{k: v} for k, v in filter_metadata.items()]
                    }

            # Perform similarity search with native filtering
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter,  # Native filtering!
                include=["documents", "metadatas", "distances"]
            )

            logger.debug(
                f"Found {len(results['ids'][0])} results for query"
                + (f" with filters {filter_metadata}" if filter_metadata else "")
            )

            # Convert results to expected format
            documents = []
            if results['ids'][0]:  # Check if we have results
                for doc, metadata, distance in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    # ChromaDB returns distance (lower is better), convert to similarity score
                    # For cosine distance, similarity = 1 - distance
                    score = 1.0 - distance if distance is not None else 0.0

                    documents.append({
                        "page_content": doc,
                        "metadata": metadata,
                        "score": float(score),
                    })

            logger.debug(f"Returning {len(documents)} documents")
            return documents

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
