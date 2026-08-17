from __future__ import annotations

from agents.hallucination_guard import HallucinationGuard


def test_hallucination_guard_limits():
    # Limit: 3.0 wps * 1.2 tolerance = 3.6 words allowed per second
    guard = HallucinationGuard(words_per_second=3.0)

    # 1.0 sec audio -> allowed words: int(1.0 * 3.6) = 3
    is_valid, actual, limit = guard.check("one two three", 1.0)
    assert is_valid is True
    assert actual == 3
    assert limit == 3

    # Exceeds limit
    is_valid, actual, limit = guard.check("one two three four", 1.0)
    assert is_valid is False
    assert actual == 4
    assert limit == 3

    # Truncation
    trunc = guard.truncate("one two three four", 1.0)
    assert trunc == "one two three..."
