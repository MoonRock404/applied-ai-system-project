import os
import sys
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import ai_utils
from ai_utils import get_ai_strategy, _gemini_strategy, _is_transient_gemini_error


STRATEGY_KWARGS = dict(
    difficulty="Normal",
    low=1,
    high=50,
    attempt_limit=8,
    attempts=3,
    history=[10, 25, 40],
    status="playing",
)


# ---------------------------------------------------------------------------
# get_ai_strategy — missing key / missing SDK guards
# ---------------------------------------------------------------------------

def test_get_ai_strategy_no_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = get_ai_strategy(**STRATEGY_KWARGS)
    assert "disabled" in result.lower()


def test_get_ai_strategy_no_sdk(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    original = ai_utils.genai
    ai_utils.genai = None
    try:
        result = get_ai_strategy(**STRATEGY_KWARGS)
    finally:
        ai_utils.genai = original
    assert "disabled" in result.lower()


# ---------------------------------------------------------------------------
# _gemini_strategy — successful response via new Client API
# ---------------------------------------------------------------------------

def test_gemini_strategy_returns_text_from_client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    fake_response = MagicMock()
    fake_response.text = "  Try 35 next.  "

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    fake_genai = MagicMock(spec=["Client"])
    fake_genai.Client.return_value = fake_client

    with patch.object(ai_utils, "genai", fake_genai):
        result = _gemini_strategy("some prompt")

    assert result == "Try 35 next."


# ---------------------------------------------------------------------------
# _gemini_strategy — successful response via legacy generate_text API
# ---------------------------------------------------------------------------

def test_gemini_strategy_returns_text_from_legacy_api(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    fake_response = MagicMock()
    fake_response.text = "Use binary search."
    del fake_response.Client  # ensure hasattr(genai, "Client") is False

    fake_genai = MagicMock(spec=["configure", "generate_text"])
    fake_genai.generate_text.return_value = fake_response

    with patch.object(ai_utils, "genai", fake_genai):
        result = _gemini_strategy("some prompt")

    assert result == "Use binary search."
    fake_genai.configure.assert_called_once_with(api_key="fake-key")


# ---------------------------------------------------------------------------
# _gemini_strategy — non-transient error returns fallback immediately
# ---------------------------------------------------------------------------

def test_gemini_strategy_non_transient_error_no_retry(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = ValueError("bad request")

    fake_genai = MagicMock(spec=["Client"])
    fake_genai.Client.return_value = fake_client

    with patch.object(ai_utils, "genai", fake_genai):
        with patch("ai_utils.time.sleep") as mock_sleep:
            result = _gemini_strategy("some prompt")

    assert "failed" in result.lower()
    mock_sleep.assert_not_called()
    assert fake_client.models.generate_content.call_count == 1


# ---------------------------------------------------------------------------
# _gemini_strategy — transient error retries once then gives fallback
# ---------------------------------------------------------------------------

def test_gemini_strategy_transient_error_retries_once(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    transient = OSError("connection reset")

    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = [transient, transient]

    fake_genai = MagicMock(spec=["Client"])
    fake_genai.Client.return_value = fake_client

    with patch.object(ai_utils, "genai", fake_genai):
        with patch("ai_utils.time.sleep") as mock_sleep:
            result = _gemini_strategy("some prompt")

    assert "failed" in result.lower()
    mock_sleep.assert_called_once_with(1.0)
    assert fake_client.models.generate_content.call_count == 2


def test_gemini_strategy_transient_then_success(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    fake_response = MagicMock()
    fake_response.text = "Recovered response."

    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = [OSError("blip"), fake_response]

    fake_genai = MagicMock(spec=["Client"])
    fake_genai.Client.return_value = fake_client

    with patch.object(ai_utils, "genai", fake_genai):
        with patch("ai_utils.time.sleep"):
            result = _gemini_strategy("some prompt")

    assert result == "Recovered response."


# ---------------------------------------------------------------------------
# _is_transient_gemini_error
# ---------------------------------------------------------------------------

def test_transient_on_status_503():
    exc = Exception("server error")
    exc.status_code = 503
    assert _is_transient_gemini_error(exc) is True


def test_not_transient_on_status_400():
    exc = Exception("bad request")
    exc.status_code = 400
    assert _is_transient_gemini_error(exc) is False


def test_transient_on_oserror():
    assert _is_transient_gemini_error(OSError("reset")) is True


def test_not_transient_on_value_error():
    assert _is_transient_gemini_error(ValueError("nope")) is False


# ---------------------------------------------------------------------------
# Integration test — skipped unless GEMINI_API_KEY is set
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set — skipping live API test",
)
def test_get_ai_strategy_live():
    result = get_ai_strategy(**STRATEGY_KWARGS)
    assert isinstance(result, str)
    assert len(result) > 20
