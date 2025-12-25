import asyncio
import inspect
import logging
import os
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Set

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from ..base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class VLLMEmbeddingProvider(BaseEmbeddingProvider):
    """VLLM嵌入提供者（使用OpenAI兼容接口）"""

    # Parameters that need special mapping from config to langchain
    _PARAM_MAPPING = {
        "model_name": "model",
        "api_base": "base_url",
    }

    # Parameters that are internal to our config and should not be passed to langchain
    _INTERNAL_PARAMS = {
        "provider_type",  # Our internal field
        "model_type",  # Our internal field
    }

    # Parameters that should go into extra_body for VLLM API
    _EXTRA_BODY_PARAMS = {
        "truncate_prompt_tokens",  # VLLM-specific parameter
        "guided_json",
        "guided_regex",
        "guided_choice",
        "guided_grammar",
        "guided_decoding_backend",
        "guided_whitespace_pattern",
    }

    @classmethod
    def _get_known_openai_params(cls) -> Set[str]:
        """Get the set of known OpenAIEmbeddings parameters by inspecting the class."""
        # Get the __init__ signature
        sig = inspect.signature(OpenAIEmbeddings.__init__)
        # Extract parameter names (excluding 'self')
        return {param for param in sig.parameters.keys() if param != "self"}

    def __init__(self, config: Dict[str, Any], **kwargs: Any) -> None:
        """
        初始化VLLM嵌入提供者

        Args:
            config: 配置字典，所有参数都会传递给OpenAIEmbeddings，除了内部参数
            **kwargs: 额外参数，会覆盖config中的同名参数
        """
        # Calculate tiktoken cache directory
        tiktoken_cache_dir = str(
            Path(__file__).parent.parent.parent / ".tiktoken_cache"
        )

        # Set tiktoken cache directory environment variable
        os.environ["TIKTOKEN_CACHE_DIR"] = tiktoken_cache_dir

        # Get known OpenAI parameters dynamically
        known_params = self._get_known_openai_params()

        # Build parameters dict by mapping config keys to langchain parameter names
        embedding_params: Dict[str, Any] = {
            "tiktoken_enabled": True,  # Always enable tiktoken for VLLM
        }
        extra_body: Dict[str, Any] = {}

        for key, value in config.items():
            # Skip internal parameters
            if key in self._INTERNAL_PARAMS:
                continue

            # Skip None values
            if value is None:
                continue

            # Map parameter name if needed
            param_name = self._PARAM_MAPPING.get(key, key)

            # Parameters that should go into extra_body
            if key in self._EXTRA_BODY_PARAMS or param_name in self._EXTRA_BODY_PARAMS:
                extra_body[param_name] = value
                logger.debug(
                    f"Adding extra_body parameter: {key} -> {param_name}={value}"
                )
            # Known OpenAI parameters - pass directly
            elif param_name in known_params:
                embedding_params[param_name] = value
                logger.debug(f"Adding config parameter: {key} -> {param_name}={value}")
            # Unknown parameters - try to pass directly, will be caught by error handler if invalid
            else:
                embedding_params[param_name] = value
                logger.debug(f"Adding unknown parameter: {key} -> {param_name}={value}")

        # Add extra_body if there are any parameters
        if extra_body:
            embedding_params["model_kwargs"] = {"extra_body": extra_body}
            logger.debug(f"Setting model_kwargs with extra_body: {extra_body}")

        # Set defaults if not provided
        if "base_url" not in embedding_params:
            embedding_params["base_url"] = "http://localhost:8000/v1"
        if "timeout" not in embedding_params:
            embedding_params["timeout"] = 30

        # 记录初始化信息（隐藏敏感信息）
        safe_params = embedding_params.copy()
        if "api_key" in safe_params:
            safe_params["api_key"] = "******" if safe_params["api_key"] else None

        # kwargs override config parameters
        embedding_params.update(kwargs)

        # Try to initialize with all parameters
        try:
            self._embeddings = OpenAIEmbeddings(**embedding_params)
            self._max_retries = 3
            self._retry_delay = 1.0  # 初始重试延迟（秒）
        except TypeError as e:
            # If initialization fails due to unexpected parameters, retry without them
            error_msg = str(e)
            if (
                "unexpected keyword argument" in error_msg
                or "got an unexpected" in error_msg
            ):
                # Extract the invalid parameter name from error message
                import re

                match = re.search(r"'(\w+)'", error_msg)
                if match:
                    invalid_param = match.group(1)
                    warnings.warn(
                        f"Parameter '{invalid_param}' is not supported by OpenAIEmbeddings and will be ignored. "
                        f"Error: {error_msg}"
                    )
                    # Remove the invalid parameter and retry
                    embedding_params.pop(invalid_param, None)
                    self._embeddings = OpenAIEmbeddings(**embedding_params)
                    self._max_retries = 3
                    self._retry_delay = 1.0
                else:
                    # Can't parse error, re-raise
                    raise
            else:
                # Different type of TypeError, re-raise
                raise

    @property
    def embedding_model(self) -> Embeddings:
        """获取嵌入模型"""
        return self._embeddings

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文本列表（同步版本）

        Args:
            texts: 要嵌入的文本列表

        Returns:
            嵌入向量列表
        """
        if not texts:
            return []

        retry_count = 0
        last_error = None

        while retry_count < self._max_retries:
            try:
                result = self._embeddings.embed_documents(texts)
                return result
            except Exception as e:
                retry_count += 1
                last_error = e

                if retry_count < self._max_retries:
                    # 指数退避重试
                    wait_time = self._retry_delay * (2 ** (retry_count - 1))
                    time.sleep(wait_time)

        # 所有重试都失败，报告错误
        raise Exception(f"VLLM嵌入文本失败: {str(last_error)}")

    async def embed_texts_async(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文本列表（异步版本）

        Args:
            texts: 要嵌入的文本列表

        Returns:
            嵌入向量列表
        """
        if not texts:
            return []

        retry_count = 0
        last_error = None

        while retry_count < self._max_retries:
            try:
                result = await self._embeddings.aembed_documents(texts)
                return result
            except Exception as e:
                retry_count += 1
                last_error = e

                if retry_count < self._max_retries:
                    # 指数退避重试
                    wait_time = self._retry_delay * (2 ** (retry_count - 1))
                    await asyncio.sleep(wait_time)

        # 所有重试都失败，报告错误
        raise Exception(f"VLLM嵌入文本失败: {str(last_error)}")
