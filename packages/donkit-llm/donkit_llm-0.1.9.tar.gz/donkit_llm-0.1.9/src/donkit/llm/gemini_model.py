import json
from typing import AsyncIterator

import google.genai as genai
from google.genai.types import Content, FunctionDeclaration, Part
from google.genai.types import Tool as GeminiTool

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


class GeminiModel(LLMModelAbstract):
    """Google Gemini model implementation."""

    name = "gemini"

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        project_id: str | None = None,
        location: str = "us-central1",
        use_vertex: bool = False,
    ):
        """
        Initialize Gemini model.

        Args:
            model_name: Model identifier (e.g., "gemini-2.0-flash-exp", "gemini-1.5-pro")
            api_key: Google AI API key (for AI Studio)
            project_id: GCP project ID (for Vertex AI)
            location: GCP location (for Vertex AI)
            use_vertex: Whether to use Vertex AI instead of AI Studio
        """
        self._model_name = model_name
        self._use_vertex = use_vertex

        if use_vertex:
            if not project_id:
                raise ValueError("project_id required for Vertex AI")
            self.client = genai.Client(
                vertexai=True,
                project=project_id,
                location=location,
            )
        else:
            self.client = genai.Client(api_key=api_key)

        self._capabilities = self._determine_capabilities()

    def _determine_capabilities(self) -> ModelCapability:
        """Determine capabilities based on model name."""
        caps = (
            ModelCapability.TEXT_GENERATION
            | ModelCapability.STREAMING
            | ModelCapability.STRUCTURED_OUTPUT
            | ModelCapability.TOOL_CALLING
            | ModelCapability.MULTIMODAL_INPUT
            | ModelCapability.VISION
            | ModelCapability.AUDIO_INPUT
        )
        return caps

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def capabilities(self) -> ModelCapability:
        return self._capabilities

    def _convert_message(self, msg: Message) -> Content:
        """Convert internal Message to Gemini Content format."""
        parts = []

        if isinstance(msg.content, str):
            parts.append(Part(text=msg.content))
        else:
            # Multimodal content
            for part in msg.content:
                if part.content_type == ContentType.TEXT:
                    parts.append(Part(text=part.content))
                elif part.content_type == ContentType.IMAGE_URL:
                    # Gemini expects inline data for images
                    parts.append(
                        Part(
                            inline_data={
                                "mime_type": part.mime_type or "image/jpeg",
                                "data": part.content,
                            }
                        )
                    )
                elif part.content_type == ContentType.IMAGE_BASE64:
                    parts.append(
                        Part(
                            inline_data={
                                "mime_type": part.mime_type or "image/jpeg",
                                "data": part.content,
                            }
                        )
                    )
                # Add more content types as needed

        # Map roles: assistant -> model
        role = "model" if msg.role == "assistant" else msg.role

        return Content(role=role, parts=parts)

    def _convert_tools(self, tools: list[Tool]) -> list[GeminiTool]:
        """Convert internal Tool definitions to Gemini format."""
        function_declarations = []
        for tool in tools:
            func_def = tool.function
            # Clean schema: remove $ref and $defs
            parameters = self._clean_json_schema(func_def.parameters)

            function_declarations.append(
                FunctionDeclaration(
                    name=func_def.name,
                    description=func_def.description,
                    parameters=parameters,
                )
            )

        return [GeminiTool(function_declarations=function_declarations)]

    def _clean_json_schema(self, schema: dict) -> dict:
        """
        Remove $ref and $defs from JSON Schema as Gemini doesn't support them.

        This is a simplified version - for production you'd want to resolve references.
        """
        if not isinstance(schema, dict):
            return schema

        cleaned = {}
        for key, value in schema.items():
            if key in ("$ref", "$defs", "definitions"):
                continue
            if isinstance(value, dict):
                cleaned[key] = self._clean_json_schema(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    self._clean_json_schema(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                cleaned[key] = value

        return cleaned

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a response using Gemini API."""
        await self.validate_request(request)

        # Separate system message from conversation
        system_instruction = None
        messages = []
        for msg in request.messages:
            if msg.role == "system":
                system_instruction = msg.content if isinstance(msg.content, str) else ""
            else:
                messages.append(self._convert_message(msg))

        config_kwargs = {}
        if request.temperature is not None:
            config_kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            config_kwargs["max_output_tokens"] = request.max_tokens
        if request.top_p is not None:
            config_kwargs["top_p"] = request.top_p
        if request.stop:
            config_kwargs["stop_sequences"] = request.stop
        if request.response_format:
            # Gemini uses response_mime_type and response_schema
            config_kwargs["response_mime_type"] = "application/json"
            if "schema" in request.response_format:
                config_kwargs["response_schema"] = self._clean_json_schema(
                    request.response_format["schema"]
                )

        generate_kwargs = {
            "model": self._model_name,
            "contents": messages,
        }

        if system_instruction:
            generate_kwargs["system_instruction"] = system_instruction
        if config_kwargs:
            generate_kwargs["config"] = config_kwargs
        if request.tools:
            generate_kwargs["tools"] = self._convert_tools(request.tools)

        response = await self.client.aio.models.generate_content(**generate_kwargs)

        # Extract content
        content = None
        if response.text:
            content = response.text

        # Extract tool calls (function calls in Gemini)
        tool_calls = None
        if response.candidates and response.candidates[0].content.parts:
            function_calls = []
            for part in response.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    # Convert function call args to JSON string
                    args_dict = dict(fc.args) if fc.args else {}
                    function_calls.append(
                        ToolCall(
                            id=fc.name,  # Gemini doesn't have separate ID
                            type="function",
                            function=FunctionCall(
                                name=fc.name,
                                arguments=json.dumps(args_dict),
                            ),
                        )
                    )
            if function_calls:
                tool_calls = function_calls

        # Extract finish reason
        finish_reason = None
        if response.candidates:
            finish_reason = str(response.candidates[0].finish_reason)

        # Extract usage
        usage = None
        if response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            }

        return GenerateResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
        )

    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming response using Gemini API."""
        await self.validate_request(request)

        # Separate system message from conversation
        system_instruction = None
        messages = []
        for msg in request.messages:
            if msg.role == "system":
                system_instruction = msg.content if isinstance(msg.content, str) else ""
            else:
                messages.append(self._convert_message(msg))

        config_kwargs = {}
        if request.temperature is not None:
            config_kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            config_kwargs["max_output_tokens"] = request.max_tokens
        if request.top_p is not None:
            config_kwargs["top_p"] = request.top_p
        if request.stop:
            config_kwargs["stop_sequences"] = request.stop
        if request.response_format:
            config_kwargs["response_mime_type"] = "application/json"
            if "schema" in request.response_format:
                config_kwargs["response_schema"] = self._clean_json_schema(
                    request.response_format["schema"]
                )

        generate_kwargs = {
            "model": self._model_name,
            "contents": messages,
        }

        if system_instruction:
            generate_kwargs["system_instruction"] = system_instruction
        if config_kwargs:
            generate_kwargs["config"] = config_kwargs
        if request.tools:
            generate_kwargs["tools"] = self._convert_tools(request.tools)

        stream = await self.client.aio.models.generate_content_stream(**generate_kwargs)

        async for chunk in stream:
            content = None
            if chunk.text:
                content = chunk.text

            # Extract tool calls from chunk
            tool_calls = None
            if chunk.candidates and chunk.candidates[0].content.parts:
                function_calls = []
                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        args_dict = dict(fc.args) if fc.args else {}
                        function_calls.append(
                            ToolCall(
                                id=fc.name,
                                type="function",
                                function=FunctionCall(
                                    name=fc.name,
                                    arguments=json.dumps(args_dict),
                                ),
                            )
                        )
                if function_calls:
                    tool_calls = function_calls

            finish_reason = None
            if chunk.candidates:
                finish_reason = str(chunk.candidates[0].finish_reason)

            yield StreamChunk(
                content=content,
                tool_calls=tool_calls,
                finish_reason=finish_reason,
            )


class GeminiEmbeddingModel(LLMModelAbstract):
    """Google Gemini embedding model implementation."""

    def __init__(
        self,
        model_name: str = "text-embedding-004",
        api_key: str | None = None,
        project_id: str | None = None,
        location: str = "us-central1",
        use_vertex: bool = False,
    ):
        """
        Initialize Gemini embedding model.

        Args:
            model_name: Embedding model name
            api_key: Google AI API key (for AI Studio)
            project_id: GCP project ID (for Vertex AI)
            location: GCP location (for Vertex AI)
            use_vertex: Whether to use Vertex AI
        """
        self._model_name = model_name
        self._use_vertex = use_vertex

        if use_vertex:
            if not project_id:
                raise ValueError("project_id required for Vertex AI")
            self.client = genai.Client(
                vertexai=True,
                project=project_id,
                location=location,
            )
        else:
            self.client = genai.Client(api_key=api_key)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def capabilities(self) -> ModelCapability:
        return ModelCapability.EMBEDDINGS

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        raise NotImplementedError("Embedding models do not support text generation")

    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        raise NotImplementedError("Embedding models do not support text generation")

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using Gemini API."""
        inputs = [request.input] if isinstance(request.input, str) else request.input

        # Gemini embedding API expects list of Content objects
        contents = [Content(parts=[Part(text=text)]) for text in inputs]

        response = await self.client.aio.models.embed_content(
            model=self._model_name,
            contents=contents,
        )

        embeddings = [emb.values for emb in response.embeddings]

        return EmbeddingResponse(
            embeddings=embeddings,
            usage=0,  # Gemini doesn't provide token usage for embeddings
        )
