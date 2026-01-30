"""Tests for Gemini parsing logic with mocked responses."""

import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the genai configuration before importing
with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
    import google.generativeai as genai


def mock_gemini_response(response_text):
    """Create a mock Gemini response object."""
    mock_response = MagicMock()
    mock_response.text = response_text
    return mock_response


@patch("shared.gemini_client.genai")
def test_parse_simple_reply(mock_genai):
    """Should parse a simple habit reply correctly."""
    from shared.gemini_client import parse_habit_reply

    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.return_value = mock_gemini_response(
        '{"habits": {"Walking/Running": 45, "Cook Morning": 30}}'
    )

    result = parse_habit_reply("walked 45, cooked 30")
    assert result == {"Walking/Running": 45, "Cook Morning": 30}


@patch("shared.gemini_client.genai")
def test_parse_sandhi_both(mock_genai):
    """Should handle 'sandhi both' correctly."""
    from shared.gemini_client import parse_habit_reply

    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.return_value = mock_gemini_response(
        '{"habits": {"Sandhi - Morning": 10, "Sandhi - Evening": 5}}'
    )

    result = parse_habit_reply("sandhi both")
    assert result == {"Sandhi - Morning": 10, "Sandhi - Evening": 5}


@patch("shared.gemini_client.genai")
def test_parse_default_times(mock_genai):
    """Should use default times when no duration specified."""
    from shared.gemini_client import parse_habit_reply

    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.return_value = mock_gemini_response(
        '{"habits": {"Utensils": 15, "Clothes": 15, "Yoga": 15}}'
    )

    result = parse_habit_reply("utensils, clothes, yoga")
    assert result["Utensils"] == 15
    assert result["Clothes"] == 15
    assert result["Yoga"] == 15


@patch("shared.gemini_client.genai")
def test_parse_with_markdown_wrapping(mock_genai):
    """Should handle response wrapped in markdown code blocks."""
    from shared.gemini_client import parse_habit_reply

    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.return_value = mock_gemini_response(
        '```json\n{"habits": {"Walking/Running": 30}}\n```'
    )

    result = parse_habit_reply("walked 30")
    assert result == {"Walking/Running": 30}


@patch("shared.gemini_client.genai")
def test_parse_invalid_response_retries(mock_genai):
    """Should retry once on invalid response, then raise ValueError."""
    from shared.gemini_client import parse_habit_reply

    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.return_value = mock_gemini_response("not valid json")

    try:
        parse_habit_reply("gibberish input")
        assert False, "Should have raised ValueError"
    except ValueError:
        # Called twice (initial + 1 retry)
        assert mock_model.generate_content.call_count == 2


@patch("shared.gemini_client.genai")
def test_parse_filters_invalid_habit_names(mock_genai):
    """Should filter out habit names that aren't in the config."""
    from shared.gemini_client import parse_habit_reply

    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.return_value = mock_gemini_response(
        '{"habits": {"Walking/Running": 45, "Meditation": 20, "Invalid Habit": 10}}'
    )

    result = parse_habit_reply("walked 45, meditated 20")
    assert "Walking/Running" in result
    assert "Meditation" not in result
    assert "Invalid Habit" not in result


@patch("shared.gemini_client.genai")
def test_parse_full_message(mock_genai):
    """Should parse a realistic full daily reply."""
    from shared.gemini_client import parse_habit_reply

    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.return_value = mock_gemini_response(json.dumps({
        "habits": {
            "Walking/Running": 45,
            "Sandhi - Morning": 10,
            "Sandhi - Evening": 5,
            "Daily Brief": 20,
            "Cook Morning": 30,
            "Utensils": 15,
            "Clothes": 15,
            "Audiobooks/Reading": 20,
        }
    }))

    result = parse_habit_reply("walked 45, sandhi both, brief 20, cooked, utensils, clothes, read 20")
    assert len(result) == 8
    assert result["Walking/Running"] == 45
    assert result["Sandhi - Morning"] == 10
    assert result["Sandhi - Evening"] == 5
    assert result["Audiobooks/Reading"] == 20
