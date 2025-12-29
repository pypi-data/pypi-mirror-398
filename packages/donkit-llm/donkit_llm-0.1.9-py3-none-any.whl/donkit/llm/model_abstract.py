from abc import ABC, abstractmethod
from enum import Enum, Flag, auto
from typing import Any, AsyncIterator, Literal

from pydantic import BaseModel


class ModelCapability(Flag):
    """Capabilities that a model can support."""

    TEXT_GENERATION = auto()
    STREAMING = auto()
    MULTIMODAL_INPUT = auto()  # Images, files, audio
    STRUCTURED_OUTPUT = auto()  # JSON schema / response format
    TOOL_CALLING = auto()  # Function calling
    EMBEDDINGS = auto()
    VISION = auto()  # Specifically image understanding
    AUDIO_INPUT = auto()
    FILE_INPUT = auto()


class ContentType(str, Enum):
    """Types of content that can be included in messages."""

    TEXT = "text"
    IMAGE_URL = "image_url"
    IMAGE_BASE64 = "image_base64"
    FILE_URL = "file_url"
    FILE_BASE64 = "file_base64"
    AUDIO_URL = "audio_url"
    AUDIO_BASE64 = "audio_base64"


class ContentPart(BaseModel):
    """A single part of message content (text, image, file, etc.)."""

    content_type: ContentType
    content: str  # Text, URL, or base64 data
    mime_type: str | None = None  # For files/images/audio
    metadata: dict[str, Any] | None = None


class Message(BaseModel):
    """A single message in a conversation."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[ContentPart] | None = (
        None  # Simple text, multimodal parts, or None for tool calls
    )
    name: str | None = None  # For tool/function messages
    tool_call_id: str | None = None  # For tool response messages
    tool_calls: list["ToolCall"] | None = None  # For assistant requesting tools


class FunctionCall(BaseModel):
    """Details of a function call."""

    name: str
    arguments: str  # JSON string of arguments


class ToolCall(BaseModel):
    """A tool/function call requested by the model."""

    id: str
    type: Literal["function"] = "function"
    function: FunctionCall


class FunctionDefinition(BaseModel):
    """Definition of a function that can be called."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for parameters
    strict: bool | None = None  # For strict schema adherence (OpenAI)


class Tool(BaseModel):
    """Definition of a tool/function available to the model."""

    type: Literal["function"] = "function"
    function: FunctionDefinition


class GenerateRequest(BaseModel):
    """Request for text generation."""

    messages: list[Message]
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    stop: list[str] | None = None
    tools: list[Tool] | None = None  # Available tools for function calling
    tool_choice: str | dict[str, Any] | None = None  # "auto", "none", or specific tool
    response_format: dict[str, Any] | None = None  # For structured output (JSON schema)
    stream: bool = False
    metadata: dict[str, Any] | None = None


class GenerateResponse(BaseModel):
    """Response from text generation."""

    content: str | None = None  # Generated text
    tool_calls: list[ToolCall] | None = None  # Requested tool calls
    finish_reason: str | None = None  # "stop", "length", "tool_calls", etc.
    usage: dict[str, int | None] | None = None  # Token usage stats
    metadata: dict[str, Any] | None = None


class StreamChunk(BaseModel):
    """A chunk of streamed response."""

    content: str | None = None
    tool_calls: list[ToolCall] | None = None  # Partial or complete tool calls
    finish_reason: str | None = None
    metadata: dict[str, Any] | None = None


class EmbeddingRequest(BaseModel):
    """Request for embeddings."""

    input: str | list[str]  # Text(s) to embed
    dimensions: int | None = None  # Output dimensionality (if supported)
    metadata: dict[str, Any] | None = None


class EmbeddingResponse(BaseModel):
    """Response from embedding generation."""

    embeddings: list[list[float]]  # List of embedding vectors
    usage: dict[str, int] | None = None
    metadata: dict[str, Any] | None = None


class LLMModelAbstract(ABC):
    """
    Abstract base class for all LLM model providers.

    Provides a unified interface for:
    - Text generation (sync and streaming)
    - Multimodal input (images, files, audio)
    - Structured output (JSON schema)
    - Tool/function calling
    - Embeddings

    Not all models support all capabilities. Use `supports_capability()` to check.
    """

    name: str = ""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name/identifier."""
        raise NotImplementedError

    @model_name.setter
    @abstractmethod
    def model_name(self, value: str) -> None:
        """Set the model name/identifier."""
        raise NotImplementedError

    @property
    @abstractmethod
    def capabilities(self) -> ModelCapability:
        """Return the capabilities supported by this model."""
        raise NotImplementedError

    def supports_capability(self, capability: ModelCapability) -> bool:
        """Check if this model supports a specific capability."""
        return capability in list(self.capabilities)

    @abstractmethod
    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """
        Generate a response for the given request.

        Args:
            request: The generation request with messages, tools, etc.

        Returns:
            The generated response with content and/or tool calls.

        Raises:
            NotImplementedError: If the model doesn't support text generation.
            ValueError: If request contains unsupported features.
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        """
        Generate a streaming response for the given request.

        Args:
            request: The generation request with messages, tools, etc.

        Yields:
            Chunks of the generated response.

        Raises:
            NotImplementedError: If the model doesn't support streaming.
            ValueError: If request contains unsupported features.
        """
        raise NotImplementedError

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings for the given input.

        Args:
            request: The embedding request with input text(s).

        Returns:
            The embedding vectors.

        Raises:
            NotImplementedError: If the model doesn't support embeddings.
        """
        raise NotImplementedError(
            f"Model {self.model_name} does not support embeddings"
        )

    async def validate_request(self, request: GenerateRequest) -> None:
        """
        Validate that the request is compatible with this model's capabilities.

        Args:
            request: The generation request to validate.

        Raises:
            ValueError: If request contains unsupported features.
        """
        # Check multimodal input
        has_multimodal = any(isinstance(msg.content, list) for msg in request.messages)
        if has_multimodal and not self.supports_capability(
            ModelCapability.MULTIMODAL_INPUT
        ):
            raise ValueError(
                f"Model {self.model_name} does not support multimodal input"
            )

        # Check tool calling
        if request.tools and not self.supports_capability(ModelCapability.TOOL_CALLING):
            raise ValueError(f"Model {self.model_name} does not support tool calling")

        # Check structured output
        if request.response_format and not self.supports_capability(
            ModelCapability.STRUCTURED_OUTPUT
        ):
            raise ValueError(
                f"Model {self.model_name} does not support structured output"
            )

        # Check streaming
        if request.stream and not self.supports_capability(ModelCapability.STREAMING):
            raise ValueError(f"Model {self.model_name} does not support streaming")


# Update forward references for Pydantic models
Message.model_rebuild()
ToolCall.model_rebuild()
Tool.model_rebuild()
