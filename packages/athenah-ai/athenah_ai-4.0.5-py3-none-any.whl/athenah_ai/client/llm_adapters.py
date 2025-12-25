#!/usr/bin/env python
# llm_adapters.py - LLM provider adapters and configurations

import os
import base64
import tempfile
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from enum import Enum
from dotenv import load_dotenv

import openai
import anthropic
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_xai import ChatXAI
from langchain_core.language_models.chat_models import BaseChatModel

from athenah_ai.logger import logger
from athenah_ai.config import config

load_dotenv()


class LLMProvider(Enum):
    """Enum for supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    XAI = "xai"
    ODINAI = "odinai"
    # Add other providers as needed
    # GOOGLE = "google"
    # COHERE = "cohere"




class BaseLLMAdapter(ABC):
    """Abstract base class for LLM adapters."""

    def __init__(self, model_name: str, temperature: float = None, max_tokens: int = None):
        self.model_name = model_name
        self.temperature = temperature if temperature is not None else config.llm.default_temperature
        self.max_tokens = max_tokens if max_tokens is not None else config.llm.default_max_tokens
        self.llm = None

    @abstractmethod
    def get_langchain_llm(self) -> BaseChatModel:
        """Get the LangChain LLM instance."""
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        """Get maximum tokens for the model."""
        pass

    @abstractmethod
    def create_completion(
        self, messages: List[Dict[str, str]], files: List[Dict[str, Any]] = None
    ) -> str:
        """Create a completion using the native API."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in the given text."""
        pass


