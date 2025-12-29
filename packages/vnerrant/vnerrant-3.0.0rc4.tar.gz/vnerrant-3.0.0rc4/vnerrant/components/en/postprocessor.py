from typing import Optional

from vnerrant.components.en.constants import (
    ChildrenErrorType,
    ParentErrorType,
    base_dir,
    language_resources,
)
from vnerrant.components.postprocessor import BasePostprocessor
from vnerrant.constants import SeparatorTypes
from vnerrant.model.edit import EditCollection
from vnerrant.utils.replacing import ReplacingRule
from vnerrant.utils.wordlist import WordListAdapter

AUXES = frozenset(
    {
        "am",
        "is",
        "are",
        "was",
        "were",
        "do",
        "does",
        "did",
        "have",
        "has",
        "had",
        "can",
        "could",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "must",
        "ought",
        # contracted negatives
        "isn't",
        "aren't",
        "wasn't",
        "weren't",
        "don't",
        "doesn't",
        "didn't",
        "haven't",
        "hasn't",
        "hadn't",
        "can't",
        "couldn't",
        "won't",
        "wouldn't",
        "shan't",
        "shouldn't",
        "mayn't",
        "mightn't",
        "mustn't",
        "oughtn't",
    }
)

PRONOUNS = frozenset(
    {
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "myself",
        "yourself",
        "himself",
        "herself",
        "itself",
        "ourselves",
        "yourselves",
        "themselves",
    }
)

NOT_TOKENS = {"not", "n't"}


