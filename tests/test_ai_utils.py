from ai_utils import build_ai_prompt, build_game_context


def test_build_game_context_includes_history():
    context = build_game_context(
        difficulty="Normal",
        low=1,
        high=50,
        attempt_limit=8,
        attempts=3,
        history=[10, 25, 40],
        status="playing",
    )

    assert "Difficulty: Normal" in context
    assert "Range: 1 to 50" in context
    assert "Guess history: 10, 25, 40" in context


def test_build_ai_prompt_references_history():
    context = (
        "Game status: playing\n"
        "Difficulty: Normal\n"
        "Range: 1 to 50\n"
        "Attempt limit: 8\n"
        "Attempts used: 3\n"
        "Guess history: 10, 25, 40\n"
    )
    prompt = build_ai_prompt(context)

    assert "Game context:" in prompt
    assert "Guess history: 10, 25, 40" in prompt
    assert "next guess" in prompt.lower()
