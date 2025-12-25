import asyncio
import hashlib
import json
import os
import random
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Literal, ParamSpec, TypeVar

from donkit.llm import (
    ContentPart,
    ContentType,
    GenerateRequest,
    LLMModelAbstract,
    Message,
    ModelFactory,
)
from dotenv import find_dotenv, load_dotenv
from loguru import logger

# Load .env file with explicit search (important for Windows)
# Try multiple locations in priority order
_env_loaded = False
for _fname in (".env.local", ".env"):
    # 1. Try current working directory
    _cwd_path = Path.cwd() / _fname
    if _cwd_path.exists():
        load_dotenv(_cwd_path, override=False)
        _env_loaded = True
    # 2. Try parent directories (walk up to 3 levels)
    _parent = Path.cwd()
    for _ in range(3):
        _parent = _parent.parent
        _parent_env = _parent / _fname
        if _parent_env.exists():
            load_dotenv(_parent_env, override=False)
            _env_loaded = True
            break
    # 3. Fallback to find_dotenv
    if not _env_loaded:
        _found = find_dotenv(filename=_fname, usecwd=True)
        if _found:
            load_dotenv(_found, override=False)
            _env_loaded = True

logger.remove()
log_level = os.getenv("RAGOPS_LOG_LEVEL", os.getenv("LOG_LEVEL", "ERROR"))
# Force INFO level if no env vars loaded to help debug
if not _env_loaded:
    log_level = "DEBUG"
logger.add(
    sys.stderr,
    level=log_level,
    enqueue=False,
    backtrace=False,
    diagnose=False,
)

# Warn if no .env was loaded
if not _env_loaded:
    logger.warning(
        "⚠️ No .env file found in current directory or parent directories. "
        "Image analysis may fail without proper credentials. "
        "Please create a .env file with RAGOPS_OPENAI_API_KEY or other provider credentials."
    )

P = ParamSpec("P")
R = TypeVar("R")


def retry_on_exception(
    max_retries: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry a callable (sync or async) on specified exceptions with backoff.

    - Supports both sync and async functions.
    - Exponential backoff with randomized jitter.
    - Raises immediately on the final failed attempt.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                last_exc: Exception | None = None
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)  # type: ignore[misc]
                    except exceptions as e:  # type: ignore[misc]
                        last_exc = e
                        if attempt == max_retries:
                            logger.error(
                                f"All {max_retries} attempts failed. Last error: {e!s}"
                            )
                            raise
                        wait_time = min(
                            initial_wait * (2**attempt)
                            + random.uniform(0, 0.2 * initial_wait),
                            max_wait,
                        )
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {e!s}. "
                            f"Retrying in {wait_time:.2f}s"
                        )
                        await asyncio.sleep(wait_time)
                # Unreachable; for type-checkers
                assert last_exc is not None
                raise last_exc

            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exc: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:  # type: ignore[misc]
                    last_exc = e
                    if attempt == max_retries:
                        logger.error(
                            f"All {max_retries} attempts failed. Last error: {e!s}"
                        )
                        raise
                    wait_time = min(
                        initial_wait * (2**attempt)
                        + random.uniform(0, 0.2 * initial_wait),
                        max_wait,
                    )
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {e!s}. "
                        f"Retrying in {wait_time:.2f}s"
                    )
                    time.sleep(wait_time)

            # Unreachable; for type-checkers
            assert last_exc is not None
            raise last_exc

        return sync_wrapper  # type: ignore[return-value]

    return decorator


DEFAULT_PROMPT: str = (
    "Analyze the document slide and extract ALL visible information in detail. "
    "Include all text, numbers, data points, labels, captions, titles, headers, footers, "
    "watermarks, logos, icons, charts, graphs, tables, diagrams, and any other visual elements. "
    "Describe layouts, positioning, and relationships between elements. "
    "Be extremely thorough and precise - do not summarize or omit any details."
)

