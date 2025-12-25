import asyncio
import inspect
import logging
import time
import warnings
from typing import Any, Dict, List, Set

from langchain_core.embeddings import Embeddings

from ..base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)

# isort:skip_file
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
)


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Gemini嵌入提供者"""

    # Parameters that need special mapping from config to langchain
    _PARAM_MAPPING = {
        "model_name": "model",
        "api_key": "google_api_key",
    }

    # Parameters that are internal to our config and should not be passed to langchain
    _INTERNAL_PARAMS = {
        "provider_type",  # Our internal field
        "model_type",  # Our internal field
        "api_base",  # Gemini doesn't use api_base
    }

    # Parameters that should go into extra_body for Gemini API
    _EXTRA_BODY_PARAMS: Set[str] = (
        set()
    )  # Gemini doesn't typically need extra_body params

    @classmethod
    def _get_known_gemini_params(cls) -> Set[str]:
        """Get the set of known GoogleGenerativeAIEmbeddings parameters by inspecting the class."""
        # Get the __init__ signature
        sig = inspect.signature(GoogleGenerativeAIEmbeddings.__init__)
        # Extract parameter names (excluding 'self')
        return {param for param in sig.parameters.keys() if param != "self"}

    def __init__(self, config: Dict[str, Any], **kwargs: Any) -> None:
        """
        初始化Gemini嵌入提供者

        Args:
            config: 配置字典，所有参数都会传递给GoogleGenerativeAIEmbeddings，除了内部参数
            **kwargs: 额外参数，会覆盖config中的同名参数
        """
        # Get known Gemini parameters dynamically
        known_params = self._get_known_gemini_params()

        # Build parameters dict by mapping config keys to langchain parameter names
        embedding_params: Dict[str, Any] = {}
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
            # Known Gemini parameters - pass directly
            elif param_name in known_params:
                embedding_params[param_name] = value
                logger.debug(f"Adding config parameter: {key} -> {param_name}={value}")
            # Unknown parameters - try to pass directly, will be caught by error handler if invalid
            else:
                embedding_params[param_name] = value
                logger.debug(f"Adding unknown parameter: {key} -> {param_name}={value}")

        # Add extra_body if there are any parameters (Gemini may not support this)
        if extra_body:
            logger.warning(
                f"Gemini may not support extra_body parameters: {extra_body}"
            )
            # Try to add them anyway, will be caught by error handler if invalid
            embedding_params["model_kwargs"] = {"extra_body": extra_body}

        # Set default timeout if not provided
        if "timeout" not in embedding_params:
            embedding_params["timeout"] = 30

        # 记录初始化信息（隐藏敏感信息）
        safe_params = embedding_params.copy()
        if "google_api_key" in safe_params:
            safe_params["google_api_key"] = (
                "******" if safe_params["google_api_key"] else None
            )

        # kwargs override config parameters
        embedding_params.update(kwargs)

        # Try to initialize with all parameters
        try:
            self._embeddings = GoogleGenerativeAIEmbeddings(**embedding_params)
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
                        f"Parameter '{invalid_param}' is not supported by GoogleGenerativeAIEmbeddings and will be ignored. "
                        f"Error: {error_msg}"
                    )
                    # Remove the invalid parameter and retry
                    embedding_params.pop(invalid_param, None)
                    self._embeddings = GoogleGenerativeAIEmbeddings(**embedding_params)
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
        raise Exception(f"嵌入文本失败: {str(last_error)}")

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
        raise Exception(f"嵌入文本失败: {str(last_error)}")
