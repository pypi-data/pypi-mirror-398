import json
import base64
from typing import Any, AsyncIterator

import google.genai as genai
from google.genai.types import Blob, Content, FunctionDeclaration, Part
from google.genai.types import Tool as GeminiTool
from google.oauth2 import service_account

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


class VertexAIModel(LLMModelAbstract):
    """
    Vertex AI model implementation using google-genai SDK.

    Supports all models available on Vertex AI:
    - Gemini models (gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash-exp)
    - Claude models via Vertex AI (claude-3-5-sonnet-v2@20241022, etc.)
    """

    name = "vertex"

    def __init__(
        self,
        project_id: str,
        model_name: str = "gemini-2.5-flash",
        location: str = "us-central1",
        credentials: dict | None = None,
    ):
        """
        Initialize Vertex AI model via google-genai SDK.

        Args:
            model_name: Model identifier (e.g., "gemini-2.0-flash-exp", "claude-3-5-sonnet-v2@20241022")
            project_id: GCP project ID
            location: GCP location (us-central1 for Gemini, us-east5 for Claude)
            credentials: Optional service account credentials dict
        """
        self._model_name = model_name
        self._project_id = project_id
        self._location = location

        # Initialize client with Vertex AI
        client_kwargs = {
            "vertexai": True,
            "project": project_id,
            "location": location,
        }

        # Add credentials if provided
        if credentials:
            creds = service_account.Credentials.from_service_account_info(
                credentials, scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            client_kwargs["credentials"] = creds

        self.client = genai.Client(**client_kwargs)
        self._capabilities = self._determine_capabilities()

    def _determine_capabilities(self) -> ModelCapability:
        """Determine capabilities based on model name."""
        caps = (
            ModelCapability.TEXT_GENERATION
            | ModelCapability.STREAMING
            | ModelCapability.STRUCTURED_OUTPUT
            | ModelCapability.TOOL_CALLING
            | ModelCapability.VISION
            | ModelCapability.MULTIMODAL_INPUT
            | ModelCapability.AUDIO_INPUT
        )
        return caps

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

    def _convert_message(self, msg: Message) -> Content:
        """Convert internal Message to Vertex AI Content format."""
        parts = []

        if isinstance(msg.content, str):
            parts.append(Part(text=msg.content))
        else:
            # Multimodal content
            for part in msg.content:
                if part.content_type == ContentType.TEXT:
                    parts.append(Part(text=part.content))
                elif part.content_type == ContentType.IMAGE_URL:
                    # For URLs, we'd need to fetch and convert to inline data
                    parts.append(
                        Part(
                            inline_data=Blob(
                                mime_type=part.mime_type or "image/jpeg",
                                data=part.content.encode(),
                            )
                        )
                    )
                elif part.content_type == ContentType.IMAGE_BASE64:
                    # part.content is base64 string; Vertex needs raw bytes
                    raw = base64.b64decode(part.content, validate=True)
                    parts.append(
                        Part(
                            inline_data=Blob(
                                mime_type=part.mime_type or "image/png",
                                data=raw,
                            )
                        )
                    )
                elif part.content_type == ContentType.AUDIO_BASE64:
                    raw = base64.b64decode(part.content, validate=True)
                    parts.append(
                        Part(
                            inline_data=Blob(
                                mime_type=part.mime_type or "audio/wav",
                                data=raw,
                            )
                        )
                    )
                elif part.content_type == ContentType.FILE_BASE64:
                    raw = base64.b64decode(part.content, validate=True)
                    parts.append(
                        Part(
                            inline_data=Blob(
                                mime_type=part.mime_type or "application/octet-stream",
                                data=raw,
                            )
                        )
                    )
        return Content(role=msg.role, parts=parts)

    def _convert_tools(self, tools: list[Tool]) -> list[GeminiTool]:
        """Convert internal Tool definitions to Vertex AI format."""
        function_declarations = []
        for tool in tools:
            func_def = tool.function
            # Clean schema: remove $ref and $defs (Vertex AI doesn't support them)
            parameters = self._clean_json_schema(func_def.parameters)

            function_declarations.append(
                FunctionDeclaration(
                    name=func_def.name,
                    description=func_def.description,
                    parameters=parameters,
                )
            )

        return [GeminiTool(function_declarations=function_declarations)]

    def _parse_response(self, response) -> tuple[str | None, list[ToolCall] | None]:
        """Parse a genai response (or stream chunk) into plain text and tool calls."""
        calls: list[ToolCall] = []

        try:
            cand_list = response.candidates
        except AttributeError:
            cand_list = None
        if not cand_list:
            return None, None

        cand = cand_list[0]

        try:
            parts = cand.content.parts or []
        except AttributeError:
            parts = []

        # Collect text and tool calls in a single pass
        collected_text: list[str] = []
        for p in parts:
            # Try to get text from this part
            try:
                t = p.text
                if t:
                    collected_text.append(t)
            except AttributeError:
                pass

            # Try to get function_call from this part
            try:
                fc = p.function_call
                if fc:
                    # Extract function name and arguments
                    try:
                        name = fc.name
                    except AttributeError:
                        name = ""

                    if not name:
                        continue

                    try:
                        args = dict(fc.args) if fc.args else {}
                    except (AttributeError, TypeError):
                        args = {}

                    calls.append(
                        ToolCall(
                            id=name,
                            type="function",
                            function=FunctionCall(
                                name=name,
                                arguments=json.dumps(args),
                            ),
                        )
                    )
            except AttributeError:
                pass

        text = "".join(collected_text)
        return text or None, calls or None

    def _clean_json_schema(self, schema: dict | None) -> dict:
        """
        Transform an arbitrary JSON Schema-like dict (possibly produced by Pydantic)
        into a format compatible with google.genai by:
        - Inlining $ref by replacing references with actual schemas from $defs
        - Removing $defs after inlining all references
        - Renaming unsupported keys to the SDK's expected snake_case
        - Recursively converting nested schemas (properties, items, anyOf)
        - Preserving fields supported by the SDK Schema model
        """
        if not isinstance(schema, dict):
            return {}

        # Step 1: Inline $ref references before any conversion
        defs = schema.get("$defs", {})

        def inline_refs(obj, definitions):
            """Recursively inline $ref references."""
            if isinstance(obj, dict):
                # If this object has a $ref, replace it with the referenced schema
                if "$ref" in obj:
                    ref_path = obj["$ref"]
                    if ref_path.startswith("#/$defs/"):
                        ref_name = ref_path.replace("#/$defs/", "")
                        if ref_name in definitions:
                            # Get the referenced schema and inline it recursively
                            referenced = definitions[ref_name].copy()
                            # Preserve description and default from the referencing object
                            if "description" in obj and "description" not in referenced:
                                referenced["description"] = obj["description"]
                            if "default" in obj:
                                referenced["default"] = obj["default"]
                            return inline_refs(referenced, definitions)
                    # If can't resolve, remove the $ref
                    return {k: v for k, v in obj.items() if k != "$ref"}

                # Recursively process all properties
                result = {}
                for key, value in obj.items():
                    if key == "$defs":
                        continue  # Remove $defs after inlining
                    # Skip additionalProperties: true as it's not well supported
                    if key == "additionalProperties" and value is True:
                        continue
                    result[key] = inline_refs(value, definitions)
                return result
            elif isinstance(obj, list):
                return [inline_refs(item, definitions) for item in obj]
            else:
                return obj

        # Inline all references
        schema = inline_refs(schema, defs)

        # Step 2: Convert to SDK schema format
        # Mapping from common JSON Schema/OpenAPI keys to google-genai Schema fields
        key_map = {
            "anyOf": "any_of",
            "additionalProperties": "additional_properties",
            "maxItems": "max_items",
            "maxLength": "max_length",
            "maxProperties": "max_properties",
            "minItems": "min_items",
            "minLength": "min_length",
            "minProperties": "min_properties",
            "propertyOrdering": "property_ordering",
        }

        def convert(obj):
            if isinstance(obj, dict):
                out: dict[str, object] = {}
                for k, v in obj.items():
                    if k == "const":
                        out["enum"] = [v]
                        continue

                    kk = key_map.get(k, k)
                    if kk == "properties" and isinstance(v, dict):
                        # properties: dict[str, Schema]
                        out[kk] = {pk: convert(pv) for pk, pv in v.items()}
                    elif kk == "items":
                        # items: Schema (treat list as first item schema)
                        if isinstance(v, list) and v:
                            out[kk] = convert(v[0])
                        else:
                            out[kk] = convert(v)
                    elif kk == "any_of" and isinstance(v, list):
                        out[kk] = [convert(iv) for iv in v]
                    else:
                        out[kk] = convert(v)
                return out
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            else:
                return obj

        return convert(schema)

    def _build_config_kwargs(
        self, request: GenerateRequest, system_instruction: str | None = None
    ) -> dict[str, Any]:
        """Build configuration kwargs for Vertex AI generate/generate_stream."""
        config_kwargs: dict[str, Any] = {
            "temperature": request.temperature
            if request.temperature is not None
            else 0.2,
            "top_p": request.top_p if request.top_p is not None else 0.95,
            "max_output_tokens": request.max_tokens
            if request.max_tokens is not None
            else 8192,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if request.stop:
            config_kwargs["stop_sequences"] = request.stop
        if request.response_format:
            config_kwargs["response_mime_type"] = "application/json"
            # If response_format is a JSON Schema dict with "type": "object", use it directly
            if isinstance(request.response_format, dict):
                if request.response_format.get("type") == "object":
                    # This is a JSON Schema - use it directly
                    config_kwargs["response_schema"] = self._clean_json_schema(
                        request.response_format
                    )
                elif "schema" in request.response_format:
                    # Already wrapped in schema key
                    config_kwargs["response_schema"] = self._clean_json_schema(
                        request.response_format["schema"]
                    )
        return config_kwargs

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a response using Vertex AI."""
        await self.validate_request(request)

        def _safe_text(text: str) -> str:
            try:
                return text.encode("utf-8", errors="replace").decode(
                    "utf-8", errors="replace"
                )
            except Exception:
                return ""

        contents: list[Content] = []
        system_instruction = ""

        # Group consecutive tool messages into single Content
        i = 0
        while i < len(request.messages):
            m = request.messages[i]

            if m.role == "tool":
                # Collect all consecutive tool messages
                tool_parts = []
                while i < len(request.messages) and request.messages[i].role == "tool":
                    tool_msg = request.messages[i]
                    content_str = (
                        tool_msg.content
                        if isinstance(tool_msg.content, str)
                        else str(tool_msg.content)
                    )
                    part = Part.from_function_response(
                        name=getattr(tool_msg, "name", "") or "",
                        response={"result": _safe_text(content_str)},
                    )
                    tool_parts.append(part)
                    i += 1
                # Add all tool responses as a single Content
                if tool_parts:
                    contents.append(Content(role="function", parts=tool_parts))
                continue
            elif m.role == "system":
                content_str = (
                    m.content if isinstance(m.content, str) else str(m.content)
                )
                system_instruction += _safe_text(content_str).strip()
                i += 1
            elif m.role == "assistant":
                # Check if message has tool_calls attribute
                if hasattr(m, "tool_calls") and m.tool_calls:
                    # Assistant message with tool calls
                    parts_list = []
                    for tc in m.tool_calls:
                        if not tc.function.name:
                            continue
                        args = (
                            json.loads(tc.function.arguments)
                            if isinstance(tc.function.arguments, str)
                            else tc.function.arguments
                        )
                        if not isinstance(args, dict):
                            args = {}
                        part = Part.from_function_call(name=tc.function.name, args=args)
                        parts_list.append(part)
                    if parts_list:
                        contents.append(Content(role="model", parts=parts_list))
                else:
                    # Regular assistant text response
                    content_str = (
                        m.content if isinstance(m.content, str) else str(m.content)
                    )
                    if content_str:
                        part = Part(text=_safe_text(content_str))
                        contents.append(Content(role="model", parts=[part]))
                i += 1
            else:
                # User message - use _convert_message to handle multimodal content
                user_content = self._convert_message(m)
                contents.append(user_content)
                i += 1

        config_kwargs = self._build_config_kwargs(request, system_instruction)
        config = genai.types.GenerateContentConfig(**config_kwargs)

        if request.tools:
            function_declarations: list[FunctionDeclaration] = []
            for t in request.tools:
                schema_obj = self._clean_json_schema(t.function.parameters or {})
                function_declarations.append(
                    FunctionDeclaration(
                        name=t.function.name,
                        description=t.function.description or "",
                        parameters=schema_obj,
                    )
                )
            gen_tools = [GeminiTool(function_declarations=function_declarations)]
            config.tools = gen_tools

        try:
            response = await self.client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=config,
            )
            text, tool_calls = self._parse_response(response)

            # If no text and no tool calls, check for errors in response
            if not text and not tool_calls:
                try:
                    # Check for blocking reasons or errors
                    if hasattr(response, "candidates") and response.candidates:
                        cand = response.candidates[0]
                        if hasattr(cand, "finish_reason") and cand.finish_reason:
                            finish_reason = cand.finish_reason
                            if finish_reason not in ("STOP", None):
                                error_msg = (
                                    f"Model finished with reason: {finish_reason}"
                                )
                                return GenerateResponse(content=f"Warning: {error_msg}")
                    # Check for safety ratings that might block content
                    if hasattr(response, "candidates") and response.candidates:
                        cand = response.candidates[0]
                        if hasattr(cand, "safety_ratings"):
                            blocked = any(
                                getattr(r, "blocked", False)
                                for r in getattr(cand, "safety_ratings", [])
                            )
                            if blocked:
                                error_msg = "Response was blocked by safety filters"
                                return GenerateResponse(content=f"Warning: {error_msg}")
                except Exception:
                    pass  # If we can't check, just return empty

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
                content=text,
                tool_calls=tool_calls,
                finish_reason=finish_reason,
                usage=usage,
            )
        except Exception as e:
            error_msg = str(e)
            # Return error message instead of empty response
            return GenerateResponse(content=f"Error: {error_msg}")

    async def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming response using Vertex AI."""
        await self.validate_request(request)

        def _safe_text(text: str) -> str:
            try:
                return text.encode("utf-8", errors="replace").decode(
                    "utf-8", errors="replace"
                )
            except Exception:
                return ""

        contents: list[Content] = []
        system_instruction = ""

        # Convert messages to genai format (same logic as generate())
        i = 0
        while i < len(request.messages):
            m = request.messages[i]

            if m.role == "tool":
                # Collect all consecutive tool messages
                tool_parts = []
                while i < len(request.messages) and request.messages[i].role == "tool":
                    tool_msg = request.messages[i]
                    content_str = (
                        tool_msg.content
                        if isinstance(tool_msg.content, str)
                        else str(tool_msg.content)
                    )
                    part = Part.from_function_response(
                        name=getattr(tool_msg, "name", "") or "",
                        response={"result": _safe_text(content_str)},
                    )
                    tool_parts.append(part)
                    i += 1
                if tool_parts:
                    contents.append(Content(role="function", parts=tool_parts))
                continue
            elif m.role == "system":
                content_str = (
                    m.content if isinstance(m.content, str) else str(m.content)
                )
                system_instruction += _safe_text(content_str).strip()
                i += 1
            elif m.role == "assistant":
                if hasattr(m, "tool_calls") and m.tool_calls:
                    parts_list = []
                    for tc in m.tool_calls:
                        if not tc.function.name:
                            continue
                        args = (
                            json.loads(tc.function.arguments)
                            if isinstance(tc.function.arguments, str)
                            else tc.function.arguments
                        )
                        if not isinstance(args, dict):
                            args = {}
                        part = Part.from_function_call(name=tc.function.name, args=args)
                        parts_list.append(part)
                    if parts_list:
                        contents.append(Content(role="model", parts=parts_list))
                else:
                    content_str = (
                        m.content if isinstance(m.content, str) else str(m.content)
                    )
                    if content_str:
                        part = Part(text=_safe_text(content_str))
                        contents.append(Content(role="model", parts=[part]))
                i += 1
            else:
                # User message - use _convert_message to handle multimodal content
                user_content = self._convert_message(m)
                contents.append(user_content)
                i += 1

        config_kwargs = self._build_config_kwargs(request, system_instruction)
        config_kwargs["automatic_function_calling"] = (
            genai.types.AutomaticFunctionCallingConfig(maximum_remote_calls=100)
        )

        config = genai.types.GenerateContentConfig(**config_kwargs)

        if request.tools:
            function_declarations: list[FunctionDeclaration] = []
            for t in request.tools:
                schema_obj = self._clean_json_schema(t.function.parameters or {})
                function_declarations.append(
                    FunctionDeclaration(
                        name=t.function.name,
                        description=t.function.description or "",
                        parameters=schema_obj,
                    )
                )
            gen_tools = [GeminiTool(function_declarations=function_declarations)]
            config.tools = gen_tools

        try:
            # Use generate_content_stream for streaming
            stream = await self.client.aio.models.generate_content_stream(
                model=self._model_name,
                contents=contents,
                config=config,
            )

            async for chunk in stream:
                text, tool_calls = self._parse_response(chunk)

                # Yield text chunks as they come
                if text:
                    yield StreamChunk(content=text, tool_calls=None)

                # Tool calls come in final chunk - yield them separately
                if tool_calls:
                    yield StreamChunk(content=None, tool_calls=tool_calls)

        except Exception as e:
            # error_msg = str(e)
            # Yield error message instead of empty response
            raise e


class VertexEmbeddingModel(LLMModelAbstract):
    """
    Vertex AI embedding model using google-genai SDK with advanced features.
    """

    def __init__(
        self,
        project_id: str,
        model_name: str = "text-multilingual-embedding-002",
        location: str = "us-central1",
        credentials: dict | None = None,
        output_dimensionality: int | None = None,
        batch_size: int = 100,
        task_type: str = "RETRIEVAL_DOCUMENT",
    ):
        self._model_name = model_name
        self._project_id = project_id
        self._location = location
        self._output_dimensionality = output_dimensionality
        self._batch_size = batch_size
        self._task_type = task_type

        client_kwargs = {
            "vertexai": True,
            "project": project_id,
            "location": location,
        }

        if credentials:
            creds = service_account.Credentials.from_service_account_info(
                credentials, scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            client_kwargs["credentials"] = creds

        self.client = genai.Client(**client_kwargs)

    @property
    def model_name(self) -> str:
        return self._model_name

    @model_name.setter
    def model_name(self, model_name: str) -> None:
        self._model_name = model_name

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
        inputs = [request.input] if isinstance(request.input, str) else request.input

        all_embeddings: list[list[float]] = []

        for i in range(0, len(inputs), self._batch_size):
            batch = inputs[i : i + self._batch_size]

            config_kwargs = {}
            if self._output_dimensionality:
                config_kwargs["output_dimensionality"] = self._output_dimensionality
            if self._task_type:
                config_kwargs["task_type"] = self._task_type

            config = (
                genai.types.EmbedContentConfig(**config_kwargs)
                if config_kwargs
                else None
            )

            try:
                response = await self.client.aio.models.embed_content(
                    model=self._model_name,
                    contents=batch,
                    config=config,
                )
            except Exception as e:
                raise Exception(f"Failed to embed batch: {e}")

            embeddings = [emb.values for emb in response.embeddings]
            all_embeddings.extend(embeddings)

        return EmbeddingResponse(
            embeddings=all_embeddings,
            usage=None,
            metadata={
                "dimensions": len(all_embeddings[0]) if len(all_embeddings) > 0 else 0,
                "batch_size": self._batch_size,
            },
        )
