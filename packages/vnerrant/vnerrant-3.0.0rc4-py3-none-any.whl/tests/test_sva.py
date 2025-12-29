import pytest

import vnerrant

annotator = vnerrant.load("en")


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "They 's pretty more taller than last year . ",
            "They 're much taller than last year .",
        ),
        (
            "There 's too many people in the room .",
            "There are too many people in the room .",
        ),
    ],
)
def test_confuse_sva_to_contraction(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    assert edits[0].edit_type[2:] == "VERB:SVA"
