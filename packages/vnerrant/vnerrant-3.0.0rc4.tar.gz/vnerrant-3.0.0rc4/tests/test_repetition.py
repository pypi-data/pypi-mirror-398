import pytest

import vnerrant
import vnerrant.constants

annotator = vnerrant.load("en")


@pytest.mark.parametrize(
    "original, corrected",
    [
        # ── ① Immediate word repetition ───────────────────────────────
        ("I I think we should leave .", "I think we should leave ."),
        ("I I I think we should leave .", "I think we should leave ."),
        ("The the meeting was too long .", "The meeting was too long ."),
        # ── ② Repetition after a linking verb / filler ────────────────
        (
            "She is is going to join us , isn't she ?",
            "She is going to join us , isn't she ?",
        ),
        ("Do you you agree ?", "Do you agree ?"),
        # ── ③ ‘that that’ / function-word duplication ────────────────
        ("I believe that that idea could work .", "I believe that idea could work ."),
        # ── ④ Repeated verb / imperative ──────────────────────────────
        ("Let's go go now .", "Let's go now ."),
        # ── ⑤ Repeated multi-word phrase ─────────────────────────────
        ("What I want what I want is clarity .", "What I want is clarity ."),
        # ── ⑥ Past-tense verb repeated ───────────────────────────────
        ("He said said he would help .", "He said he would help ."),
        # ── ⑦ Repeated subject pronoun ───────────────────────────────
        ("We we are ready to start .", "We are ready to start ."),
        # ── ⑧ Discourse-marker repetition ────────────────────────────
        ("You know you know it's true .", "You know it's true ."),
    ],
)
def test_repetition(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    for edit in edits:
        print(edit)
        assert edit.edit_type[2:] == "DISFLUENCY:REPETITION"