# JSON-specific guidance (used only when output_format == 'json')
JSON_SCHEMA_PROMPT: str = (
    "Extract and structure all slide content in JSON format with the following keys: "
    '"title": extract the main slide title, '
    '"content": all body text preserving bullet points and hierarchical structure, '
    '"tables": format any tables as nested JSON arrays with column headers, '
    '"charts": describe any charts with type, data points, and trends, '
    '"images": brief descriptions of any non-chart images, '
    '"notes": any presenter notes or footnotes. '
    "Be extremely precise and concise. Avoid any commentary or subjective interpretation. "
    "Format response as a clean JSON object without line breaks or extra formatting."
)


# Additional formatting instructions by output format
def _format_instructions(output_format: Literal["json", "text", "md"]) -> str:
    if output_format == "json":
        return (
            " Return ONLY a valid JSON object. No markdown, no codeFences, no commentary. "
            "Ensure proper escaping and valid JSON syntax."
        )
    if output_format == "md":
        return """
            Return only Markdown. Do not include JSON or code fences with language tags (like ```json).
            Only use code fences if the image explicitly contains a code snippet."""
    return (
        " Provide a concise plain text summary. Do NOT use JSON or markdown. "
        "Use paragraphs and simple lists only if needed."
    )


def _build_prompt_for_format(
    base_prompt: str, output_format: Literal["json", "text", "md"]
) -> str:
    if output_format == "json":
        return f"{JSON_SCHEMA_PROMPT}\n{_format_instructions('json')}"
    # md or text get neutral base + their formatting rules
    return f"{DEFAULT_PROMPT}\n{_format_instructions(output_format)}"


# Cache configuration
CACHE_FILE = Path("image_cache.json")


class ImageAnalysisService(ABC):
    """Interface for image analysis operations."""

    @abstractmethod
    def analyze_image(
        self,
        encoded_image: str,
        prompt: str = DEFAULT_PROMPT,
    ) -> str:
        """Analyze image content based on the provided prompt."""
        pass

    @abstractmethod
    async def aanalyze_image(
        self,
        encoded_image: str,
        prompt: str = DEFAULT_PROMPT,
    ) -> str:
        """Async: Analyze image content based on the provided prompt."""
        pass

    @abstractmethod
    def call_text_only(self, prompt: str) -> str:
        """Call the service with a text-only prompt."""
        pass


