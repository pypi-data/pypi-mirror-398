import os
from typing import Any, Dict, List, Optional, Type, Union

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

from ..base import Assistant


class OpenAIAssistant(Assistant):
    """OpenAI model assistant implementation."""

    def __init__(
        self,
        model_name: str,
        response_model: Optional[Type[BaseModel]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        top_p: float = 1.0,
        connect_timeout: Optional[int] = None,
        read_timeout: Optional[int] = None,
        model_kwargs: Optional[Dict[str, Any]] = None,
        extra_body: Optional[Dict[str, Any]] = None,
        auto_apply_parser: bool = True,
        reasoning: Optional[Dict[str, Any]] = None,
        output_version: str = "responses/v1",
        **kwargs: Any,
    ) -> None:
        """
        初始化OpenAI助手

        Args:
            model_name: 使用的模型名称
            response_model: 响应模型类型（当auto_apply_parser=False时可选）
            temperature: 采样温度
            max_tokens: 最大生成token数
            base_url: API基础URL
            api_key: API密钥
            system_prompt: 系统提示
            top_p: 采样参数
            connect_timeout: 连接超时时间
            read_timeout: 读取超时时间
            model_kwargs: 额外的模型参数
            extra_body: 额外的请求体参数，默认{"return_reasoning": False}
            auto_apply_parser: 是否自动应用解析器（默认True，保持向后兼容）
            reasoning: OpenAI推理参数，用于o系列模型（o1, o3, o4-mini等）
                      例如: {"effort": "medium", "summary": "auto"}
            output_version: 输出版本格式，推荐使用"responses/v1"以获得更好的推理支持
            **kwargs: 额外参数
        """
        # Store OpenAI-specific parameters
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url
        self.api_key = api_key
        self.top_p = top_p
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.model_kwargs = model_kwargs or {}
        self.extra_body = extra_body
        self.reasoning = reasoning
        self.output_version = output_version

        # Validate and store reasoning parameters
        if reasoning is not None:
            self._validate_reasoning_params(reasoning)

        # Initialize the base class
        super().__init__(
            response_model=response_model,
            system_prompt=system_prompt,
            auto_apply_parser=auto_apply_parser,
            **kwargs,
        )

    def _setup_prompt_and_chain(self) -> None:
        """设置提示模板和处理链"""
        # Handle extra_body with default return_reasoning setting
        extra_body = self.extra_body
        if extra_body is None:
            extra_body = {"return_reasoning": False}
        elif "return_reasoning" not in extra_body:
            extra_body["return_reasoning"] = False

        # Prepare ChatOpenAI initialization parameters
        llm_params = {
            "model": self.model_name,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "base_url": self.base_url,
            "api_key": SecretStr(
                self.api_key or os.getenv("OPENAI_API_KEY", "dummy-key") or ""
            ),
            "model_kwargs": self.model_kwargs,
            "extra_body": extra_body,
            "timeout": (self.connect_timeout, self.read_timeout),
            "output_version": self.output_version,
        }

        # Add max_tokens using the correct parameter name for newer versions
        if self.max_tokens is not None:
            llm_params["max_tokens"] = self.max_tokens

        # Add reasoning parameter if provided
        if self.reasoning is not None:
            llm_params["reasoning"] = self.reasoning
            # Automatically enable Responses API when reasoning is provided
            llm_params["use_responses_api"] = True

        # 初始化LLM with proper parameters
        self.llm: Any = ChatOpenAI(**llm_params)

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

    def apply_parser(self, response_model: Optional[Type[BaseModel]] = None) -> None:
        """
        应用解析器到链上，使输出结构化

        Args:
            response_model: 可选的响应模型类。如果提供，将创建新的解析器；
                          如果不提供，将使用现有的解析器（如果存在）

        调用此方法后，ask方法将返回解析后的结构化数据

        Raises:
            ValueError: 当没有response_model且没有现有解析器时
        """
        if response_model is not None:
            # 创建新的解析器
            base_parser = PydanticOutputParser(pydantic_object=response_model)
            self.parser = base_parser.with_retry(
                stop_after_attempt=3,
                retry_if_exception_type=(ValueError, KeyError),
            )
            # 更新response_model
            self.response_model = response_model

            # 重新设置提示模板以包含格式说明
            self._setup_prompt_and_chain()
        elif self.parser is None:
            raise ValueError(
                "Cannot apply parser: no response_model was provided during "
                "initialization and none was passed to apply_parser(). "
                "Either provide a response_model parameter or create the "
                "assistant with a response_model."
            )

        # 应用解析器到链
        # At this point, self.parser is guaranteed to be non-None
        assert self.parser is not None
        self.chain = self.base_chain | self.parser

    def _get_model_name(self) -> str:
        """获取模型名称"""
        return self.model_name