class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI models."""

    def __init__(
        self, model_name: str = None, temperature: float = None, max_tokens: int = None
    ):
        model_name = model_name or config.llm.default_openai_model
        super().__init__(model_name, temperature, max_tokens)
        openai.api_key = config.llm.openai_api_key

    def get_langchain_llm(self) -> ChatOpenAI:
        """Get the LangChain OpenAI LLM instance."""
        # Special handling for reasoning models
        temp = (
            1
            if self.model_name.startswith("o1") or self.model_name.startswith("gpt-5")
            else self.temperature
        )

        original_generate = ChatOpenAI._generate

        def patched_generate(self, messages, stop=None, **kwargs):
            kwargs.pop("stop", None)
            return original_generate(self, messages, **kwargs)

        ChatOpenAI._generate = patched_generate

        return ChatOpenAI(
            openai_api_key=config.llm.openai_api_key,
            model_name=self.model_name,
            temperature=temp,
            max_completion_tokens=self.get_max_tokens(),
            disabled_params={"stop": None},
            stop_sequences=None,
        )

    def get_max_tokens(self) -> int:
        """Get maximum tokens for the OpenAI model."""
        return config.llm.openai_model_map.get(self.model_name, 4096)

    def create_completion(
        self, messages: List[Dict[str, str]], files: List[Dict[str, Any]] = None
    ) -> str:
        """Create a completion using OpenAI API with optional file support."""
        try:
            # Special handling for reasoning models
            temp = (
                1
                if self.model_name.startswith("o1")
                or self.model_name.startswith("gpt-5")
                else self.temperature
            )

            # Add files if provided
            if files:
                for file_data in files:
                    if file_data["file_type"] == "image":
                        # Add image content for the last user message
                        for msg in reversed(messages):
                            if msg["role"] == "user":
                                if isinstance(msg["content"], str):
                                    msg["content"] = [
                                        {"type": "text", "text": msg["content"]},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{file_data['mime_type']};base64,{file_data['base64_data']}"
                                            },
                                        },
                                    ]
                                elif isinstance(msg["content"], list):
                                    msg["content"].append(
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{file_data['mime_type']};base64,{file_data['base64_data']}"
                                            },
                                        }
                                    )
                                break
                    # For other file types, we'll include them as text context
                    elif file_data["file_type"] in ["text", "csv", "json", "code"]:
                        # Decode and add as text context
                        try:
                            decoded_content = base64.b64decode(
                                file_data["base64_data"]
                            ).decode("utf-8")
                            file_context = f"\n\n--- File: {file_data['file_name']} ---\n{decoded_content}\n--- End of File ---\n"

                            # Add to the last user message
                            for msg in reversed(messages):
                                if msg["role"] == "user":
                                    if isinstance(msg["content"], str):
                                        msg["content"] += file_context
                                    elif isinstance(msg["content"], list):
                                        msg["content"].append(
                                            {"type": "text", "text": file_context}
                                        )
                                    break
                        except Exception as e:
                            logger.warning(f"Could not decode file content: {e}")

            response = openai.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                max_completion_tokens=self.max_tokens,
                stop=None,
                n=config.llm.default_n_completions,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"Failed to generate OpenAI completion: {str(e)}")

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model(self.model_name)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4


class OdinAIAdapter(BaseLLMAdapter):
    """Adapter for OdenAI models."""

    def __init__(
        self, model_name: str = None, temperature: float = None, max_tokens: int = None
    ):
        model_name = model_name or config.llm.default_odinai_model
        super().__init__(model_name, temperature, max_tokens)
        openai.api_key = config.llm.odinai_api_key

    def get_langchain_llm(self) -> ChatOpenAI:
        """Get the LangChain OpenAI LLM instance."""

        original_generate = ChatOpenAI._generate

        def patched_generate(self, messages, stop=None, **kwargs):
            kwargs.pop("stop", None)
            return original_generate(self, messages, **kwargs)

        ChatOpenAI._generate = patched_generate

        return ChatOpenAI(
            openai_api_key=config.llm.odinai_api_key,
            base_url="https://api.odin-labs.nl/v1",
            default_headers={
                "User-Agent": "Odin Labs NL SDK/python/0.1.0",
            },
            model_name=self.model_name,
            temperature=self.temperature,
            max_completion_tokens=self.get_max_tokens(),
            # disabled_params={"stop": None},
            # stop_sequences=None,
        )

    def get_max_tokens(self) -> int:
        """Get maximum tokens for the OdinAI model."""
        return config.llm.odinai_model_map.get(self.model_name, 4096)

    def create_completion(
        self, messages: List[Dict[str, str]], files: List[Dict[str, Any]] = None
    ) -> str:
        """Create a completion using OpenAI API with optional file support."""
        try:
            temp = self.temperature

            # Add files if provided
            if files:
                for file_data in files:
                    if file_data["file_type"] == "image":
                        # Add image content for the last user message
                        for msg in reversed(messages):
                            if msg["role"] == "user":
                                if isinstance(msg["content"], str):
                                    msg["content"] = [
                                        {"type": "text", "text": msg["content"]},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{file_data['mime_type']};base64,{file_data['base64_data']}"
                                            },
                                        },
                                    ]
                                elif isinstance(msg["content"], list):
                                    msg["content"].append(
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{file_data['mime_type']};base64,{file_data['base64_data']}"
                                            },
                                        }
                                    )
                                break
                    # For other file types, we'll include them as text context
                    elif file_data["file_type"] in ["text", "csv", "json", "code"]:
                        # Decode and add as text context
                        try:
                            decoded_content = base64.b64decode(
                                file_data["base64_data"]
                            ).decode("utf-8")
                            file_context = f"\n\n--- File: {file_data['file_name']} ---\n{decoded_content}\n--- End of File ---\n"

                            # Add to the last user message
                            for msg in reversed(messages):
                                if msg["role"] == "user":
                                    if isinstance(msg["content"], str):
                                        msg["content"] += file_context
                                    elif isinstance(msg["content"], list):
                                        msg["content"].append(
                                            {"type": "text", "text": file_context}
                                        )
                                    break
                        except Exception as e:
                            logger.warning(f"Could not decode file content: {e}")

            # raise NotImplementedError("OdinAI completion not yet implemented.")
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                max_completion_tokens=self.max_tokens,
                stop=None,
                n=config.llm.default_n_completions,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"Failed to generate OpenAI completion: {str(e)}")

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model(self.model_name)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4


class AnthropicAdapter(BaseLLMAdapter):
    """Adapter for Anthropic Claude models."""

    def __init__(
        self, model_name: str = None, temperature: float = None, max_tokens: int = None
    ):
        model_name = model_name or config.llm.default_anthropic_model
        super().__init__(model_name, temperature, max_tokens)
        self.client = anthropic.Anthropic(api_key=config.llm.anthropic_api_key)

    def get_langchain_llm(self) -> ChatAnthropic:
        """Get the LangChain Anthropic LLM instance."""
        return ChatAnthropic(
            anthropic_api_key=config.llm.anthropic_api_key,
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.get_max_tokens(),
        )

    def get_max_tokens(self) -> int:
        """Get maximum tokens for the Anthropic model."""
        return config.llm.anthropic_model_map.get(self.model_name, 4096)

    def create_completion(
        self, messages: List[Dict[str, str]], files: List[Dict[str, Any]] = None
    ) -> str:
        """Create a completion using Anthropic API with optional file support."""
        try:
            # Convert messages to Anthropic format
            system_message = None
            formatted_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    # Handle different content types
                    if isinstance(msg["content"], str):
                        formatted_messages.append(
                            {"role": msg["role"], "content": msg["content"]}
                        )
                    else:
                        # Support for multimodal content
                        formatted_messages.append(
                            {"role": msg["role"], "content": msg["content"]}
                        )

            # Add files if provided
            if files:
                for file_data in files:
                    if file_data["file_type"] == "image":
                        # Add image content for the last user message
                        if (
                            formatted_messages
                            and formatted_messages[-1]["role"] == "user"
                        ):
                            content = formatted_messages[-1]["content"]
                            if isinstance(content, str):
                                formatted_messages[-1]["content"] = [
                                    {"type": "text", "text": content},
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": file_data["mime_type"],
                                            "data": file_data["base64_data"],
                                        },
                                    },
                                ]
                            elif isinstance(content, list):
                                content.append(
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": file_data["mime_type"],
                                            "data": file_data["base64_data"],
                                        },
                                    }
                                )
                    elif file_data["file_type"] == "pdf":
                        # For PDFs, we'll need to use the Files API
                        # Upload the file first
                        file_id = self._upload_file_to_anthropic(file_data)
                        if (
                            file_id
                            and formatted_messages
                            and formatted_messages[-1]["role"] == "user"
                        ):
                            content = formatted_messages[-1]["content"]
                            if isinstance(content, str):
                                formatted_messages[-1]["content"] = [
                                    {"type": "text", "text": content},
                                    {
                                        "type": "document",
                                        "source": {"type": "file", "file_id": file_id},
                                    },
                                ]
                            elif isinstance(content, list):
                                content.append(
                                    {
                                        "type": "document",
                                        "source": {"type": "file", "file_id": file_id},
                                    }
                                )
                    else:
                        # For other file types, add as text context
                        try:
                            decoded_content = base64.b64decode(
                                file_data["base64_data"]
                            ).decode("utf-8")
                            file_context = f"\n\n--- File: {file_data['file_name']} ---\n{decoded_content}\n--- End of File ---\n"

                            # Add to the last user message
                            if (
                                formatted_messages
                                and formatted_messages[-1]["role"] == "user"
                            ):
                                content = formatted_messages[-1]["content"]
                                if isinstance(content, str):
                                    formatted_messages[-1]["content"] = (
                                        content + file_context
                                    )
                                elif isinstance(content, list):
                                    content.append(
                                        {"type": "text", "text": file_context}
                                    )
                        except Exception as e:
                            logger.warning(f"Could not decode file content: {e}")

            kwargs = {
                "model": self.model_name,
                "messages": formatted_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            if system_message:
                kwargs["system"] = system_message

            # Add beta headers for files API if needed
            if files and any(f["file_type"] == "pdf" for f in files):
                kwargs["extra_headers"] = {"anthropic-beta": "files-api-2025-04-14"}

            response = self.client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            raise ValueError(f"Failed to generate Anthropic completion: {str(e)}")

    def _upload_file_to_anthropic(self, file_data: Dict[str, Any]) -> Optional[str]:
        """Upload a file to Anthropic's Files API."""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{file_data['file_type']}"
            ) as tmp_file:
                tmp_file.write(base64.b64decode(file_data["base64_data"]))
                tmp_file_path = tmp_file.name

            try:
                # Upload the file
                with open(tmp_file_path, "rb") as f:
                    file_response = self.client.beta.files.upload(
                        file=(file_data["file_name"], f, file_data["mime_type"])
                    )
                return file_response.id
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)
        except Exception as e:
            logger.error(f"Error uploading file to Anthropic: {e}")
            return None

    def count_tokens(self, text: str) -> int:
        """Count tokens for Anthropic models."""
        try:
            # Use Anthropic's token counting if available
            # For now, use approximation: 1 token ≈ 3.5 characters for Claude
            return int(len(text) / 3.5)
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            return len(text) // 4


