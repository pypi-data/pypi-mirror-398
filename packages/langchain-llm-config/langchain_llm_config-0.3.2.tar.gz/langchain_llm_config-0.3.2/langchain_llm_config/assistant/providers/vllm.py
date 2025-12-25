from typing import Any, Dict, Optional, Type

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from pydantic import BaseModel

from ..base import Assistant

try:
    from langchain_community.llms.vllm import VLLMOpenAI
except ImportError:
    VLLMOpenAI = None  # type: ignore[assignment,misc]


class VLLMAssistant(Assistant):
    """VLLM助手实现（使用专用的VLLMOpenAI客户端）"""

    def __init__(
        self,
        config: Dict[str, Any],
        response_model: Optional[Type[BaseModel]] = None,
        system_prompt: Optional[str] = None,
        auto_apply_parser: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        初始化VLLM助手

        Args:
            config: 配置字典，包含vLLM服务器配置
            response_model: 响应模型类（当auto_apply_parser=False时可选）
            system_prompt: 系统提示
            auto_apply_parser: 是否自动应用解析器（默认True，保持向后兼容）
            **kwargs: 额外参数
        """
        if VLLMOpenAI is None:
            raise ImportError(
                "VLLMOpenAI not found. Please install langchain-community: "
                "pip install langchain-community"
            )

        # Store vLLM-specific parameters
        self.config = config
        self.model_name = config["model_name"]
        self.temperature = config.get("temperature", 0.6)
        self.max_tokens = config.get("max_tokens", 8192)
        self.base_url = config["api_base"]
        self.api_key = config.get("api_key", "EMPTY")
        self.top_p = config.get("top_p", 0.8)
        self.connect_timeout = config.get("connect_timeout", 30)
        self.read_timeout = config.get("read_timeout", 60)
        self.model_kwargs = config.get("model_kwargs", {})

        # Initialize the base class
        super().__init__(
            response_model=response_model,
            system_prompt=system_prompt,
            auto_apply_parser=auto_apply_parser,
            **kwargs,
        )

    def _setup_prompt_and_chain(self) -> None:
        """设置提示模板和处理链"""
        # 初始化vLLM LLM using the specialized VLLMOpenAI client
        self.llm = VLLMOpenAI(  # type: ignore[call-arg]
            openai_api_base=self.base_url,
            openai_api_key=self.api_key,
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            request_timeout=(self.connect_timeout, self.read_timeout),
            **self.model_kwargs,
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
