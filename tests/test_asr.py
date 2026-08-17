from __future__ import annotations

from asr.phonetic_shield import PhoneticShield


def test_phonetic_shield_word_subs():
    shield = PhoneticShield()
    # Force injection for test predictability
    shield._word_map = {"pwease": "please", "bwing": "bring"}

    text = "Pwease bwing me water."
    corrected, changes = shield.apply(text)

    # Substitutions are case-insensitive and lowercase by design.
    assert corrected == "please bring me water."
    assert len(changes) == 2


def test_phonetic_shield_regex():
    shield = PhoneticShield()
    shield._word_map = {}
    import re
    shield._regex_patterns = [(re.compile(r"\b(\w+)( \1){2,}\b", re.I), r"\1")]

    text = "i i i want that"
    corrected, changes = shield.apply(text)

    assert corrected == "i want that"
    assert len(changes) == 1
