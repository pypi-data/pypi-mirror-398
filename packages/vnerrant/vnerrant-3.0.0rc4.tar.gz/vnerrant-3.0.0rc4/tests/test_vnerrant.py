from __future__ import annotations

import pytest

import vnerrant

annotator = vnerrant.load("en")


def check_edits(original, corrected):
    edits = annotator.annotate_raw(original, corrected)
    edits.sort(
        key=lambda x: (
            x.original.start_char,
            x.original.end_char,
            x.corrected.start_char,
            x.corrected.end_char,
        ),
        reverse=True,
    )
    new_text = original
    for edit in edits:
        print(edit)
        start, end, corrected_text = (
            edit.original.start_char,
            edit.original.end_char,
            edit.corrected.text,
        )
        new_text = new_text[:start] + corrected_text + new_text[end:]
    assert new_text == corrected


def test_vnerrant_single():
    orig = "I never thought about, people got so many pet."
    cor = "I never thought about it before. People have so many pets."

    # orig_doc = annotator.parse(orig, tokenize_type="string")
    # cor_doc = annotator.parse(cor, tokenize_type="string")
    #
    # orig_tokens = [token.text_with_ws for token in orig_doc]
    # cor_tokens = [token.text_with_ws for token in cor_doc]

    edits = annotator.annotate_raw(orig, cor)

    for e in edits:
        print(e)


@pytest.mark.parametrize(
    "original, corrected",
    [
        (
            "I never thought about, people got so many pet.",
            "I never thought about it before. People have so many pets.",
        ),
        (
            "That I want to say, is very difficult to understand the conjuntion of the verb's in Spanish Languaje, just Imaging you the same but not in your native lenguaje.",
            "I want to say that it is very difficult to understand the conjugation of the verbs in Spanish, so just imagine the same but not in your native language.",
        ),
        (
            "Somehow, you can't always identify whether their bodies feel uncomfortable merely from their appearance, which leads to some misunderstanding between them.",
            "Somehow, not all of them can you identify whether their bodies feel uncomfortable merely from their appearance, which leads to Some misunderstanding between them?",
        ),
        (
            "We are so sorry we can give you a refund, but for the compensation, I think it a bit too much because you are sittimg here and we are also serving you. It’s salt free day, so it’s actually basically not our fault.",
            "We are so sorry. We can give you a refund, but for the compensation, I think it is a bit too much because you are sitting here and we are also serving you. It’s salt free day, so it’s actually basically not our fault.",
        ),
        (
            "Well, I, I am not sure I think they are offended, because like they do not like the black life matters.",
            "Well, I, I am not sure. I think they are offended, because they do not like black life matters.",
        ),
        (
            "It's important to spend some quality time with your loved ones to strengthen your relationships and create lasting memories.",
            "It is important to spend some quality time with your loved ones to strengthen your relationships and create lasting memories.",
        ),
    ],
)
def test_normal_errant(original, corrected):
    check_edits(original, corrected)


# Test the alignment of the original and corrected text (condition: the corrected text should be standardised)
# Ignore the type of edit #TODO: add the type of edit


@pytest.mark.parametrize(
    "original, corrected",
    [
        ("my world", "hello my world"),
        (" my world", "hello my world"),
        ("  my world", "hello my world"),
        ("   my world", "hello my world"),
        ("    my  world", "hello my world"),
        ("    my    world", "hello my world"),
        ("    my  world ", "hello my world"),
        ("    my  world  ", "hello my world"),
        ("hello word", "hello my world"),
        (" hello world", "hello my world"),
        ("  hello world", "hello my world"),
        ("   hello world", "hello my world"),
        ("   hello  world", "hello my world"),
        ("   hello   world", "hello my world"),
        ("   hello  world ", "hello my world"),
        ("   hello   world  ", "hello my world"),
        ("hello my", "hello my world"),
        (" hello my", "hello my world"),
        ("  hello my", "hello my world"),
        ("  hello  my", "hello my world"),
        ("  hello   my", "hello my world"),
        ("  hello   my ", "hello my world"),
        ("  hello   my  ", "hello my world"),
        ("I'm a student", "I'm a student at the University of Science"),
        ("I'm a student ", "I'm a student at the University of Science"),
        ("I'm a student  ", "I'm a student at the University of Science"),
        (
            "I'm  student at the University of Science",
            "I'm a student at the University of Science",
        ),
        (
            "I a student at the University of Science",
            "I'm a student at the University of Science",
        ),
        (
            "I' a student at the University of Science",
            "I'm a student at the University of Science",
        ),
        (
            "I'm   student at the University of Science",
            "I'm a student at the University of Science",
        ),
        ("This is a book That is a pen.", "This is a book. That is a pen."),
        ("This is a book  That is a pen.", "This is a book. That is a pen."),
        ("This is a  book  That is a pen.", "This is a book. That is a pen."),
        ("This is a  book  That is a pen", "This is a book. That is a pen."),
        ("This is a  book  That is a pen ", "This is a book. That is a pen."),
        ("This is a  book  That is a pen  ", "This is a book. That is a pen."),
        ("This is a  book  that is a pen  ", "This is a book, that is a pen."),
        ("what is your name", "what is your name?"),
        ("what is your name? ", "what is your name?"),
        ("what is your name ? ", "what is your name?"),
        ("what is your name ?  ", "what is your name?"),
    ],
)
def test_missing_and_space_alignment_vnerrant(original, corrected):
    check_edits(original, corrected)


@pytest.mark.parametrize(
    "original, corrected",
    [
        ("hello my world", "my world"),
        ("hello  my world", "my world"),
        ("hello   my world", "my world"),
        (" hello   my world", "my world"),
        (" hello   my world", "my world"),
        ("  hello   my world", "my world"),
        ("   hello   my world", "my world"),
        ("   hello   my  world", "my world"),
        ("   hello   my   world", "my world"),
        ("   hello   my   world ", "my world"),
        ("   hello   my   world  ", "my world"),
        ("hello my world", "world"),
        (" hello my world", "world"),
        ("  hello my world", "world"),
        ("  hello  my world", "world"),
        ("  hello  my  world", "world"),
        ("   hello  my  world ", "world"),
        ("   hello  my  world  ", "world"),
        ("hello my world", "hello world"),
        (" hello my world", "hello world"),
        (" hello  my world", "hello world"),
        (" hello  my  world", "hello world"),
        (" hello  my   world", "hello world"),
        (" hello  my  world ", "hello world"),
        (" hello  my  world ", "hello world"),
        (" hello  my  world", "hello"),
        ("hello my  world", "hello"),
    ],
)
def test_unnecessary_and_space_alignment_vnerrant(original, corrected):
    check_edits(original, corrected)


@pytest.mark.parametrize(
    "original, corrected",
    [
        ("hello me world", "hello my world"),
        ("hello me  world", "hello my world"),
        ("hello  me  world", "hello my world"),
        ("hello  me   world", "hello my world"),
        ("hello   me  world ", "hello my world"),
        (" hello  me  world", "hello my world"),
        (" hello  me   world ", "hello my world"),
        ("  hello  me   world  ", "hello my world"),
        (" hello  me   world .", "hello my world"),
        (" hello  me   world ,", "hello my world."),
        (" hello  me   world ?", "hello my world."),
    ],
)
def test_replace_and_space_alignment_vnerrant(original, corrected):
    check_edits(original, corrected)


def test_empty_vnerrant():
    original = corrected = ""
    edits = annotator.annotate_raw(original, corrected)
    assert len(edits) == 0
