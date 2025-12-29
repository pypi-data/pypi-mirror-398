from typing import Any, AsyncIterator

from openai import AsyncAzureOpenAI, AsyncOpenAI

from .model_abstract import (
    ContentType,
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


class OpenAIModel(LLMModelAbstract):
    """OpenAI model implementation supporting GPT-4, GPT-3.5, etc."""

    name = "openai"

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: str | None = None,
        organization: str | None = None,
    ):
        """
        Initialize OpenAI model.

        Args:
            model_name: Model identifier (e.g., "gpt-4o", "gpt-4o-mini")
            api_key: OpenAI API key
            base_url: Optional custom base URL
            organization: Optional organization ID
        """
        self._model_name = model_name
        self._init_client(api_key, base_url, organization)
        self._capabilities = self._determine_capabilities()

    def _clean_schema_for_openai(self, schema: dict, is_gpt5: bool = False) -> dict:
        """Clean JSON Schema for OpenAI strict mode.

        Args:
            schema: JSON Schema to clean
            is_gpt5: Currently unused - both GPT-4o and GPT-5 support title/description

        OpenAI Structured Outputs supports:
            - title and description (useful metadata for the model)
            - Automatically adds additionalProperties: false for all objects
            - Recursively processes nested objects and arrays

        Note: The main requirement is additionalProperties: false for all objects,
        which is automatically added by this method.
        """
        cleaned = {}

        # Copy all fields, recursively processing nested structures
        for key, value in schema.items():
            if key == "properties" and isinstance(value, dict):
                # Recursively clean properties
                cleaned["properties"] = {
                    k: self._clean_schema_for_openai(v, is_gpt5)
                    if isinstance(v, dict)
                    else v
                    for k, v in value.items()
                }
            elif key == "items" and isinstance(value, dict):
                # Recursively clean array items
                cleaned["items"] = self._clean_schema_for_openai(value, is_gpt5)
            else:
                cleaned[key] = value

        # Ensure additionalProperties is false for objects (required by OpenAI)
        if cleaned.get("type") == "object" and "additionalProperties" not in cleaned:
            cleaned["additionalProperties"] = False

        return cleaned

    def _get_base_model_name(self) -> str:
        """Get base model name for capability/parameter detection.

        For Azure models, use _base_model_name; for OpenAI, use _model_name.
        """
        return getattr(self, "_base_model_name", self._model_name)

    def _is_reasoning_model(self) -> bool:
        """Check if model is a reasoning model (GPT-5, o1, o3, o4 series).

        Reasoning models don't support temperature, top_p, presence_penalty, frequency_penalty.
        They only support max_completion_tokens (not max_tokens).
        """
        model_lower = self.model_name.lower()
        # Check for reasoning model prefixes
        reasoning_prefixes = ("gpt-5", "o1", "o3", "o4", "deepseek")
        return any(model_lower.startswith(prefix) for prefix in reasoning_prefixes)

    def _supports_max_completion_tokens(self) -> bool:
        """Check if model uses max_completion_tokens instead of max_tokens.

        GPT-4.1+, GPT-5, and reasoning models (o1, o3, o4) use max_completion_tokens.
        """
        model_lower = self._get_base_model_name().lower()
        # Reasoning models always use max_completion_tokens
        if self._is_reasoning_model():
            return True
        # GPT-4.1+ series use max_completion_tokens
        if "gpt-4.1" in model_lower or "gpt-5" in model_lower:
            return True
        # GPT-4o and newer also use max_completion_tokens
        if "gpt-4o" in model_lower:
            return True
        return False

    def _init_client(
        self,
        api_key: str,
        base_url: str | None = None,
        organization: str | None = None,
    ) -> None:
        """Initialize the OpenAI client. Can be overridden by subclasses."""
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            organization=organization,
        )

    def _determine_capabilities(self) -> ModelCapability:
        """Determine capabilities based on model name."""
        caps = (
            ModelCapability.TEXT_GENERATION
            | ModelCapability.STREAMING
            | ModelCapability.STRUCTURED_OUTPUT
            | ModelCapability.TOOL_CALLING
            | ModelCapability.VISION
            | ModelCapability.MULTIMODAL_INPUT
        )

        model_lower = self._model_name.lower()
        # Audio models
        if "audio" in model_lower:
            caps |= ModelCapability.AUDIO_INPUT | ModelCapability.MULTIMODAL_INPUT

        return caps

    @property
    def model_name(self) -> str:
        return self._model_name

    @model_name.setter
    def model_name(self, value: str):
        """
        Set new model name and recalculate capabilities.

        Args:
            value: New model name
        """
        self._model_name = value
        # Recalculate capabilities based on new model name
        self._capabilities = self._determine_capabilities()

    @property
    def capabilities(self) -> ModelCapability:
        return self._capabilities

    def _convert_message(self, msg: Message) -> dict:
        """Convert internal Message to OpenAI format."""
        result = {"role": msg.role}

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
                    content_parts.append(
                        {"type": "image_url", "image_url": {"url": part.content}}
                    )
                elif part.content_type == ContentType.IMAGE_BASE64:
                    content_parts.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{part.mime_type or 'image/jpeg'};base64,{part.content}"
                            },
                        }
                    )
                # Add more content types as needed
            result["content"] = content_parts

        # Handle tool calls
        if msg.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]

        # Handle tool responses
        if msg.tool_call_id:
            result["tool_call_id"] = msg.tool_call_id

        if msg.name:
            result["name"] = msg.name

        return result

    def _convert_tools(self, tools: list[Tool]) -> list[dict]:
        """Convert internal Tool definitions to OpenAI format."""
        return [
            {
                "type": tool.type,
                "function": {
                    "name": tool.function.name,
                    "description": tool.function.description,
                    "parameters": tool.function.parameters,
                    **(
                        {"strict": tool.function.strict}
                        if tool.function.strict is not None
                        else {}
                    ),
                },
            }
            for tool in tools
        ]

    def _build_request_kwargs(
        self,
        request: GenerateRequest,
        messages: list[dict],
        stream: bool = False,
    ) -> dict:
        """Build kwargs for OpenAI API request with parameter filtering.

        Args:
            request: Generate request with parameters
            messages: Converted messages in OpenAI format
            stream: Whether this is a streaming request

        Returns:
            Dictionary of kwargs for OpenAI API call
        """
        kwargs: dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
        }

        if stream:
            kwargs["stream"] = True

        is_reasoning = self._is_reasoning_model()

        # Reasoning models (GPT-5, o1, o3, o4) don't support temperature/top_p
        # They use fixed temperature=1 and top_p=1 internally
        if not is_reasoning:
            if request.temperature is not None:
                kwargs["temperature"] = request.temperature
            if request.top_p is not None:
                kwargs["top_p"] = request.top_p

        # Handle max_tokens vs max_completion_tokens
        if request.max_tokens is not None:
            # Clamp value between 8192 and 16384
            clamped_tokens = max(8192, min(request.max_tokens, 16384))
            if self._supports_max_completion_tokens():
                # GPT-4.1+, GPT-5, reasoning models use max_completion_tokens
                kwargs["max_completion_tokens"] = clamped_tokens
            else:
                # Older models use max_tokens
                kwargs["max_tokens"] = clamped_tokens

        if request.stop:
            kwargs["stop"] = request.stop

        if request.tools:
            kwargs["tools"] = self._convert_tools(request.tools)
            # Only add tool_choice if tools are present
            if request.tool_choice:
                # Validate tool_choice - OpenAI only supports 'none', 'auto', 'required', or dict
                if isinstance(request.tool_choice, str):
                    if request.tool_choice in ("none", "auto", "required"):
                        kwargs["tool_choice"] = request.tool_choice
                    else:
                        # Invalid string value - default to 'auto'
                        kwargs["tool_choice"] = "auto"
                elif isinstance(request.tool_choice, dict):
                    kwargs["tool_choice"] = request.tool_choice

        if request.response_format:
            # OpenAI requires specific format for structured output
            # If response_format is a JSON Schema dict with "type": "object", wrap it
            if isinstance(request.response_format, dict):
                if request.response_format.get("type") == "object":
                    # This is a JSON Schema - clean and wrap it in json_schema format
                    # GPT-5 and reasoning models need stricter schema cleaning
                    is_gpt5 = self._is_reasoning_model()
                    cleaned_schema = self._clean_schema_for_openai(
                        request.response_format, is_gpt5=is_gpt5
                    )
                    kwargs["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "response",
                            "strict": True,
                            "schema": cleaned_schema,
                        },
                    }
                else:
                    # Already in correct format or simple type
                    kwargs["response_format"] = request.response_format
            else:
                kwargs["response_format"] = request.response_format

        return kwargs

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a response using OpenAI API."""
        await self.validate_request(request)

        messages = [self._convert_message(msg) for msg in request.messages]
        kwargs = self._build_request_kwargs(request, messages, stream=False)

        # Log request to LLM
        # request_log = {
        #     "model": self._model_name,
        #     "messages": messages,
        #     "temperature": kwargs.get("temperature"),
        #     "max_tokens": kwargs.get("max_tokens")
        #     or kwargs.get("max_completion_tokens"),
        #     "top_p": kwargs.get("top_p"),
        #     "tools": kwargs.get("tools"),
        #     "tool_choice": kwargs.get("tool_choice"),
        # }

        try:
            response = await self.client.chat.completions.create(**kwargs)

            if not response.choices:
                return GenerateResponse(content="Error: No response choices returned")

            choice = response.choices[0]
            message = choice.message

            # Extract content
            content = message.content

            # Extract tool calls
            tool_calls = None
            if message.tool_calls:
                tool_calls = [
                    ToolCall(
                        id=tc.id,
                        type=tc.type,
                        function=FunctionCall(
                            name=tc.function.name, arguments=tc.function.arguments
                        ),
                    )
                    for tc in message.tool_calls
                ]

            # Log response from LLM
            # response_log = {
            #     "content": content,
            #     "tool_calls": [
            #         {
            #             "id": tc.id,
            #             "type": tc.type,
            #             "function": {
            #                 "name": tc.function.name,
            #                 "arguments": tc.function.arguments,
            #             },
            #         }
            #         for tc in (message.tool_calls or [])
            #     ],
            #     "finish_reason": choice.finish_reason,
            #     "usage": {
            #         "prompt_tokens": response.usage.prompt_tokens,
            #         "completion_tokens": response.usage.completion_tokens,
            #         "total_tokens": response.usage.total_tokens,
            #     }
            #     if response.usage
            #     else None,
            # }
            # logger.info(
            #     f"LLM Response (generate): {json.dumps(response_log, ensure_ascii=False, indent=2)}"
            # )

            return GenerateResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage
                else None,
            )
        except Exception as e:
            error_msg = str(e)
            return GenerateResponse(content=f"Error: {error_msg}")

    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming response using OpenAI API."""
        await self.validate_request(request)

        messages = [self._convert_message(msg) for msg in request.messages]
        kwargs = self._build_request_kwargs(request, messages, stream=True)

        # Log request to LLM
        # request_log = {
        #     "model": self._model_name,
        #     "messages": messages,
        #     "temperature": kwargs.get("temperature"),
        #     "max_tokens": kwargs.get("max_tokens")
        #     or kwargs.get("max_completion_tokens"),
        #     "top_p": kwargs.get("top_p"),
        #     "tools": kwargs.get("tools"),
        #     "tool_choice": kwargs.get("tool_choice"),
        #     "stream": True,
        # }
        # logger.info(
        #     f"LLM Request (generate_stream): {json.dumps(request_log, ensure_ascii=False, indent=2)}"
        # )

        try:
            stream = await self.client.chat.completions.create(**kwargs)

            # Accumulate tool calls across chunks
            accumulated_tool_calls: dict[int, dict] = {}

            async for chunk in stream:
                if not chunk.choices:
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                # Yield text content if present
                if delta.content:
                    # Log chunk content: uncomment to debug
                    # chunk_log = {"content": delta.content}
                    # logger.info(
                    #     f"LLM Stream Chunk: {json.dumps(chunk_log, ensure_ascii=False)}"
                    # )
                    yield StreamChunk(content=delta.content, tool_calls=None)

                # Accumulate tool calls
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in accumulated_tool_calls:
                            accumulated_tool_calls[idx] = {
                                "id": tc_delta.id or "",
                                "type": tc_delta.type or "function",
                                "function": {"name": "", "arguments": ""},
                            }

                        if tc_delta.id:
                            accumulated_tool_calls[idx]["id"] = tc_delta.id
                        if tc_delta.type:
                            accumulated_tool_calls[idx]["type"] = tc_delta.type
                        if tc_delta.function:
                            if tc_delta.function.name:
                                accumulated_tool_calls[idx]["function"]["name"] = (
                                    tc_delta.function.name
                                )
                            if tc_delta.function.arguments:
                                accumulated_tool_calls[idx]["function"][
                                    "arguments"
                                ] += tc_delta.function.arguments

                # Yield finish reason if present
                if choice.finish_reason:
                    yield StreamChunk(content=None, finish_reason=choice.finish_reason)

            # Yield final response with accumulated tool calls if any
            if accumulated_tool_calls:
                tool_calls = [
                    ToolCall(
                        id=tc_data["id"],
                        type=tc_data["type"],
                        function=FunctionCall(
                            name=tc_data["function"]["name"],
                            arguments=tc_data["function"]["arguments"],
                        ),
                    )
                    for tc_data in accumulated_tool_calls.values()
                ]
                # Log final tool calls
                # tool_calls_log = [
                #     {
                #         "id": tc.id,
                #         "type": tc.type,
                #         "function": {
                #             "name": tc.function.name,
                #             "arguments": tc.function.arguments,
                #         },
                #     }
                #     for tc in tool_calls
                # ]
                # logger.info(
                #     f"LLM Stream Final Tool Calls: {json.dumps(tool_calls_log, ensure_ascii=False, indent=2)}"
                # )
                yield StreamChunk(content=None, tool_calls=tool_calls)

        except Exception as e:
            error_msg = str(e)
            yield StreamChunk(content=f"Error: {error_msg}")


