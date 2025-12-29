import pytest

import vnerrant

annotator = vnerrant.load("en")


def test_type_error_single():
    original = "The teacher I admire the most is Mr. Smith."
    corrected = "The teacher whom I admire the most is Mr. Smith."
    edits = annotator.annotate_raw(original, corrected)
    for edit in edits:
        print(edit)


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "They won't be able to attend the meeting.",
            "They will not be able to attend the meeting.",
        ),
        ("She'd like to visit the museum.", "She would like to visit the museum."),
        ("It doesn't make any sense.", "It does not make any sense."),
        (
            "She'll finish the task by tomorrow.",
            "She will finish the task by tomorrow.",
        ),
        ("You weren't supposed to open it.", "You were not supposed to open it."),
    ],
)
def test_contraction_type_error(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    for edit in edits:
        print(edit)
    # assert len(edits) == 1
    assert edits[0].edit_type[2:] == "CONTR"


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "The book I bought yesterday is interesting.",
            "The book that I bought yesterday is interesting.",
        ),
        ("The car she drives is very fast.", "The car which she drives is very fast."),
        (
            "The teacher I admire the most is Mr. Smith.",
            "The teacher whom I admire the most is Mr. Smith.",
        ),
    ],
)
def test_pronoun_type_error(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    for edit in edits:
        print(edit)
    assert len(edits) == 1
    assert edits[0].edit_type[2:] == "PRON"


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "The restaurant we ate dinner last night was excellent.",
            "The restaurant where we ate dinner last night was excellent.",
        ),
    ],
)
def test_adverb_type_error(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    for edit in edits:
        print(edit)
    assert len(edits) == 1
    assert edits[0].edit_type[2:] == "ADV"


@pytest.mark.parametrize(
    "original, corrected, type_error",
    [
        (
            "He hadn't been to the dentist in over two years.",
            "He had not been to the dentist in over two years.",
            "CONTR",
        ),
        (
            "Economic growth are expected to decline due to several external factor.",
            "Economic growth is expected to decline due to several external factor.",
            "VERB:SVA",
        ),
        (
            "Advanced technologies are changing face of modern medicine very quickly.",
            "Advanced technologies are changing the face of modern medicine very quickly.",
            "DET",
        ),
        (
            "She likes eat apples.",
            "She likes to eat apples.",
            "VERB:FORM",
        ),
        # (
        #     "Actually, I am busy all the time, so I do n’t have many time to watch movies. But whenever I have free time, I will pump myself up in movies,",
        #     "Actually, I am busy all the time, so I don't have many time to watch movies. But whenever I have free time, I will pump myself up in movies,",
        #     "OTHER",
        # ),
    ],
)
def test_type_error(original, corrected, type_error):
    edits = annotator.annotate_raw(original, corrected)
    for edit in edits:
        print(edit)
    assert len(edits) == 1
    assert edits[0].edit_type[2:] == type_error
