from __future__ import annotations

import re

import spacy.symbols as POS
from rapidfuzz.distance import Levenshtein
from spacy.tokens import Token
from spacy.tokens.span import Span

from vnerrant.components.classifier import BaseClassifer
from vnerrant.components.en.constants import (
    ChildrenErrorType,
    ChildrenFluencyType,
    ParentDisfluencyType,
    ParentErrorType,
    dependency_resources,
    language_resources,
    pos_resources,
)
from vnerrant.constants import Operator, SeparatorTypes, StyleGuide
from vnerrant.model.edit import Edit


class Classifier(BaseClassifer):
    """
    Classifier class for English
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def only_orth_change(o_toks: list[Token], c_toks: list[Token]) -> bool:
        """
        Check if the difference between two lists of tokens is only whitespace or case.
        :param o_toks: A list of spacy tokens.
        :param c_toks: A list of spacy tokens.
        :return: Boolean.
        """
        o_join = "".join([o.lower_ for o in o_toks])
        c_join = "".join([c.lower_ for c in c_toks])
        if o_join == c_join:
            return True
        return False

    @staticmethod
    def exact_reordering(o_toks: list[Token], c_toks: list[Token]) -> bool:
        """
        Check if the difference between two lists of tokens is only reordering.
        :param o_toks: A list of spacy tokens.
        :param c_toks: A list of spacy tokens.
        :return: Boolean.
        """
        # Sorting lets us keep duplicates.
        o_set = sorted([o.lower_ for o in o_toks])
        c_set = sorted([c.lower_ for c in c_toks])
        if o_set == c_set:
            return True
        return False

    @staticmethod
    def preceded_by_aux(o_toks: list[Token], c_toks: list[Token]) -> bool:
        """
        Check if two tokens are preceded by an auxiliary verb.
        :param o_toks: A list of spacy tokens.
        :param c_toks: A list of spacy tokens.
        :return: Boolean.
        """
        # If the toks are aux, we need to check if they are the first aux.
        if o_toks[0].dep_.startswith("aux") and c_toks[0].dep_.startswith("aux"):
            # Find the parent verb
            o_head = o_toks[0].head
            c_head = c_toks[0].head
            # Find the children of the parent
            o_children = o_head.children
            c_children = c_head.children
            # Check the orig children.
            for o_child in o_children:
                # Look at the first aux...
                if o_child.dep_.startswith("aux"):
                    # Check if the string matches o_tok
                    if o_child.text != o_toks[0].text:
                        # If it doesn't, o_tok is not first so check cor
                        for c_child in c_children:
                            # Find the first aux in cor...
                            if c_child.dep_.startswith("aux"):
                                # If that doesn't match either, neither are first aux
                                if c_child.text != c_toks[0].text:
                                    return True
                                # Break after the first cor aux
                                break
                    # Break after the first orig aux.
                    break
        # Otherwise, the toks are main verbs so we need to look for any aux.
        else:
            o_deps = [o_dep.dep_ for o_dep in o_toks[0].children]
            c_deps = [c_dep.dep_ for c_dep in c_toks[0].children]
            if "aux" in o_deps or "auxpass" in o_deps:
                if "aux" in c_deps or "auxpass" in c_deps:
                    return True
        return False

    @staticmethod
    def get_pos_and_dep(toks: list[Token]) -> tuple[list[str], list[str]]:
        """
        Extract POS and dependency parse info from a list of spacy tokens.
        :param toks: A list of spacy tokens.
        :return: A tuple of lists of POS and dependency parse tags.
        """
        pos = []
        dep = []
        for tok in toks:
            pos.append(pos_resources.pos_map[tok.tag_])
            dep.append(tok.dep_)
        return pos, dep

    @staticmethod
    def infer_head_pos(toks: list[Token], *, mode: str = "first") -> str:

        assert mode in {
            "first",
            "last",
            "head",
        }, "mode must be 'first', 'last' or 'head'"

        if mode == "first":
            return pos_resources.pos_map[toks[0].tag_]
        elif mode == "last":
            return pos_resources.pos_map[toks[-1].tag_]
        else:
            span = Span(toks[0].doc, toks[0].i, toks[-1].i + 1)
            return pos_resources.pos_map[span.root.tag_]

    @staticmethod
    def remove_punctuation(text: str) -> str:
        """
        Remove punctuation from a string.
        :param text: A string.
        :return: A string without punctuation.
        """
        return "".join([c for c in text if c.isalnum() or c.isspace()]).strip()

    @staticmethod
    def filler_word(toks: list[Token]) -> bool:
        """
        Check if a list of tokens contains a filler word.
        :param toks: A list of spacy tokens.
        :return: Boolean.
        """
        for tok in toks:
            if tok.lower_ in language_resources.filler_words:
                return True
            if tok.lemma_.lower() in {"feel", "look", "seem", "sound", "like"}:
                if tok.pos_ == "INTJ": # Interjection
                    return True
        return False

    @staticmethod
    def get_pharse_repetition(
        toks: list[Token], remo_punct: bool = True, case_insensitive: bool = True
    ) -> str | None:

        list_toks = list(toks)
        if remo_punct:
            list_toks = [t for t in list_toks if not t.is_punct and not t.is_space]

        if not list_toks:
            return None

        words = [t.text.lower() if case_insensitive else t.text for t in list_toks]
        n = len(words)

        for p in range(1, n):
            phrase = words[:p]
            k, r = divmod(n, p)
            if words[: k * p] != phrase * k:
                continue
            if r and words[-r:] != phrase[:r]:
                continue
            return " ".join(phrase)
        return None

    def is_filler_word(self, o_toks: list[Token]) -> bool:
        """
        Check if a list of tokens contains a filler word.
        :param o_toks: A list of spacy tokens.
        :return: Boolean.
        """
        return self.filler_word(o_toks)

    def is_only_orth_change(self, o_toks: list[Token], c_toks: list[Token]) -> bool:
        """
        Check if the difference between two lists of tokens is only whitespace or case.
        :param o_toks: A list of spacy tokens.
        :param c_toks: A list of spacy tokens.
        :return: Boolean.
        """
        return self.only_orth_change(o_toks, c_toks)

    def is_repetition(
        self, o_toks: list[Token], ignore_punctuation: bool = True
    ) -> bool:
        """
        Check if the difference between two lists of tokens is a repetition.
        :param o_toks: A list of spacy tokens.
        :param c_toks: A list of spacy tokens.
        :return: Boolean.
        Example:
            "I am am going to the store" -> "I am going to the store" > token level "am"
            "I mean mean mean to go to the store" -> "I mean to go to the store" > token level "mean mean"
            "I mean I mean to go to the store" -> "I mean to go to the store" > pharse level "I mean"
            "I is is is going to the store" -> "I am going to the store" > token level "is"
            "I mean I mean I mean to go to the store" -> "I mean to go to the store" > pharse level "I mean I mean"
        """

        def remove_punctuation(text: str) -> str:
            """
            Remove punctuation from a string.
            :param text: A string.
            :return: A string without punctuation.
            """
            return (
                "".join([c for c in text if c.isalnum() or c.isspace()]).strip().lower()
            )

        if self.get_pharse_repetition(o_toks):
            return True

        cur_text = " ".join([t.text for t in o_toks if t.text != " "])
        cur_start_token = o_toks[0].i
        cur_end_token = o_toks[-1].i + 1
        ref_cur_end_token = o_toks[-1].i + 1
        # Loop Minus ref_cur_end_token if the last token is a punctuation mark
        while (
            ref_cur_end_token > 0
            and ref_cur_end_token >= cur_start_token
            and o_toks[0].doc[ref_cur_end_token - 1].is_punct
        ):
            ref_cur_end_token -= 1

        prev_end_token = cur_start_token
        prev_start_token = cur_start_token - (ref_cur_end_token - cur_start_token)

        if prev_start_token <= 0 or prev_end_token <= 0:
            prev_text = ""  # No previous tokens
        else:
            prev_toks = o_toks[0].doc[prev_start_token:prev_end_token]
            prev_text = " ".join([t.text for t in prev_toks if t.text != " "])

        next_start_token = cur_end_token
        next_end_token = cur_end_token + (ref_cur_end_token - cur_start_token)
        if next_start_token >= len(o_toks[0].doc) or next_end_token >= len(
            o_toks[0].doc
        ):
            next_text = ""  # No next tokens
        else:
            next_toks = o_toks[0].doc[next_start_token:next_end_token]
            next_text = " ".join([t.text for t in next_toks if t.text != " "])
        if ignore_punctuation:
            cur_text = remove_punctuation(cur_text)
            prev_text = remove_punctuation(prev_text)
            next_text = remove_punctuation(next_text)
        if not cur_text:
            return False
        if (
            cur_text.lower() == prev_text.lower()
            or cur_text.lower() == next_text.lower()
        ):
            return True
        return False

    def is_exact_reordering(self, o_toks: list[Token], c_toks: list[Token]) -> bool:
        """
        Check if the difference between two lists of tokens is only reordering.
        :param o_toks: A list of spacy tokens.
        :param c_toks: A list of spacy tokens.
        :return: Boolean.
        """
        return self.exact_reordering(o_toks, c_toks)

    def is_preceded_by_aux(self, o_toks: list[Token], c_toks: list[Token]) -> bool:
        """
        Check if two tokens are preceded by an auxiliary verb.
        :param o_toks: A list of spacy tokens.
        :param c_toks: A list of spacy tokens.
        :return: Boolean.
        """
        return self.preceded_by_aux(o_toks, c_toks)

    def is_false_start(self, o_toks: list[Token]) -> bool:
        if o_toks[-1].i + 1 >= len(o_toks[0].doc):
            return False
        restart_token = o_toks[0].doc[o_toks[-1].i + 1]

        pos_list, dep_list = self.get_pos_and_dep([o_toks[0]])
        _, restart_dep_list = self.get_pos_and_dep([restart_token])
        if dep_list[0] == restart_dep_list[0] and pos_list[0] in {
            "PRON",
            "DET",
            "PREP",
        }:
            return True
        return False

    def _get_error_type_by_pos(
        self, pos: str, *, fst_toks: list[Token] = [], snd_toks: list[Token] = []
    ) -> str:
        if pos == "NOUN":
            return ParentErrorType.NOUN
        elif pos == "VERB":
            if not fst_toks and not snd_toks:
                return ParentErrorType.VERB
            if not snd_toks:  # one-sided edit with more than one token
                if len(fst_toks) >= 2:
                    # Check if the verb is preceded by "to"
                    if (
                        fst_toks[0].lower_ == "to"
                        and fst_toks[0].pos == POS.PART
                        and fst_toks[0].dep_ != "prep"
                    ):
                        return (
                            ParentErrorType.VERB
                            + SeparatorTypes.COLON
                            + ChildrenErrorType.FORM
                        )
                deps = [t.dep_ for t in fst_toks]
                if set(deps).issubset({"aux", "auxpass"}):
                    return (
                        ParentErrorType.VERB
                        + SeparatorTypes.COLON
                        + ChildrenErrorType.TENSE
                    )
                return ParentErrorType.VERB
            fst_pos, fst_dep = self.get_pos_and_dep(fst_toks)
            snd_pos, snd_dep = self.get_pos_and_dep(snd_toks)

            idx_fst_verb = [i for i, p in enumerate(fst_pos) if p == pos]
            idx_snd_verb = [i for i, p in enumerate(snd_pos) if p == pos]

            fst_lemma, fst_pos, fst_number, fst_tense = (
                fst_toks[idx_fst_verb[0]].lemma_,
                fst_toks[idx_fst_verb[0]].pos_,
                fst_toks[idx_fst_verb[0]].morph.get("Number"),
                fst_toks[idx_fst_verb[0]].morph.get("Tense"),
            )
            snd_lemma, snd_pos, snd_number, snd_tense = (
                snd_toks[idx_snd_verb[0]].lemma_,
                snd_toks[idx_snd_verb[0]].pos_,
                snd_toks[idx_snd_verb[0]].morph.get("Number"),
                snd_toks[idx_snd_verb[0]].morph.get("Tense"),
            )
            if (
                fst_lemma == snd_lemma
                and fst_tense == snd_tense
                and fst_number != snd_number
            ):
                return (
                    ParentErrorType.VERB
                    + SeparatorTypes.COLON
                    + ChildrenErrorType.SUBJECT_VERB_AGREEMENT
                )
            if fst_lemma == snd_lemma and fst_tense != snd_tense:
                return (
                    ParentErrorType.VERB
                    + SeparatorTypes.COLON
                    + ChildrenErrorType.TENSE
                )
            if (
                fst_lemma != snd_lemma
                or fst_pos[0] in {"VERB", "AUX"}
                or snd_pos[0] in {"VERB", "AUX"}
            ):
                return ParentErrorType.VERB
            if (
                fst_toks[idx_fst_verb[0]].lower_ in dependency_resources.aux_conts
                or snd_toks[idx_snd_verb[0]].lower_ in dependency_resources.aux_conts
            ):
                return (
                    ParentErrorType.VERB
                    + SeparatorTypes.COLON
                    + ChildrenErrorType.TENSE
                )
            if set(fst_dep).issubset({"aux", "auxpass"}) and set(snd_dep).issubset(
                {"aux", "auxpass"}
            ):
                return (
                    ParentErrorType.VERB
                    + SeparatorTypes.COLON
                    + ChildrenErrorType.TENSE
                )
            if set(fst_pos + snd_pos) == {"PART", "VERB"}:
                if fst_toks[idx_fst_verb[0]].lemma == snd_toks[idx_snd_verb[0]].lemma:
                    return (
                        ParentErrorType.VERB
                        + SeparatorTypes.COLON
                        + ChildrenErrorType.FORM
                    )
                return ParentErrorType.VERB

            return ParentErrorType.VERB

        elif pos == "ADJ":
            return ParentErrorType.ADJECTIVE
        elif pos == "ADV":
            return ParentErrorType.ADVERB
        elif pos == "PREP":
            return ParentErrorType.PREPOSITION
        elif pos == "PART":
            return ParentErrorType.PARTICLE
        elif pos == "DET":
            return ParentErrorType.DETERMINER
        elif pos == "PRON":
            return ParentErrorType.PRONOUN
        elif pos == "CONJ":
            return ParentErrorType.CONJUNCTION
        else:
            return ParentErrorType.OTHER

    def _get_one_sided_type(self, toks: list[Token], *, mode: str = "head") -> str:
        """
        Classify an edit with only one side of tokens.
        :param toks: A list of spacy tokens.
        :param doc: A spacy Doc object.
        :return: An error type string.
        """
        # Preprocessing [disfulency layer] before classification
        # Check if the tokens are a filler word
        if self.is_filler_word(toks):
            return (
                ParentDisfluencyType.DISFLUENCY
                + SeparatorTypes.COLON
                + ChildrenFluencyType.FILLER_PAUSE
            )

        if self.is_repetition(toks):
            return (
                ParentDisfluencyType.DISFLUENCY
                + SeparatorTypes.COLON
                + ChildrenFluencyType.REPETITION
            )
        if self.is_false_start(toks):
            return (
                ParentDisfluencyType.DISFLUENCY
                + SeparatorTypes.COLON
                + ChildrenFluencyType.FALSE_START
            )

        # Special cases
        if len(toks) == 1:
            # Possessive noun suffixes; e.g. ' -> 's
            if toks[0].tag_ == "POS":
                return (
                    ParentErrorType.NOUN
                    + SeparatorTypes.COLON
                    + ChildrenErrorType.POSSESSIVE
                )
            # Contractions. Rule must come after possessive
            if toks[0].lower_ in dependency_resources.conts:
                return ParentErrorType.CONTRACTION
            # Infinitival "to" is treated as part of a verb form
            if (
                toks[0].lower_ == "to"
                and toks[0].pos == POS.PART
                and toks[0].dep_ != "prep"
            ):
                return (
                    ParentErrorType.VERB + SeparatorTypes.COLON + ChildrenErrorType.FORM
                )
            # Punctuation
            if toks[0].is_punct:
                return ParentErrorType.PUNCTUATION
        # Extract pos tags and parse info from the toks
        pos_list, dep_list = self.get_pos_and_dep(toks)
        # Auxiliary verbs
        if set(dep_list).issubset({"aux", "auxpass"}):
            return ParentErrorType.VERB + SeparatorTypes.COLON + ChildrenErrorType.TENSE
        # POS-based tags. Ignores rare, uninformative categories
        if len(set(pos_list)) == 1 and pos_list[0] not in pos_resources.rare_pos:
            return pos_list[0]  # TODO: check if this is correct
        # More POS-based tags using special dependency labels
        if (
            len(set(dep_list)) == 1
            and dep_list[0] in dependency_resources.dep_map.keys()
        ):
            return dependency_resources.dep_map[dep_list[0]]
        # To-infinitives and phrasal verbs
        if set(pos_list) == {"PART", "VERB"}:
            return ParentErrorType.VERB
        # Tricky cases
        # if len(toks) >= 2:
        #     predominant_pos = self.infer_head_pos(toks, mode=mode)
        #     if predominant_pos == "PUNCT":
        #         # Reupdate the predominant pos if it's punctuation
        #         predominant_pos = self.infer_head_pos(toks, mode="head")
        #     return self._get_error_type_by_pos(predominant_pos, fst_toks=toks)
        if len(toks) == 2 and "PUNCT" in pos_list:
            # If one of the tokens is punctuation, classify based on the dep of other token
            idx_non_punct = pos_list.index(
                next(p for p in pos_list if p != "PUNCT")
            )
            if dep_list[idx_non_punct] in {"nsubj", "nsubjpass", "dobj", "pobj"}:
                return ParentErrorType.PRONOUN
            elif pos_list[idx_non_punct] == "VERB":
                return ParentErrorType.VERB
            else:
                return ParentErrorType.WORD_CHOICE
        else:
            return ParentErrorType.PHRASE_CHOICE

    def _get_two_sided_type(self, o_toks: list[Token], c_toks: list[Token]) -> str:
        """
        Classify an edit with two sides of tokens.
        :param o_toks: A list of spacy tokens.
        :param c_toks: A list of spacy tokens.
        :return: An error type string.
        """
        # Extract pos tags and parse info from the toks as lists
        o_pos, o_dep = self.get_pos_and_dep(o_toks)
        c_pos, c_dep = self.get_pos_and_dep(c_toks)

        # Preprocessing [disfluency layer] before classification
        # Repetition error
        if self.is_repetition(o_toks):
            return (
                ParentDisfluencyType.DISFLUENCY
                + SeparatorTypes.COLON
                + ChildrenFluencyType.REPETITION
            )

        if self.is_false_start(o_toks):
            return (
                ParentDisfluencyType.DISFLUENCY
                + SeparatorTypes.COLON
                + ChildrenFluencyType.FALSE_START
            )

        # Orthography; i.e. whitespace and/or case errors.
        if self.is_only_orth_change(o_toks, c_toks):
            return ParentErrorType.ORTHOGRAPHY
        # Word Order; only matches exact reordering.
        if self.is_exact_reordering(o_toks, c_toks):
            return ParentErrorType.WORD_ORDER

        # 1:1 replacements (very common)
        if len(o_toks) == len(c_toks) == 1:
            # 1. SPECIAL CASES
            # Possessive noun suffixes; e.g. ' -> 's
            if o_toks[0].tag_ == "POS" or c_toks[0].tag_ == "POS":
                return (
                    ParentErrorType.NOUN
                    + SeparatorTypes.COLON
                    + ChildrenErrorType.POSSESSIVE
                )
            # if (
            #     o_toks[0].lower_ in dependency_resources.conts and c_toks[0].lower_ in dependency_resources.conts
            # ) and o_pos == c_pos:
            #     # Both sides are contractions; e.g. "he's" -> "they 're"
            #     return ParentErrorType.VERB + SeparatorTypes.COLON + ChildrenErrorType.SUBJECT_VERB_AGREEMENT

            # # One side is a contraction; e.g. "he's" -> "they are"
            # if o_toks[0].lower_ in dependency_resources.conts:
            #     if c_toks[0].lower_ in dependency_resources.mapping_conts and dependency_resources.mapping_conts[c_toks[0].lower_] != o_toks[0].lower_:
            #         return ParentErrorType.VERB + SeparatorTypes.COLON + ChildrenErrorType.SUBJECT_VERB_AGREEMENT
            # if c_toks[0].lower_ in dependency_resources.conts:
            #     if o_toks[0].lower_ in dependency_resources.mapping_conts and dependency_resources.mapping_conts[o_toks[0].lower_] != c_toks[0].lower_:
            #         return ParentErrorType.VERB + SeparatorTypes.COLON + ChildrenErrorType.SUBJECT_VERB_AGREEMENT
            # Contraction. Rule must come after possessive.
            if (
                o_toks[0].lower_ in dependency_resources.conts
                or c_toks[0].lower_ in dependency_resources.conts
            ) and o_pos == c_pos:
                o_lemma, o_pos_, o_number, o_tense = (
                    o_toks[0].lemma_,
                    o_toks[0].pos_,
                    o_toks[0].morph.get("Number"),
                    o_toks[0].morph.get("Tense"),
                )
                c_lemma, c_pos_, c_number, c_tense = (
                    c_toks[0].lemma_,
                    c_toks[0].pos_,
                    c_toks[0].morph.get("Number"),
                    c_toks[0].morph.get("Tense"),
                )
                if o_lemma == c_lemma and o_tense == c_tense and o_number != c_number:
                    return (
                        ParentErrorType.VERB
                        + SeparatorTypes.COLON
                        + ChildrenErrorType.SUBJECT_VERB_AGREEMENT
                    )
                elif o_lemma == c_lemma and o_tense != c_tense:
                    return (
                        ParentErrorType.VERB
                        + SeparatorTypes.COLON
                        + ChildrenErrorType.TENSE
                    )
                elif (
                    o_lemma != c_lemma
                    or o_pos_[0] in {"VERB", "AUX"}
                    or c_pos_[0] in {"VERB", "AUX"}
                ):
                    return ParentErrorType.VERB

                return ParentErrorType.CONTRACTION
            # Special auxiliaries in contractions (1); e.g. ca -> can, wo -> will
            # Rule was broken in V1. Turned off this fix for compatibility.
            if (
                o_toks[0].lower_ in dependency_resources.aux_conts
                and c_toks[0].lower_ == dependency_resources.aux_conts[o_toks[0].lower_]
            ) or (
                c_toks[0].lower_ in dependency_resources.aux_conts
                and o_toks[0].lower_ == dependency_resources.aux_conts[c_toks[0].lower_]
            ):
                return ParentErrorType.CONTRACTION
            # Special auxiliaries in contractions (2); e.g. ca -> could, wo -> should
            if (
                o_toks[0].lower_ in dependency_resources.aux_conts
                or c_toks[0].lower_ in dependency_resources.aux_conts
            ):
                return (
                    ParentErrorType.VERB
                    + SeparatorTypes.COLON
                    + ChildrenErrorType.TENSE
                )
            # Special: "was" and "were" are the only past tense SVA
            if {o_toks[0].lower_, c_toks[0].lower_} == {"was", "were"}:
                return (
                    ParentErrorType.VERB
                    + SeparatorTypes.COLON
                    + ChildrenErrorType.SUBJECT_VERB_AGREEMENT
                )

            # 2. SPELLING AND INFLECTION
            # Only check alphabetical strings on the original side
            # Spelling errors take precedence over POS errors; this rule is ordered
            if o_toks[0].text.isalpha():
                # Check a GB English dict for both orig and lower case.
                # E.g. "cat" is in the dict, but "Cat" is not.
                if (
                    o_toks[0].text not in language_resources.spell
                    and o_toks[0].lower_ not in language_resources.spell
                ):
                    # Check if both sides have a common lemma
                    if o_toks[0].lemma == c_toks[0].lemma:
                        # Inflection; often count vs mass nouns or e.g. got vs getted
                        if o_pos == c_pos and o_pos[0] in {"NOUN", "VERB"}:
                            return (
                                o_pos[0]
                                + SeparatorTypes.COLON
                                + ChildrenErrorType.INFLECTION
                            )
                        # Unknown morphology; i.e. we cannot be more specific.
                        else:
                            return ParentErrorType.MORPHOLOGY
                    # Use string similarity to detect true spelling errors.
                    else:
                        # Normalised Lev distance works better than Lev ratio
                        str_sim = Levenshtein.normalized_similarity(
                            o_toks[0].lower_,
                            c_toks[0].lower_,
                        )
                        # WARNING: THIS IS AN APPROXIMATION.
                        # Thresholds tuned manually on FCE_train + W&I_train
                        # str_sim > 0.55 is almost always a true spelling error
                        if str_sim > 0.55:
                            return ParentErrorType.SPELLING
                        # Special scores for shorter sequences are usually SPELL
                        if str_sim == 0.5 or round(str_sim, 3) == 0.333:
                            # Short strings are more likely to be spell: eles -> else
                            if len(o_toks[0].text) <= 4 and len(c_toks[0].text) <= 4:
                                return ParentErrorType.SPELLING
                        # The remainder are usually word choice: amounght -> number
                        # Classifying based on cor_pos alone is generally enough.
                        if c_pos[0] not in pos_resources.rare_pos:
                            return c_pos[0]
                        # Anything that remains is OTHER
                        else:
                            return ParentErrorType.OTHER

            # 3. MORPHOLOGY
            # Only ADJ, ADV, NOUN and VERB can have inflectional changes.
            if (
                o_toks[0].lemma == c_toks[0].lemma
                and o_pos[0] in pos_resources.open_pos2
                and c_pos[0] in pos_resources.open_pos2
            ):
                # Same POS on both sides
                if o_pos == c_pos:
                    # Adjective form; e.g. comparatives
                    if o_pos[0] == "ADJ":
                        return (
                            ParentErrorType.ADJECTIVE
                            + SeparatorTypes.COLON
                            + ChildrenErrorType.FORM
                        )
                    # Noun number
                    if o_pos[0] == "NOUN":
                        return (
                            ParentErrorType.NOUN
                            + SeparatorTypes.COLON
                            + ChildrenErrorType.NUMBER
                        )
                    # Verbs - various types
                    if o_pos[0] == "VERB":
                        # NOTE: These rules are carefully ordered.
                        # Use the dep parse to find some form errors.
                        # Main verbs preceded by aux cannot be tense or SVA.
                        if self.is_preceded_by_aux(o_toks, c_toks):
                            return (
                                ParentErrorType.VERB
                                + SeparatorTypes.COLON
                                + ChildrenErrorType.FORM
                            )
                        # Use fine PTB tags to find various errors.
                        # FORM errors normally involve VBG or VBN.
                        if o_toks[0].tag_ in {"VBG", "VBN"} or c_toks[0].tag_ in {
                            "VBG",
                            "VBN",
                        }:
                            return (
                                ParentErrorType.VERB
                                + SeparatorTypes.COLON
                                + ChildrenErrorType.FORM
                            )
                        # Of what's left, TENSE errors normally involved VBD.
                        if o_toks[0].tag_ == "VBD" or c_toks[0].tag_ == "VBD":
                            return (
                                ParentErrorType.VERB
                                + SeparatorTypes.COLON
                                + ChildrenErrorType.TENSE
                            )
                        # Of what's left, SVA errors normally involve VBZ.
                        if o_toks[0].tag_ == "VBZ" or c_toks[0].tag_ == "VBZ":
                            return (
                                ParentErrorType.VERB
                                + SeparatorTypes.COLON
                                + ChildrenErrorType.SUBJECT_VERB_AGREEMENT
                            )
                        # Any remaining aux verbs are called TENSE.
                        if o_dep[0].startswith("aux") and c_dep[0].startswith("aux"):
                            return (
                                ParentErrorType.VERB
                                + SeparatorTypes.COLON
                                + ChildrenErrorType.TENSE
                            )
                # Use dep labels to find some more ADJ:FORM
                if set(o_dep + c_dep).issubset({"acomp", "amod"}):
                    return (
                        ParentErrorType.ADJECTIVE
                        + SeparatorTypes.COLON
                        + ChildrenErrorType.FORM
                    )
                # Adj to plural noun is usually noun number; e.g. musical -> musicals.
                if o_pos[0] == "ADJ" and c_toks[0].tag_ == "NNS":
                    return (
                        ParentErrorType.NOUN
                        + SeparatorTypes.COLON
                        + ChildrenErrorType.NUMBER
                    )
                # For remaining verb errors (rare), rely on c_pos
                if c_toks[0].tag_ in {"VBG", "VBN"}:
                    return (
                        ParentErrorType.VERB
                        + SeparatorTypes.COLON
                        + ChildrenErrorType.FORM
                    )
                if c_toks[0].tag_ == "VBD":
                    return (
                        ParentErrorType.VERB
                        + SeparatorTypes.COLON
                        + ChildrenErrorType.TENSE
                    )
                if c_toks[0].tag_ == "VBZ":
                    return (
                        ParentErrorType.VERB
                        + SeparatorTypes.COLON
                        + ChildrenErrorType.SUBJECT_VERB_AGREEMENT
                    )
                # Tricky cases that all have the same lemma.
                else:
                    return ParentErrorType.MORPHOLOGY
            # Derivational morphology.
            if (
                language_resources.stemmer.stem(o_toks[0].text)
                == language_resources.stemmer.stem(c_toks[0].text)
                and o_pos[0] in pos_resources.open_pos2
                and c_pos[0] in pos_resources.open_pos2
            ):
                return ParentErrorType.MORPHOLOGY

            # 4. GENERAL
            # Auxiliaries with different lemmas
            if o_dep[0].startswith("aux") and c_dep[0].startswith("aux"):
                return (
                    ParentErrorType.VERB
                    + SeparatorTypes.COLON
                    + ChildrenErrorType.TENSE
                )
            # POS-based tags. Some of these are context sensitive mispellings.
            if o_pos == c_pos and o_pos[0] not in pos_resources.rare_pos:
                return o_pos[0]
            # Some dep labels map to POS-based tags.
            if o_dep == c_dep and o_dep[0] in dependency_resources.dep_map.keys():
                return dependency_resources.dep_map[o_dep[0]]
            # Phrasal verb particles.
            if set(o_pos + c_pos) == {"PART", "PREP"} or set(o_dep + c_dep) == {
                "prt",
                "prep",
            }:
                return ParentErrorType.PARTICLE
            # Can use dep labels to resolve DET + PRON combinations.
            if set(o_pos + c_pos) == {"DET", "PRON"} or set(
                (o_toks[0].pos_, c_toks[0].pos_)
            ).issubset({"DET", "PRON", "PROPN"}):
                # DET cannot be a subject or object.
                if c_dep[0] in {"nsubj", "nsubjpass", "dobj", "pobj"}:
                    return ParentErrorType.PRONOUN
                # "poss" indicates possessive determiner
                if c_dep[0] == "poss":
                    return ParentErrorType.DETERMINER
            # Can use dep labels to resolve DET + PREP combinations.
            if set(o_pos + c_pos) == {"DET", "PREP"}:
                if c_dep[0] == "det":
                    return ParentErrorType.DETERMINER
            # NUM and DET are usually DET; e.g. a <-> one
            if set(o_pos + c_pos) == {"NUM", "DET"}:
                return ParentErrorType.DETERMINER
            # Special: other <-> another
            if {o_toks[0].lower_, c_toks[0].lower_} == {"other", "another"}:
                return ParentErrorType.DETERMINER
            # Special: your (sincerely) -> yours (sincerely)
            if o_toks[0].lower_ == "your" and c_toks[0].lower_ == "yours":
                return ParentErrorType.PRONOUN
            if {o_toks[0].pos_, c_toks[0].pos_} == {"PRON", "SCONJ"}:
                return ParentErrorType.PRONOUN
            # Special: no <-> not; this is very context sensitive
            if {o_toks[0].lower_, c_toks[0].lower_} == {"no", "not"}:
                return ParentErrorType.OTHER

            # 5. STRING SIMILARITY
            # These rules are quite language specific.
            if o_toks[0].text.isalpha() and c_toks[0].text.isalpha():
                # Normalised Lev distance works better than Lev ratio
                str_sim = Levenshtein.normalized_similarity(
                    o_toks[0].lower_,
                    c_toks[0].lower_,
                )
                # WARNING: THIS IS AN APPROXIMATION.
                # Thresholds tuned manually on FCE_train + W&I_train
                # A. Short sequences are likely to be SPELL or function word errors
                if len(o_toks[0].text) == 1:
                    # i -> in, a -> at
                    if len(c_toks[0].text) == 2 and str_sim == 0.5:
                        return ParentErrorType.SPELLING
                if len(o_toks[0].text) == 2:
                    # in -> is, he -> the, to -> too
                    if 2 <= len(c_toks[0].text) <= 3 and str_sim >= 0.5:
                        return ParentErrorType.SPELLING
                if len(o_toks[0].text) == 3:
                    # Special: the -> that (relative pronoun)
                    if o_toks[0].lower_ == "the" and c_toks[0].lower_ == "that":
                        return ParentErrorType.PRONOUN
                    # Special: all -> everything
                    if o_toks[0].lower_ == "all" and c_toks[0].lower_ == "everything":
                        return ParentErrorType.PRONOUN
                    # off -> of, too -> to, out -> our, now -> know
                    if 2 <= len(c_toks[0].text) <= 4 and str_sim >= 0.5:
                        return ParentErrorType.SPELLING
                # B. Longer sequences are also likely to include content word errors
                if len(o_toks[0].text) == 4:
                    # Special: that <-> what
                    if {o_toks[0].lower_, c_toks[0].lower_} == {"that", "what"}:
                        return ParentErrorType.PRONOUN
                    # Special: well <-> good
                    if {o_toks[0].lower_, c_toks[0].lower_} == {
                        "good",
                        "well",
                    } and c_pos[0] not in pos_resources.rare_pos:
                        return c_pos[0]
                    # knew -> new,
                    if len(c_toks[0].text) == 3 and str_sim > 0.5:
                        return ParentErrorType.SPELLING
                    # then <-> than, form -> from
                    if len(c_toks[0].text) == 4 and str_sim >= 0.5:
                        return ParentErrorType.SPELLING
                    # gong -> going, hole -> whole
                    if len(c_toks[0].text) == 5 and str_sim == 0.8:
                        return ParentErrorType.SPELLING
                    # high -> height, west -> western
                    if (
                        len(c_toks[0].text) > 5
                        and str_sim > 0.5
                        and c_pos[0] not in pos_resources.rare_pos
                    ):
                        return c_pos[0]
                if len(o_toks[0].text) == 5:
                    # Special: after -> later
                    if {o_toks[0].lower_, c_toks[0].lower_} == {
                        "after",
                        "later",
                    } and c_pos[0] not in pos_resources.rare_pos:
                        return c_pos[0]
                    # where -> were, found -> fund
                    if len(c_toks[0].text) == 4 and str_sim == 0.8:
                        return ParentErrorType.SPELLING
                    # thing <-> think, quite -> quiet, their <-> there
                    if len(c_toks[0].text) == 5 and str_sim >= 0.6:
                        return ParentErrorType.SPELLING
                    # house -> domestic, human -> people
                    if (
                        len(c_toks[0].text) > 5
                        and c_pos[0] not in pos_resources.rare_pos
                    ):
                        return c_pos[0]
                # C. Longest sequences include MORPH errors
                if len(o_toks[0].text) > 5 and len(c_toks[0].text) > 5:
                    # Special: therefor -> therefore
                    if (
                        o_toks[0].lower_ == "therefor"
                        and c_toks[0].lower_ == "therefore"
                    ):
                        return ParentErrorType.SPELLING
                    # Special: whether <-> weather
                    if {o_toks[0].lower_, c_toks[0].lower_} == {"whether", "weather"}:
                        return ParentErrorType.SPELLING
                    # Special: though <-> thought
                    if {o_toks[0].lower_, c_toks[0].lower_} == {"though", "thought"}:
                        return ParentErrorType.SPELLING
                    # Morphology errors: stress -> stressed, health -> healthy
                    if (
                        o_toks[0].text.startswith(c_toks[0].text)
                        or c_toks[0].text.startswith(o_toks[0].text)
                    ) and str_sim >= 0.66:
                        return ParentErrorType.MORPHOLOGY
                    # Spelling errors: exiting -> exciting, wether -> whether
                    if str_sim > 0.8:
                        return ParentErrorType.SPELLING
                    # Content word errors: learning -> studying, transport -> travel
                    if str_sim < 0.55 and c_pos[0] not in pos_resources.rare_pos:
                        return c_pos[0]
                    # NOTE: Errors between 0.55 and 0.8 are a mix of SPELL, MORPH and POS
                if len(o_toks[0].text) == 6:
                    # The conjunction have 6 letters. {"unless", "though", "before", "either"}
                    # The similarity is not very high
                    if str_sim > 0.6:
                        return ParentErrorType.SPELLING  # 6 and 4 > 0.6
            # Tricky cases
            # 6. Conjuntion error
            if set(o_pos + c_pos) == {"CONJ", "PUNCT"}:
                return ParentErrorType.CONJUNCTION

            # 7. Check redundant space or punctuation errors
            if o_toks[0].text.strip() == c_toks[0].text.strip():
                return "SPACE"
            # Remove punctuation and check again
            if self.remove_punctuation(o_toks[0].text) == self.remove_punctuation(
                c_toks[0].text
            ):
                return ParentErrorType.PUNCTUATION
            # 8. Default to word choice for remaining 1:1 edits
            return ParentErrorType.WORD_CHOICE

        # Multi-token replacements (uncommon)
        # All auxiliaries
        if set(o_dep + c_dep).issubset({"aux", "auxpass"}):
            return ParentErrorType.VERB + SeparatorTypes.COLON + ChildrenErrorType.TENSE
        # All same POS
        if len(set(o_pos + c_pos)) == 1:
            # Final verbs with the same lemma are tense; e.g. eat -> has eaten
            if o_pos[0] == "VERB" and o_toks[-1].lemma == c_toks[-1].lemma:
                return (
                    ParentErrorType.VERB
                    + SeparatorTypes.COLON
                    + ChildrenErrorType.TENSE
                )
            # POS-based tags.
            elif o_pos[0] not in pos_resources.rare_pos:
                return o_pos[0]
        # All same special dep labels.
        if (
            len(set(o_dep + c_dep)) == 1
            and o_dep[0] in dependency_resources.dep_map.keys()
        ):
            return dependency_resources.dep_map[o_dep[0]]
        # Infinitives, gerunds, phrasal verbs.
        if set(o_pos + c_pos) == {"PART", "VERB"}:
            # Final verbs with the same lemma are form; e.g. to eat -> eating
            if o_toks[-1].lemma == c_toks[-1].lemma:
                return (
                    ParentErrorType.VERB + SeparatorTypes.COLON + ChildrenErrorType.FORM
                )
            # Remaining edits are often verb; e.g. to eat -> consuming, look at -> see
            else:
                return ParentErrorType.VERB
        # Possessive nouns; e.g. friends -> friend 's
        if (o_pos == ["NOUN", "PART"] or c_pos == ["NOUN", "PART"]) and o_toks[
            0
        ].lemma == c_toks[0].lemma:
            return (
                ParentErrorType.NOUN
                + SeparatorTypes.COLON
                + ChildrenErrorType.POSSESSIVE
            )
        # Possessive nouns; e.g. ones -> one 's
        if (o_pos[0] in ["NOUN", "NUM"] and (c_pos == ["NOUN", "PART"] or c_pos == ["NUM", "PART"] or c_pos == ["PRON", "PART"])) and o_toks[
            0
        ].lemma == c_toks[0].lemma:
            return (
                ParentErrorType.NOUN
                + SeparatorTypes.COLON
                + ChildrenErrorType.POSSESSIVE
            )
        if (c_pos[0] in ["NOUN", "NUM"] and (o_pos == ["NOUN", "PART"] or o_pos == ["NUM", "PART"] or o_pos == ["PRON", "PART"])) and c_toks[
            0
        ].lemma == o_toks[0].lemma:
            return (
                ParentErrorType.NOUN
                + SeparatorTypes.COLON
                + ChildrenErrorType.POSSESSIVE
            )
        # Adjective forms with "most" and "more"; e.g. more free -> freer
        if (
            (
                o_toks[0].lower_ in {"most", "more"}
                or c_toks[0].lower_ in {"most", "more"}
            )
            and o_toks[-1].lemma == c_toks[-1].lemma
            and len(o_toks) <= 2
            and len(c_toks) <= 2
        ):
            return (
                ParentErrorType.ADJECTIVE
                + SeparatorTypes.COLON
                + ChildrenErrorType.FORM
            )
        # Prepositions; e.g. more than -> to; to -> more than
        if (o_pos[-1] == c_pos[-1] == "PREP") and (len(o_toks) != len(c_toks)):
            return ParentErrorType.PREPOSITION
        if o_pos[0] == "PRON" and c_pos[0] == "DET":
            return ParentErrorType.PRONOUN

        # Special: wild lifes <-> wildlife
        if {o_toks[0].lower_, c_toks[0].lower_}.issubset(
            {"wild", "wildlife", "life", "lives"}
        ):
            return ParentErrorType.ORTHOGRAPHY

        # Verb + preposition; e.g. look at -> see; see -> look at; see as -> look
        if (
            list(set(o_pos + c_pos)) == ["VERB", "PREP"]
            and "VERB" in o_pos
            and "VERB" in c_pos
        ):
            return ParentErrorType.VERB
        # # Process same length, same dep edits
        # if len(o_toks) == len(c_toks) == 2 and o_dep == c_dep:
        #     # The first token is root (mean verb / auxiliary) and the seccond is negative particle.
        #     if o_dep[0] == "ROOT" and o_dep[1] == "neg":
        #         return ParentErrorType.CONTRACTION
        # Tricky cases.

        # TODO: yellow issue

        # Process more Corr POS -> one Orig POS edits
        if len(c_pos) > len(o_pos) and len(o_pos) == 1:
            return ParentErrorType.PHRASE_CHOICE

        # Process more Orig POS -> one Corr POS edits
        if len(o_pos) > len(c_pos) and len(c_pos) == 1:
            # if c_pos[0] in o_pos:
            #     return self._get_error_type_by_pos(
            #         c_pos[0], fst_toks=o_toks, snd_toks=c_toks
            #     )
            # else:
            return ParentErrorType.WORD_CHOICE

        # Process more Orig POS -> more Corr POS edits
        if len(o_pos) > 1 and len(c_pos) > 1:
            return ParentErrorType.PHRASE_CHOICE

        else:
            return ParentErrorType.OTHER

    def classify(self, edit: Edit, style_guide: str = StyleGuide.WRITING) -> Edit:
        """
        Classify an edit into a specific error type with preprocessing the delimiters in edit.
        :param edit: An Edit object.
        :return: The error type of the edit.
        """
        clone_edit = edit.copy()

        if clone_edit.original.text.strip() or clone_edit.corrected.text.strip():
            clone_edit.original.strip()
            clone_edit.corrected.strip()

        clone_edit = self._classify(clone_edit, style_guide=style_guide)

        edit.edit_type = clone_edit.edit_type
        return edit

    def _classify(self, edit: Edit, style_guide: str = StyleGuide.WRITING) -> Edit:
        """
        Classify an edit into a specific error type.
        :param edit: An Edit object.
        :return: The error type of the edit.
        """
        # Nothing to nothing is a detected but not corrected edit
        if not edit.original.tokens and not edit.corrected.tokens:
            edit.edit_type = ParentErrorType.UNK
        # Missing
        elif not edit.original.tokens and edit.corrected.tokens:
            op = Operator.MISSING
            cat = self._get_one_sided_type(edit.corrected.tokens, mode="first")
            edit.edit_type = op + SeparatorTypes.COLON + cat
        # Unnecessary
        elif edit.original.tokens and not edit.corrected.tokens:
            op = Operator.UNNECESSARY
            cat = self._get_one_sided_type(edit.original.tokens, mode="head")
            edit.edit_type = op + SeparatorTypes.COLON + cat
            if edit.corrected.text != "":
                op = Operator.REPLACE
                edit.edit_type = op + SeparatorTypes.COLON + cat
        # Replacement and special cases
        else:
            # Same to same is a detected but not corrected edit
            if edit.original.text == edit.corrected.text:
                # ' hello' -> 'hello ' # TODO: Dicussion needed for this case
                # edit.edit_type = ParentErrorType.UNK
                edit.edit_type = (
                    Operator.REPLACE + SeparatorTypes.COLON + ParentErrorType.OTHER
                )
            # Special: Ignore case change at the end of multi token edits
            # E.g. [Doctor -> The doctor], [, since -> . Since]
            # Classify the edit as if the last token wasn't there
            elif edit.original.tokens[-1].lower == edit.corrected.tokens[-1].lower and (
                len(edit.original.tokens) == 2 or len(edit.corrected.tokens) == 2
            ):
                # Store a copy of the full orig and cor toks
                all_o_toks = edit.original.tokens[:]
                all_c_toks = edit.corrected.tokens[:]
                # Truncate the instance toks for classification
                edit.original.tokens = edit.original.tokens[:-1]
                edit.corrected.tokens = edit.corrected.tokens[:-1]
                # Classify the truncated edit
                edit = self._classify(edit=edit)
                # Restore the full orig and cor toks
                edit.original.tokens = all_o_toks
                edit.corrected.tokens = all_c_toks
            # Replacement
            else:
                op = Operator.REPLACE
                cat = self._get_two_sided_type(
                    edit.original.tokens, edit.corrected.tokens
                )
                # if cat == ParentErrorType.CONTRACTION and "'" in edit.original.text:
                #     edit.corrected.text = " " + edit.corrected.text
                edit.edit_type = op + SeparatorTypes.COLON + cat
        return edit