class XAIAdapter(BaseLLMAdapter):
    """Adapter for xAI Grok models."""

    def __init__(
        self, model_name: str = None, temperature: float = None, max_tokens: int = None
    ):
        model_name = model_name or config.llm.default_xai_model
        super().__init__(model_name, temperature, max_tokens)
        self.client = openai.OpenAI(
            api_key=config.llm.xai_api_key, base_url="https://api.x.ai/v1"
        )

    def get_langchain_llm(self) -> ChatXAI:
        """Get the LangChain xAI LLM instance."""
        kwargs = {
            "xai_api_key": config.llm.xai_api_key,
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.get_max_tokens(),
        }

        # Add search parameters for models that support it
        if self.model_name in ["grok-3"]:
            kwargs["search_parameters"] = {"mode": "auto"}

        return ChatXAI(**kwargs)

    def get_max_tokens(self) -> int:
        """Get maximum tokens for the xAI model."""
        return config.llm.xai_model_map.get(self.model_name, 8192)

    def create_completion(
        self, messages: List[Dict[str, str]], files: List[Dict[str, Any]] = None
    ) -> str:
        """Create a completion using xAI API with optional file support."""
        try:
            # Add files if provided (similar to OpenAI format)
            if files:
                for file_data in files:
                    if file_data["file_type"] == "image":
                        # Add image content for the last user message
                        for msg in reversed(messages):
                            if msg["role"] == "user":
                                if isinstance(msg["content"], str):
                                    msg["content"] = [
                                        {"type": "text", "text": msg["content"]},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{file_data['mime_type']};base64,{file_data['base64_data']}"
                                            },
                                        },
                                    ]
                                elif isinstance(msg["content"], list):
                                    msg["content"].append(
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{file_data['mime_type']};base64,{file_data['base64_data']}"
                                            },
                                        }
                                    )
                                break
                    # For other file types, include as text context
                    elif file_data["file_type"] in ["text", "csv", "json", "code"]:
                        try:
                            decoded_content = base64.b64decode(
                                file_data["base64_data"]
                            ).decode("utf-8")
                            file_context = f"\n\n--- File: {file_data['file_name']} ---\n{decoded_content}\n--- End of File ---\n"

                            # Add to the last user message
                            for msg in reversed(messages):
                                if msg["role"] == "user":
                                    if isinstance(msg["content"], str):
                                        msg["content"] += file_context
                                    elif isinstance(msg["content"], list):
                                        msg["content"].append(
                                            {"type": "text", "text": file_context}
                                        )
                                    break
                        except Exception as e:
                            logger.warning(f"Could not decode file content: {e}")
            # save to file for debugging
            with open("messages_debug.json", "w") as f:
                import json

                json.dump(messages, f, indent=2)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_completion_tokens=self.max_tokens,
                n=3,
            )
            with open("response_debug.txt", "w") as f:
                f.write(str(response))
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"Failed to generate xAI completion: {str(e)}")

    def count_tokens(self, text: str) -> int:
        """Count tokens for xAI models."""
        try:
            # xAI uses similar tokenization to OpenAI, so we can use tiktoken
            import tiktoken

            # Use gpt-4 encoding as approximation for Grok
            encoding = tiktoken.encoding_for_model("gpt-4")
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4


