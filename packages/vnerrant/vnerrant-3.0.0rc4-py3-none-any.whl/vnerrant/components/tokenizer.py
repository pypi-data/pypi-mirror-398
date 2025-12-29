# Ref: https://spacy.io/usage/linguistic-features#tokenization
# https://en.wikipedia.org/wiki/Wikipedia:List_of_English_contractions
from __future__ import annotations

import re

import spacy
from spacy.tokenizer import Tokenizer
from spacy.util import compile_infix_regex, compile_prefix_regex, compile_suffix_regex

# Patterns for prefix and suffix tokenization
PATTENRS_PREFIX = [r"""^[\[\({<"'-=\*\+,;:\.]+""", r"^'''"]
PATTERNS_SUFFIX = [r"""[\]\)}>"'-\*\+!?\.,;:]$""", r"'''$", r"\.+$"]

# patterns for cotraction in the middle of a word. e.g. "I'm", "you're", "we'll", "they've"
# Use case:
# Personal pronouns: "I", "you", "he", "she", "it", "we", "they", "someone", "somebody", "something"
# Interrogative pronouns: "who", "what", "where", "when", "why", "how", "which"
# Demonstrative pronouns: "this", "that", "these", "those", "here", "there"
# Verbs: "am", "is", "are", "was", "were", \
# "will", "can", "could", "should", "would", "might", "must",
# "do", "does", "did", "have", "has", "had"

PATTERNS_INFIX = [
    r"(?<=\w)('m)",
    r"(?<=\w)('re)",
    r"(?<=\w)('s)",
    r"(?<=\w)('d)",
    r"(?<=\w)('ve)",
    r"(?<=\w)('ll)",
    r"(?<=\w)(n't)",
    r"(?<=\w)('all)",
    r"""(?<=\w)[?!"'<>\[\]\(\)\+=]""",
]


def custom_tokenizer(nlp):
    # Compile custom tokenization patterns
    custom_prefixes = PATTENRS_PREFIX
    custom_suffixes = PATTERNS_SUFFIX
    custom_infixes = PATTERNS_INFIX
    simple_url_re = re.compile(r"""^https?://""")

    prefix_re = compile_prefix_regex(custom_prefixes)
    suffix_re = compile_suffix_regex(custom_suffixes)
    infix_re = compile_infix_regex(custom_infixes)

    return Tokenizer(
        nlp.vocab,
        prefix_search=prefix_re.search,
        suffix_search=suffix_re.search,
        infix_finditer=infix_re.finditer,
        url_match=simple_url_re.match,
    )


if __name__ == "__main__":
    # Load a SpaCy model
    nlp = spacy.load("en_core_web_sm")

    # Set the custom tokenizer
    nlp.tokenizer = custom_tokenizer(nlp)

    # Test the tokenizer
    test_text = """**The tech giants Apple-Microsoft and X who've considering the acquisition of a U.K. startup for a sum of $1 billion. \
This potential deal is scheduled to be discussed at 10:00 a.m on March 21/1997. \
The initiative isn't internally referred to as "Project-Alpha". \
For any queries or further communication, please avoid using the email address xxx@gmail.com. Do you any questions?"""
    doc = nlp(test_text)
    for token in doc:
        print(token.text)
