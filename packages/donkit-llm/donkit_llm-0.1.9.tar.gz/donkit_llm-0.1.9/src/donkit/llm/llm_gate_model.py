from typing import Any, AsyncIterator

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


class LLMGateModel(LLMModelAbstract):
    name = "llm_gate"

    @staticmethod
    def _get_client() -> type:
        try:
            from donkit.llm_gate.client import LLMGate

            return LLMGate
        except Exception as e:
            raise ImportError(
                "LLMGateModel requires 'donkit-llm-gate-client' to be installed"
            ) from e

    def __init__(
        self,
        base_url: str = "http://localhost:8002",
        provider: str = "default",
        model_name: str | None = None,
        embedding_provider: str | None = None,
        embedding_model_name: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
    ):
        self.base_url = base_url
        self.provider = provider
        self._model_name = model_name
        self.embedding_provider = embedding_provider
        self.embedding_model_name = embedding_model_name
        self.user_id = user_id
        self.project_id = project_id
        self._capabilities = self._determine_capabilities()

    @property
    def model_name(self) -> str:
        return self._model_name or "default"

    @model_name.setter
    def model_name(self, value: str):
        self._model_name = value
        self._capabilities = self._determine_capabilities()

    @property
    def capabilities(self) -> ModelCapability:
        return self._capabilities

    def _determine_capabilities(self) -> ModelCapability:
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
        result: dict[str, Any] = {"role": msg.role}
        if isinstance(msg.content, str):
            result["content"] = msg.content
        else:
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
        return [tool.model_dump(exclude_none=True) for tool in tools]

    def _prepare_generate_kwargs(self, request: GenerateRequest) -> dict:
        messages = [self._convert_message(msg) for msg in request.messages]
        tools_payload = self._convert_tools(request.tools) if request.tools else None

        kwargs: dict[str, Any] = {
            "provider": self.provider,
            "model_name": self.model_name,
            "messages": messages,
            "user_id": self.user_id,
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
        await self.validate_request(request)

        kwargs = self._prepare_generate_kwargs(request)

        llm_gate = self._get_client()

        async with llm_gate(base_url=self.base_url) as client:
            response = await client.generate(**kwargs)

        tool_calls = None
        if response.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    type=tc.type,
                    function=FunctionCall(
                        name=tc.function.name,
                        arguments=tc.function.arguments,
                    ),
                )
                for tc in response.tool_calls
            ]

        return GenerateResponse(
            content=response.content,
            tool_calls=tool_calls,
            finish_reason=response.finish_reason,
            usage=response.usage,
            metadata=response.metadata,
        )

    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        await self.validate_request(request)

        kwargs = self._prepare_generate_kwargs(request)

        llm_gate = self._get_client()

        async with llm_gate(base_url=self.base_url) as client:
            async for chunk in client.generate_stream(**kwargs):
                tool_calls = None
                if chunk.tool_calls:
                    tool_calls = [
                        ToolCall(
                            id=tc.id,
                            type=tc.type,
                            function=FunctionCall(
                                name=tc.function.name,
                                arguments=tc.function.arguments,
                            ),
                        )
                        for tc in chunk.tool_calls
                    ]

                yield StreamChunk(
                    content=chunk.content,
                    tool_calls=tool_calls,
                    finish_reason=chunk.finish_reason,
                )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        provider = self.embedding_provider or self.provider
        model_name = self.embedding_model_name

        llm_gate = self._get_client()

        async with llm_gate(base_url=self.base_url) as client:
            response = await client.embeddings(
                provider=provider,
                input=request.input,
                model_name=model_name,
                dimensions=request.dimensions,
                user_id=self.user_id,
                project_id=self.project_id,
            )

        return EmbeddingResponse(
            embeddings=response.embeddings,
            usage=response.usage,
            metadata=response.metadata,
        )
