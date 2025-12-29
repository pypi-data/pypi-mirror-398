import pytest

import vnerrant

annotator = vnerrant.load("en")


def test_postprocessor_single():
    original = (
        "Many writers have drawn inspiration from nature for write their famous works."
    )
    corrected = (
        "Many writers have drawn inspiration from nature to write their famous works."
    )
    edits = annotator.annotate_raw(original, corrected)
    for edit in edits:
        print(edit)


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "Eating junk foods are bad for you're health.",
            "Eating junk food is bad for your health.",
        )
    ],
)
def test_postprocess_noun_number_to_noun_inflection(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    assert edits[0].edit_type[2:] == "NOUN:INFL"


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "He gotted a new soccer shoes that fit him more better.",
            "He got a new pair of soccer shoes that fit him better.",
        ),
        (
            "In last holiday, we went to a very beautiful beaches and swimmed in the clear blue waters.",
            "In last holiday, we went to a very beautiful beaches and swam in the clear blue waters.",
        ),
    ],
)
def test_postprocess_verb_choice_to_verb_inflection(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    assert edits[0].edit_type[2:] == "VERB:INFL"


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "Eating healthy food can help you live longer and feel more better every day.",
            "Eating healthy food can help you live longer and feel better every day.",
        ),
    ],
)
def test_postprocess_adverb_to_adjective_form(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    assert edits[0].edit_type[2:] == "ADJ:FORM"


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "The book which I read yesterday is very interesting.",
            "The book that I read yesterday is very interesting.",
        ),
    ],
)
def test_postprocess_determiner_to_pronoun(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    assert edits[0].edit_type[2:] == "PRON"


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "Many species are being endangered due to deforestation.",
            "Many species are becoming endangered due to deforestation.",
        ),
    ],
)
def test_postprocess_verb_tense_to_verb_choice(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    assert edits[0].edit_type[2:] == "VERB"


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "The latest innovations in tech have make our lives much easier than before.",
            "The latest innovations in tech have made our lives much easier than before.",
        ),
        (
            "Eating too much fast food can leaded to health issues like obesity and high blood pressure.",
            "Eating too much fast food can lead to health issues like obesity and high blood pressure.",
        ),
        ("He has work here for two years.", "He has worked here for two years."),
        ("We going to the beach last summer.", "We went to the beach last summer."),
        (
            "The scientist explain that they had discovered a new element.",
            "The scientist explained that they had discovered a new element.",
        ),
    ],
)
def test_postprocess_verb_form_to_verb_tense(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    assert edits[0].edit_type[2:] == "VERB:TENSE"


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "Can I has those blue trousers and this yellow sweater?",
            "Can I have those blue trousers and this yellow sweater?",
        )
    ],
)
def test_postprocess_verb_form_to_verb_sva(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    assert edits[0].edit_type[2:] == "VERB:SVA"


@pytest.mark.parametrize(
    "original, corrected",
    [
        ("She like the songs of that band.", "She likes the songs of that band."),
        (
            "He like painting, and he has created many beautiful pieces of art.",
            "He likes painting, and he has created many beautiful pieces of art.",
        ),
    ],
)
def test_postprocess_spelling_to_verb_sva(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    assert edits[0].edit_type[2:] == "VERB:SVA"


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "Advanced technologys are changing the face of modern medicine very quickly.",
            "Advanced technologies are changing the face of modern medicine very quickly.",
        ),
        (
            "Recent studys show that eating fewer carbohydrates can be beneficial.",
            "Recent studies show that eating fewer carbohydrates can be beneficial.",
        ),
    ],
)
def test_postprocess_spelling_to_noun_inflection(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    assert edits[0].edit_type[2:] == "NOUN:INFL"


@pytest.mark.parametrize(
    "original, corrected, edit_type",
    [
        (
            "You did the dishes already , did n't you ?",
            "You did the dishes already , did you ?",
            "QUESTION_TAG",
        ),
        (
            "You did the dishes already , did you ?",
            "You did the dishes already , did n't you ?",
            "QUESTION_TAG",
        ),
        (
            "You did the dishes already , did n't you ?",
            "You did the dishes already , did not you ?",
            "CONTR",
        ),
        # ── ① Wrong polarity ────────────────────────────────────────────
        ("She is coming , is she ?", "She is coming , isn't she ?", "QUESTION_TAG"),
        (
            "He hasn't arrived yet , hasn't he ?",
            "He hasn't arrived yet , has he ?",
            "QUESTION_TAG",
        ),
        # ── ② Wrong auxiliary/modal ────────────────────────────────────
        (
            "She can play the guitar , does she ?",
            "She can play the guitar , can't she ?",
            "QUESTION_TAG",
        ),
        (
            "They will call us , do they ?",
            "They will call us , won't they ?",
            "QUESTION_TAG",
        ),
        # ── ③ Wrong pronoun ────────────────────────────────────────────
        (
            "My brother is older than me , isn't it ?",
            "My brother is older than me , isn't he ?",
            "QUESTION_TAG",
        ),
        (
            "My brother is older than me , isn't ?",
            "My brother is older than me , isn't he ?",
            "QUESTION_TAG",
        ),
        (
            "My brother is older than me , isn't it ?",
            "My brother is older than me , isn't ?",
            "QUESTION_TAG",
        ),
        (
            "My brother is older than me , isn't it",
            "My brother is older than me , isn't he ?",
            "QUESTION_TAG",
        ),
        (
            "The team won the match , didn't they ?",
            "The team won the match , didn't it ?",
            "QUESTION_TAG",
        ),
        # ── ④ Repeating the noun instead of using a pronoun ────────────
        (
            "Anna is late again , isn't Anna ?",
            "Anna is late again , isn't she ?",
            "QUESTION_TAG",
        ),
        # ── ⑤ Tense mismatch in the tag ────────────────────────────────
        (
            "They went home yesterday , don't they ?",
            "They went home yesterday , didn't they ?",
            "QUESTION_TAG",
        ),
        # ── ⑥ Imperative sentence with an unsuitable tag ───────────────
        ("Close the door , can you ?", "Close the door , will you ?", "QUESTION_TAG"),
        # ── ⑦ Tag after let’s (should be 'shall we') ───────────────────
        ("Let's start , will you ?", "Let's start , shall we ?", "QUESTION_TAG"),
        # ── ⑧ Irregular 'I am' tag (should be 'aren’t I') ──────────────
        ("I'm next , am I ?", "I'm next , aren't I ?", "QUESTION_TAG"),
        # ── ⑨ Missing contraction (did not you → didn’t you) ───────────
        (
            "You cleaned the room , did not you ?",
            "You cleaned the room , didn't you ?",
            "QUESTION_TAG",
        ),
        # DNAI - 925
        ("He isn't ready, isn't he?", "He isn't ready, is he?", "QUESTION_TAG"),
        ("I'm late, aren't I?", "I'm late, am I?", "QUESTION_TAG"),
        (
            "She can speak French, doesn't she?",
            "She can speak French, can't she?",
            "QUESTION_TAG",
        ),
    ],
)
def test_postprocess_question_tag(original, corrected, edit_type):
    edits = annotator.annotate_raw(original, corrected)
    for edit in edits:
        print(edit)
        assert edit.edit_type[2:] == edit_type
        break
