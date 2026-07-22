"""Tier-L long-context flag (CRPA stub) and token estimation."""
from app.router.crpa import crpa_route, estimate_tokens


def test_estimate_tokens_scales_with_length():
    assert estimate_tokens("") >= 1
    assert estimate_tokens("a" * 400) == 100  # ~4 chars/token


def test_short_prompt_not_flagged_long():
    out = crpa_route("hello there", threshold_tokens=8000)
    assert out["long_context"] is False
    assert out["strategy"] == "none"


def test_long_prompt_is_flagged():
    out = crpa_route("word " * 20000, threshold_tokens=8000)
    assert out["long_context"] is True
    assert out["approx_prompt_tokens"] >= 8000
    assert "CRPA" in out["strategy"]
