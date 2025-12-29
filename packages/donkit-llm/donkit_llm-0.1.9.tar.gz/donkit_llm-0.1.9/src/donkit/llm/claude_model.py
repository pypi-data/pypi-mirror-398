import json
from typing import AsyncIterator

from anthropic import AsyncAnthropic, AsyncAnthropicVertex

from .model_abstract import (
    ContentType,
    FunctionCall,
    GenerateRequest,
    GenerateResponse,
    LLMModelAbstract,
    Message,
    ModelCapability,
    StreamChunk,
    Tool,
    ToolCall,
)


class ClaudeModel(LLMModelAbstract):
    """Anthropic Claude model implementation."""

    name = "claude"

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: str | None = None,
    ):
        """
        Initialize Claude model via Anthropic API.

        Args:
            model_name: Model identifier (e.g., "claude-3-5-sonnet-20241022", "claude-3-opus-20240229")
            api_key: Anthropic API key
            base_url: Optional custom base URL
        """
        self._model_name = model_name
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=base_url,
        )
        self._capabilities = self._determine_capabilities()

    def _determine_capabilities(self) -> ModelCapability:
        """Determine capabilities based on model name."""
        caps = (
            ModelCapability.TEXT_GENERATION
            | ModelCapability.STREAMING
            | ModelCapability.TOOL_CALLING
        )

        # Claude 3+ models support vision
        if "claude-3" in self._model_name.lower():
            caps |= ModelCapability.VISION | ModelCapability.MULTIMODAL_INPUT

        # Structured output via tool use (not native JSON mode like OpenAI)
        caps |= ModelCapability.STRUCTURED_OUTPUT

        return caps

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def capabilities(self) -> ModelCapability:
        return self._capabilities

    def _convert_message(self, msg: Message) -> dict:
        """Convert internal Message to Claude format."""
        result = {"role": msg.role}

        # Claude uses "user" and "assistant" roles, no "system" in messages array
        if msg.role == "system":
            # System messages should be handled separately
            result["role"] = "user"

        # Handle content
        if isinstance(msg.content, str):
            result["content"] = msg.content
        else:
            # Multimodal content
            content_parts = []
            for part in msg.content:
                if part.content_type == ContentType.TEXT:
                    content_parts.append({"type": "text", "text": part.content})
                elif part.content_type == ContentType.IMAGE_URL:
                    # Claude expects base64 images, not URLs
                    content_parts.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": part.content,
                            },
                        }
                    )
                elif part.content_type == ContentType.IMAGE_BASE64:
                    content_parts.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": part.mime_type or "image/jpeg",
                                "data": part.content,
                            },
                        }
                    )
            result["content"] = content_parts

        return result

    def _convert_tools(self, tools: list[Tool]) -> list[dict]:
        """Convert internal Tool definitions to Claude format."""
        return [
            {
                "name": tool.function.name,
                "description": tool.function.description,
                "input_schema": tool.function.parameters,
            }
            for tool in tools
        ]

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a response using Claude API."""
        await self.validate_request(request)

        # Extract system message
        system_message = None
        messages = []
        for msg in request.messages:
            if msg.role == "system":
                system_message = msg.content if isinstance(msg.content, str) else ""
            else:
                messages.append(self._convert_message(msg))

        kwargs = {
            "model": self._model_name,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,  # Claude requires max_tokens
        }

        if system_message:
            kwargs["system"] = system_message
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.stop:
            kwargs["stop_sequences"] = request.stop
        if request.tools:
            kwargs["tools"] = self._convert_tools(request.tools)

        response = await self.client.messages.create(**kwargs)

        # Extract content
        content = None
        text_blocks = [block.text for block in response.content if block.type == "text"]
        if text_blocks:
            content = "".join(text_blocks)

        # Extract tool calls
        tool_calls = None
        tool_use_blocks = [
            block for block in response.content if block.type == "tool_use"
        ]
        if tool_use_blocks:
            tool_calls = [
                ToolCall(
                    id=block.id,
                    type="function",
                    function=FunctionCall(
                        name=block.name,
                        arguments=json.dumps(block.input),
                    ),
                )
                for block in tool_use_blocks
            ]

        return GenerateResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens
                + response.usage.output_tokens,
            },
        )

    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming response using Claude API."""
        await self.validate_request(request)

        # Extract system message
        system_message = None
        messages = []
        for msg in request.messages:
            if msg.role == "system":
                system_message = msg.content if isinstance(msg.content, str) else ""
            else:
                messages.append(self._convert_message(msg))

        kwargs = {
            "model": self._model_name,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
        }

        if system_message:
            kwargs["system"] = system_message
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.stop:
            kwargs["stop_sequences"] = request.stop
        if request.tools:
            kwargs["tools"] = self._convert_tools(request.tools)

        async with self.client.messages.stream(**kwargs) as stream:
            async for event in stream:
                content = None
                tool_calls = None
                finish_reason = None

                if event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        content = event.delta.text

                elif event.type == "content_block_stop":
                    if (
                        hasattr(event, "content_block")
                        and event.content_block.type == "tool_use"
                    ):
                        tool_calls = [
                            ToolCall(
                                id=event.content_block.id,
                                type="function",
                                function=FunctionCall(
                                    name=event.content_block.name,
                                    arguments=json.dumps(event.content_block.input),
                                ),
                            )
                        ]

                elif event.type == "message_stop":
                    finish_reason = "stop"

                if content or tool_calls or finish_reason:
                    yield StreamChunk(
                        content=content,
                        tool_calls=tool_calls,
                        finish_reason=finish_reason,
                    )


