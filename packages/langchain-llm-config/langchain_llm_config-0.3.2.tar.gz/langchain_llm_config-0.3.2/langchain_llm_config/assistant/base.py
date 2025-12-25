import time
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional, Type, Union

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable
from pydantic import BaseModel


class Assistant(ABC):
    """
    AI助手抽象基类，定义所有助手实现的接口

    这是一个纯接口类，定义了所有助手实现必须提供的方法和属性。
    具体的实现应该在providers目录下的各个提供者类中。

    Attributes:
        system_prompt: 系统提示
        response_model: 响应模型类型
        auto_apply_parser: 是否自动应用解析器
        parser: 输出解析器
        prompt: 提示模板
        chain: 处理链
        base_chain: 基础链（不包含解析器）
        llm: 语言模型实例
    """

    def __init__(
        self,
        response_model: Optional[Type[BaseModel]] = None,
        system_prompt: Optional[str] = None,
        auto_apply_parser: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        初始化AI助手抽象基类

        Args:
            response_model: 响应模型类型（当auto_apply_parser=False时可选）
            system_prompt: 系统提示
            auto_apply_parser: 是否自动应用解析器（默认True，保持向后兼容）
            **kwargs: 额外参数，由具体实现处理
        """
        # Validate parameters
        if auto_apply_parser and response_model is None:
            raise ValueError(
                "response_model is required when auto_apply_parser=True. "
                "Either provide a response_model or set auto_apply_parser=False "
                "for raw text output."
            )

        self.system_prompt = system_prompt
        self.response_model = response_model
        self.auto_apply_parser = auto_apply_parser
        self.output_version = kwargs.get("output_version", "responses/v1")

        # Initialize parser as None with proper type annotation
        self.parser: Optional[Runnable[Union[BaseMessage, str], Any]] = None

        # These will be set by concrete implementations
        self.llm: Any = None
        self.prompt: Any = None
        self.chain: Any = None
        self.base_chain: Any = None

        # Call abstract setup method
        self._setup_prompt_and_chain()

        # Apply parser if requested
        if auto_apply_parser:
            self.apply_parser()

    @abstractmethod
    def _setup_prompt_and_chain(self) -> None:
        """设置提示模板和处理链 - 由具体实现提供"""
        pass

    def _validate_reasoning_params(self, reasoning: Dict[str, Any]) -> None:
        """
        Validate reasoning parameters according to OpenAI requirements

        Args:
            reasoning: Dictionary containing reasoning parameters

        Raises:
            ValueError: If reasoning parameters are invalid
        """
        if not isinstance(reasoning, dict):
            raise ValueError("reasoning parameter must be a dictionary")

        # Validate effort parameter
        if "effort" in reasoning:
            valid_efforts = ["low", "medium", "high"]
            if reasoning["effort"] not in valid_efforts:
                raise ValueError(
                    f"reasoning.effort must be one of {valid_efforts}, "
                    f"got: {reasoning['effort']}"
                )

        # Validate summary parameter
        if "summary" in reasoning:
            valid_summaries = ["auto", "concise", "detailed", None]
            if reasoning["summary"] not in valid_summaries:
                raise ValueError(
                    f"reasoning.summary must be one of {valid_summaries}, "
                    f"got: {reasoning['summary']}"
                )

    @staticmethod
    def get_reasoning_example() -> Dict[str, Any]:
        """
        Get an example of valid reasoning parameters

        Returns:
            Dictionary with example reasoning parameters
        """
        return {
            "effort": "medium",  # 'low', 'medium', or 'high'
            "summary": "auto",  # 'auto', 'concise', 'detailed', or None
        }

    def _extract_reasoning(self, output: Any) -> Optional[str]:
        """
        Extract reasoning content from LLM output

        Args:
            output: The LLM output object

        Returns:
            Reasoning content if found, None otherwise
        """
        # Try different extraction methods
        reasoning = self._extract_responses_v1_reasoning(output)
        if reasoning:
            return reasoning

        reasoning = self._extract_think_tags_reasoning(output)
        if reasoning:
            return reasoning

        reasoning = self._extract_legacy_reasoning(output)
        if reasoning:
            return reasoning

        return None

    def _extract_responses_v1_reasoning(self, output: Any) -> Optional[str]:
        """Extract reasoning from responses/v1 format."""
        if not (hasattr(output, "content") and isinstance(output.content, list)):
            return None

        for block in output.content:
            if isinstance(block, dict) and block.get("type") == "reasoning":
                summary = block.get("summary", [])
                if summary and isinstance(summary, list):
                    reasoning_texts = [
                        item["text"]
                        for item in summary
                        if isinstance(item, dict) and "text" in item
                    ]
                    if reasoning_texts:
                        return "\n".join(reasoning_texts)
        return None

    def _extract_think_tags_reasoning(self, output: Any) -> Optional[str]:
        """Extract reasoning from <think> tags."""
        if not (hasattr(output, "content") and isinstance(output.content, str)):
            return None

        import re

        think_pattern = r"<think>(.*?)</think>"
        matches = re.findall(think_pattern, output.content, re.DOTALL)
        if matches:
            return "\n".join(match.strip() for match in matches)
        return None

    def _extract_legacy_reasoning(self, output: Any) -> Optional[str]:
        """Extract reasoning from legacy additional_kwargs format."""
        if not (hasattr(output, "additional_kwargs") and output.additional_kwargs):
            return None

        additional_kwargs = output.additional_kwargs
        if isinstance(additional_kwargs, dict) and "content" in additional_kwargs:
            reasoning_content = additional_kwargs["content"]
            if reasoning_content and isinstance(reasoning_content, str):
                return str(reasoning_content)
        return None

    def _extract_reasoning_from_text(self, text: str) -> Optional[str]:
        """
        Extract reasoning content from text string (for direct string outputs)

        Args:
            text: Raw text content

        Returns:
            Reasoning content if found, None otherwise
        """
        import re

        think_pattern = r"<think>(.*?)</think>"
        matches = re.findall(think_pattern, text, re.DOTALL)
        if matches:
            return "\n".join(match.strip() for match in matches)
        return None

    def _clean_content_for_parsing(self, content: str) -> str:
        """
        Clean content by removing reasoning tags before JSON parsing

        Args:
            content: Raw content from LLM

        Returns:
            Cleaned content ready for JSON parsing
        """
        import re

        # Remove <think> tags and their content
        cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
        return cleaned.strip()

    def _build_system_prompt(self, extra_system_prompt: Optional[str] = None) -> str:
        """Build the complete system prompt."""
        system_prompt = self.system_prompt or ""
        if extra_system_prompt:
            system_prompt = (
                f"{system_prompt}\n{extra_system_prompt}"
                if system_prompt
                else extra_system_prompt
            )
        return system_prompt

    def _build_context_string(self, context: Optional[str] = None) -> str:
        """Build the context string."""
        return f"背景信息：{context}" if context else ""

    def _extract_raw_content(self, output: Any) -> str:
        """Extract raw content from different output types."""
        if hasattr(output, "content"):
            # Message object with content attribute
            return str(output.content)
        elif isinstance(output, str):
            # Direct string output (e.g., from VLLMOpenAI)
            return output
        else:
            # Fallback: convert to string
            return str(output)

    def _process_parsed_response(
        self, parsed_response: Any, reasoning: Optional[str]
    ) -> Dict[str, Any]:
        """Process parsed response and add reasoning if available."""
        if self.output_version == "responses/v1":
            # New format with reasoning support
            result = {"response": parsed_response}
            if reasoning:
                result["reasoning"] = reasoning
            return result
        else:
            # Legacy format - return parsed response directly
            return {"response": parsed_response}  # Ensure dict format

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
            self._base_parser = base_parser  # Store the original parser
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

    def ask(  # noqa: C901
        self,
        query: Union[str, List[Dict[str, Any]]],
        extra_system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], str]:
        """
        处理用户查询并返回响应（同步版本）

        Args:
            query: 用户查询文本或多模态内容列表
            extra_system_prompt: 额外的系统提示
            context: 可选的上下文信息
            **kwargs: 额外参数

        Returns:
            当应用解析器时返回结构化响应 (Dict[str, Any])，
            否则返回原始文本内容 (str)

        Raises:
            ValueError: 当处理查询时发生错误
        """
        try:
            # 构建系统提示
            system_prompt = self.system_prompt or ""
            if extra_system_prompt:
                system_prompt = (
                    f"{system_prompt}\n{extra_system_prompt}"
                    if system_prompt
                    else extra_system_prompt
                )

            # 构建上下文信息
            context_str = f"背景信息：{context}" if context else ""

            # 检查是否应用了解析器
            if self.parser is not None:
                # 使用基础链获取原始输出，然后手动处理
                output = self.base_chain.invoke(
                    {
                        "question": query,
                        "system_prompt": system_prompt,
                        "context": context_str,
                    }
                )

                # Extract reasoning from raw output
                reasoning = self._extract_reasoning(output)

                # Handle different output types
                if hasattr(output, "content"):
                    # Message object with content attribute
                    raw_content = output.content
                elif isinstance(output, str):
                    # Direct string output (e.g., from VLLMOpenAI)
                    raw_content = output
                else:
                    # Fallback to string conversion
                    raw_content = str(output)

                # Extract reasoning from raw content
                reasoning = self._extract_reasoning_from_text(raw_content)

                # Clean content for parsing
                cleaned_content = self._clean_content_for_parsing(raw_content)

                # Parse the cleaned content
                try:
                    parsed_result = self._base_parser.parse(cleaned_content)
                    result: Dict[str, Any] = parsed_result.model_dump()

                    return result
                except Exception as e:
                    # If parsing fails, return error with reasoning
                    error_result = {
                        "error": f"Failed to parse response: {str(e)}",
                        "raw_content": cleaned_content,
                    }
                    if reasoning:
                        error_result["reasoning_content"] = reasoning
                    return error_result
            else:
                # 解析器未应用，使用基础链返回原始文本内容
                output = self.base_chain.invoke(
                    {
                        "question": query,
                        "system_prompt": system_prompt,
                        "context": context_str,
                    }
                )

                if hasattr(output, "content"):
                    content = output.content
                    # Check for reasoning in output
                    reasoning = self._extract_reasoning(output)

                    # Return enhanced response with reasoning if available
                    if reasoning:
                        return {
                            "content": str(content) if content is not None else "",
                            "reasoning_content": reasoning,
                        }
                    else:
                        # Ensure we return a string, not another object
                        return str(content) if content is not None else ""
                else:
                    return str(output)

        except Exception as e:
            raise ValueError(f"处理查询时出错: {str(e)}") from e

    async def ask_async(  # noqa: C901
        self,
        query: Union[str, List[Dict[str, Any]]],
        extra_system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], str]:
        """
        处理用户查询并返回响应（异步版本）

        Args:
            query: 用户查询文本或多模态内容列表
            extra_system_prompt: 额外的系统提示
            context: 可选的上下文信息
            **kwargs: 额外参数

        Returns:
            当应用解析器时返回结构化响应 (Dict[str, Any])，
            否则返回原始文本内容 (str)

        Raises:
            ValueError: 当处理查询时发生错误
        """
        try:
            # 构建系统提示
            system_prompt = self.system_prompt or ""
            if extra_system_prompt:
                system_prompt = (
                    f"{system_prompt}\n{extra_system_prompt}"
                    if system_prompt
                    else extra_system_prompt
                )

            # 构建上下文信息
            context_str = f"背景信息：{context}" if context else ""

            # 检查是否应用了解析器
            if self.parser is not None:
                # 使用基础链获取原始输出，然后手动处理
                output = await self.base_chain.ainvoke(
                    {
                        "question": query,
                        "system_prompt": system_prompt,
                        "context": context_str,
                    }
                )

                # Extract reasoning from raw output
                reasoning = self._extract_reasoning(output)

                # Clean content for parsing
                if hasattr(output, "content"):
                    raw_content = output.content
                    cleaned_content = self._clean_content_for_parsing(raw_content)

                    # Parse the cleaned content
                    try:
                        parsed_result = self._base_parser.parse(cleaned_content)
                        result: Dict[str, Any] = parsed_result.model_dump()

                        # Add reasoning if available
                        if reasoning:
                            result["reasoning_content"] = reasoning

                        return result
                    except Exception as e:
                        # If parsing fails, return error with reasoning
                        error_result = {
                            "error": f"Failed to parse response: {str(e)}",
                            "raw_content": cleaned_content,
                        }
                        if reasoning:
                            error_result["reasoning_content"] = reasoning
                        return error_result
                else:
                    return {"error": "No content in output"}
            else:
                # 解析器未应用，使用基础链返回原始文本内容
                output = await self.base_chain.ainvoke(
                    {
                        "question": query,
                        "system_prompt": system_prompt,
                        "context": context_str,
                    }
                )

                if hasattr(output, "content"):
                    content = output.content
                    # Check for reasoning in output
                    reasoning = self._extract_reasoning(output)

                    # Return enhanced response with reasoning if available
                    if reasoning:
                        return {
                            "content": str(content) if content is not None else "",
                            "reasoning_content": reasoning,
                        }
                    else:
                        # Ensure we return a string, not another object
                        return str(content) if content is not None else ""
                else:
                    return str(output)

        except Exception as e:
            raise ValueError(f"处理查询时出错: {str(e)}") from e

    def chat(
        self,
        query: Union[str, List[Dict[str, Any]]],
        extra_system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """
        处理用户查询并返回流式响应（同步版本）

        Args:
            query: 用户查询文本或多模态内容列表
            extra_system_prompt: 额外的系统提示
            context: 可选的上下文信息
            **kwargs: 额外参数

        Yields:
            流式响应的文本片段

        Raises:
            ValueError: 当处理查询时发生错误
        """
        try:
            # 构建系统提示
            system_prompt = self.system_prompt or ""
            if extra_system_prompt:
                system_prompt = (
                    f"{system_prompt}\n{extra_system_prompt}"
                    if system_prompt
                    else extra_system_prompt
                )

            # 构建上下文信息
            context_str = f"背景信息：{context}" if context else ""

            # 使用基础链进行流式响应（不应用解析器）
            for chunk in self.base_chain.stream(
                {
                    "question": query,
                    "system_prompt": system_prompt,
                    "context": context_str,
                }
            ):
                # Handle different chunk types
                if hasattr(chunk, "content") and chunk.content:
                    # Message object with content attribute (e.g., ChatOpenAI)
                    content = chunk.content
                    # Ensure content is a string
                    if isinstance(content, list):
                        content = "".join(str(item) for item in content)
                    yield content
                elif isinstance(chunk, str) and chunk:
                    # Direct string chunk (e.g., VLLMOpenAI)
                    yield chunk

        except Exception as e:
            raise ValueError(f"处理查询时出错: {str(e)}") from e

    async def chat_async(
        self,
        query: Union[str, List[Dict[str, Any]]],
        extra_system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        处理用户查询并返回流式响应（异步版本）

        Args:
            query: 用户查询文本或多模态内容列表
            extra_system_prompt: 额外的系统提示
            context: 可选的上下文信息
            **kwargs: 额外参数

        Yields:
            流式响应的文本片段

        Raises:
            ValueError: 当处理查询时发生错误
        """
        try:
            # 构建系统提示
            system_prompt = self.system_prompt or ""
            if extra_system_prompt:
                system_prompt = (
                    f"{system_prompt}\n{extra_system_prompt}"
                    if system_prompt
                    else extra_system_prompt
                )

            # 构建上下文信息
            context_str = f"背景信息：{context}" if context else ""

            # 使用基础链进行流式响应（不应用解析器）
            async for chunk in self.base_chain.astream(
                {
                    "question": query,
                    "system_prompt": system_prompt,
                    "context": context_str,
                }
            ):
                # Handle different chunk types
                if hasattr(chunk, "content") and chunk.content:
                    # Message object with content attribute (e.g., ChatOpenAI)
                    content = chunk.content
                    # Ensure content is a string
                    if isinstance(content, list):
                        content = "".join(str(item) for item in content)
                    yield content
                elif isinstance(chunk, str) and chunk:
                    # Direct string chunk (e.g., VLLMOpenAI)
                    yield chunk

        except Exception as e:
            raise ValueError(f"处理查询时出错: {str(e)}") from e

    @abstractmethod
    def _get_model_name(self) -> str:
        """获取模型名称 - 由具体实现提供"""
        pass

    async def chat_stream(
        self,
        query: Union[str, List[Dict[str, Any]]],
        extra_system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式聊天响应，返回带有元数据的丰富流式数据

        Args:
            query: 用户查询文本或多模态内容列表
            extra_system_prompt: 额外的系统提示
            context: 可选的上下文信息
            **kwargs: 额外参数

        Yields:
            包含以下字段的字典:
            - type: "stream", "final", "error"
            - content: 文本内容
            - full_response: 完整响应（仅在stream类型中）
            - processing_time: 处理时间
            - model_used: 使用的模型名称
            - is_complete: 是否完成

        Raises:
            ValueError: 当处理查询时发生错误
        """
        start_time = time.time()
        full_response = ""

        try:
            # 构建系统提示
            system_prompt = self.system_prompt or ""
            if extra_system_prompt:
                system_prompt = (
                    f"{system_prompt}\n{extra_system_prompt}"
                    if system_prompt
                    else extra_system_prompt
                )

            # 构建上下文信息
            context_str = f"背景信息：{context}" if context else ""

            # 使用基础链进行流式响应（不应用解析器）
            async for chunk in self.base_chain.astream(
                {
                    "question": query,
                    "system_prompt": system_prompt,
                    "context": context_str,
                }
            ):
                # Handle different chunk types
                content = None
                if hasattr(chunk, "content") and chunk.content:
                    # Message object with content attribute (e.g., ChatOpenAI)
                    content = chunk.content
                    # Ensure content is a string
                    if isinstance(content, list):
                        content = "".join(str(item) for item in content)
                elif isinstance(chunk, str) and chunk:
                    # Direct string chunk (e.g., VLLMOpenAI)
                    content = chunk

                if content:
                    full_response += content

                    yield {
                        "type": "stream",
                        "content": content,
                        "full_response": full_response,
                        "processing_time": time.time() - start_time,
                        "model_used": self._get_model_name(),
                        "is_complete": False,
                    }

            # Send final message
            yield {
                "type": "final",
                "content": "",
                "full_response": full_response,
                "processing_time": time.time() - start_time,
                "model_used": self._get_model_name(),
                "is_complete": True,
            }

        except Exception as e:
            yield {
                "type": "error",
                "content": f"处理查询时出错: {str(e)}",
                "full_response": full_response,
                "processing_time": time.time() - start_time,
                "model_used": self._get_model_name(),
                "is_complete": True,
            }

    async def stream_async(
        self,
        query: Union[str, List[Dict[str, Any]]],
        extra_system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        简化的流式响应，仅返回文本内容

        Args:
            query: 用户查询文本或多模态内容列表
            extra_system_prompt: 额外的系统提示
            context: 可选的上下文信息
            **kwargs: 额外参数

        Yields:
            文本片段

        Raises:
            ValueError: 当处理查询时发生错误
        """
        try:
            # 构建系统提示
            system_prompt = self.system_prompt or ""
            if extra_system_prompt:
                system_prompt = (
                    f"{system_prompt}\n{extra_system_prompt}"
                    if system_prompt
                    else extra_system_prompt
                )

            # 构建上下文信息
            context_str = f"背景信息：{context}" if context else ""

            # 使用基础链进行流式响应（不应用解析器）
            async for chunk in self.base_chain.astream(
                {
                    "question": query,
                    "system_prompt": system_prompt,
                    "context": context_str,
                }
            ):
                # Handle different chunk types
                if hasattr(chunk, "content") and chunk.content:
                    # Message object with content attribute (e.g., ChatOpenAI)
                    content = chunk.content
                    # Ensure content is a string
                    if isinstance(content, list):
                        content = "".join(str(item) for item in content)
                    yield content
                elif isinstance(chunk, str) and chunk:
                    # Direct string chunk (e.g., VLLMOpenAI)
                    yield chunk

        except Exception as e:
            raise ValueError(f"处理查询时出错: {str(e)}") from e
