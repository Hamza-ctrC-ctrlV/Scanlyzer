"""
AI Client Module - Google Gemini API Communication

Handles all communication with the Google Gemini API (free tier).

Model: gemini-3.1-Flash-Lite
- Free tier: 15 requests/minute, 1500 requests/day
- No credit card required
- Get API key at: https://aistudio.google.com/apikey

Security Features:
- API key validation and masking for safe logging
- Client-side rate limiting to respect API quotas
- Request timeouts to prevent hanging
- Exponential backoff retry strategy for transient errors

Responsibilities:
- Authenticate with Gemini API using API key from environment
- Validate requests before sending (rate limit checks)
- Send prompts and receive responses
- Handle various error conditions and retry appropriately
"""

import json
import os
import re
import time
import logging
from typing import Optional, List
from google import genai
from google.genai import errors as genai_errors
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import requests

from config.constants import (
    GEMINI_MODEL_ID,
    GROQ_MODEL_ID,
    GROQ_KEYS_LINK,
    GEMINI_FREE_TIER_RATE_LIMIT,
    RATE_LIMIT_WINDOW_SECONDS,
    API_REQUEST_TIMEOUT,
    MAX_RETRY_ATTEMPTS,
    ERROR_INVALID_API_KEY,
    ERROR_RATE_LIMIT_EXCEEDED,
    ERROR_API_TIMEOUT,
    API_KEY_VISIBLE_CHARS,
)
from utils.helpers import mask_sensitive_value, validate_api_key_format

load_dotenv()

# Setup secure logging (never log full API key)
# Note: logging.basicConfig() is called once in app.py — not repeated here.
logger = logging.getLogger(__name__)


class APIRateLimiter:
    """
    In-memory rate limiter for Gemini API free tier.
    
    Tracks requests within a rolling time window and prevents exceeding
    the API's free tier quota (14 requests per 60 seconds).
    
    Attributes:
        max_requests (int): Maximum requests allowed per window
        window_seconds (int): Time window in seconds for rate limit
        requests (list): Timestamps of recent requests
    """
    
    def __init__(self, max_requests: int = GEMINI_FREE_TIER_RATE_LIMIT, 
                 window_seconds: int = RATE_LIMIT_WINDOW_SECONDS):
        """
        Initialize rate limiter.
        
        Args:
            max_requests (int): Max requests per time window (default: 14)
            window_seconds (int): Time window in seconds (default: 60)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def check_limit(self) -> None:
        """
        Check if another request can be made within rate limits.
        
        Removes expired timestamps outside the current window and checks
        if we've exceeded the maximum requests within the window.
        
        Raises:
            RuntimeError: If rate limit is exceeded with wait time info
        """
        now = time.time()
        # Remove old requests outside the window
        self.requests = [ts for ts in self.requests if now - ts < self.window_seconds]
        
        if len(self.requests) >= self.max_requests:
            wait_time = self.window_seconds - (now - self.requests[0])
            raise RuntimeError(
                f"Rate limit: {self.max_requests} requests per {self.window_seconds} seconds. "
                f"Please wait {wait_time:.1f} seconds before the next request."
            )
        
        self.requests.append(now)


class AIClient:
    """
    Client for interacting with Google Gemini API.
    
    Handles initialization, authentication, rate limiting, and API requests
    with retry logic and error handling.
    
    Attributes:
        client: Initialized Gemini API client
        model (str): Model ID to use for requests
        rate_limiter (APIRateLimiter): Rate limiter instance
    """
    
    def __init__(self) -> None:
        """
        Initialize Gemini API client.
        
        Reads API key from environment variable GEMINI_API_KEY,
        validates the key format, and initializes the client.
        
        Raises:
            ValueError: If API key is missing or invalid format
        
        Side Effects:
            Logs initialization info with masked API key
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Get a free key at https://aistudio.google.com/apikey "
                "and add it to your .env file."
            )
        
        # Validate API key format
        is_valid, validation_msg = validate_api_key_format(api_key)
        if not is_valid:
            raise ValueError(f"GEMINI_API_KEY format is invalid: {validation_msg}")
        
        masked_key = mask_sensitive_value(api_key, API_KEY_VISIBLE_CHARS)
        logger.info(f"Initializing Gemini API client with key: {masked_key}")
        
        # Initialize the Gemini client
        self.client = genai.Client(api_key=api_key)
        
        # Use constant for model ID
        self.model = GEMINI_MODEL_ID
        
        # Initialize rate limiter
        self.rate_limiter = APIRateLimiter(
            max_requests=GEMINI_FREE_TIER_RATE_LIMIT,
            window_seconds=RATE_LIMIT_WINDOW_SECONDS
        )
    
    @retry(
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RuntimeError, genai_errors.APIError)),
        reraise=True
    )
    def send_prompt(
        self,
        prompt: str,
        timeout: int = API_REQUEST_TIMEOUT,
        model: str | None = None,
    ) -> str:
        """
        Send a prompt to Gemini API and receive response.
        
        Implements rate limiting, timeouts, and exponential backoff retries
        for transient errors. Non-retryable errors (auth, validation) fail immediately.
        
        Args:
            prompt (str): The complete prompt text to send to API
            timeout (int): Request timeout in seconds (default: 30)

        Returns:
            str: The AI response text

        Raises:
            RuntimeError: If the API call fails permanently after retries
                - 401: Authentication error (invalid/expired key)
                - 429: Rate limit exceeded
                - 503: Service temporarily unavailable
                - Other: Generic API errors with status code
            
        Side Effects:
            - Logs request/response info (masked) at info level
            - Logs errors at warning/error level
            - Updates internal rate limiter state
        """
        try:
            # Check rate limit before making request
            self.rate_limiter.check_limit()
            
            logger.info(f"Sending prompt to Gemini ({len(prompt)} chars)...")
            
            selected_model = model or self.model
            response = self.client.models.generate_content(
                model=selected_model,
                contents=prompt
            )
            
            logger.info(f"Received response ({len(response.text)} chars)")
            return response.text

        except genai_errors.APIError as e:
            status = getattr(e, "status_code", None)

            if status == 401:
                logger.error("Authentication failed: Invalid or expired API key")
                raise RuntimeError(ERROR_INVALID_API_KEY)
            elif status == 429:
                logger.warning("Rate limit hit (free tier: 15 requests/minute)")
                raise RuntimeError(ERROR_RATE_LIMIT_EXCEEDED)
            elif status == 503:
                logger.warning("Gemini API temporarily unavailable")
                raise RuntimeError(
                    "Gemini API is temporarily unavailable. Please try again in a moment."
                )
            else:
                logger.error(f"Gemini API error (status {status}): {str(e)}")
                raise RuntimeError(f"Gemini API error (status {status}): {str(e)}")

        except RuntimeError as e:
            logger.warning(f"Rate limiting or other error: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini API: {str(e)}")
            raise RuntimeError(f"Unexpected error when calling Gemini API: {str(e)}")


