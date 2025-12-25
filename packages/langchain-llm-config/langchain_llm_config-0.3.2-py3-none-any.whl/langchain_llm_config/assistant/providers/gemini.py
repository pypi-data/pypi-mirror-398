import os
from typing import Any, Dict, List, Optional, Type, Union

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from pydantic import BaseModel

from ..base import Assistant

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None  # type: ignore[assignment,misc]


class GeminiAssistant(Assistant):
    """Google Gemini model assistant implementation."""

    def __init__(
        self,
        model_name: str = "gemini-1.5-flash",
        response_model: Optional[Type[BaseModel]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        top_p: float = 1.0,
        auto_apply_parser: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        初始化Gemini助手

        Args:
            model_name: 使用的模型名称
            response_model: 响应模型类型（当auto_apply_parser=False时可选）
            temperature: 采样温度
            max_tokens: 最大生成token数
            api_key: API密钥
            system_prompt: 系统提示
            top_p: 采样参数
            auto_apply_parser: 是否自动应用解析器（默认True，保持向后兼容）
            **kwargs: 额外参数
        """
        if ChatGoogleGenerativeAI is None:
            raise ImportError(
                "Google Generative AI package not found. "
                "Please install it with: pip install langchain-google-genai"
            )

        # Store Gemini-specific parameters
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.top_p = top_p

        # Initialize the base class
        super().__init__(
            response_model=response_model,
            system_prompt=system_prompt,
            auto_apply_parser=auto_apply_parser,
            **kwargs,
        )

    def _setup_prompt_and_chain(self) -> None:
        """设置提示模板和处理链"""
        # 初始化Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            google_api_key=self.api_key or os.getenv("GOOGLE_API_KEY"),
            top_p=self.top_p,
        )

        if self.response_model is not None:
            # 创建基础解析器（仅当有response_model时）
            base_parser = PydanticOutputParser(pydantic_object=self.response_model)
            self._base_parser = base_parser  # Store the original parser

            # 获取格式说明
            format_instructions = base_parser.get_format_instructions()
            escaped_format_instructions = format_instructions.replace(
                "{", "{{"
            ).replace("}", "}}")

            # 创建带重试的解析器
            self.parser = base_parser.with_retry(
                stop_after_attempt=3,
                retry_if_exception_type=(ValueError, KeyError),
            )

            # 创建结构化提示模板（用于JSON输出）
            self.prompt = PromptTemplate(
                template=(
                    "{system_prompt}\n"
                    "请严格按照以下格式提供您的回答。您的回答必须：\n"
                    "1. 完全符合指定的JSON格式\n"
                    "2. 不要添加任何额外的解释或注释\n"
                    "3. 对于有默认值的字段（如intension、language），如果不知道具体值，"
                    "请直接省略该字段，不要使用null\n"
                    "4. 对于没有默认值的可选字段，如果确实没有值，才使用null\n"
                    "5. 必须使用标准ASCII字符作为JSON语法（如 : 而不是 ：）\n"
                    "格式要求：\n"
                    "{format_instructions}\n\n"
                    "{context}\n"
                    "用户: {question}\n"
                    "助手:"
                ),
                input_variables=["question", "system_prompt", "context"],
                partial_variables={"format_instructions": escaped_format_instructions},
            )
        else:
            # 没有response_model时，使用简单的提示模板（用于原始文本输出）
            self.parser = None
            self.prompt = PromptTemplate(
                template=(
                    "{system_prompt}\n" "{context}\n" "用户: {question}\n" "助手:"
                ),
                input_variables=["question", "system_prompt", "context"],
            )

        # 构建基础链（不包含解析器）
        self.base_chain: Runnable = RunnablePassthrough() | self.prompt | self.llm

        # 初始化时使用基础链
        self.chain: Runnable = self.base_chain

    def _get_model_name(self) -> str:
        """获取模型名称"""
        return self.model_name
