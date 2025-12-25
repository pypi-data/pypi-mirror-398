#!/usr/bin/env python
# coding: utf-8

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import Language

from athenah_ai.config import config


def code_splitter(
    language: Language = Language.CPP, chunk_size: int = None, chunk_overlap: int = None
) -> RecursiveCharacterTextSplitter:
    chunk_size = chunk_size if chunk_size is not None else config.text_processing.default_chunk_size
    chunk_overlap = chunk_overlap if chunk_overlap is not None else config.text_processing.default_chunk_overlap
    return RecursiveCharacterTextSplitter.from_language(
        language,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )


def text_splitter(
    chunk_size: int = None, chunk_overlap: int = None
) -> RecursiveCharacterTextSplitter:
    chunk_size = chunk_size if chunk_size is not None else config.text_processing.default_chunk_size
    chunk_overlap = chunk_overlap if chunk_overlap is not None else config.text_processing.default_chunk_overlap
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