class AzureOpenAIModel(OpenAIModel):
    """Azure OpenAI model implementation."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        azure_endpoint: str,
        deployment_name: str,
        api_version: str = "2024-08-01-preview",
    ):
        """
        Initialize Azure OpenAI model.

        Args:
            model_name: Model identifier for capability detection
            api_key: Azure OpenAI API key
            azure_endpoint: Azure endpoint URL
            deployment_name: Azure deployment name
            api_version: API version
        """
        # Store Azure-specific parameters before calling super().__init__()
        self._api_key = api_key
        self._azure_endpoint = azure_endpoint
        self._api_version = api_version
        self._model_name = model_name
        self._deployment_name = deployment_name

        # Call parent constructor (will call our overridden _init_client)
        super().__init__(model_name, api_key)

    def _init_client(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        organization: str | None = None,
    ) -> None:
        """Initialize Azure OpenAI client."""
        self.client = AsyncAzureOpenAI(
            api_key=self._api_key,
            azure_endpoint=self._azure_endpoint,
            api_version=self._api_version,
            azure_deployment=self._deployment_name,
        )

    def _determine_capabilities(self) -> ModelCapability:
        """Determine capabilities based on base model name."""
        caps = (
            ModelCapability.TEXT_GENERATION
            | ModelCapability.STREAMING
            | ModelCapability.TOOL_CALLING
            | ModelCapability.STRUCTURED_OUTPUT
            | ModelCapability.MULTIMODAL_INPUT
            | ModelCapability.VISION
        )
        return caps

    @property
    def deployment_name(self) -> str:
        """Get current deployment name."""
        return self._deployment_name

    @deployment_name.setter
    def deployment_name(self, value: str):
        """
        Set new deployment name and reinitialize client.

        Args:
            value: New deployment name
        """
        self._deployment_name = value
        # Reinitialize client with new deployment name
        self._init_client(self._api_key)

    @property
    def model_name(self) -> str:
        return self._model_name

    @model_name.setter
    def model_name(self, value: str):
        """
        Set new model name and recalculate capabilities.

        Args:
            value: New model name
        """
        self._model_name = value
        self._deployment_name = value
        self.client = AsyncAzureOpenAI(
            api_key=self._api_key,
            azure_endpoint=self._azure_endpoint,
            api_version=self._api_version,
            azure_deployment=value,
        )

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a response using Azure OpenAI API with parameter adaptation."""
        # Azure OpenAI uses deployment name instead of model name
        # Temporarily override model_name with deployment_name
        original_model = self._model_name
        self._model_name = self._deployment_name
        try:
            return await super().generate(request)
        finally:
            self._model_name = original_model

    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming response using Azure OpenAI API."""
        # Azure OpenAI uses deployment name instead of model name
        original_model = self._model_name
        self._model_name = self._deployment_name
        try:
            async for chunk in super().generate_stream(request):
                yield chunk
        finally:
            self._model_name = original_model


class OpenAIEmbeddingModel(LLMModelAbstract):
    """OpenAI embedding model implementation."""

    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize OpenAI embedding model.

        Args:
            model_name: Embedding model name
            api_key: OpenAI API key
            base_url: Optional custom base URL
        """
        self._base_url = base_url
        self._api_key = api_key
        self._model_name = model_name
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._capabilities = self._determine_capabilities()

    def _determine_capabilities(self) -> ModelCapability:
        """Determine capabilities based on model name."""
        caps = ModelCapability.EMBEDDINGS
        return caps

    @property
    def capabilities(self) -> ModelCapability:
        """Return the capabilities supported by this model."""
        return self._capabilities

    def supports_capability(self, capability: ModelCapability) -> bool:
        """Check if this model supports a specific capability."""
        return bool(self.capabilities & capability)

    @property
    def model_name(self) -> str:
        return self._model_name

    @model_name.setter
    def model_name(self, value: str):
        """
        Set new model name and recalculate capabilities.

        Args:
            value: New model name
        """
        self._model_name = value
        # Recalculate capabilities based on new model name

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, value: str):
        self._base_url = value
        self.client = AsyncOpenAI(api_key=self._api_key, base_url=value)

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, value: str):
        self._api_key = value
        self.client = AsyncOpenAI(api_key=value, base_url=self._base_url)

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        raise NotImplementedError("Embedding models do not support text generation")

    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        raise NotImplementedError("Embedding models do not support text generation")

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using OpenAI API."""
        inputs = [request.input] if isinstance(request.input, str) else request.input

        kwargs = {"model": self._model_name, "input": inputs}

        if request.dimensions:
            kwargs["dimensions"] = request.dimensions

        try:
            response = await self.client.embeddings.create(**kwargs)

            embeddings = [item.embedding for item in response.data]

            return EmbeddingResponse(
                embeddings=embeddings,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage
                else None,
                metadata={
                    "dimensionality": len(embeddings[0]) if len(embeddings) > 0 else 0
                },
            )
        except Exception as e:
            raise Exception(f"Failed to generate embeddings: {e}")


class AzureOpenAIEmbeddingModel(LLMModelAbstract):
    """Azure OpenAI embedding model implementation."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        azure_endpoint: str,
        deployment_name: str,
        api_version: str = "2024-08-01-preview",
    ):
        """
        Initialize Azure OpenAI embedding model.

        Args:
            model_name: Model identifier (e.g., "text-embedding-3-small")
            api_key: Azure OpenAI API key
            azure_endpoint: Azure endpoint URL
            deployment_name: Azure deployment name
            api_version: API version
        """
        self._model_name = model_name
        self._deployment_name = deployment_name
        self._api_key = api_key
        self._azure_endpoint = azure_endpoint
        self._api_version = api_version

        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            azure_deployment=deployment_name,
        )

    @property
    def model_name(self) -> str:
        return self._model_name

    @model_name.setter
    def model_name(self, value: str):
        """
        Set new model name.

        Args:
            value: New model name
        """
        self._model_name = value
        self._deployment_name = value
        self.client = AsyncAzureOpenAI(
            api_key=self._api_key,
            azure_endpoint=self._azure_endpoint,
            api_version=self._api_version,
            azure_deployment=value,
        )

    @property
    def capabilities(self) -> ModelCapability:
        return ModelCapability.EMBEDDINGS

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        raise NotImplementedError("Embedding models does not support text generation")

    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        raise NotImplementedError("Embedding models does not support text generation")

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using Azure OpenAI API."""
        inputs = [request.input] if isinstance(request.input, str) else request.input

        kwargs = {"model": self._deployment_name, "input": inputs}

        if request.dimensions:
            kwargs["dimensions"] = request.dimensions

        try:
            response = await self.client.embeddings.create(**kwargs)

            embeddings = [item.embedding for item in response.data]

            return EmbeddingResponse(
                embeddings=embeddings,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage
                else None,
                metadata={
                    "dimensions": len(embeddings[0]) if len(embeddings) > 0 else 0
                },
            )
        except Exception as e:
            raise Exception(f"Failed to generate embeddings: {e}")
