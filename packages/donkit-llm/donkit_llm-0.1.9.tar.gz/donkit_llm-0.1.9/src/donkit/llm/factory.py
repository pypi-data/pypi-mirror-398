from typing import Literal

from .claude_model import ClaudeModel
from .claude_model import ClaudeVertexModel
from .donkit_model import DonkitModel
from .gemini_model import GeminiModel

try:
    from .llm_gate_model import LLMGateModel
except ModuleNotFoundError:
    LLMGateModel = None
from .model_abstract import LLMModelAbstract
from .openai_model import AzureOpenAIEmbeddingModel
from .openai_model import AzureOpenAIModel
from .openai_model import OpenAIEmbeddingModel
from .openai_model import OpenAIModel
from .vertex_model import VertexAIModel
from .vertex_model import VertexEmbeddingModel


class ModelFactory:
    """Factory for creating LLM model instances."""

    @staticmethod
    def create_openai_model(
        model_name: str,
        api_key: str,
        base_url: str | None = None,
        organization: str | None = None,
    ) -> OpenAIModel:
        return OpenAIModel(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            organization=organization,
        )

    @staticmethod
    def create_azure_openai_model(
        model_name: str,
        api_key: str,
        azure_endpoint: str,
        api_version: str = "2024-08-01-preview",
        deployment_name: str | None = None,
    ) -> AzureOpenAIModel:
        return AzureOpenAIModel(
            model_name=deployment_name or model_name,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            deployment_name=deployment_name,
        )

    @staticmethod
    def create_embedding_model(
        provider: Literal["openai", "azure_openai", "vertex", "custom", "default"],
        model_name: str | None = None,
        api_key: str | None = None,
        **kwargs,
    ) -> LLMModelAbstract:
        if provider == "openai":
            return OpenAIEmbeddingModel(
                model_name=model_name or "text-embedding-3-small",
                api_key=api_key,
                base_url=kwargs.get("base_url"),
            )
        elif provider == "azure_openai":
            return AzureOpenAIEmbeddingModel(
                model_name=model_name or "text-embedding-ada-002",
                api_key=api_key,
                azure_endpoint=kwargs["azure_endpoint"],
                deployment_name=kwargs.get("deployment_name")
                or model_name
                or "text-embedding-ada-002",
                api_version=kwargs.get("api_version", "2024-08-01-preview"),
            )
        elif provider == "vertex":
            return VertexEmbeddingModel(
                project_id=kwargs["project_id"],
                model_name=model_name or "text-multilingual-embedding-002",
                location=kwargs.get("location", "us-central1"),
                credentials=kwargs.get("credentials"),
                output_dimensionality=kwargs.get("output_dimensionality"),
                batch_size=kwargs.get("batch_size", 100),
                task_type=kwargs.get("task_type", "RETRIEVAL_DOCUMENT"),
            )
        else:
            raise ValueError(f"Unknown embedding provider: {provider}")

    @staticmethod
    def create_claude_model(
        model_name: str,
        api_key: str,
        base_url: str | None = None,
    ) -> ClaudeModel:
        return ClaudeModel(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
        )

    @staticmethod
    def create_gemini_model(
        model_name: str,
        api_key: str | None = None,
        project_id: str | None = None,
        location: str = "us-central1",
        use_vertex: bool = False,
    ) -> GeminiModel:
        """
        Create a Gemini model instance.

        Args:
            model_name: Model identifier (e.g., "gemini-2.0-flash-exp")
            api_key: Google AI API key (for AI Studio)
            project_id: GCP project ID (for Vertex AI)
            location: GCP location (for Vertex AI)
            use_vertex: Whether to use Vertex AI instead of AI Studio

        Returns:
            Configured Gemini model instance
        """
        return GeminiModel(
            model_name=model_name,
            api_key=api_key,
            project_id=project_id,
            location=location,
            use_vertex=use_vertex,
        )

    @staticmethod
    def create_claude_vertex_model(
        model_name: str,
        project_id: str,
        location: str = "us-east5",
    ) -> ClaudeVertexModel:
        return ClaudeVertexModel(
            model_name=model_name,
            project_id=project_id,
            location=location,
        )

    @staticmethod
    def create_vertex_model(
        model_name: str,
        project_id: str,
        location: str = "us-central1",
        credentials: dict | None = None,
    ) -> VertexAIModel:
        return VertexAIModel(
            model_name=model_name,
            project_id=project_id,
            location=location,
            credentials=credentials,
        )

    @staticmethod
    def create_donkit_model(
        model_name: str | None,
        api_key: str,
        base_url: str = "https://api.donkit.ai",
        provider: str = "default",
    ) -> DonkitModel:
        """Create a Donkit model that proxies through RagOps API Gateway.

        Args:
            model_name: Name of the model to use
            api_key: API key for authentication
            base_url: Base URL of the RagOps API Gateway
            provider: Provider to use e.g.:
                vertex, openai, azure_openai, ollama, default
        Returns:
            DonkitModel instance
        """
        return DonkitModel(
            base_url=base_url,
            api_token=api_key,
            provider=provider,
            model_name=model_name,
        )

    @staticmethod
    def create_llm_gate_model(
        model_name: str | None,
        base_url: str,
        provider: str = "default",
        embedding_provider: str | None = None,
        embedding_model_name: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
    ) -> LLMGateModel:
        if LLMGateModel is None:
            raise ImportError(
                "Provider 'llm_gate' requires optional dependency 'donkit-llm-gate-client'"
            )
        return LLMGateModel(
            base_url=base_url,
            provider=provider,
            model_name=model_name,
            embedding_provider=embedding_provider,
            embedding_model_name=embedding_model_name,
            user_id=user_id,
            project_id=project_id,
        )

    @staticmethod
    def create_model(
        provider: Literal[
            "openai",
            "azure_openai",
            "claude",
            "claude_vertex",
            "vertex",
            "ollama",
            "donkit",
            "llm_gate",
        ],
        model_name: str | None,
        credentials: dict,
    ) -> LLMModelAbstract:
        if model_name is None:
            default_models = {
                "openai": "gpt-5-mini",
                "azure_openai": "gpt-4.1-mini",
                "claude": "claude-4-5-sonnet",
                "claude_vertex": "claude-4-5-sonnet",
                "gemini": "gemini-2.5-flash",
                "vertex": "gemini-2.5-flash",
                "ollama": "mistral",
                "donkit": None,
                "llm_gate": None,
            }
            model_name = default_models.get(provider, "default")
        if provider == "openai":
            return ModelFactory.create_openai_model(
                model_name=model_name,
                api_key=credentials["api_key"],
                base_url=credentials.get("base_url"),
                organization=credentials.get("organization"),
            )
        elif provider == "azure_openai":
            return ModelFactory.create_azure_openai_model(
                model_name=model_name,
                api_key=credentials.get("api_key"),
                azure_endpoint=credentials.get("azure_endpoint"),
                api_version=credentials.get("api_version", "2024-08-01-preview"),
                deployment_name=credentials.get("deployment_name"),
            )
        elif provider == "gemini":
            return ModelFactory.create_gemini_model(
                model_name=model_name,
                api_key=credentials.get("api_key"),
                project_id=credentials.get("project_id"),
                location=credentials.get("location", "us-central1"),
                use_vertex=credentials.get("use_vertex", False),
            )
        elif provider == "claude":
            return ModelFactory.create_claude_model(
                model_name=model_name,
                api_key=credentials["api_key"],
                base_url=credentials.get("base_url"),
            )
        elif provider == "claude_vertex":
            return ModelFactory.create_claude_vertex_model(
                model_name=model_name,
                project_id=credentials["project_id"],
                location=credentials.get("location", "us-east5"),
            )
        elif provider == "vertex":
            return ModelFactory.create_vertex_model(
                model_name=model_name,
                project_id=credentials["project_id"],
                location=credentials.get("location", "us-central1"),
                credentials=credentials.get("credentials"),
            )
        elif provider == "ollama":
            # Ollama uses OpenAI-compatible API
            ollama_url = credentials.get("ollama_url")
            if "/v1" not in ollama_url:
                ollama_url += "/v1"
            return ModelFactory.create_openai_model(
                model_name=model_name,
                api_key=credentials.get("api_key", "ollama"),
                base_url=ollama_url,
            )
        elif provider == "donkit":
            return ModelFactory.create_donkit_model(
                model_name=model_name,
                api_key=credentials["api_key"],
                base_url=credentials["base_url"],
            )
        elif provider == "llm_gate":
            return ModelFactory.create_llm_gate_model(
                model_name=model_name,
                base_url=credentials["base_url"],
                provider=credentials.get("provider", "default"),
                embedding_provider=credentials.get("embedding_provider"),
                embedding_model_name=credentials.get("embedding_model_name"),
                user_id=credentials.get("user_id"),
                project_id=credentials.get("project_id"),
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
