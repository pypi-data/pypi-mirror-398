from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, List

from spacy.tokens import Doc, Token

from vnerrant.components.alignment import Alignment
from vnerrant.components.classifier import BaseClassifer
from vnerrant.components.explainer import BaseExplainer
from vnerrant.components.merger import BaseMerger
from vnerrant.components.postprocessor import BasePostprocessor
from vnerrant.constants import MergeType, StyleGuide, TokenizeTypes
from vnerrant.model.edit import Edit, EditCollection
from vnerrant.utils import edit_utils
from vnerrant.utils.string_utils import StringTokenizer

Token.set_extension("full_text", default=None, force=True)


def update_doc(doc: Doc, tokens: List[str]):
    """
    Update the full_text attribute of the tokens in a spacy Doc object.
    Args:
        doc (Doc): A spacy Doc object
        tokens (list[str]): A list of token texts with whitespace
    """
    # assert len(doc) == len(tokens) # Pass only if tokenzize with spacy
    for token, text in zip(doc, tokens):
        token._.full_text = text


class Annotator:
    """
    Annotator class for automatic annotation of parallel text with ERRANT edits.
    """

    def __init__(
        self,
        lang: str,
        nlp: Any = None,
        merger: BaseMerger = None,
        classifier: BaseClassifer = None,
        explainer: BaseExplainer = None,
        postprocessor: BasePostprocessor = None,
    ):
        """
        Initialise the annotator with a language id, spacy processing object,
        merging module, and classifier module.
        :param lang: A string language id: e.g. "en"
        :param nlp: A spacy processing object for the language
        :param merger: A merging module for the language
        :param classifier: A classifier module for the language
        """
        self.lang = lang
        self.nlp = nlp

        self.merger = merger or self._import_module(merger, "merger")
        self.classifier = classifier or self._import_module(classifier, "classifier")
        self.explainer = explainer or self._import_module(explainer, "explainer")
        self.postprocessor = postprocessor or self._import_module(
            postprocessor, "postprocessor"
        )

    def _import_module(self, module, module_type):
        """
        Import a module from the components' directory.
        :param module: A module object
        :param module_type: A string module type
        :return: A module object
        """
        base_path = Path(__file__).resolve().parent
        module_name = f"vnerrant.components.{self.lang}.{module_type}"
        module_path = base_path / "components" / self.lang / f"{module_type}.py"

        if module_path.exists():
            Module = importlib.import_module(module_name).__getattribute__(
                module_type.capitalize(),
            )
            return Module()
        else:
            raise ValueError(f"No {module_type} available for language: {self.lang}")

    def parse(self, text: str, tokenize_type: str = TokenizeTypes.SPLIT) -> Doc:
        """
        Parse a text string with spacy.
        :param text: A text string
        :param tokenize_type: A flag to tokenize the text string
        :return: A spacy Doc object
        """
        if tokenize_type == TokenizeTypes.SPACY:
            text = self.nlp(text)
        elif tokenize_type == TokenizeTypes.SPLIT:
            text = Doc(self.nlp.vocab, text.split())
            text = self.nlp(text)
        elif tokenize_type == TokenizeTypes.STRING:
            doc = self.nlp(text)
            tokens = [token.text_with_ws for token in doc]
            words = []
            for token in tokens:
                tokenizer = StringTokenizer(token, return_delimiter=True)
                sub_tokens = []
                while tokenizer.has_more_tokens():
                    sub_tokens.append(tokenizer.next_token())
                words.extend(sub_tokens)

            spaces = [False] * len(words)
            text = Doc(self.nlp.vocab, words=words, spaces=spaces)
            text = self.nlp(text)
        else:
            raise ValueError(f"Tokenize Type {tokenize_type} is not supported")

        return text

    def parse_raw(self, text: str, tokenize_type: str = TokenizeTypes.SPLIT) -> Doc:
        """
        Parse a raw text string with spacy.
        :param text: A text string
        :param tokenize_type: A flag to tokenize the text string
        :return: A spacy Doc object
        """
        # Normalise text and get list of token texts with whitespace
        # Example: " this a    test." -> " this a test." and [" ", "this ", "a    ", "test", "."]
        processed_text, tokens = self.preprocess(text)

        # Parse text
        doc = self.parse(processed_text, tokenize_type=tokenize_type)

        # Update the full_text attribute of the tokens in the spacy Doc object
        update_doc(doc, tokens)

        return doc

    def align(self, orig: Doc, cor: Doc, lev: bool = False) -> Alignment:
        """
        Align an original and corrected text string.
        :param orig: An original text string
        :param cor: A corrected text string
        :param lev: A flag to use levenshtein alignment
        :return: An Alignment object
        """
        return Alignment(orig, cor, lev)

    def merge(self, alignment: Alignment, merging: str = MergeType.RULES) -> list[Edit]:
        """
        Merge an alignment into a list of edits.
        :param alignment: An Alignment object
        :param merging: A string merging strategy
        :return: A list of Edit objects
        """
        # rules: Rule-based merging
        if merging == MergeType.RULES:
            edits = self.merger.get_all_rule_merge_edits(
                alignment.orig,
                alignment.cor,
                alignment.align_seq,
            )
        # all-split: Don't merge anything
        elif merging == MergeType.ALL_SPLIT:
            edits = self.merger.get_all_split_edits(
                alignment.orig,
                alignment.cor,
                alignment.align_seq,
            )
        # all-merge: Merge all adjacent non-match ops
        elif merging == MergeType.ALL_MERGE:
            edits = self.merger.get_all_merge_edits(
                alignment.orig,
                alignment.cor,
                alignment.align_seq,
            )
        # all-equal: Merge all edits of the same operation type
        elif merging == MergeType.ALL_EQUAL:
            edits = self.merger.get_all_equal_edits(
                alignment.orig,
                alignment.cor,
                alignment.align_seq,
            )
        # Unknown
        else:
            raise Exception(
                "Unknown merging strategy. Choose from: rules, all-split, all-merge, all-equal.",
            )
        return edits

    def classify(self, edit: Edit) -> Edit:
        """
        Classify an edit with the classifier.
        :param edit: An Edit object
        :return: An Edit object
        """
        return self.classifier.classify(edit)

    def explain(self, edit: Edit) -> Edit:
        """
        Explain an edit with the explainer.
        :param edit: An Edit object
        :return: An Edit object
        """
        return self.explainer.explain(edit)

    def annotate(
        self,
        orig: Doc,
        cor: Doc,
        lev: bool = False,
        merging: str = MergeType.RULES,
    ) -> list[Edit]:
        """
        Annotate a pair of original and corrected spacy Doc objects.
        :param orig: An original spacy Doc object
        :param cor: A corrected spacy Doc object
        :param lev: A flag to use levenshtein alignment
        :param merging: A string merging strategy
        :return: A list of Edit objects
        """
        alignment = self.align(orig, cor, lev)
        edits = self.merge(alignment, merging)
        for edit in edits:
            self.classify(edit)
            self.explain(edit)
        return edits

    def annotate_raw(
        self,
        orig: str,
        cor: str,
        lev: bool = False,
        merging: str = MergeType.RULES,
        tokenize_type: str = TokenizeTypes.SPACY,
    ) -> list[Edit]:
        """
        Annotate a pair of original and corrected string objects.
        :param orig: An original text
        :param cor: A corrected text
        :param lev: A flag to use levenshtein alignment
        :param merging: A string merging strategy
        :param tokenize_type: A string tokenize type strategy
        :return: A list of Edit objects
        """
        orig_doc = self.parse_raw(orig, tokenize_type=tokenize_type)
        cor_doc = self.parse_raw(cor, tokenize_type=tokenize_type)

        # Get edits and match edits
        alignment = self.align(orig_doc, cor_doc, lev)
        match_edits = edit_utils.get_match_edits(alignment)
        edits = self.merge(alignment, merging)

        # Classify and explain edits
        for edit in edits:
            self.classify(edit)
            self.explain(edit)

        edit_collection = EditCollection(
            orig, cor, orig_doc, cor_doc, edits, match_edits
        )
        self.postprocess(edit_collection)

        return edit_collection.edits

    def preprocess(self, text: str, **kwargs) -> tuple[str, list[str]]:
        """
        Normalise a text string.
        :param text: A text string
        :return: A normalised text string and a list of token texts with whitespace
        """
        if not text:
            return text, []

        doc = self.nlp(text)
        token_with_ws_texts = [token.text_with_ws for token in doc]

        # Merge space token to the previous token
        merged_token_with_ws_texts = []
        for index in range(len(doc)):
            if index == 0:
                merged_token_with_ws_texts.append(token_with_ws_texts[index])
                continue

            if doc[index].is_space:
                merged_token_with_ws_texts[-1] += token_with_ws_texts[index]
            else:
                merged_token_with_ws_texts.append(token_with_ws_texts[index])

        assert (
            "".join(merged_token_with_ws_texts) == text
        ), "Error in normalised text processing"

        processed_text = " ".join([token for token in text.split() if token.strip()])
        if not merged_token_with_ws_texts[0].strip():
            processed_text = merged_token_with_ws_texts[0] + processed_text

        return processed_text, merged_token_with_ws_texts

    def postprocess(
        self,
        edit_collection: EditCollection,
        is_update_span: bool = True,
        is_update_contraction_edit: bool = True,
    ):
        """
        Postprocess the edit collection.

        Args:
            edit_collection (EditCollection): An EditCollection object
            is_update_span (bool): A flag to update the span of the edits
            is_update_contraction_edit (bool): A flag to update the contraction edits

        Returns:
            None
        """
        edit_utils.update_edits(
            edit_collection.orig_doc, edit_collection.cor_doc, edit_collection.edits
        )
        edit_utils.update_edits(
            edit_collection.orig_doc,
            edit_collection.cor_doc,
            edit_collection.match_edits,
        )

        space_edits = []
        for edit in edit_collection.match_edits:
            if edit.original.text == edit.corrected.text:
                continue

            space_edits.append(edit_utils.process_space_edit(edit))

        edit_utils.merge_edit_collection_with_space_edits(edit_collection, space_edits)
        edit_utils.update_operator(edit_collection.edits)
        if is_update_span:
            edit_utils.update_span_edit(edit_collection.edits)

        if is_update_contraction_edit:
            edit_utils.merge_contraction_with_aux(edit_collection)

        self.postprocessor.process(edit_collection)

    def import_edit(
        self,
        orig: Doc,
        cor: Doc,
        edit: list,
        min: bool = True,
        old_cat: bool = False,
    ) -> Edit:
        """
        Import an edit from an external source.
        :param orig: An original text string
        :param cor: A corrected text string
        :param edit: An edit list of the form: [o_start, o_end, c_start, c_end]
        :param min: A flag to minimise the edit
        :param old_cat: A flag to use the old error type classification
        :return: An Edit object
        """
        # Undefined error type
        if len(edit) == 4:
            edit_obj = Edit.from_original_and_correction(orig, cor, edit)
        # Existing error type
        elif len(edit) == 5:
            edit_obj = Edit.from_original_and_correction(orig, cor, edit[:4], edit[4])
        # Unknown edit format
        else:
            raise Exception(
                "Edit not of the form: " "[o_start, o_end, c_start, c_end, (cat)]",
            )
        # Minimise edit
        if min:
            edit_obj = edit_obj.minimise()
        # Classify edit
        if not old_cat:
            edit_obj = self.classify(edit_obj)
        return edit_obj
