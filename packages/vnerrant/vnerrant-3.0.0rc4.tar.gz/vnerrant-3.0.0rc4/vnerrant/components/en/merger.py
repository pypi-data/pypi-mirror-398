from __future__ import annotations

from itertools import combinations, groupby
from re import sub
from string import punctuation

import spacy.symbols as POS
from rapidfuzz.distance import Indel
from spacy.tokens import Doc

from vnerrant.components.en.constants import language_resources
from vnerrant.components.merger import BaseMerger
from vnerrant.model.edit import Edit

# Merger resources
open_pos = {POS.ADJ, POS.AUX, POS.ADV, POS.NOUN, POS.VERB}

# added more allowed bigrams
ALLOWED_POS_BIGRAMS = {
    ("DET", "NOUN"),
    ("DET", "PROPN"),
    ("ADJ", "NOUN"),
    ("NUM", "NOUN"),
    ("PART", "VERB"),     # to + V
    ("AUX", "VERB"),
    ("AUX", "AUX"),       # could have
    ("VERB", "PART"),     # give up (phrasal) - tuỳ bạn
    ("ADP", "NOUN"),
    ("ADP", "PROPN"),
    ("ADP", "PRON"),
    ("ADV", "ADJ"),
    ("ADV", "ADV"),
}



class Merger(BaseMerger):
    def __init__(self):
        super().__init__()
        pass

    @staticmethod
    def is_punct(token):
        """
        Check whether token is punctuation.
        :param token: A spacy token.
        :return: True if token is punctuation, False otherwise.
        """
        return token.pos == POS.PUNCT or token.text in punctuation

    @staticmethod
    def char_cost(a, b):
        """
        Calculate the cost of character alignment; i.e. char similarity.
        :param a: A spacy token.
        :param b: A spacy token.
        :return: The character cost.
        """
        return 1 - Indel.normalized_distance(a.text, b.text)

    def _token_of_DI(self, orig, corr, edit):
        """Return the single spaCy Token for a D/I alignment edit."""
        op, o_start, _, c_start, _ = edit
        if op == "D":
            return orig[o_start]  # span length 1
        elif op == "I":
            return corr[c_start]  # span length 1
        else:
            raise ValueError(f"Expected D or I edit, got {op}")

    def _can_merge_DI(self, prev_tok, tok) -> bool:
        """Rule: merge only if same POS (strict) and no punctuation."""
        if prev_tok is None or tok is None:
            return False
        if prev_tok.is_punct or tok.is_punct:
            return False
        if prev_tok.pos_ == tok.pos_:
            return True        
        # allow common phrase-level bigrams
        if (prev_tok.pos_, tok.pos_) in ALLOWED_POS_BIGRAMS:
            return True
        return False

    def _merge_DI_with_rules(self, orig, corr, group_edits):
        if len(group_edits) <= 1:
            return group_edits
    
        segments = []
        cur = [group_edits[0]]
        prev_tok = self._token_of_DI(orig, corr, group_edits[0])

        for e in group_edits[1:]:
            tok = self._token_of_DI(orig, corr, e)
            if self._can_merge_DI(prev_tok, tok):
                cur.append(e)
            else:
                segments.append(cur)
                cur = [e]
            prev_tok = tok

        segments.append(cur)

        out = []
        for seg in segments:
            if len(seg) > 1:
                out.extend(self.merge_edits(seg))
            else:
                out.extend(seg)
        return out

    def get_all_rule_merge_edits(
        self,
        orig: Doc,
        corr: Doc,
        align_edits: list[tuple],
    ) -> list[Edit]:
        """
        Merge adjacent edits according to a set of rules.
        :param orig: The original spacy Doc.
        :param corr: The corrected spacy Doc.
        :param align_edits: The alignment edits.
        :return: A list of Edit objects.
        """
        edits = []
        # Split alignment into groups of M, T and rest. (T has a number after it)
        for op, group in groupby(
            align_edits,
            lambda x: x[0][0] if x[0][0] in {"M", "T"} else False,
        ):
            group = list(group)
            # Ignore M
            if op == "M":
                continue
            # T is always split
            elif op == "T":
                for seq in group:
                    edits.append(Edit.from_original_and_correction(orig, corr, seq[1:]))
            # Process D, I and S subsequence
            else:
                processed = self.get_rule_merge_edits(
                    orig,
                    corr,
                    group_edits=group,
                    align_edits=align_edits,
                )
                # Turn the processed sequence into edits
                for seq in processed:
                    edits.append(Edit.from_original_and_correction(orig, corr, seq[1:]))
        return edits

    def get_rule_merge_edits(self, orig, corr, group_edits, align_edits):
        """
        Merge adjacent edits according to a set of rules.
        :param orig: The original spacy Doc.
        :param corr: The corrected spacy Doc.
        :param group_edits: A list of alignment edits.
        :param align_edits: The alignment edits.
        :return: A list of alignment edits.
        """
        # Return single alignments
        if len(group_edits) <= 1:
            return group_edits
        # Get the ops for the whole sequence
        ops = [op[0] for op in group_edits]
        # Merge all D xor I ops. (95% of human multi-token edits contain S).
        if set(ops) == {"D"} or set(ops) == {"I"}:
            # return self._merge_DI_with_rules(orig, corr, group_edits)
            return self.merge_edits(group_edits)

        content = False  # True if edit includes a content word
        # Get indices of all start-end combinations in the seq: 012 = 01, 02, 12
        combos = list(combinations(range(0, len(group_edits)), 2))
        # Sort them starting with largest spans first
        combos.sort(key=lambda x: x[1] - x[0], reverse=True)
        # Loop through combos

        # Loop through combos
        for start, end in combos:
            # Ignore ranges that do NOT contain a substitution.
            if "S" not in ops[start : end + 1]:
                continue
            # Get the tokens in orig and cor. They will now never be empty.
            o = orig[group_edits[start][1] : group_edits[end][2]]
            c = corr[group_edits[start][3] : group_edits[end][4]]

            # Only merge Delete ops if they are at the start and text is punctuation or fillerword
            if (
                start == 0
                and ops[start] == "D"
                and o[0].text.lower() in language_resources.filler_words
            ):
                # Merge filler word at the start: [ um i -> I]
                return [group_edits[0]] + self.get_rule_merge_edits(
                    orig,
                    corr,
                    group_edits[1:],
                    align_edits,
                )
            if start == 0 and ops[start] == "D" and self.is_punct(o[0]):
                # Merge punctuation at the start: [ , i -> I]
                return [group_edits[0]] + self.get_rule_merge_edits(
                    orig,
                    corr,
                    group_edits[1:],
                    align_edits,
                )

            # Only merge Delete ops if they are at the end and text is punctuation or fillerword
            if (
                end == len(group_edits) - 1
                and ops[end] == "D"
                and o[-1].text.lower() in language_resources.filler_words
            ):
                # Merge filler word at the end: [i um -> I]
                return self.get_rule_merge_edits(
                    orig,
                    corr,
                    group_edits[:-1],
                    align_edits,
                ) + [group_edits[-1]]
            if end == len(group_edits) - 1 and ops[end] == "D" and self.is_punct(o[-1]):
                # Merge punctuation at the end: [i , -> I]
                return self.get_rule_merge_edits(
                    orig,
                    corr,
                    group_edits[:-1],
                    align_edits,
                ) + [group_edits[-1]]

            # First token possessive suffixes
            if start == 0 and (o[0].tag_ == "POS" or c[0].tag_ == "POS"):
                return [group_edits[0]] + self.get_rule_merge_edits(
                    orig,
                    corr,
                    group_edits[1:],
                    align_edits,
                )
            # Merge possessive suffixes: [friends -> friend 's]
            if o[-1].tag_ == "POS" or c[-1].tag_ == "POS":
                return (
                    self.get_rule_merge_edits(
                        orig,
                        corr,
                        group_edits[: end - 1],
                        align_edits,
                    )
                    + self.merge_edits(group_edits[end - 1 : end + 1])
                    + self.get_rule_merge_edits(
                        orig,
                        corr,
                        group_edits[end + 1 :],
                        align_edits,
                    )
                )
            # Case changes
            if o[-1].lower == c[-1].lower:
                # Merge first token I or D: [Cat -> The big cat]
                if start == 0 and (
                    (len(o) == 1 and c[0].text[0].isupper())
                    or (len(c) == 1 and o[0].text[0].isupper())
                ):
                    return self.merge_edits(
                        group_edits[start : end + 1],
                    ) + self.get_rule_merge_edits(
                        orig,
                        corr,
                        group_edits[end + 1 :],
                        align_edits,
                    )
                # Merge with previous punctuation: [, we -> . We], [we -> . We]
                if (len(o) > 1 and self.is_punct(o[-2])) or (
                    len(c) > 1 and self.is_punct(c[-2])
                ):
                    return (
                        self.get_rule_merge_edits(
                            orig,
                            corr,
                            group_edits[: end - 1],
                            align_edits,
                        )
                        + self.merge_edits(group_edits[end - 1 : end + 1])
                        + self.get_rule_merge_edits(
                            orig,
                            corr,
                            group_edits[end + 1 :],
                            align_edits,
                        )
                    )
            # Merge whitespace/hyphens: [acat -> a cat], [sub - way -> subway]
            s_str = sub("['-]", "", "".join([tok.lower_ for tok in o]))
            t_str = sub("['-]", "", "".join([tok.lower_ for tok in c]))
            if s_str == t_str:
                return (
                    self.get_rule_merge_edits(
                        orig,
                        corr,
                        group_edits[:start],
                        align_edits,
                    )
                    + self.merge_edits(group_edits[start : end + 1])
                    + self.get_rule_merge_edits(
                        orig,
                        corr,
                        group_edits[end + 1 :],
                        align_edits,
                    )
                )
            # Merge same POS or auxiliary/infinitive/phrasal verbs:
            # [to eat -> eating], [watch -> look at]
            pos_set = set([tok.pos for tok in o] + [tok.pos for tok in c])
            if len(o) != len(c) and (
                len(pos_set) == 1
                # 87, 94 , 100
                or pos_set.issubset({POS.AUX, POS.PART, POS.VERB})
            ):
                if "living" in o.text:  # TODO
                    return (
                        self.get_rule_merge_edits(
                            orig,
                            corr,
                            group_edits[:start],
                            align_edits,
                        )
                        + group_edits[start : end + 1]
                        + self.get_rule_merge_edits(
                            orig,
                            corr,
                            group_edits[end + 1 :],
                            align_edits,
                        )
                    )
                else:
                    return (
                        self.get_rule_merge_edits(
                            orig,
                            corr,
                            group_edits[:start],
                            align_edits,
                        )
                        + self.merge_edits(group_edits[start : end + 1])
                        + self.get_rule_merge_edits(
                            orig,
                            corr,
                            group_edits[end + 1 :],
                            align_edits,
                        )
                    )
            # Split rules take effect when we get to smallest chunks
            if end - start < 2:
                # # Merge adjacent substitutions if they are auxiliary verbs or contractions
                # if set(ops) == {"S"} and (
                #     # o[0] and c[0] are auxiliary verbs
                #     (o[0].pos in {POS.AUX, POS.VERB} and c[0].pos in {POS.AUX, POS.VERB})
                #     # o[-1] and c[-1] are contractions
                #     and (
                #         (
                #             o[-1].text in dependency_resources.conts or o[-1].text in dependency_resources.mapping_conts
                #         )
                #         and (c[-1].text in dependency_resources.conts or c[-1].text in dependency_resources.mapping_conts)
                #     )
                # ):
                #     return self.merge_edits(group_edits[start : end + 1])
                # Split adjacent substitutions
                if len(o) == len(c) == 2:
                    return self.get_rule_merge_edits(
                        orig,
                        corr,
                        group_edits[: start + 1],
                        align_edits,
                    ) + self.get_rule_merge_edits(
                        orig,
                        corr,
                        group_edits[start + 1 :],
                        align_edits,
                    )
                # Split similar substitutions at sequence boundaries
                if (ops[start] == "S" and self.char_cost(o[0], c[0]) > 0.75) or (
                    ops[end] == "S" and self.char_cost(o[-1], c[-1]) > 0.75
                ):
                    return self.get_rule_merge_edits(
                        orig,
                        corr,
                        group_edits[: start + 1],
                        align_edits,
                    ) + self.get_rule_merge_edits(
                        orig,
                        corr,
                        group_edits[start + 1 :],
                        align_edits,
                    )
                # Split final determiners
                if end == len(group_edits) - 1 and (
                    (ops[-1] in {"D", "S"} and o[-1].pos == POS.DET)
                    or (ops[-1] in {"I", "S"} and c[-1].pos == POS.DET)
                ):
                    return self.get_rule_merge_edits(
                        orig,
                        corr,
                        group_edits[:-1],
                        align_edits,
                    ) + [group_edits[-1]]
            # Set content word flag
            if not pos_set.isdisjoint(open_pos):
                content = True
        # Merge sequences that contain content words
        if content:
            return self.merge_edits(group_edits)
        else:
            return group_edits
