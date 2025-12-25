from abc import ABC, abstractmethod
from typing import List

from langchain_core.embeddings import Embeddings
from pydantic import BaseModel, Field


class EmbeddingResponse(BaseModel):
    """嵌入响应模型"""

    embeddings: List[List[float]] = Field(..., description="嵌入向量列表")
    dimensions: int = Field(..., description="嵌入维度")


class BaseEmbeddingProvider(ABC):
    """嵌入提供者基类"""

    @property
    @abstractmethod
    def embedding_model(self) -> Embeddings:
        """获取嵌入模型"""
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文本列表（同步版本）

        Args:
            texts: 要嵌入的文本列表

        Returns:
            嵌入向量列表
        """
        pass

    @abstractmethod
    async def embed_texts_async(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文本列表（异步版本）

        Args:
            texts: 要嵌入的文本列表

        Returns:
            嵌入向量列表
        """
        pass