class ClaudeVertexModel(LLMModelAbstract):
    """Anthropic Claude model via Vertex AI."""

    def __init__(
        self,
        model_name: str,
        project_id: str,
        location: str = "us-east5",
    ):
        """
        Initialize Claude model via Vertex AI.

        Args:
            model_name: Model identifier (e.g., "claude-3-5-sonnet-v2@20241022")
            project_id: GCP project ID
            location: GCP location (us-east5 for Claude)
        """
        self._model_name = model_name
        self.client = AsyncAnthropicVertex(
            project_id=project_id,
            region=location,
        )
        self._capabilities = self._determine_capabilities()

    def _determine_capabilities(self) -> ModelCapability:
        """Determine capabilities based on model name."""
        caps = (
            ModelCapability.TEXT_GENERATION
            | ModelCapability.STREAMING
            | ModelCapability.TOOL_CALLING
            | ModelCapability.STRUCTURED_OUTPUT
        )

        # Claude 3+ models support vision
        if "claude-3" in self._model_name.lower():
            caps |= ModelCapability.VISION | ModelCapability.MULTIMODAL_INPUT

        return caps

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def capabilities(self) -> ModelCapability:
        return self._capabilities

    def _convert_message(self, msg: Message) -> dict:
        """Convert internal Message to Claude format."""
        result = {"role": msg.role}

        if msg.role == "system":
            result["role"] = "user"

        # Handle content
        if isinstance(msg.content, str):
            result["content"] = msg.content
        else:
            # Multimodal content
            content_parts = []
            for part in msg.content:
                if part.content_type == ContentType.TEXT:
                    content_parts.append({"type": "text", "text": part.content})
                elif part.content_type == ContentType.IMAGE_BASE64:
                    content_parts.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": part.mime_type or "image/jpeg",
                                "data": part.content,
                            },
                        }
                    )
            result["content"] = content_parts

        return result

    def _convert_tools(self, tools: list[Tool]) -> list[dict]:
        """Convert internal Tool definitions to Claude format."""
        return [
            {
                "name": tool.function.name,
                "description": tool.function.description,
                "input_schema": tool.function.parameters,
            }
            for tool in tools
        ]

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a response using Claude via Vertex AI."""
        await self.validate_request(request)

        # Extract system message
        system_message = None
        messages = []
        for msg in request.messages:
            if msg.role == "system":
                system_message = msg.content if isinstance(msg.content, str) else ""
            else:
                messages.append(self._convert_message(msg))

        kwargs = {
            "model": self._model_name,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
        }

        if system_message:
            kwargs["system"] = system_message
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.stop:
            kwargs["stop_sequences"] = request.stop
        if request.tools:
            kwargs["tools"] = self._convert_tools(request.tools)

        response = await self.client.messages.create(**kwargs)

        # Extract content
        content = None
        text_blocks = [block.text for block in response.content if block.type == "text"]
        if text_blocks:
            content = "".join(text_blocks)

        # Extract tool calls
        tool_calls = None
        tool_use_blocks = [
            block for block in response.content if block.type == "tool_use"
        ]
        if tool_use_blocks:
            tool_calls = [
                ToolCall(
                    id=block.id,
                    type="function",
                    function=FunctionCall(
                        name=block.name,
                        arguments=json.dumps(block.input),
                    ),
                )
                for block in tool_use_blocks
            ]

        return GenerateResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens
                + response.usage.output_tokens,
            },
        )

    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming response using Claude via Vertex AI."""
        await self.validate_request(request)

        # Extract system message
        system_message = None
        messages = []
        for msg in request.messages:
            if msg.role == "system":
                system_message = msg.content if isinstance(msg.content, str) else ""
            else:
                messages.append(self._convert_message(msg))

        kwargs = {
            "model": self._model_name,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
        }

        if system_message:
            kwargs["system"] = system_message
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.stop:
            kwargs["stop_sequences"] = request.stop
        if request.tools:
            kwargs["tools"] = self._convert_tools(request.tools)

        async with self.client.messages.stream(**kwargs) as stream:
            async for event in stream:
                content = None
                tool_calls = None
                finish_reason = None

                if event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        content = event.delta.text

                elif event.type == "content_block_stop":
                    if (
                        hasattr(event, "content_block")
                        and event.content_block.type == "tool_use"
                    ):
                        tool_calls = [
                            ToolCall(
                                id=event.content_block.id,
                                type="function",
                                function=FunctionCall(
                                    name=event.content_block.name,
                                    arguments=json.dumps(event.content_block.input),
                                ),
                            )
                        ]

                elif event.type == "message_stop":
                    finish_reason = "stop"

                if content or tool_calls or finish_reason:
                    yield StreamChunk(
                        content=content,
                        tool_calls=tool_calls,
                        finish_reason=finish_reason,
                    )
