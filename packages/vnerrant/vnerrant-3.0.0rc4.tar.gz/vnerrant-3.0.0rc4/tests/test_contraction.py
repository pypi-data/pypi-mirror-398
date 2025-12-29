import pytest

import vnerrant

annotator = vnerrant.load("en")


@pytest.mark.parametrize(
    "original, corrected, edit_type",
    [
        (
            "They 're much taller than last year .",
            "They are much taller than last year .",
            "CONTR",
        ),  # Contraction
        (
            "They are much taller than last year .",
            "They 're much taller than last year .",
            "CONTR",
        ),  # Contraction
        (
            "There 're too many people in the room .",
            "There 's too many people in the room .",
            "VERB:SVA",
        ),  # SVA
        (
            "There 're too many people in the room .",
            "There is too many people in the room .",
            "VERB:SVA",
        ),  # SVA
        (
            "There are too many people in the room .",
            "There 's too many people in the room .",
            "VERB:SVA",
        ),  # SVA
        (
            "There 's too many people in the room .",
            "There were too many people in the room .",
            "VERB:TENSE",
        ),  # Tense
        (
            "There 's too many people in the room .",
            "There was too many people in the room .",
            "VERB:TENSE",
        ),  # Tense
        (
            "There had too many people in the room .",
            "There 's too many people in the room .",
            "VERB",
        ),  # Choice
        (
            "there aren't wrong sentences",
            "there are not wrong sentences",
            "CONTR",
        ),  # Contraction
    ],
)
def test_contraction(original, corrected, edit_type):
    edits = annotator.annotate_raw(original, corrected)
    for edit in edits:
        print(edit)
        assert edit.edit_type[2:] == edit_type
