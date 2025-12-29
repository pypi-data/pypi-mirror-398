from __future__ import annotations

from typing import Any

import spacy

from vnerrant.annotator import Annotator
from vnerrant.utils.utils import get_spacy_models_for_language

__version__ = "v3.0.0rc4"


def load(
    lang: str = "en",
    model_name: str = "en_core_web_sm",
    nlp: Any = None,
) -> Annotator:
    """
    Load an VNERRANT Annotator object for a given language.
    :param lang: The language code (e.g., 'en' for English) to load.
    :param model_name: The spaCy model name to load.
    :param nlp: The spaCy model object to load.
    :return: An Annotator object.
    """
    # Make sure the language is supported
    supported = {"en"}  # TODO for other languages. English only for now.
    if lang not in supported:
        raise Exception("%s is an unsupported or unknown language" % lang)

    model_names = get_spacy_models_for_language(lang)
    if model_name not in model_names:
        spacy.cli.download(model_name)

    # Load spacy model if not provided
    nlp = nlp or spacy.load(model_name, disable=["ner"])

    return Annotator(lang, nlp)