class LLMFactory:
    """Factory class for creating LLM adapters."""

    @staticmethod
    def create_adapter(
        provider: LLMProvider,
        model_name: str = None,
        temperature: float = None,
        max_tokens: int = None,
    ) -> BaseLLMAdapter:
        """Create an LLM adapter based on the provider."""

        if isinstance(provider, str):
            provider = LLMProvider(provider.lower())

        if provider == LLMProvider.OPENAI:
            return OpenAIAdapter(model_name, temperature, max_tokens)
        elif provider == LLMProvider.ANTHROPIC:
            return AnthropicAdapter(model_name, temperature, max_tokens)
        elif provider == LLMProvider.XAI:
            return XAIAdapter(model_name, temperature, max_tokens)
        elif provider == LLMProvider.ODINAI:
            return OdinAIAdapter(model_name, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


# Utility functions for backward compatibility
def get_max_tokens(model_name: str) -> int:
    """
    Get the maximum number of tokens for a given model.

    Args:
        model_name (str): The name of the model.

    Returns:
        int: The maximum number of tokens for the model.
    """
    # Import from config module to use centralized helper
    from athenah_ai.config import get_max_tokens as config_get_max_tokens
    return config_get_max_tokens(model_name)


def get_token_total(prompt: str, model_name: str = None) -> int:
    """
    Get the total number of tokens for a given prompt.

    Args:
        prompt (str): The prompt to count tokens for.
        model_name (str, optional): The model name for accurate counting.

    Returns:
        int: The total number of tokens.
    """
    if not model_name:
        model_name = config.llm.default_openai_model

    try:
        # Determine provider based on model name
        if model_name in config.llm.openai_model_map:
            adapter = OpenAIAdapter(model_name)
        elif model_name in config.llm.anthropic_model_map:
            adapter = AnthropicAdapter(model_name)
        elif model_name in config.llm.xai_model_map:
            adapter = XAIAdapter(model_name)
        else:
            # Default to OpenAI
            adapter = OpenAIAdapter(model_name)

        return adapter.count_tokens(prompt)
    except Exception as e:
        logger.warning(f"Error counting tokens: {e}")
        return len(prompt) // 4  # Rough approximation
