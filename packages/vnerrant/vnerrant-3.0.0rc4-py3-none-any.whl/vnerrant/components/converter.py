from __future__ import annotations

import re

from vnerrant.annotator import Annotator
from vnerrant.constants import TokenizeTypes
from vnerrant.model.edit import noop_edit


class Converter:
    """
    Convert between M2 and parallel formats. This is a wrapper for the
    M2Processor class.
    """

    def __init__(self, annotator: Annotator = None):
        self.annotator_ = annotator

    @property
    def annotator(self) -> Annotator:
        """
        Return the annotator object.
        """
        if self.annotator_ is None:
            import vnerrant

            self.annotator_ = vnerrant.load(
                lang="en",
                model_name="en_core_web_sm",
            )
        return self.annotator_

    @staticmethod
    def parse_m2(m2_line: str) -> tuple:
        """
        Parse an edit from an M2 line.
        :param m2_line: An M2 line.
        :return: A tuple of editor id, edit type, edit span, and edit correction.
        """
        m2_line = m2_line.strip().split("|||")
        span = m2_line[0].split(" ")
        start = int(span[1])
        end = int(span[2])
        cat = m2_line[1]
        cor = m2_line[2]
        editor = m2_line[-1]
        if cat == "noop":
            return None
        else:
            return editor, cat, (start, end), cor

    def m2_to_parallel(self, m2s: list[list[str]]) -> tuple[list[str], list[str]]:
        """
        Convert M2 data to parallel format.
        :param m2s: A list of M2 lines.
        :return: A tuple of lists of original and corrected sentences.
        Examples:
        >>> m2s = [['S This is a test .', 'A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||0'],
                   ['S This is another test .'
                    'A 2 3|||R:DET|||a|||REQUIRED|||-NONE-|||0'
                    'A 4 4|||M:ADV|||too|||REQUIRED|||-NONE-|||0']]
        >>> converter = Converter()
        >>> converter.m2_to_parallel(m2s)
        (['This is a test .', 'This is another test .'],
            ['This is a test .', 'This is a test too .'])
        """
        origs = []
        corrs = []
        for m2 in m2s:
            orig = m2[0][2:]
            origs.append(orig)
            edits = {}
            for edit in m2[1:]:
                edit = self.parse_m2(edit)
                if not edit:
                    continue
                editor, cat, span, cor = edit
                if editor not in edits:
                    edits[editor] = []
                edits[editor].append({"span": span, "cat": cat, "cor": cor})
            if edits:
                for editor in edits:
                    sent = orig.split(" ")
                    for edit in edits[editor]:
                        span, cat, cor = (
                            edit["span"],
                            edit["cat"],
                            edit["cor"],
                        )
                        if cat[0] == "U":
                            sent[span[0] : span[1]] = [
                                " " for _ in range(span[1] - span[0])
                            ]
                        else:
                            if cat[0] == "M":
                                if span[0] != 0:
                                    sent[span[0] - 1] += " " + cor
                                else:
                                    sent[span[0]] = cor + " " + sent[span[0]]
                            elif cat[0] == "R":
                                src_tokens_len = len(sent[span[0] : span[1]])
                                sent[span[0] : span[1]] = [cor] + [
                                    " " for _ in range(src_tokens_len - 1)
                                ]
                    sent = " ".join(sent).strip()
                    res_sent = re.sub(" +", " ", sent)
                    corrs.append(res_sent)
            else:
                corrs.append(orig)
        return origs, corrs

    def parallel_to_m2(
        self,
        origs: list[str],
        corrs: list[str],
        tokenise: bool = False,
        lev: bool = False,
        merge: str = "rules",
    ) -> list[list[str]]:
        """
        Convert parallel data to M2 format.
        :param origs: A list of original sentences.
        :param corrs: A list of corrected sentences.
        :param tokenise: Whether to tokenise the input.
        :param lev: Whether to use Levenshtein alignment.
        :param merge: The merge strategy to use.
        :return: A list of M2 lines.
        Examples:
        >>> origs = ["This is a test .", "This is another test ."]
        >>> corrs = ["This is a test .", "This is a test too ."]
        >>> converter = Converter()
        >>> converter.parallel_to_m2(origs, corrs)
        [['S This is a test .', 'A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||0'],
         ['S This is another test .'
          'A 2 3|||R:DET|||a|||REQUIRED|||-NONE-|||0'
          'A 4 4|||M:ADV|||too|||REQUIRED|||-NONE-|||0']
        ]
        """
        assert len(origs) == len(corrs)
        assert merge in ["rules", "all-split", "all-merge"]
        tokenize_type = TokenizeTypes.SPACY if tokenise else TokenizeTypes.SPLIT
        out_m2 = []

        for orig, corr in zip(origs, corrs):
            m2 = []
            # Skip empty lines
            orig = orig.strip()
            corr = corr.strip()
            # Parse orig and corr with spacy
            orig = self.annotator.parse(orig, tokenize_type)
            corr = self.annotator.parse(corr, tokenize_type)
            # Write orig to the output m2 file
            m2.append(" ".join(["S"] + [token.text for token in orig]))
            # Align the texts and extract and classify the edits
            if orig.text.strip() == corr.text.strip():
                m2.append(noop_edit(0))  # 0 is the id of the annotator
            else:
                edits = self.annotator.annotate(orig, corr, lev, merge)
                # Loop through the edits
                for edit in edits:
                    m2.append(edit.to_m2(0))
            # Write the edits to the output m2 file
            out_m2.append(m2)
        return out_m2

    def m2_to_m2(self, m2s: list[list[str]]) -> list[list[str]]:
        pass

    def __repr__(self) -> str:
        return f"Converter(annotator={self.annotator})"

    def __str__(self) -> str:
        return f"Converter(annotator={self.annotator})"