# Implementation classes
class FileBasedImageCache:
    """File-based implementation of image caching service."""

    def __init__(self, cache_file: Path = CACHE_FILE):
        self.cache_file = cache_file
        self._cache = self._load_cache()

    def _load_cache(self) -> dict[str, str]:
        if self.cache_file.exists():
            try:
                content = self.cache_file.read_text()
                if not content.strip():
                    return {}
                return json.loads(content)
            except Exception as e:
                logger.error(
                    f"Failed to load cache: {e}. Deleting corrupted cache file."
                )
                try:
                    self.cache_file.unlink()
                except Exception as unlink_error:
                    logger.error(f"Failed to delete corrupted cache: {unlink_error}")
        return {}

    def _save_cache(self) -> None:
        try:
            self.cache_file.write_text(
                json.dumps(self._cache, indent=4, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def get_hash(self, image_bytes: bytes) -> str:
        return hashlib.md5(image_bytes).hexdigest()

    def get(self, image_hash: str) -> str | None:
        return self._cache.get(image_hash)

    def set(self, image_hash: str, content: str) -> None:
        if not image_hash:
            return
        self._cache[image_hash] = content
        self._save_cache()


class LLMImageAnalysisService(ImageAnalysisService):
    """Image analysis via unified LLM (donkit.models)."""

    def __init__(
        self,
        cache_service: FileBasedImageCache | None = None,
        *,
        output_format: Literal["json", "text", "md"] = "json",
        llm_model: LLMModelAbstract | None = None,
    ):
        self.cache_service = cache_service or FileBasedImageCache()
        self.model = llm_model if llm_model else self._create_llm_from_env()
        self.max_tokens = int(os.getenv("IMAGE_ANALYSIS_MAX_TOKENS", "16384"))
        self.output_format: Literal["json", "text", "md"] = output_format

    @classmethod
    def _create_llm_from_env(cls) -> LLMModelAbstract:
        provider = os.getenv(
            "RAGOPS_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "openai")
        ).lower()
        model_name = os.getenv("RAGOPS_LLM_MODEL") if provider != "donkit" else None
        # Provider-specific defaults when model is not explicitly set
        if not model_name:
            if provider in ("vertex", "vertexai", "gemini"):
                # Default Vertex/Gemini model
                model_name = os.getenv("VERTEX_DEFAULT_MODEL", "gemini-2.5-flash")
            elif provider in ("azure", "azure_openai", "azure-openai"):
                model_name = os.getenv("AZURE_OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
            elif provider in ("claude", "anthropic", "claude_vertex", "claude-vertex"):
                model_name = os.getenv("CLAUDE_DEFAULT_MODEL", "claude-3-5-sonnet")
            elif provider == "ollama":
                model_name = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen3-vl")
            elif provider == "donkit":
                model_name = None
            else:
                model_name = "gpt-4.1-mini"

        if provider == "openai":
            api_key = os.getenv("RAGOPS_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("RAGOPS_OPENAI_BASE_URL") or os.getenv(
                "OPENAI_BASE_URL"
            )
            org = os.getenv("OPENAI_ORG")
            creds = {"api_key": api_key, "base_url": base_url, "organization": org}
            return ModelFactory.create_model("openai", model_name, creds)

        if provider in ("azure_openai", "azure"):
            api_key = os.getenv("RAGOPS_AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("RAGOPS_AZURE_OPENAI_ENDPOINT")
            api_version = os.getenv(
                "RAGOPS_AZURE_OPENAI_API_VERSION", "2024-08-01-preview"
            )
            deployment = os.getenv("RAGOPS_AZURE_OPENAI_DEPLOYMENT", model_name)
            creds = {
                "api_key": api_key,
                "azure_endpoint": endpoint,
                "api_version": api_version,
                "deployment_name": deployment,
            }
            return ModelFactory.create_model("azure_openai", model_name, creds)

        # Vertex/Gemini (use ADC or provided creds)
        if provider in ("vertex", "vertexai", "gemini"):
            location = (
                os.getenv("VERTEXAI_LOCATION")
                or os.getenv("GOOGLE_CLOUD_REGION")
                or "us-central1"
            )
            creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
            creds_path = os.getenv("RAGOPS_VERTEX_CREDENTIALS")
            creds_dict = None
            # Prefer explicit JSON string; else read from file path; else None (ADC)
            if creds_json:
                try:
                    creds_dict = json.loads(creds_json)
                except Exception:
                    logger.warning(
                        "Invalid GOOGLE_CREDENTIALS_JSON; falling back to file/ADC"
                    )
            if creds_dict is None and creds_path:
                try:
                    with open(creds_path, "r", encoding="utf-8") as f:
                        creds_dict = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to read RAGOPS_VERTEX_CREDENTIALS: {e!s}")
            project = (
                os.getenv("VERTEXAI_PROJECT")
                or os.getenv("VERTEX_PROJECT")
                or os.getenv("GOOGLE_CLOUD_PROJECT")
                or (
                    creds_dict.get("project_id") if isinstance(creds_dict, dict) else ""
                )
            )
            creds = {
                "project_id": project,
                "location": location,
                "credentials": creds_dict,
            }
            return ModelFactory.create_model("vertex", model_name, creds)

        # Ollama (local LLM server with OpenAI-compatible API)
        if provider == "ollama":
            api_key = os.getenv("RAGOPS_OPENAI_API_KEY", "ollama")
            base_url = os.getenv("RAGOPS_OLLAMA_BASE_URL") or os.getenv(
                "OLLAMA_BASE_URL", "http://localhost:11434/v1"
            )
            # Use vision model for image analysis if available
            model_name = os.getenv("RAGOPS_OLLAMA_VISION_MODEL", "qwen3-vl")
            creds = {"api_key": api_key, "base_url": base_url}
            return ModelFactory.create_model("ollama", model_name, creds)
        if provider == "donkit":
            creds = {
                "api_key": os.getenv("RAGOPS_DONKIT_API_KEY", "donkit"),
                "base_url": os.getenv(
                    "RAGOPS_DONKIT_BASE_URL", "https://api.donkit.ai"
                ),
            }
            return ModelFactory.create_model(
                provider="donkit", model_name=model_name, credentials=creds
            )
        raise ValueError(
            "Unsupported LLM provider: "
            + provider
            + ". Please set RAGOPS_LLM_PROVIDER or LLM_PROVIDER environment "
            "variable to 'openai', 'azure_openai', 'vertex', or 'ollama'"
        )

    @staticmethod
    def _build_messages(prompt: str, encoded_image: str) -> list[Message]:
        parts: list[ContentPart] = [
            ContentPart(
                content_type=ContentType.TEXT,
                content=prompt,
            ),
            ContentPart(
                content_type=ContentType.IMAGE_BASE64,
                content=encoded_image,
                mime_type="image/png",
            ),
        ]
        return [
            Message(role="user", content=parts),
        ]

    @retry_on_exception()
    def analyze_image(
        self,
        encoded_image: str,
        prompt: str = DEFAULT_PROMPT,
    ) -> str:
        if self.cache_service:
            image_hash = self.cache_service.get_hash(encoded_image.encode())
            cached = self.cache_service.get(image_hash)
            if cached:
                return cached
        prompt_for_format = _build_prompt_for_format(prompt, self.output_format)
        messages = self._build_messages(prompt_for_format, encoded_image)
        req = GenerateRequest(messages=messages, max_tokens=self.max_tokens)
        try:
            content = asyncio.run(self.model.generate(req)).content
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                content = loop.run_until_complete(self.model.generate(req)).content
            finally:
                loop.close()

        content = content or ""
        if self.cache_service and content:
            image_hash = self.cache_service.get_hash(encoded_image.encode())
            self.cache_service.set(image_hash, content)
        return content

    @retry_on_exception()
    async def aanalyze_image(
        self,
        encoded_image: str,
        prompt: str = DEFAULT_PROMPT,
    ) -> str:
        prompt_for_format = _build_prompt_for_format(prompt, self.output_format)
        image_hash = None
        # Cache key should include image + output format + prompt to avoid collisions
        if self.cache_service:
            key_material = (
                encoded_image + "|" + self.output_format + "|" + prompt_for_format
            ).encode("utf-8")
            image_hash = self.cache_service.get_hash(key_material)
            cached = self.cache_service.get(image_hash)
            if cached:
                return cached

        messages = self._build_messages(prompt_for_format, encoded_image)
        req = GenerateRequest(
            messages=messages, max_tokens=self.max_tokens, temperature=0
        )
        resp = await self.model.generate(req)
        content = resp.content or ""
        if self.cache_service and content:
            # Store under the same composite key
            self.cache_service.set(image_hash, content)
        return content

    # @retry_on_exception()
    def call_text_only(self, prompt: str) -> str:
        # Use model without image
        req = GenerateRequest(
            messages=[Message(role="user", content=prompt)], max_tokens=self.max_tokens
        )
        try:
            content = asyncio.run(self.model.generate(req)).content  # type: ignore[arg-type]
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                content = loop.run_until_complete(self.model.generate(req)).content  # type: ignore[arg-type]
            finally:
                loop.close()
        return content or ""


def get_image_analysis_service(
    cache_service: FileBasedImageCache | None = None,
    *,
    output_format: Literal["json", "text", "md"] = "json",
    llm_model: LLMModelAbstract | None = None,
) -> LLMImageAnalysisService:
    return LLMImageAnalysisService(
        cache_service=cache_service,
        output_format=output_format,
        llm_model=llm_model,
    )
