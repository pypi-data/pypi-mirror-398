# #!/usr/bin/env python
# # coding: utf-8


# import os
# from typing import Dict, Any, List, Tuple, TypedDict

# from dotenv import load_dotenv

# import openai

# from langchain_openai import ChatOpenAI
# from langchain_community.vectorstores import FAISS
# from langchain.chains import create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain

# from langgraph.graph import START, StateGraph
# from langchain import hub
# from athenah_ai.client.vector_store import VectorStore
# from athenah_ai.logger import logger
# from langchain.agents import (
#     AgentType,
#     Tool,
#     initialize_agent,
# )
# from langchain.chains import RetrievalQA
# from langchain.memory import ConversationBufferMemory
# from langchain.chains import ConversationalRetrievalChain
# from langchain_core.documents import Document

# load_dotenv()

# OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY")
# openai.api_key = OPENAI_API_KEY
# OPENAI_API_MODEL: str = "gpt-4.1"

# MODEL_MAP = {
#     "gpt-4o-mini": 16383,
#     "gpt-4o": 4095,
#     "gpt-4-turbo": 4095,
#     "gpt-4": 8191,
#     "gpt-4.1": 32768,
#     "o4-mini": 100000,
# }


# def get_max_tokens(model_name: str) -> int:
#     """
#     Get the maximum number of tokens for a given OpenAI model.

#     Args:
#         model_name (str): The name of the OpenAI model.

#     Returns:
#         int: The maximum number of tokens for the model.
#     """
#     return MODEL_MAP.get(model_name, 4096)  # Default to 4096 if model not found


# def get_token_total(prompt: str) -> int:
#     import tiktoken

#     openai_model = "gpt-4o-mini"
#     encoding = tiktoken.encoding_for_model(openai_model)
#     return len(encoding.encode(prompt))


# # Define state for application
# class State(TypedDict):
#     question: str
#     context: List[Document]
#     answer: str


# class AthenahClient(VectorStore):
#     """
#     A client for interacting with the Athenah AI chat model.

#     Attributes:
#         id (str): The ID of the client.
#         model_group (str): The model group to use for the chat model.
#         custom_model (str): The custom model to use for the chat model.
#         version (str): The version of the chat model.
#         model_name (str): The name of the chat model.
#         temperature (float): The temperature parameter for generating responses.
#         max_tokens (int): The maximum number of tokens for generating responses.
#         top_p (int): The top-p parameter for generating responses.
#         best_of (int): The best-of parameter for generating responses.
#         frequency_penalty (float): The frequency penalty parameter for generating
#         responses.
#         presence_penalty (float): The presence penalty parameter for generating
#         responses.
#         stop (List[str]): The list of stop words for generating responses.
#         has_history (bool): Whether the client has chat history.
#         chat_history (List[str]): The chat history of the client.
#         db (FAISS): The FAISS vector store for document retrieval.
#     """

#     id: str = ""
#     model_group: str = "dist"
#     custom_model: str = ""
#     version: str = "v1"
#     model_name: str = OPENAI_API_MODEL
#     temperature: float = 0
#     max_tokens: int = 600
#     top_p: int = 1
#     best_of: int = 1
#     frequency_penalty: float = 0
#     presence_penalty: float = 0
#     stop: List[str] = []

#     has_history: bool = False
#     chat_history: List[Tuple[str, str]] = []
#     memory: ConversationBufferMemory = None
#     db: FAISS = None
#     llm: ChatOpenAI = None

#     def __init__(
#         cls,
#         id: str,
#         model_group: str = "dist",
#         custom_model: str = "",
#         version: str = "v1",
#         model_name: str = OPENAI_API_MODEL,
#         temperature: float = 0,
#         max_tokens: int = 1200,
#         top_p: int = 1,
#         best_of: int = 3,
#         frequency_penalty: float = 0,
#         presence_penalty: float = 0,
#         stop: List[str] = [],
#     ):
#         cls.id = id
#         cls.model_group = model_group
#         cls.custom_model = custom_model
#         cls.version = version
#         cls.model_name = model_name
#         cls.temperature = temperature
#         cls.max_tokens = max_tokens
#         cls.top_p = top_p
#         cls.best_of = best_of
#         cls.frequency_penalty = frequency_penalty
#         cls.presence_penalty = presence_penalty
#         cls.stop = stop