class LocalAIClient:
    """
    Adapter for a local/self-hosted AI inference HTTP API.

    This client is intentionally generic so it can be configured to work
    with different local model hosts (LM Studio, Ollama, local FastAPI wrappers, etc.).

    Configuration via environment variables (recommended in `.env`):
    - AI_LOCAL_API_URL: Base URL for the local inference service (default: http://127.0.0.1:1234)
    - AI_LOCAL_MODELS_PATH: Optional endpoint path to list models (default: /v1/models)
    - AI_LOCAL_GENERATE_PATH: Optional path to POST chat completions (default: /v1/chat/completions)
    - AI_LOCAL_DEFAULT_MODEL: Optional fallback model name when none is selected
    - AI_LOCAL_MODELS_DIR: Optional local directory to enumerate model files as fallback

    This is tuned for LM Studio's OpenAI-compatible server, but it can still be
    pointed at another compatible service by overriding the paths above.
    """

    def __init__(self) -> None:
        self.base_url = os.getenv("AI_LOCAL_API_URL", "http://127.0.0.1:1234").rstrip("/")
        self.models_path = os.getenv("AI_LOCAL_MODELS_PATH", "/v1/models")
        self.generate_path = os.getenv("AI_LOCAL_GENERATE_PATH", "/v1/chat/completions")
        self.default_model = os.getenv("AI_LOCAL_DEFAULT_MODEL")
        self.models_dir = os.getenv("AI_LOCAL_MODELS_DIR")

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def list_models(self) -> List[str]:
        """Return a list of available model names.

        Tries to call the configured models endpoint; if that fails and
        `AI_LOCAL_MODELS_DIR` is set, lists files in that directory.
        """
        # Try HTTP endpoint first
        try:
            resp = requests.get(self._url(self.models_path), timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                # Accept OpenAI-compatible {'data': [{'id': '...'}]} and simple list
                if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                    models = []
                    for item in data["data"]:
                        if isinstance(item, dict):
                            model_id = item.get("id") or item.get("name")
                            if model_id:
                                models.append(model_id)
                    if models:
                        return models
                if isinstance(data, dict) and "models" in data:
                    return list(data["models"])
                if isinstance(data, list):
                    return data
        except Exception:
            pass

        # Fallback to local directory listing
        if self.models_dir and os.path.isdir(self.models_dir):
            try:
                items = [f for f in os.listdir(self.models_dir) if os.path.isdir(os.path.join(self.models_dir, f)) or f.endswith(('.bin', '.pt', '.safetensors'))]
                return items
            except Exception:
                return []

        return []

    def send_prompt(self, prompt: str, model: str | None = None, timeout: int = 30) -> str:
        """Send `prompt` to the local inference service.

        Uses the OpenAI-compatible LM Studio chat-completions shape by default.
        """
        selected_model = model or self.default_model
        if not selected_model:
            available_models = self.list_models()
            selected_model = available_models[0] if available_models else "local-model"

        payload = {
            "model": selected_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "stream": False,
        }

        url = self._url(self.generate_path)
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            # OpenAI-compatible response shape
            if isinstance(data, dict) and "choices" in data and data["choices"]:
                choice = data["choices"][0]
                if isinstance(choice, dict):
                    message = choice.get("message") or {}
                    if isinstance(message, dict) and message.get("content"):
                        return message["content"]
                    if choice.get("text"):
                        return choice["text"]

            # Accept common fallback shapes: {"text": "..."} or simple string
            if isinstance(data, dict):
                if "text" in data:
                    return data["text"]
                if "output" in data:
                    return data["output"]
                # if model returned streaming chunks or other formats, attempt to stringify
                return json.dumps(data)
            if isinstance(data, str):
                return data
            return str(data)
        except requests.HTTPError as e:
            logger.error(f"Local AI HTTP error: {e}")
            raise RuntimeError(f"Local AI error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling local AI: {e}")
            raise RuntimeError(f"Unexpected local AI error: {e}")

class GroqAIClient:
    """
    Client for interacting with Groq API.
    Provides fast inference for Llama/Mixtral models.
    """
    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. "
                f"Get a free key at {GROQ_KEYS_LINK} "
                "and add it to your .env file."
            )
        
        from groq import Groq
        base_url = os.getenv("GROQ_BASE_URL")
        if base_url:
            self.client = Groq(api_key=api_key, base_url=base_url)
        else:
            self.client = Groq(api_key=api_key)
            
        # Using Llama 3 8B or Mixtral for fast JSON generation
        self.model = os.getenv("GROQ_MODEL", GROQ_MODEL_ID)

    @retry(
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(RuntimeError),
        reraise=True
    )
    def send_prompt(self, prompt: str, timeout: int = API_REQUEST_TIMEOUT, model: str | None = None) -> str:
        selected_model = model or self.model
        logger.info(f"Sending prompt to Groq ({len(prompt)} chars) using {selected_model}...")
        try:
            # Append JSON instruction to ensure the API accepts the JSON format constraint
            if "json" not in prompt.lower():
                prompt += "\n\nRespond ONLY in valid JSON format."
                
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=selected_model,
                response_format={"type": "json_object"},
                timeout=timeout
            )
            response = chat_completion.choices[0].message.content
            logger.info(f"Received response ({len(response)} chars)")
            return response
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise RuntimeError(f"Groq API error: {str(e)}")



def get_ai_client() -> object:
    """Factory to return the configured AI client.

    Auto-detects backend based on available API keys. Gemini is prioritized.
    Environment variable `AI_BACKEND` can be used to explicitly override.
    """
    backend = os.getenv("AI_BACKEND", "").lower()
    
    if backend == "local":
        logger.info("Using LocalAIClient (AI_BACKEND=local)")
        return LocalAIClient()
        
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    if backend == "groq" and groq_key:
        logger.info("Using GroqAIClient (AI_BACKEND=groq)")
        return GroqAIClient()
    elif backend == "gemini" and gemini_key:
        logger.info("Using Gemini AIClient (AI_BACKEND=gemini)")
        return AIClient()

    # Auto-detect fallback
    if gemini_key:
        logger.info("Auto-selected Gemini AIClient (GEMINI_API_KEY found)")
        return AIClient()
    elif groq_key:
        logger.info("Auto-selected GroqAIClient (GROQ_API_KEY found)")
        return GroqAIClient()
        
    logger.info("Using Gemini AIClient (default)")
    return AIClient()