import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import boto3
    import google.generativeai as genai
    import ollama
    from anthropic import Anthropic
    from openai import AzureOpenAI, OpenAI
else:
    Anthropic = None
    boto3 = None
    genai = None
    ollama = None
    OpenAI = None
    AzureOpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    pass
try:
    import boto3
except ImportError:
    pass
try:
    import google.generativeai as genai
except ImportError:
    pass
try:
    import ollama
except ImportError:
    pass
try:
    from openai import AzureOpenAI, OpenAI
except ImportError:
    pass

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM client"""

    api_key: Optional[str] = None
    llm_provider: str = (
        "ollama"  # 'openai', 'ollama', 'gemini', 'bedrock', 'claude', 'azure'
    )

    # OpenAI
    openai_model: str = "gpt-4o-mini"

    # Ollama
    ollama_model: str = "arctic-text2sql-r1:7b"
    ollama_host: Optional[str] = None

    # Google AI (Gemini)
    gemini_model: str = "gemini-pro"
    gemini_api_key: Optional[str] = None

    # AWS Bedrock
    bedrock_model: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # Anthropic Claude (direct API)
    claude_model: str = "claude-3-5-sonnet-20241022"
    claude_api_key: Optional[str] = None

    # Azure OpenAI
    azure_endpoint: Optional[str] = None
    azure_deployment: str = "gpt-4o-mini"
    azure_api_version: str = "2024-02-15-preview"
    azure_api_key: Optional[str] = None

    # Common settings
    temperature: float = 0.3
    max_tokens: int = 300
    timeout: int = 30


class LLMClient:
    """
    Client for interacting with multiple LLM providers.

    Supported providers: OpenAI, Ollama, Google AI, AWS Bedrock, Anthropic, Azure.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.provider = self.config.llm_provider.lower()
        self._ollama_client: Any = None
        self.client: Any = None

        if self.provider == "openai":
            if OpenAI is None:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )
            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI API key not found. Set OPENAI_API_KEY environment "
                    "variable or pass it in LLMConfig."
                )
            self.client = OpenAI(api_key=api_key, timeout=self.config.timeout)
            self.model = self.config.openai_model
            logger.info(f"Initialized OpenAI client with model: {self.model}")

        elif self.provider == "ollama":
            if ollama is None:
                raise ImportError(
                    "ollama package not installed. Run: pip install ollama"
                )
            if self.config.ollama_host and hasattr(ollama, "Client"):
                try:
                    self._ollama_client = ollama.Client(host=self.config.ollama_host)
                    logger.info(
                        "Initialized Ollama client with custom host: %s",
                        self.config.ollama_host,
                    )
                except (
                    Exception
                ) as client_error:  # pragma: no cover - network dependent
                    logger.warning(
                        "Failed to initialize Ollama client with host %s (%s). "
                        "Falling back to default host.",
                        self.config.ollama_host,
                        client_error,
                    )
                    self._ollama_client = None
            self.model = self.config.ollama_model
            logger.info(f"Initialized Ollama client with model: {self.model}")

        elif self.provider == "gemini":
            if genai is None:
                raise ImportError(
                    "google-generativeai package not installed. "
                    "Run: pip install google-generativeai"
                )
            api_key = (
                self.config.gemini_api_key
                or os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
            )
            if not api_key:
                raise ValueError(
                    "Google API key not found. Set GEMINI_API_KEY or "
                    "GOOGLE_API_KEY environment variable or pass "
                    "gemini_api_key in LLMConfig."
                )
            genai.configure(api_key=api_key)
            self.model = self.config.gemini_model
            self.client = genai.GenerativeModel(self.model)
            logger.info(f"Initialized Google Gemini client with model: {self.model}")

        elif self.provider == "bedrock":
            if boto3 is None:
                raise ImportError("boto3 package not installed. Run: pip install boto3")
            aws_access_key = self.config.aws_access_key_id or os.getenv(
                "AWS_ACCESS_KEY_ID"
            )
            aws_secret_key = self.config.aws_secret_access_key or os.getenv(
                "AWS_SECRET_ACCESS_KEY"
            )

            session_kwargs = {"region_name": self.config.aws_region}
            if aws_access_key and aws_secret_key:
                session_kwargs["aws_access_key_id"] = aws_access_key
                session_kwargs["aws_secret_access_key"] = aws_secret_key

            self.client = boto3.client("bedrock-runtime", **session_kwargs)
            self.model = self.config.bedrock_model
            logger.info(
                f"Initialized AWS Bedrock client with model: {self.model} "
                f"in region: {self.config.aws_region}"
            )

        elif self.provider == "claude":
            if Anthropic is None:
                raise ImportError(
                    "anthropic package not installed. Run: pip install anthropic"
                )
            api_key = self.config.claude_api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "Anthropic API key not found. Set ANTHROPIC_API_KEY environment "
                    "variable or pass claude_api_key in LLMConfig."
                )
            self.client = Anthropic(api_key=api_key, timeout=self.config.timeout)
            self.model = self.config.claude_model
            logger.info(f"Initialized Anthropic Claude client with model: {self.model}")

        elif self.provider == "azure":
            if AzureOpenAI is None:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )
            api_key = self.config.azure_api_key or os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = self.config.azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
            if not api_key:
                raise ValueError(
                    "Azure OpenAI API key not found. Set AZURE_OPENAI_API_KEY "
                    "environment variable or pass azure_api_key in LLMConfig."
                )
            if not endpoint:
                raise ValueError(
                    "Azure OpenAI endpoint not found. Set AZURE_OPENAI_ENDPOINT "
                    "environment variable or pass azure_endpoint in LLMConfig."
                )
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version=self.config.azure_api_version,
                azure_endpoint=endpoint,
                timeout=self.config.timeout,
            )
            self.model = self.config.azure_deployment
            logger.info(
                f"Initialized Azure OpenAI client with deployment: {self.model}"
            )

        else:
            raise ValueError(
                f"Unknown LLM provider: {self.provider}. "
                f"Supported: openai, ollama, gemini, bedrock, claude, azure"
            )

    def generate_recommendations(
        self,
        query_text: str,
        avg_duration: float,
        frequency: int,
        max_duration: Optional[float] = None,
        impact_score: Optional[float] = None,
    ) -> str:
        """
        Uses LLM to analyze query and suggest optimizations
        """
        try:
            prompt = self._build_prompt(
                query_text, avg_duration, frequency, max_duration, impact_score
            )
            logger.debug(
                f"Requesting recommendations for query (avg: {avg_duration:.2f}ms)"
            )

            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a PostgreSQL performance "
                            "optimization expert.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                recommendation = response.choices[0].message.content or ""
                logger.info("Successfully generated recommendations (OpenAI)")
                return recommendation

            elif self.provider == "ollama":
                chat_target = self._ollama_client or ollama
                response = chat_target.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                logger.debug(f"Ollama response type: {type(response)}")
                logger.debug(f"Ollama response: {response}")

                # Type-safe response parsing
                content: str = ""
                # Handle both ChatResponse objects and dict responses (for tests)
                try:
                    if hasattr(response, "message") and hasattr(
                        response.message, "content"
                    ):
                        raw_content = response.message.content
                        logger.debug(f"Raw content (ChatResponse): {raw_content}")
                        if isinstance(raw_content, str):
                            content = raw_content.strip()
                    elif hasattr(response, "get"):  # dict-like object
                        message = response.get("message")
                        logger.debug(f"Message (dict): {message}")
                        if isinstance(message, dict):
                            raw_content = message.get("content")
                            logger.debug(f"Raw content (dict): {raw_content}")
                            if isinstance(raw_content, str):
                                content = raw_content.strip()
                except (AttributeError, TypeError):
                    logger.warning("Could not parse Ollama response format")

                if content:
                    logger.info(
                        f"Successfully generated Ollama recommendations "
                        f"({len(content)} chars)"
                    )
                else:
                    logger.warning("Ollama returned empty content")

                return content

            elif self.provider == "gemini":
                response = self.client.generate_content(
                    prompt,
                    generation_config={
                        "temperature": self.config.temperature,
                        "max_output_tokens": self.config.max_tokens,
                    },
                )
                content = response.text.strip() if hasattr(response, "text") else ""
                logger.info(
                    f"Successfully generated Gemini recommendations "
                    f"({len(content)} chars)"
                )
                return content

            elif self.provider == "bedrock":
                import json

                body = json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": self.config.max_tokens,
                        "temperature": self.config.temperature,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                )
                response = self.client.invoke_model(modelId=self.model, body=body)
                response_body = json.loads(response["body"].read())
                content = response_body.get("content", [{}])[0].get("text", "")
                logger.info(
                    f"Successfully generated Bedrock recommendations "
                    f"({len(content)} chars)"
                )
                return content

            elif self.provider == "claude":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.content[0].text if response.content else ""
                logger.info(
                    f"Successfully generated Claude recommendations "
                    f"({len(content)} chars)"
                )
                return content

            elif self.provider == "azure":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a PostgreSQL performance "
                            "optimization expert.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                recommendation = response.choices[0].message.content or ""
                logger.info("Successfully generated recommendations (Azure OpenAI)")
                return recommendation

            else:  # pragma: no cover - defensive
                raise ValueError(f"Unhandled LLM provider: {self.provider}")
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return f"Error generating recommendations: {str(e)}"

    def _build_prompt(
        self,
        query_text: str,
        avg_duration: float,
        frequency: int,
        max_duration: Optional[float],
        impact_score: Optional[float],
    ) -> str:
        """Builds the prompt for the LLM"""

        stats = [
            f"Average Duration: {avg_duration:.2f} ms",
            f"Execution Frequency: {frequency} times",
        ]

        if max_duration:
            stats.append(f"Max Duration: {max_duration:.2f} ms")

        if impact_score:
            stats.append(f"Impact Score: {impact_score:.2f}")

        stats_text = "\n".join(stats)

        prompt = f"""You are a PostgreSQL database performance expert.

Analyze this slow-running query:

Query: {query_text}

Statistics:
{stats_text}

Provide:
1. Most likely root cause of slowness
2. Specific, actionable optimization recommendation (e.g., add index, rewrite query)
3. Estimated performance impact (e.g., "30-50% faster")

Keep response concise and under 150 words."""

        return prompt

    def batch_generate_recommendations(
        self, queries: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate recommendations for multiple queries

        Args:
            queries: List of dicts with keys: query_text, avg_duration, frequency

        Returns:
            List of recommendation strings
        """
        recommendations: List[str] = []

        for i, query_info in enumerate(queries):
            logger.info(f"Processing query {i + 1}/{len(queries)}")

            rec = self.generate_recommendations(
                query_text=str(query_info.get("query_text", "")),
                avg_duration=float(query_info.get("avg_duration", 0)),
                frequency=int(query_info.get("frequency", 0)),
                max_duration=query_info.get("max_duration"),
                impact_score=query_info.get("impact_score"),
            )
            recommendations.append(rec)

        return recommendations


# Backward compatibility - keep the original function
_default_client = None


def generate_recommendations(
    query_text: str, avg_duration: float, frequency: int
) -> str:
    """
    Legacy function for backward compatibility
    Uses GPT to analyze query and suggest optimizations
    """
    global _default_client

    if _default_client is None:
        _default_client = LLMClient()

    return _default_client.generate_recommendations(query_text, avg_duration, frequency)
