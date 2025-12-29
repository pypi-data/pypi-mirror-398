from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import spacy.symbols as POS

from vnerrant.components.en.lancaster import LancasterStemmer
from vnerrant.components.en.utils import load_pos_map, load_text_file, load_word_list


@dataclass
class LanguageResources:
    """
    Language resources.
    """

    stemmer: LancasterStemmer = LancasterStemmer()
    spell: set[str] = field(default_factory=set)
    filler_words: set[str] = field(default_factory=set)

    @staticmethod
    def load_spell_list(base_dir: Path) -> set[str]:
        return load_word_list(base_dir / "resources" / "en_GB-large.txt")

    @staticmethod
    def load_filler_words(base_dir: Path) -> set[str]:
        return load_text_file(base_dir / "resources" / "filler_words.txt")


@dataclass
class POSResources:
    """
    POS resources.
    """

    pos_map: dict = field(default_factory=dict)
    open_pos1: set = field(
        default_factory=lambda: {POS.ADJ, POS.ADV, POS.NOUN, POS.VERB},
    )
    open_pos2: set = field(default_factory=lambda: {"ADJ", "ADV", "NOUN", "VERB"})
    rare_pos: set = field(default_factory=lambda: {"INTJ", "NUM", "SYM", "X"})

    @staticmethod
    def load_pos_map(base_dir: Path) -> dict:
        return load_pos_map(base_dir / "resources" / "en-ptb_map")


@dataclass
class DependencyResources:
    """
    Dependency resources.
    """

    conts: set = field(
        default_factory=lambda: {"'d", "'ll", "'m", "n't", "'re", "'s", "'ve"},
    )
    mapping_conts: set = field(
        default_factory=lambda: {
            "had": "'d",
            "will": "'ll",
            "am": "'m",
            "not": "n't",
            "are": "'re",
            "is": "'s",
            "have": "'ve",
            "would": "'d",
        }
    )
    aux_conts: dict = field(
        default_factory=lambda: {"ca": "can", "sha": "shall", "wo": "will"},
    )
    dep_map: dict = field(
        default_factory=lambda: {
            "acomp": "ADJ",
            "amod": "ADJ",
            "advmod": "ADV",
            "det": "DET",
            "prep": "PREP",
            "prt": "PART",
            "punct": "PUNCT",
        },
    )


def initialize_resources(
    base_dir: Path,
) -> tuple[LanguageResources, POSResources, DependencyResources]:
    language_resources = LanguageResources()
    language_resources.spell = LanguageResources.load_spell_list(base_dir)
    language_resources.filler_words = LanguageResources.load_filler_words(base_dir)

    pos_resources = POSResources()
    pos_resources.pos_map = POSResources.load_pos_map(base_dir)

    dependency_resources = DependencyResources()

    return language_resources, pos_resources, dependency_resources


base_dir = Path(__file__).resolve().parent
language_resources, pos_resources, dependency_resources = initialize_resources(base_dir)


@dataclass(frozen=True)
class ParentErrorType:
    """
    Parent error types.
    """

    UNK: str = "UNK"
    NOUN: str = "NOUN"
    VERB: str = "VERB"
    ADJECTIVE: str = "ADJ"
    ADVERB: str = "ADV"
    PREPOSITION: str = "PREP"
    PARTICLE: str = "PART"
    DETERMINER: str = "DET"
    PRONOUN: str = "PRON"
    SPELLING: str = "SPELL"
    MORPHOLOGY: str = "MORPH"
    ORTHOGRAPHY: str = "ORTH"
    CONTRACTION: str = "CONTR"
    CONJUNCTION: str = "CONJ"
    WORD_ORDER: str = "WO"
    OTHER: str = "OTHER"
    PUNCTUATION: str = "PUNCT"
    QUESTION_TAG: str = "QUESTION_TAG"
    WORD_CHOICE: str = "WORD_CHOICE"
    PHRASE_CHOICE: str = "PHRASE_CHOICE"


@dataclass(frozen=True)
class ChildrenErrorType:
    """
    Child error types.
    """

    FORM: str = "FORM"
    INFLECTION: str = "INFL"
    NUMBER: str = "NUM"
    POSSESSIVE: str = "POSS"
    SUBJECT_VERB_AGREEMENT: str = "SVA"
    TENSE: str = "TENSE"


@dataclass(frozen=True)
class ParentDisfluencyType:
    """
    Disfluency types.
    """

    DISFLUENCY: str = "DISFLUENCY"


@dataclass(frozen=True)
class ChildrenFluencyType:
    """
    Child fluency types.
    """

    REPETITION: str = "REPETITION"
    FALSE_START: str = "FALSE_START"
    FILLER_PAUSE: str = "FILLER_PAUSE"
