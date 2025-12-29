from typing import Any, AsyncIterator

from donkit.ragops_api_gateway_client.client import RagopsAPIGatewayClient
from .model_abstract import (
    EmbeddingRequest,
    EmbeddingResponse,
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


class DonkitModel(LLMModelAbstract):
    """
    Implementation of LLMModelAbstract that proxies requests via RagopsAPIGatewayClient.
    """

    name = "donkit"

    def __init__(
        self,
        base_url: str,
        api_token: str,
        provider: str = "default",
        model_name: str | None = None,
        project_id: str | None = None,
    ):
        """
        Initialize DonkitModel.

        Args:
            base_url: Base URL for the API Gateway
            api_token: API token for authentication
            provider: The LLM provider name
                (e.g., "openai", "anthropic", "vertex", "azure_openai", "ollama", "default")
            model_name: The specific model identifier (e.g., "gpt-4o", "claude-3-opus")
            project_id: The project ID for the gateway
        """
        self.base_url = base_url
        self.api_token = api_token
        self.provider = provider
        self._model_name = model_name
        self.project_id = project_id
        self._capabilities = self._determine_capabilities()

    @property
    def model_name(self) -> str:
        return self._model_name

    @model_name.setter
    def model_name(self, value: str):
        self._model_name = value
        self._capabilities = self._determine_capabilities()

    @property
    def capabilities(self) -> ModelCapability:
        return self._capabilities

    def _determine_capabilities(self) -> ModelCapability:
        """
        Estimate capabilities based on model name.
        Since this is a proxy, we assume modern defaults but refine based on keywords.
        """
        caps = (
            ModelCapability.TEXT_GENERATION
            | ModelCapability.STREAMING
            | ModelCapability.STRUCTURED_OUTPUT
            | ModelCapability.TOOL_CALLING
            | ModelCapability.MULTIMODAL_INPUT
            | ModelCapability.EMBEDDINGS
        )
        return caps

    def _convert_message(self, msg: Message) -> dict:
        """Convert internal Message to dictionary format expected by the Gateway."""
        result: dict[str, Any] = {"role": msg.role}
        if isinstance(msg.content, str):
            result["content"] = msg.content
        else:
            # Multimodal content processing
            content_parts = []
            for part in msg.content if msg.content else []:
                content_parts.append(part.model_dump(exclude_none=True))
            result["content"] = content_parts
        if msg.tool_calls:
            result["tool_calls"] = [tc.model_dump() for tc in msg.tool_calls]
        if msg.tool_call_id:
            result["tool_call_id"] = msg.tool_call_id
        if msg.name:
            result["name"] = msg.name

        return result

    def _convert_tools(self, tools: list[Tool]) -> list[dict]:
        """Convert internal Tool definitions to Gateway dictionary format."""
        return [tool.model_dump(exclude_none=True) for tool in tools]

    def _prepare_generate_kwargs(self, request: GenerateRequest) -> dict:
        """Prepare kwargs for generate/generate_stream calls."""
        messages = [self._convert_message(msg) for msg in request.messages]
        tools_payload = self._convert_tools(request.tools) if request.tools else None

        kwargs: dict[str, Any] = {
            "provider": self.provider,
            "model_name": self._model_name,
            "messages": messages,
            "project_id": self.project_id,
        }

        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.stop:
            kwargs["stop"] = request.stop
        if tools_payload:
            kwargs["tools"] = tools_payload
            if request.tool_choice:
                if isinstance(request.tool_choice, (str, dict)):
                    kwargs["tool_choice"] = request.tool_choice
                else:
                    kwargs["tool_choice"] = "auto"
        if request.response_format:
            kwargs["response_format"] = request.response_format

        return kwargs

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a response using RagopsAPIGatewayClient."""
        await self.validate_request(request)

        kwargs = self._prepare_generate_kwargs(request)

        async with RagopsAPIGatewayClient(
            base_url=self.base_url,
            api_token=self.api_token,
        ) as client:
            response_dict = await client.generate(**kwargs)

        # Gateway returns simplified format: {content, tool_calls, finish_reason, usage}
        content = response_dict.get("content")
        finish_reason = response_dict.get("finish_reason")

        # Extract tool calls
        tool_calls = None
        if response_dict.get("tool_calls"):
            tool_calls = [
                ToolCall(
                    id=tc.get("id"),
                    type=tc.get("type", "function"),
                    function=FunctionCall(
                        name=tc.get("function", {}).get("name"),
                        arguments=tc.get("function", {}).get("arguments"),
                    ),
                )
                for tc in response_dict["tool_calls"]
            ]

        usage_data = response_dict.get("usage", {})

        return GenerateResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage={
                "prompt_tokens": usage_data.get("prompt_tokens"),
                "completion_tokens": usage_data.get("completion_tokens"),
                "total_tokens": usage_data.get("total_tokens"),
            }
            if usage_data
            else None,
            metadata=response_dict.get("metadata"),
        )

    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming response using RagopsAPIGatewayClient."""
        await self.validate_request(request)

        kwargs = self._prepare_generate_kwargs(request)

        async with RagopsAPIGatewayClient(
            base_url=self.base_url,
            api_token=self.api_token,
        ) as client:
            # Iterate over the stream from client
            async for chunk_dict in client.generate_stream(**kwargs):
                content = chunk_dict.get("content")
                finish_reason = chunk_dict.get("finish_reason")

                tool_calls = None
                if chunk_dict.get("tool_calls"):
                    tool_calls = [
                        ToolCall(
                            id=tc.get("id", ""),
                            type=tc.get("type", "function"),
                            function=FunctionCall(
                                name=tc.get("function", {}).get("name", ""),
                                arguments=tc.get("function", {}).get("arguments", ""),
                            ),
                        )
                        for tc in chunk_dict["tool_calls"]
                    ]

                yield StreamChunk(
                    content=content,
                    tool_calls=tool_calls,
                    finish_reason=finish_reason,
                    metadata=chunk_dict.get("metadata", {}),
                )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using RagopsAPIGatewayClient."""

        kwargs: dict[str, Any] = {
            "provider": self.provider,
            "input": request.input,
            "model_name": self._model_name,
            "project_id": self.project_id,
        }

        if request.dimensions:
            kwargs["dimensions"] = request.dimensions
        async with RagopsAPIGatewayClient(
            base_url=self.base_url,
            api_token=self.api_token,
        ) as client:
            response_dict = await client.embeddings(**kwargs)

        return EmbeddingResponse(**response_dict)
