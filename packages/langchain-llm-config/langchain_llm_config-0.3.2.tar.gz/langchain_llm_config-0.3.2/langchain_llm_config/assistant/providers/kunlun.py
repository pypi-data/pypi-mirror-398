from typing import Any, Dict, Optional, Type

import httpx
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from pydantic import BaseModel, SecretStr

from ..base import Assistant

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None  # type: ignore[assignment,misc]


class KunlunAssistant(Assistant):
    """Kunlun API assistant implementation (OpenAI-compatible with bearer token authentication)"""

    def __init__(
        self,
        config: Dict[str, Any],
        response_model: Optional[Type[BaseModel]] = None,
        system_prompt: Optional[str] = None,
        auto_apply_parser: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        初始化Kunlun助手

        Args:
            config: 配置字典，包含Kunlun API配置
            response_model: 响应模型类（当auto_apply_parser=False时可选）
            system_prompt: 系统提示
            auto_apply_parser: 是否自动应用解析器（默认True，保持向后兼容）
            **kwargs: 额外参数
        """
        if ChatOpenAI is None:
            raise ImportError(
                "ChatOpenAI not found. Please install langchain-openai: "
                "pip install langchain-openai"
            )

        # Store Kunlun-specific parameters
        self.config = config
        self.model_name = config["model_name"]
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 8000)
        self.base_url = config["api_base"]
        self.bearer_token = config["bearer_token"]  # Bearer token for authentication

        # Validate bearer token
        if not self.bearer_token or self.bearer_token.strip() == "":
            raise ValueError(
                "Kunlun bearer token is required. "
                "Set KUNLUN_BEARER_TOKEN environment variable or provide it in config."
            )

        self.top_p = config.get("top_p", 1.0)
        self.connect_timeout = config.get("connect_timeout", 60)
        self.read_timeout = config.get("read_timeout", 60)
        self.model_kwargs = config.get("model_kwargs", {})
        self.extra_body = config.get("extra_body", {})

        # Initialize the base class
        super().__init__(
            response_model=response_model,
            system_prompt=system_prompt,
            auto_apply_parser=auto_apply_parser,
            **kwargs,
        )

    def _setup_prompt_and_chain(self) -> None:
        """设置提示模板和处理链"""
        # Initialize ChatOpenAI with bearer token
        # Kunlun uses bearer token authentication, passed as api_key to ChatOpenAI
        # Disable SSL verification for Kunlun platform (self-signed certificate)
        http_client = httpx.Client(verify=False)
        http_async_client = httpx.AsyncClient(verify=False)

        self.llm = ChatOpenAI(
            model=self.model_name,
            base_url=self.base_url,
            api_key=SecretStr(self.bearer_token),  # Use bearer token as api_key
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens,
            top_p=self.top_p,
            timeout=(self.connect_timeout, self.read_timeout),
            model_kwargs=self.model_kwargs,
            extra_body=self.extra_body,
            http_client=http_client,
            http_async_client=http_async_client,
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
        return str(self.model_name)
