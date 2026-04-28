import logging
import os
import time
from typing import List

try:
    import google.genai as genai
    from google.genai.errors import ClientError as GeminiClientError
    from google.genai.types import HttpOptions, HttpRetryOptions
except ImportError:
    genai = None
    GeminiClientError = None
    HttpOptions = None
    HttpRetryOptions = None
    try:
        import google.generativeai as genai
        from google.generativeai.errors import ClientError as GeminiClientError
    except ImportError:
        genai = None
        GeminiClientError = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

logger = logging.getLogger(__name__)


def build_game_context(
    difficulty: str,
    low: int,
    high: int,
    attempt_limit: int,
    attempts: int,
    history: List[int],
    status: str,
) -> str:
    history_text = ", ".join(str(x) for x in history) if history else "No guesses yet."
    return (
        f"Game status: {status}\n"
        f"Difficulty: {difficulty}\n"
        f"Range: {low} to {high}\n"
        f"Attempt limit: {attempt_limit}\n"
        f"Attempts used: {attempts}\n"
        f"Guess history: {history_text}\n"
    )


def build_ai_prompt(context: str) -> str:
    return (
        "You are a coaching assistant for a number guessing game.\n"
        "Use only the game context provided below to give the player a safe and helpful strategy for the next guess.\n"
        "Do not guess the secret number directly or make claims that are not supported by the game history.\n\n"
        "Game context:\n"
        f"{context}\n"
        "Please provide:\n"
        "1. A short summary of the current state.\n"
        "2. One suggestion for the next guess or how to narrow the range.\n"
        "3. A reminder about remaining attempts.\n"
    )


def _mask_api_key(key: str) -> str:
    if not key:
        return "not set"
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"


def get_gemini_debug_info() -> dict[str, str]:
    key = os.getenv("GEMINI_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", "not set")
    loaded = bool(key)
    sdk = "none"
    if genai is not None:
        sdk = genai.__name__
    return {
        "gemini_sdk": sdk,
        "gemini_key_loaded": "yes" if loaded else "no",
        "gemini_key_masked": _mask_api_key(key),
        "gemini_model": model,
    }


def _is_transient_gemini_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        return status_code in {500, 502, 503, 504}

    if isinstance(exc, GeminiClientError):
        return False

    if isinstance(exc, OSError):
        return True

    name = type(exc).__name__.lower()
    return "timeout" in name or "connection" in name or "protocol" in name


def _gemini_strategy(prompt: str) -> str:
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-turbo")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set.")
        return "AI strategy coach is disabled. Set GEMINI_API_KEY in your environment to use it."

    if genai is None:
        logger.warning("google.genai nor google.generativeai is not installed. Gemini support disabled.")
        return (
            "AI strategy coach is disabled because the Gemini client library is not installed. "
            "Install it with `pip install -r requirements.txt` and restart the app."
        )

    max_attempts = 2
    backoff_seconds = 1.0
    attempt = 0

    while attempt < max_attempts:
        try:
            if hasattr(genai, "Client"):
                http_options = None
                if HttpOptions is not None and HttpRetryOptions is not None:
                    http_options = HttpOptions(
                        retryOptions=HttpRetryOptions(
                            attempts=1,
                            initialDelay=1.0,
                            maxDelay=2.0,
                            expBase=2.0,
                            jitter=0.0,
                            httpStatusCodes=[500, 502, 503, 504],
                        )
                    )
                client = genai.Client(api_key=api_key, http_options=http_options)
                response = client.models.generate_content(model=model, contents=prompt)
            else:
                genai.configure(api_key=api_key)
                response = genai.generate_text(model=model, prompt=prompt)

            if hasattr(response, "text") and response.text:
                return response.text.strip()
            if hasattr(response, "output") and hasattr(response.output, "text"):
                return response.output.text.strip()
            return str(response)
        except Exception as exc:
            attempt += 1
            if attempt >= max_attempts or not _is_transient_gemini_error(exc):
                logger.exception("Gemini request failed.")
                return "AI strategy coach failed to generate a response from Gemini."

            logger.warning(
                "Transient Gemini failure detected; retrying after %.1f seconds (%s)",
                backoff_seconds,
                exc,
            )
            time.sleep(backoff_seconds)
            backoff_seconds *= 2


def get_ai_strategy(
    difficulty: str,
    low: int,
    high: int,
    attempt_limit: int,
    attempts: int,
    history: List[int],
    status: str,
) -> str:
    context = build_game_context(difficulty, low, high, attempt_limit, attempts, history, status)
    prompt = build_ai_prompt(context)

    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY is not set.")
        return "AI strategy coach is disabled. Set GEMINI_API_KEY in your environment to use it."

    if genai is None:
        logger.warning("google-generativeai is not installed. Gemini support disabled.")
        return (
            "AI strategy coach is disabled because the Gemini client library is not installed. "
            "Install it with `pip install -r requirements.txt` and restart the app."
        )

    return _gemini_strategy(prompt)
