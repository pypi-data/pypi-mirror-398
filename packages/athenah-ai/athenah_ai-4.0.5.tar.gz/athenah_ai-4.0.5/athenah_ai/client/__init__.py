#!/usr/bin/env python
# athenah_client.py - Main multi-LLM client implementation

import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, TypedDict, Optional, Union
import uuid
import traceback

from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS

# from langchain.chains import create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
from langgraph.graph import START, StateGraph
from langsmith import Client as LangSmithClient
from langchain_core.tools import Tool
from langchain_core.runnables import RunnableConfig

# AgentExecutor removed; we will invoke the created agent directly via agent.invoke()
from langchain.agents import create_agent

# from langchain.memory import ConversationBufferMemory
from langchain_core.documents import Document
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from .llm_adapters import LLMProvider, LLMFactory, BaseLLMAdapter
from athenah_ai.client.file_handler import FileHandler
from athenah_ai.utils.fs import write_json
from athenah_ai.utils.agent import build_agent_tools
from athenah_ai.client.vector_store import VectorStore
from athenah_ai.logger import logger

load_dotenv()


# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


class AthenahClient(VectorStore):
    """
    A client for interacting with multiple LLM providers for chat and RAG functionality.

    Attributes:
        id (str): The ID of the client.
        provider (LLMProvider): The LLM provider to use.
        model_group (str): The model group to use for the chat model.
        custom_model (str): The custom model to use for the chat model.
        version (str): The version of the chat model.
        model_name (str): The name of the chat model.
        temperature (float): The temperature parameter for generating responses.
        max_tokens (int): The maximum number of tokens for generating responses.
        llm_adapter (BaseLLMAdapter): The LLM adapter instance.
        chat_history (ChatMessageHistory): Chat message history for conversation.
        db (FAISS): The FAISS vector store for document retrieval.
    """

    def __init__(
        self,
        id: str,
        provider: Union[LLMProvider, str] = LLMProvider.OPENAI,
        model_group: str = "dist",
        custom_model: str = "",
        version: str = "v1",
        model_name: str = None,
        temperature: float = 0,
        max_tokens: int = 8000,
        **kwargs,
    ):
        """
        Initialize the AthenahClient.

        Args:
            id (str): The ID of the client.
            provider (Union[LLMProvider, str]): The LLM provider to use.
            model_group (str): The model group to use for the chat model.
            custom_model (str): The custom model to use for the chat model.
            version (str): The version of the chat model.
            model_name (str): The name of the chat model.
            temperature (float): The temperature parameter for generating responses.
            max_tokens (int): The maximum number of tokens for generating responses.
            **kwargs: Additional arguments.
        """
        self.id = id
        self.provider = (
            LLMProvider(provider.lower()) if isinstance(provider, str) else provider
        )
        self.model_group = model_group
        self.custom_model = custom_model
        self.version = version
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Create LLM adapter
        self.llm_adapter = LLMFactory.create_adapter(
            self.provider, self.model_name, self.temperature, self.max_tokens
        )

        # Initialize chat history
        self.chat_history = ChatMessageHistory()

        # Initialize parent class
        super().__init__(storage_type="local" if model_group == "dist" else "gcs")

        # Load vector store if custom model is provided
        if self.model_group and self.custom_model:
            self.db = self.load(self.custom_model, self.model_group, self.version)

        # Initialize LangChain LLM
        self.llm = self.llm_adapter.get_langchain_llm()

    def get_token_count(self, text: str) -> int:
        """
        Get the total number of tokens for the given text.

        Args:
            text (str): The text to count tokens for.

        Returns:
            int: The total number of tokens.
        """
        return self.llm_adapter.count_tokens(text)

    def base_prompt(
        self,
        system: str = None,
        prompt: str = None,
        files: List[Union[str, Dict[str, Any]]] = None,
        *args,
    ) -> str:
        """
        Generate a response using the base LLM without RAG, with optional file support.

        Args:
            system (str): The system message.
            prompt (str): The user prompt.
            files (List[Union[str, Dict[str, Any]]]): List of file paths or file data dictionaries.
            *args: Additional message dictionaries.

        Returns:
            str: The generated response.
        """
        try:
            messages: List[Dict[str, str]] = []

            if isinstance(system, str) and system != "":
                messages.append({"role": "system", "content": system})
            if isinstance(prompt, str) and prompt != "":
                messages.append({"role": "user", "content": prompt})

            for arg in args:
                if isinstance(arg, dict):
                    messages.append(arg)

            # Process files if provided
            processed_files = []
            if files:
                for file_item in files:
                    if isinstance(file_item, str):
                        # It's a file path
                        if Path(file_item).exists():
                            file_data = FileHandler.encode_file_for_llm(file_item)
                            processed_files.append(file_data)
                        else:
                            logger.warning(f"File not found: {file_item}")
                    elif isinstance(file_item, dict):
                        # It's already processed file data
                        processed_files.append(file_item)

            return self.llm_adapter.create_completion(
                messages, processed_files if processed_files else None
            )
        except Exception as e:
            raise ValueError(f"Failed to generate a prompt completion: {str(e)}")

    def base_prompt_with_documents(
        self,
        system: str = None,
        prompt: str = None,
        file_paths: List[str] = None,
        extract_text: bool = True,
    ) -> str:
        """
        Generate a response using document content extracted via LangChain loaders.

        Args:
            system (str): The system message.
            prompt (str): The user prompt.
            file_paths (List[str]): List of file paths to process.
            extract_text (bool): Whether to extract text from files.

        Returns:
            str: The generated response.
        """
        try:
            messages: List[Dict[str, str]] = []

            if isinstance(system, str) and system != "":
                messages.append({"role": "system", "content": system})

            # Process files and extract content
            document_content = ""
            if file_paths:
                for file_path in file_paths:
                    try:
                        documents = FileHandler.process_file(file_path, extract_text)
                        for doc in documents:
                            document_content += (
                                f"\n\n--- Document: {Path(file_path).name} ---\n"
                            )
                            document_content += doc.page_content
                            document_content += "\n--- End Document ---\n"
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")

            # Combine prompt with document content
            full_prompt = prompt
            if document_content:
                full_prompt = f"{prompt}\n\nDocument Content:{document_content}"

            if isinstance(full_prompt, str) and full_prompt != "":
                messages.append({"role": "user", "content": full_prompt})

            return self.llm_adapter.create_completion(messages)
        except Exception as e:
            raise ValueError(f"Failed to generate a prompt completion: {str(e)}")

    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """
        Upload a file and return its metadata.

        Args:
            file_path (str): Path to the file to upload.

        Returns:
            Dict[str, Any]: File metadata including encoded data.
        """
        return FileHandler.encode_file_for_llm(file_path)

    def process_file_to_documents(
        self, file_path: str, extract_text: bool = True
    ) -> List[Document]:
        """
        Process a file and return LangChain documents.

        Args:
            file_path (str): Path to the file to process.
            extract_text (bool): Whether to extract text from the file.

        Returns:
            List[Document]: List of processed documents.
        """
        return FileHandler.process_file(file_path, extract_text)

    def chat_with_files(
        self,
        prompt: str,
        file_paths: List[str] = None,
        system_message: str = None,
        use_document_extraction: bool = True,
    ) -> str:
        """
        Chat with the LLM using files as context.

        Args:
            prompt (str): The user prompt.
            file_paths (List[str]): List of file paths to include.
            system_message (str): Optional system message.
            use_document_extraction (bool): Whether to use document extraction or direct file upload.

        Returns:
            str: The generated response.
        """
        if not file_paths:
            return self.base_prompt(system_message, prompt)

        if use_document_extraction:
            # Use LangChain document loaders to extract text
            return self.base_prompt_with_documents(system_message, prompt, file_paths)
        else:
            # Use direct file upload (better for images, supports multimodal)
            return self.base_prompt(system_message, prompt, file_paths)

    def chat_with_directory(
        self,
        prompt: str,
        directory_path: str,
        max_files: int = 50,
        system_message: str = None,
    ) -> str:
        """
        Chat with the LLM about a directory/codebase.

        Args:
            prompt (str): The user prompt.
            directory_path (str): Path to the directory to analyze.
            max_files (int): Maximum number of files to analyze from directory.
            system_message (str): Optional system message.

        Returns:
            str: The generated response.
        """
        # Analyze directory and create summary
        codebase_summary = self.analyze_codebase(directory_path, max_files)
        full_prompt = f"{prompt}\n\n{codebase_summary}"

        # Use a code-focused system message if none provided
        if not system_message:
            system_message = """You are an expert software developer and code analyst. You can:
- Analyze code structure and architecture
- Identify bugs and potential issues
- Suggest improvements and optimizations
- Explain code functionality
- Help with refactoring and debugging
- Provide best practices and coding standards advice
- Generate documentation and comments
- Convert code between programming languages

Please provide detailed, technical responses with code examples when relevant."""

        return self.base_prompt(system_message, full_prompt)

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported programming languages.

        Returns:
            List[str]: List of supported programming languages.
        """
        return sorted(set(FileHandler.LANGUAGE_MAP.values()))

    def get_code_extensions(self) -> List[str]:
        """
        Get list of supported code file extensions.

        Returns:
            List[str]: List of supported code file extensions.
        """
        return [
            ext
            for ext, file_type in FileHandler.SUPPORTED_EXTENSIONS.items()
            if file_type.value == "code"
        ]

    def get_supported_file_types(self) -> List[str]:
        """
        Get list of supported file types.

        Returns:
            List[str]: List of supported file extensions.
        """
        return list(FileHandler.SUPPORTED_EXTENSIONS.keys())

    def prompt(self, prompt: str) -> str:
        """
        Generate a response using RAG (Retrieval-Augmented Generation).

        Args:
            prompt (str): The prompt to generate a response to.

        Returns:
            str: The generated response.
        """
        if not self.db:
            raise ValueError(
                "Vector store not initialized. Cannot use RAG functionality."
            )

        try:
            # Update LLM instance
            self.llm = self.llm_adapter.get_langchain_llm()

            num_indexes = len(self.db.index_to_docstore_id)
            logger.debug(f"DB INDEXES: {num_indexes}")

            # Pull RAG prompt from hub using LangSmith
            langsmith_client = LangSmithClient()
            rag_prompt = langsmith_client.pull_prompt("rlm/rag-prompt")

            def retrieve(state: State):
                retrieved_docs = self.db.similarity_search(state["question"])
                return {"context": retrieved_docs}

            def generate(state: State):
                docs_content = "\n\n".join(doc.page_content for doc in state["context"])
                messages = rag_prompt.invoke(
                    {"question": state["question"], "context": docs_content}
                )
                response = self.llm.invoke(messages)
                return {"answer": response.content}

            # Create and run the graph
            graph_builder = StateGraph(State).add_sequence([retrieve, generate])
            graph_builder.add_edge(START, "retrieve")
            graph = graph_builder.compile()

            response = graph.invoke({"question": prompt})
            return response["answer"]

        except Exception as e:
            logger.error(f"Error in RAG prompt: {e}")
            raise ValueError(f"Failed to generate RAG response: {str(e)}")

    def rag_prompt_v2(
        self, system_prompt: str, user_prompt: str, *args: Dict[str, str]
    ) -> str:
        """
        Generate a response using RAG with custom system and user prompts.

        Args:
            system_prompt (str): The system message.
            user_prompt (str): The user prompt.
            *args: Additional message dictionaries.

        Returns:
            str: The generated response.
        """
        if not self.db:
            raise ValueError(
                "Vector store not initialized. Cannot use RAG functionality."
            )

        try:
            # Prepare messages
            messages = []
            messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

            for value in args:
                messages.append(value)

            # Combine all message content for retrieval
            question_w_system = " ".join([msg["content"] for msg in messages])

            # Update LLM instance
            self.llm = self.llm_adapter.get_langchain_llm()

            # Use RAG with retry logic
            try:
                langsmith_client = LangSmithClient()
                rag_prompt = langsmith_client.pull_prompt("rlm/rag-prompt")

                def retrieve(state: State):
                    retrieved_docs = self.db.similarity_search(state["question"])
                    return {"context": retrieved_docs}

                def generate(state: State):
                    docs_content = "\n\n".join(
                        doc.page_content for doc in state["context"]
                    )
                    messages = rag_prompt.invoke(
                        {"question": state["question"], "context": docs_content}
                    )
                    response = self.llm.invoke(messages)
                    return {"answer": response.content}

                graph_builder = StateGraph(State).add_sequence([retrieve, generate])
                graph_builder.add_edge(START, "retrieve")
                graph = graph_builder.compile()

                response = graph.invoke({"question": question_w_system})
                return response["answer"]

            except Exception as e:
                logger.error(f"RAG attempt failed: {e}. Retrying...")
                raise e

        except Exception as e:
            logger.error(f"Error in RAG prompt v2: {e}")
            raise ValueError(f"Failed to generate RAG response: {str(e)}")

    def agent_prompt(
        self,
        name: str,
        description: str,
        prompt: str,
        tools: List[Tool] = None,
        add_default_tools: bool = True,
        no_temp: bool = False,
    ) -> str:
        try:
            llm = self.llm_adapter.get_langchain_llm()

            # Prepare tools
            all_tools = []
            if tools:
                all_tools.extend(tools)

            if add_default_tools:
                default_tools = []

                if self.custom_model and self.db:
                    logger.info("=== RAG ENABLED: Adding RAG tools to agent ===")
                    logger.info(f"Vector DB has {len(self.db.index_to_docstore_id)} indexed documents")
                    print("Adding RAG tools to agent...")

                    # Wrap methods to avoid type hint inspection issues
                    def similarity_search(query: str) -> str:
                        """Search the knowledge base for relevant information."""
                        logger.info(f"🔍 RAG similarity_search CALLED with query: {query[:100]}...")
                        results = self.db.similarity_search(query)
                        logger.info(f"📚 Retrieved {len(results)} documents from vector store")
                        for i, doc in enumerate(results):
                            logger.debug(f"Document {i+1}: {doc.page_content[:100]}...")
                        return "\n\n".join(doc.page_content for doc in results)

                    def rag_llm(prompt: str) -> str:
                        """Generate a response using the LLM."""
                        response = self.llm.invoke(prompt)
                        return (
                            response.content
                            if hasattr(response, "content")
                            else str(response)
                        )

                    default_tools.append(
                        Tool(
                            name="similarity_search",
                            func=similarity_search,
                            description="Use this tool when you need to look up information from the knowledge base to answer questions. Input should be a fully formed question.",
                        ),
                    )
                    default_tools.append(
                        Tool(
                            name="rag_llm",
                            func=rag_llm,
                            description="Generate a response based on a prompt using the AI LLM.",
                        ),
                    )
                else:
                    logger.warning(f"⚠️  RAG NOT ENABLED - custom_model: {self.custom_model}, db: {self.db is not None}")

                all_tools.extend(default_tools)

            if not all_tools:
                raise ValueError("No tools provided to the agent.")

            # Initialize and run agent
            agent = create_agent(llm, all_tools, debug=False)

            logger.info(f"🤖 Invoking agent with {len(all_tools)} tools")
            logger.info(f"Available tools: {[tool.name for tool in all_tools]}")
            print("Invoking agent with prompt...")
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            result = agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]}, config=config
            )
            logger.info(f"✅ Agent invocation completed")

            # Extract response
            if (
                isinstance(result, dict)
                and "messages" in result
                and len(result["messages"]) > 0
            ):
                return result["messages"][-1].content
            if isinstance(result, dict) and "output" in result:
                return result["output"]
            return str(result)

        except Exception as e:
            logger.error(f"Error in agent_prompt: {e}")
            return f"Agent failed: {e}"

    def switch_provider(
        self, provider: Union[LLMProvider, str], model_name: str = None
    ) -> None:
        """
        Switch to a different LLM provider.

        Args:
            provider (Union[LLMProvider, str]): The new LLM provider.
            model_name (str, optional): The new model name.
        """
        self.provider = (
            LLMProvider(provider.lower()) if isinstance(provider, str) else provider
        )
        self.model_name = model_name

        # Create new adapter
        self.llm_adapter = LLMFactory.create_adapter(
            self.provider, self.model_name, self.temperature, self.max_tokens
        )

        # Update LangChain LLM
        self.llm = self.llm_adapter.get_langchain_llm()

        logger.info(
            f"Switched to {self.provider.value} with model {self.llm_adapter.model_name}"
        )

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the current LLM provider and model.

        Returns:
            Dict[str, Any]: Provider information.
        """
        return {
            "provider": self.provider.value,
            "model_name": self.llm_adapter.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_model_tokens": self.llm_adapter.get_max_tokens(),
        }