class Postprocessor(BasePostprocessor):

    def __init__(self):
        self.noun_wordlist = self._import(WordListAdapter, "wrong_nouns.txt")
        self.replacing_rule = self._import(ReplacingRule, "replacing.dat")

    @staticmethod
    def _import(obj_class, filename: Optional[str] = None):
        data_path = base_dir / "resources"
        if filename:
            data_path = data_path / filename

        if data_path.exists():
            return obj_class(data_path.absolute().as_posix())
        else:
            return None

    def process(self, edit_collection: EditCollection, **kwargs):
        self._postprocess_noun_number(edit_collection)
        self._postprocess_verb_choice(edit_collection)
        self._postprocess_adverb(edit_collection)
        self._postprocess_determiner(edit_collection)
        self._postprocess_verb_tense(edit_collection)
        self._postprocess_verb_form(edit_collection)
        self._postprocess_spelling(edit_collection)
        self._postprocess_question_tag(edit_collection)
        self._postprocess_space_tag(edit_collection)

    @staticmethod
    def __find_next_token_span(
        current_start_char: int, current_end_char: int, sequence: str, order: int = 1
    ):
        """
        Find the next token span in the sequence based on the current start and end character indices.

        Args:
            current_start_char (int): The start character index of the current token.
            current_end_char (int): The end character index of the current token.
            sequence (str): The text sequence to search within.

        Returns:
            tuple: A tuple containing the start and end character indices of the next token.
        """
        start, end = current_start_char, current_end_char

        for _ in range(order):
            # find the very next token after the current span
            found_start = None
            for i, ch in enumerate(sequence[end:]):
                if found_start is None and not ch.isspace():
                    # mark the first non-space character
                    found_start = end + i
                elif found_start is not None and ch.isspace():
                    # we've reached the end of that token
                    start, end = found_start, end + i
                    break
            else:
                # hit end of string before another space
                if found_start is None:
                    # no more tokens at all
                    raise ValueError("No further token found")
                start, end = found_start, len(sequence)

        return start, end

    @staticmethod
    def __find_prev_token_span(
        current_start_char: int, sequence: str, order: int = 1
    ) -> tuple[int, int]:
        """
        Find the span of the n-th previous token in the sequence.

        Args:
            current_start_char (int): start index of the current token
            sequence           (str): the full text
            order              (int): which previous token to find (1 = first previous, 2 = second previous, ...)

        Returns:
            (start, end) span of the requested previous token
        """
        end = current_start_char
        start = current_start_char

        for _ in range(order):
            found_end = None
            # scan backward from just before the current token start
            for i in range(start - 1, -1, -1):
                ch = sequence[i]
                # first non-space we encounter marks the end of the previous token
                if not ch.isspace() and found_end is None:
                    found_end = i + 1
                # once we've marked the end, the next space marks the start boundary
                elif found_end is not None and ch.isspace():
                    start, end = i + 1, found_end
                    break
            else:
                # reached the beginning of the string
                if found_end is None:
                    raise ValueError("No previous token found")
                start, end = 0, found_end

        return start, end

    @staticmethod
    def __remove_punctuation(text: str) -> str:
        return "".join(ch for ch in text if ch.isalnum() or ch.isspace())

    def __safe_next(self, start: int, end: int, text: str, order: int = 1):
        """Return (s, e, tok_lower) for the `order`-th token after span, or None."""
        try:
            s, e = self.__find_next_token_span(start, end, text, order=order)
            return s, e, text[s:e].lower()
        except Exception:
            return None

    def __safe_prev(self, start: int, text: str, order: int = 1):
        """Return (s, e, tok_lower) for the `order`-th token before start, or None."""
        try:
            s, e = self.__find_prev_token_span(start, text, order=order)
            return s, e, text[s:e].lower()
        except Exception:
            return None

    def __has_qmark_within(
        self, text: str, start: int, end: int, max_steps: int
    ) -> bool:
        """Look for '?' within the next `max_steps` tokens after [start:end]."""
        for k in range(1, max_steps + 1):
            nxt = self.__safe_next(start, end, text, order=k)
            if not nxt:
                continue
            _, _, tok = nxt
            if "?" in tok:
                return True
        return False

    def __next_shape_is_pronoun_or_not_pronoun(
        self, text: str, start: int, end: int
    ) -> bool:
        """
        Check if following tokens match:
        - PRONOUN
        - or Negative token then PRONOUN
        """
        n1 = self.__safe_next(start, end, text, order=1)
        if not n1:
            return False
        _, _, n1_tok = n1

        if self.__remove_punctuation(n1_tok) in PRONOUNS:
            return True

        if n1_tok in NOT_TOKENS:
            n2 = self.__safe_next(start, end, text, order=2)
            if not n2:
                return False
            _, _, n2_tok = n2
            return self.__remove_punctuation(n2_tok) in PRONOUNS
        return False

    def __prev_shape_is_aux_or_not_aux(self, text: str, start: int) -> bool:
        """
        Check if preceding tokens match:
          - AUX
          - or NOT_TOKENS then AUX
        """
        p1 = self.__safe_prev(start, text, order=1)
        if not p1:
            return False
        _, _, p1_tok = p1

        if p1_tok in AUXES:
            return True

        if p1_tok in NOT_TOKENS:
            p2 = self.__safe_prev(start, text, order=2)
            if not p2:
                return False
            _, _, p2_tok = p2
            return p2_tok in AUXES
        return False

    def _postprocess_noun_number(self, edit_collection: EditCollection):
        """
        Postprocess the edit collection for noun number.
        Update NOUN_NUMBER -> NOUN_INFLECTION if the word is in the noun wordlist.

        Args:
            edit_collection (EditCollection): An EditCollection object

        Returns:
            None
        """
        if self.noun_wordlist is None:
            return

        noun_number = (
            ParentErrorType.NOUN + SeparatorTypes.COLON + ChildrenErrorType.NUMBER
        )
        noun_inflection = (
            ParentErrorType.NOUN + SeparatorTypes.COLON + ChildrenErrorType.INFLECTION
        )

        for edit in edit_collection.edits:
            if edit.is_space:
                continue
            if edit.edit_type[2:] != noun_number:
                continue

            text = edit.original.text.strip().lower()
            if self.noun_wordlist.check(text):
                edit.edit_type = edit.edit_type[:2] + noun_inflection

            # special case "every days" -> "every day"
            index = edit.original.start_token
            if (
                text == "days"
                and index - 1 >= 0
                and edit_collection.orig_doc[index - 1].lower_ == "every"
            ):
                edit.edit_type = edit.edit_type[:2] + noun_inflection

    def _postprocess_verb_choice(self, edit_collection: EditCollection):
        """
        Postprocess the edit collection for verb choice.
        Update VERB_CHOICE -> VERB_INFLECTION if the corrected word is in the replacing rule.

        Args:
            edit_collection (EditCollection): An EditCollection object

        Returns:
            None
        """
        if self.replacing_rule is None:
            return

        verb_choice = ParentErrorType.VERB
        verb_inflection = (
            ParentErrorType.VERB + SeparatorTypes.COLON + ChildrenErrorType.INFLECTION
        )

        for edit in edit_collection.edits:
            if edit.is_space:
                continue
            if edit.edit_type[2:] != verb_choice:
                continue

            text = edit.original.text.strip()
            corrected = edit.corrected.text.strip()
            replacing = self.replacing_rule.suggest(text)
            if corrected in replacing:
                edit.edit_type = edit.edit_type[:2] + verb_inflection

    def _postprocess_adverb(self, edit_collection: EditCollection):
        """
        Postprocess the edit collection for adverb.
        Update ADV -> ADJECTIVE_FORM if the word is in {more, most} and place before an adj.

        Args:
            edit_collection (EditCollection): An EditCollection object

        Returns:
            None
        """

        def _is_next_token_adj(doc, index):
            if index < len(doc):
                return doc[index].pos_ == "ADJ"
            return False

        adverb_choice = ParentErrorType.ADVERB
        adjective_form = (
            ParentErrorType.ADJECTIVE + SeparatorTypes.COLON + ChildrenErrorType.FORM
        )

        for edit in edit_collection.edits:
            if edit.is_space:
                continue
            if edit.edit_type[2:] != adverb_choice:
                continue

            original = edit.original.text.strip().lower()
            corrected = edit.corrected.text.strip().lower()

            if original in ["more", "most"]:
                next_token_index = edit.original.start_token + 1
                if _is_next_token_adj(edit_collection.orig_doc, next_token_index):
                    edit.edit_type = edit.edit_type[:2] + adjective_form

            if corrected in ["more", "most"]:
                next_token_index = edit.corrected.start_token + 1
                if _is_next_token_adj(edit_collection.cor_doc, next_token_index):
                    edit.edit_type = edit.edit_type[:2] + adjective_form

    def _postprocess_determiner(self, edit_collection: EditCollection):
        """
        Postprocess the edit collection for determiner.
        Update DET -> PRONOUN because the wrong pos mapping.

        Args:
            edit_collection (EditCollection): An EditCollection object

        Returns:
            None
        """
        determiner = ParentErrorType.DETERMINER
        pronoun = ParentErrorType.PRONOUN

        for edit in edit_collection.edits:
            if edit.is_space:
                continue
            if edit.edit_type[2:] != determiner:
                continue

            relative_pronouns = [
                "that",
                "which",
                "who",
                "whom",
                "whose",
                "where",
                "whoever",
                "whomever",
            ]

            if (
                edit.original.end_token - edit.original.start_token == 1
                and edit.original.tokens
            ):
                if (
                    edit.original.tokens[0].pos_ == "PRON"
                    and edit.original.text.strip().lower() in relative_pronouns
                ):
                    edit.edit_type = edit.edit_type[:2] + pronoun

            if (
                edit.corrected.end_token - edit.corrected.start_token == 1
                and edit.corrected.tokens
            ):
                if (
                    edit.corrected.tokens[0].pos_ == "PRON"
                    and edit.corrected.text.strip().lower() in relative_pronouns
                ):
                    edit.edit_type = edit.edit_type[:2] + pronoun

    def _postprocess_verb_tense(self, edit_collection: EditCollection):
        """
        Postprocess the edit collection for verb tense.
        Update VERB_TENSE -> VERB_CHOICE if both original and corrected are verb, have same tag and different lemma.

        Args:
            edit_collection (EditCollection): An EditCollection object

        Returns:
            None
        """
        verb_tense = (
            ParentErrorType.VERB + SeparatorTypes.COLON + ChildrenErrorType.TENSE
        )
        verb_choice = ParentErrorType.VERB

        for edit in edit_collection.edits:
            if edit.is_space:
                continue
            if edit.edit_type[2:] != verb_tense:
                continue
            if edit.original.end_token - edit.original.start_token != 1:
                continue
            if edit.corrected.end_token - edit.corrected.start_token != 1:
                continue
            if not edit.original.tokens or not edit.corrected.tokens:
                continue

            o_token = edit.original.tokens[0]
            c_token = edit.corrected.tokens[0]

            if o_token.tag_ == c_token.tag_ and o_token.lemma_ != c_token.lemma_:
                edit.edit_type = edit.edit_type[:2] + verb_choice

    def _postprocess_verb_form(self, edit_collection: EditCollection):
        """
        Postprocess the edit collection for verb form.
        Update VERB_FORM -> VERB_TENSE if either original or corrected is verb, and tag is in [VBN, VBD]
        Update VERB_FORM -> SUBJECT_VERB_AGREEMENT because the wrong pos in special case "has/have"

        Args:
            edit_collection (EditCollection): An EditCollection object

        Returns:
            None
        """
        verb_form = ParentErrorType.VERB + SeparatorTypes.COLON + ChildrenErrorType.FORM
        verb_tense = (
            ParentErrorType.VERB + SeparatorTypes.COLON + ChildrenErrorType.TENSE
        )
        subject_verb_agreement = (
            ParentErrorType.VERB
            + SeparatorTypes.COLON
            + ChildrenErrorType.SUBJECT_VERB_AGREEMENT
        )

        for edit in edit_collection.edits:
            if edit.is_space:
                continue
            if edit.edit_type[2:] != verb_form:
                continue
            if edit.original.end_token - edit.original.start_token != 1:
                continue
            if edit.corrected.end_token - edit.corrected.start_token != 1:
                continue
            if not edit.original.tokens or not edit.corrected.tokens:
                continue

            o_token = edit.original.tokens[0]
            c_token = edit.corrected.tokens[0]

            # VERB_FORM -> VERB_TENSE
            if (
                o_token.tag_ in ["VBN", "VBD"] or c_token.tag_ in ["VBN", "VBD"]
            ) and o_token.tag_ != c_token.tag_:
                edit.edit_type = edit.edit_type[:2] + verb_tense
                continue

            # VERB_FORM -> SUBJECT_VERB_AGREEMENT
            if (
                edit.original.text.strip().lower() in ["has", "have"]
                and edit.corrected.text.strip().lower() in ["has", "have"]
                and c_token.tag_ in ["VB", "VBZ"]
            ):
                edit.edit_type = edit.edit_type[:2] + subject_verb_agreement

    def _postprocess_spelling(self, edit_collection: EditCollection):
        """
        Postprocess the edit collection for spelling.
        Update SPELLING -> SUBJECT_VERB_AGREEMENT because the wrong pos in special case "like/likes"
        Update SPELLING -> NOUN_INFLECTION because the wrong lemma of some special wrong nouns (technologys, studys).

        Args:
            edit_collection (EditCollection): An EditCollection object

        Returns:
            None
        """
        spelling = ParentErrorType.SPELLING
        subject_verb_agreement = (
            ParentErrorType.VERB
            + SeparatorTypes.COLON
            + ChildrenErrorType.SUBJECT_VERB_AGREEMENT
        )
        noun_inflection = (
            ParentErrorType.NOUN + SeparatorTypes.COLON + ChildrenErrorType.INFLECTION
        )

        for edit in edit_collection.edits:
            if edit.is_space:
                continue
            if edit.edit_type[2:] != spelling:
                continue
            if edit.original.end_token - edit.original.start_token != 1:
                continue
            if edit.corrected.end_token - edit.corrected.start_token != 1:
                continue
            if not edit.original.tokens or not edit.corrected.tokens:
                continue

            # SPELLING -> SUBJECT_VERB_AGREEMENT
            if (
                edit.original.text.strip().lower() in ["like", "likes"]
                and edit.corrected.text.strip().lower() in ["like", "likes"]
                and edit.corrected.tokens[0].tag_ in ["VB", "VBZ"]
            ):
                edit.edit_type = edit.edit_type[:2] + subject_verb_agreement
                continue

            # SPELLING -> NOUN_INFLECTION
            if (
                edit.original.text.strip().isalpha()
                and edit.original.tokens[0].text not in language_resources.spell
                and edit.original.tokens[0].lower_ not in language_resources.spell
                and edit.corrected.tokens[0].pos_ == "NOUN"
                and edit.corrected.text.strip()
                in self.replacing_rule.suggest(edit.original.text.strip())
            ):
                edit.edit_type = edit.edit_type[:2] + noun_inflection
                continue

    def _postprocess_question_tag(self, edit_collection: EditCollection):
        """
        Postprocess the edit collection for contraction.
        Update CONTRACTION -> QUESTION TAG
        """

        # question have pattern
        # aux[not] + proun + ?/EOF
        for edit in edit_collection.edits:
            if edit.is_space:
                continue

            parent_error = edit.edit_type.split(":")[1]
            orig_text = edit.original.text.strip().lower()
            corr_text = edit.corrected.text.strip().lower()
            orig_start, orig_end = edit.original.start_char, edit.original.end_char
            corr_start, corr_end = edit.corrected.start_char, edit.corrected.end_char

            # ----------------- Case 1: CONTRACTION -> QUESTION_TAG -----------------
            if parent_error == ParentErrorType.CONTRACTION:
                if orig_text in NOT_TOKENS and corr_text in NOT_TOKENS:
                    # both original and corrected are NOT_TOKENS, so we can skip this edit for contraction
                    continue
                # Check shape in both original and corrected: prev AUX (or self is AUX), next PRONOUN

                orig_prev = self.__safe_prev(
                    orig_start, edit_collection.orig_doc.text, order=1
                )
                orig_next = self.__safe_next(
                    orig_start, orig_end, edit_collection.orig_doc.text, order=1
                )
                corr_prev = self.__safe_prev(
                    corr_start, edit_collection.cor_doc.text, order=1
                )
                corr_next = self.__safe_next(
                    corr_start, corr_end, edit_collection.cor_doc.text, order=1
                )

                if not (orig_prev and orig_next and corr_prev and corr_next):
                    continue
                _, _, orig_prev_tok = orig_prev
                _, _, corr_prev_tok = corr_prev
                _, _, orig_next_tok = orig_next
                _, _, corr_next_tok = corr_next

                orig_has_aux_near = orig_prev_tok in AUXES or orig_text in AUXES
                corr_has_aux_near = corr_prev_tok in AUXES or corr_text in AUXES

                if (
                    orig_has_aux_near
                    and corr_has_aux_near
                    and self.__remove_punctuation(orig_next_tok) in PRONOUNS
                    and self.__remove_punctuation(corr_next_tok) in PRONOUNS
                    and self.__has_qmark_within(
                        edit_collection.cor_doc.text, corr_start, corr_end, max_steps=2
                    )  # check if there is a question mark within the next 2 tokens
                ):
                    edit.edit_type = edit.edit_type[:2] + ParentErrorType.QUESTION_TAG

            # --------- Case 2: AUX change (wrong auxiliary in question tag) -------
            if orig_text in AUXES or corr_text in AUXES:
                # Next tokens must be PRONOUN or NOT + PRONOUN on both sides
                if (
                    self.__next_shape_is_pronoun_or_not_pronoun(
                        edit_collection.orig_doc.text, orig_start, orig_end
                    )
                    and self.__next_shape_is_pronoun_or_not_pronoun(
                        edit_collection.cor_doc.text, corr_start, corr_end
                    )
                    and self.__has_qmark_within(
                        edit_collection.cor_doc.text, corr_start, corr_end, max_steps=3
                    )
                ):

                    edit.edit_type = edit.edit_type[:2] + ParentErrorType.QUESTION_TAG

            # ------------- Case 3: PRONOUN change in question tag -----------------
            if parent_error == ParentErrorType.PRONOUN:
                if self.__prev_shape_is_aux_or_not_aux(
                    edit_collection.orig_doc.text, orig_start
                ) and self.__prev_shape_is_aux_or_not_aux(
                    edit_collection.cor_doc.text, corr_start
                ):
                    nxt = self.__safe_next(
                        corr_start, corr_end, edit_collection.cor_doc.text, order=1
                    )
                    if nxt:
                        _, _, tok = nxt
                        if "?" in tok:
                            edit.edit_type = (
                                edit.edit_type[:2] + ParentErrorType.QUESTION_TAG
                            )

    def _postprocess_space_tag(self, edit_collection: EditCollection):
        """
        Postprocess the edit collection for space tag.
        Update OTHER -> SPACE if the edit is not just space change.

        Args:
            edit_collection (EditCollection): An EditCollection object

        Returns:
            None
        """

        for edit in edit_collection.edits:
            if edit.edit_type[2:] == ParentErrorType.OTHER:
                if edit.original.text.strip() == edit.corrected.text.strip():
                    edit.edit_type = edit.edit_type[:2] + "SPACE"
