"""Tier-L long-context route — orthogonal to the 0..3 reliability tiers.

CRPA (Chunked Retrieval-Prioritized Attention) is stubbed here as a pass-through
that simply flags long-context requests so telemetry/UI can show the route was
taken. Real CRPA (chunk + prioritize + stitch) would slot in behind this
interface without changing the router.
"""
from __future__ import annotations

# ~4 chars/token heuristic for prompt-length estimation without a tokenizer.
_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def crpa_route(prompt: str, threshold_tokens: int) -> dict:
    approx = estimate_tokens(prompt)
    is_long = approx >= threshold_tokens
    return {
        "long_context": is_long,
        "approx_prompt_tokens": approx,
        "threshold_tokens": threshold_tokens,
        "strategy": "CRPA(stub:pass-through)" if is_long else "none",
    }
