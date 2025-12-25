#!/usr/bin/env python
# file_handler.py - File processing and code analysis utilities

import os
import base64
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredPDFLoader,
    CSVLoader,
    TextLoader,
    UnstructuredImageLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
)

from athenah_ai.logger import logger


class FileType(Enum):
    """Enum for supported file types."""

    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    CSV = "csv"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    JSON = "json"
    CODE = "code"
    MARKDOWN = "markdown"
    XML = "xml"
    YAML = "yaml"


class FileHandler:
    """Handles file processing for different file types."""

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        ".pdf": FileType.PDF,
        ".txt": FileType.TEXT,
        ".csv": FileType.CSV,
        ".docx": FileType.DOCX,
        ".pptx": FileType.PPTX,
        ".xlsx": FileType.XLSX,
        ".json": FileType.JSON,
        ".png": FileType.IMAGE,
        ".jpg": FileType.IMAGE,
        ".jpeg": FileType.IMAGE,
        ".gif": FileType.IMAGE,
        ".bmp": FileType.IMAGE,
        ".tiff": FileType.IMAGE,
        ".webp": FileType.IMAGE,
        # Code files
        ".py": FileType.CODE,
        ".js": FileType.CODE,
        ".ts": FileType.CODE,
        ".jsx": FileType.CODE,
        ".tsx": FileType.CODE,
        ".java": FileType.CODE,
        ".c": FileType.CODE,
        ".cpp": FileType.CODE,
        ".cc": FileType.CODE,
        ".cxx": FileType.CODE,
        ".h": FileType.CODE,
        ".hpp": FileType.CODE,
        ".cs": FileType.CODE,
        ".php": FileType.CODE,
        ".rb": FileType.CODE,
        ".go": FileType.CODE,
        ".rs": FileType.CODE,
        ".swift": FileType.CODE,
        ".kt": FileType.CODE,
        ".scala": FileType.CODE,
        ".r": FileType.CODE,
        ".m": FileType.CODE,
        ".sql": FileType.CODE,
        ".sh": FileType.CODE,
        ".bash": FileType.CODE,
        ".zsh": FileType.CODE,
        ".fish": FileType.CODE,
        ".ps1": FileType.CODE,
        ".bat": FileType.CODE,
        ".cmd": FileType.CODE,
        ".html": FileType.CODE,
        ".htm": FileType.CODE,
        ".css": FileType.CODE,
        ".scss": FileType.CODE,
        ".sass": FileType.CODE,
        ".less": FileType.CODE,
        ".vue": FileType.CODE,
        ".svelte": FileType.CODE,
        ".dart": FileType.CODE,
        ".lua": FileType.CODE,
        ".pl": FileType.CODE,
        ".pm": FileType.CODE,
        ".tcl": FileType.CODE,
        ".vb": FileType.CODE,
        ".vbs": FileType.CODE,
        ".f": FileType.CODE,
        ".f90": FileType.CODE,
        ".f95": FileType.CODE,
        ".for": FileType.CODE,
        ".asm": FileType.CODE,
        ".s": FileType.CODE,
        ".lisp": FileType.CODE,
        ".cl": FileType.CODE,
        ".scm": FileType.CODE,
        ".clj": FileType.CODE,
        ".cljs": FileType.CODE,
        ".elm": FileType.CODE,
        ".hs": FileType.CODE,
        ".ml": FileType.CODE,
        ".mli": FileType.CODE,
        ".fs": FileType.CODE,
        ".fsx": FileType.CODE,
        ".erl": FileType.CODE,
        ".hrl": FileType.CODE,
        ".ex": FileType.CODE,
        ".exs": FileType.CODE,
        ".jl": FileType.CODE,
        ".nim": FileType.CODE,
        ".cr": FileType.CODE,
        ".zig": FileType.CODE,
        ".v": FileType.CODE,
        ".mod": FileType.CODE,
        ".sum": FileType.CODE,
        ".toml": FileType.CODE,
        ".cfg": FileType.CODE,
        ".ini": FileType.CODE,
        ".conf": FileType.CODE,
        ".config": FileType.CODE,
        ".env": FileType.CODE,
        ".dockerfile": FileType.CODE,
        ".makefile": FileType.CODE,
        ".cmake": FileType.CODE,
        ".gradle": FileType.CODE,
        ".maven": FileType.CODE,
        ".sbt": FileType.CODE,
        ".gemfile": FileType.CODE,
        ".podfile": FileType.CODE,
        ".package": FileType.CODE,
        ".lock": FileType.CODE,
        ".gitignore": FileType.CODE,
        ".gitattributes": FileType.CODE,
        ".editorconfig": FileType.CODE,
        ".eslintrc": FileType.CODE,
        ".prettierrc": FileType.CODE,
        ".babelrc": FileType.CODE,
        ".tsconfig": FileType.CODE,
        ".jsconfig": FileType.CODE,
        ".webpack": FileType.CODE,
        ".vite": FileType.CODE,
        ".rollup": FileType.CODE,
        ".postcss": FileType.CODE,
        ".tailwind": FileType.CODE,
        # Documentation and markup
        ".md": FileType.MARKDOWN,
        ".markdown": FileType.MARKDOWN,
        ".rst": FileType.MARKDOWN,
        ".adoc": FileType.MARKDOWN,
        ".asciidoc": FileType.MARKDOWN,
        ".org": FileType.MARKDOWN,
        ".tex": FileType.MARKDOWN,
        ".latex": FileType.MARKDOWN,
        # Data formats
        ".xml": FileType.XML,
        ".xsd": FileType.XML,
        ".xsl": FileType.XML,
        ".xslt": FileType.XML,
        ".svg": FileType.XML,
        ".yaml": FileType.YAML,
        ".yml": FileType.YAML,
        ".jsonl": FileType.JSON,
        ".ndjson": FileType.JSON,
    }

    # Programming language detection
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".php": "php",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".m": "objective-c",
        ".sql": "sql",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".fish": "fish",
        ".ps1": "powershell",
        ".bat": "batch",
        ".cmd": "batch",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".vue": "vue",
        ".svelte": "svelte",
        ".dart": "dart",
        ".lua": "lua",
        ".pl": "perl",
        ".pm": "perl",
        ".tcl": "tcl",
        ".vb": "vbnet",
        ".vbs": "vbscript",
        ".f": "fortran",
        ".f90": "fortran",
        ".f95": "fortran",
        ".for": "fortran",
        ".asm": "assembly",
        ".s": "assembly",
        ".lisp": "lisp",
        ".cl": "common-lisp",
        ".scm": "scheme",
        ".clj": "clojure",
        ".cljs": "clojurescript",
        ".elm": "elm",
        ".hs": "haskell",
        ".ml": "ocaml",
        ".mli": "ocaml",
        ".fs": "fsharp",
        ".fsx": "fsharp",
        ".erl": "erlang",
        ".hrl": "erlang",
        ".ex": "elixir",
        ".exs": "elixir",
        ".jl": "julia",
        ".nim": "nim",
        ".cr": "crystal",
        ".zig": "zig",
        ".v": "vlang",
        ".toml": "toml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".xml": "xml",
        ".json": "json",
        ".dockerfile": "dockerfile",
        ".makefile": "makefile",
        ".cmake": "cmake",
        ".md": "markdown",
        ".markdown": "markdown",
        ".rst": "restructuredtext",
        ".tex": "latex",
        ".latex": "latex",
    }

    @staticmethod
    def get_file_type(file_path: str) -> Optional[FileType]:
        """Get the file type based on the file extension."""
        ext = Path(file_path).suffix.lower()

        # Handle special cases for files without extensions
        filename = Path(file_path).name.lower()
        if filename in [
            "dockerfile",
            "makefile",
            "gemfile",
            "podfile",
            "rakefile",
            "vagrantfile",
        ]:
            return FileType.CODE
        if filename.startswith("."):
            # Common dotfiles
            if filename in [
                ".gitignore",
                ".gitattributes",
                ".dockerignore",
                ".eslintrc",
                ".prettierrc",
                ".babelrc",
                ".editorconfig",
                ".env",
                ".env.local",
                ".env.development",
                ".env.production",
            ]:
                return FileType.CODE

        return FileHandler.SUPPORTED_EXTENSIONS.get(ext)

    @staticmethod
    def get_programming_language(file_path: str) -> Optional[str]:
        """Get the programming language for a code file."""
        ext = Path(file_path).suffix.lower()
        filename = Path(file_path).name.lower()

        # Handle special cases
        if filename in ["dockerfile"]:
            return "dockerfile"
        if filename in ["makefile", "rakefile"]:
            return "makefile"
        if filename in ["gemfile", "podfile"]:
            return "ruby"
        if filename in ["vagrantfile"]:
            return "ruby"
        if filename.startswith(".eslintrc"):
            return "json"
        if filename.startswith(".prettierrc"):
            return "json"
        if filename.startswith(".babelrc"):
            return "json"
        if filename.endswith("tsconfig.json") or filename.endswith("jsconfig.json"):
            return "json"
        if filename.endswith("package.json") or filename.endswith("package-lock.json"):
            return "json"
        if filename.endswith("composer.json") or filename.endswith("composer.lock"):
            return "json"
        if filename.endswith("cargo.toml") or filename.endswith("cargo.lock"):
            return "toml"
        if filename.endswith("pyproject.toml"):
            return "toml"
        if filename.endswith("requirements.txt") or filename.endswith(
            "requirements-dev.txt"
        ):
            return "text"
        if filename.endswith("poetry.lock"):
            return "toml"
        if filename.endswith("pipfile") or filename.endswith("pipfile.lock"):
            return "toml"
        if filename.endswith(".gitignore") or filename.endswith(".dockerignore"):
            return "gitignore"
        if filename.endswith(".env") or ".env." in filename:
            return "dotenv"

        return FileHandler.LANGUAGE_MAP.get(ext)

    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """Get the MIME type for a file."""
        ext = Path(file_path).suffix.lower()
        file_type = FileHandler.get_file_type(file_path)

        # Code files and text files
        if file_type in [
            FileType.CODE,
            FileType.TEXT,
            FileType.MARKDOWN,
            FileType.XML,
            FileType.YAML,
        ]:
            return "text/plain"

        mime_types = {
            ".pdf": "application/pdf",
            ".csv": "text/csv",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            ".webp": "image/webp",
        }
        return mime_types.get(ext, "text/plain")

    @staticmethod
    def process_file(file_path: str, extract_text: bool = True) -> List[Document]:
        """
        Process a file and return LangChain documents.

        Args:
            file_path (str): Path to the file to process.
            extract_text (bool): Whether to extract text from the file.

        Returns:
            List[Document]: List of processed documents.
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_type = FileHandler.get_file_type(file_path)
        if not file_type:
            raise ValueError(f"Unsupported file type: {Path(file_path).suffix}")

        try:
            if file_type == FileType.PDF:
                loader = PyPDFLoader(file_path)
                return loader.load()

            elif file_type in [
                FileType.TEXT,
                FileType.CODE,
                FileType.MARKDOWN,
                FileType.XML,
                FileType.YAML,
            ]:
                # Handle code files and text files
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Get programming language for syntax highlighting context
                language = FileHandler.get_programming_language(file_path)

                metadata = {
                    "source": file_path,
                    "file_type": file_type.value,
                    "language": language,
                    "file_name": Path(file_path).name,
                    "file_extension": Path(file_path).suffix.lower(),
                    "file_size": len(content),
                    "line_count": len(content.splitlines()),
                }

                # Add syntax highlighting markers for code files
                if file_type == FileType.CODE and language:
                    content = f"```{language}\n{content}\n```"
                    metadata["formatted_content"] = True

                return [Document(page_content=content, metadata=metadata)]

            elif file_type == FileType.CSV:
                loader = CSVLoader(file_path)
                return loader.load()

            elif file_type == FileType.IMAGE:
                if extract_text:
                    loader = UnstructuredImageLoader(file_path)
                    return loader.load()
                else:
                    # Return file info for direct image processing
                    with open(file_path, "rb") as f:
                        content = f.read()
                    return [
                        Document(
                            page_content=f"Image file: {Path(file_path).name}",
                            metadata={
                                "source": file_path,
                                "file_type": "image",
                                "mime_type": FileHandler.get_mime_type(file_path),
                                "file_size": len(content),
                                "base64_data": base64.b64encode(content).decode(
                                    "utf-8"
                                ),
                            },
                        )
                    ]

            elif file_type == FileType.DOCX:
                loader = UnstructuredWordDocumentLoader(file_path)
                return loader.load()

            elif file_type == FileType.PPTX:
                loader = UnstructuredPowerPointLoader(file_path)
                return loader.load()

            elif file_type == FileType.XLSX:
                loader = UnstructuredExcelLoader(file_path)
                return loader.load()

            elif file_type == FileType.JSON:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return [
                    Document(
                        page_content=f"```json\n{content}\n```",
                        metadata={
                            "source": file_path,
                            "file_type": "json",
                            "language": "json",
                            "mime_type": "application/json",
                            "formatted_content": True,
                        },
                    )
                ]

            else:
                raise ValueError(f"Unsupported file type: {file_type}")

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise ValueError(f"Failed to process file: {str(e)}")

    @staticmethod
    def encode_file_for_llm(file_path: str) -> Dict[str, Any]:
        """
        Encode a file for direct LLM processing.

        Args:
            file_path (str): Path to the file.

        Returns:
            Dict[str, Any]: Encoded file data for LLM processing.
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_type = FileHandler.get_file_type(file_path)
        mime_type = FileHandler.get_mime_type(file_path)
        language = FileHandler.get_programming_language(file_path)

        # For text-based files (code, text, etc.), read as text
        if file_type in [
            FileType.CODE,
            FileType.TEXT,
            FileType.MARKDOWN,
            FileType.XML,
            FileType.YAML,
            FileType.JSON,
        ]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                base64_data = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            except Exception as e:
                logger.warning(f"Could not read file as text: {e}")
                with open(file_path, "rb") as f:
                    content = f.read()
                base64_data = base64.b64encode(content).decode("utf-8")
        else:
            # For binary files (images, PDFs, etc.)
            with open(file_path, "rb") as f:
                content = f.read()
            base64_data = base64.b64encode(content).decode("utf-8")

        result = {
            "file_name": Path(file_path).name,
            "file_type": file_type.value if file_type else "unknown",
            "mime_type": mime_type,
            "base64_data": base64_data,
            "file_size": (
                len(content)
                if isinstance(content, bytes)
                else len(content.encode("utf-8"))
            ),
            "file_extension": Path(file_path).suffix.lower(),
        }

        # Add language information for code files
        if language:
            result["language"] = language

        # Add line count for text-based files
        if file_type in [
            FileType.CODE,
            FileType.TEXT,
            FileType.MARKDOWN,
            FileType.XML,
            FileType.YAML,
            FileType.JSON,
        ]:
            if isinstance(content, str):
                result["line_count"] = len(content.splitlines())
            else:
                try:
                    text_content = content.decode("utf-8", errors="ignore")
                    result["line_count"] = len(text_content.splitlines())
                except:
                    pass

        return result
