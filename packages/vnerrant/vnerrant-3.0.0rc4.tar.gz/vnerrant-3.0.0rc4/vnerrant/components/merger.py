from __future__ import annotations

import itertools
from abc import ABC, abstractmethod

from spacy.tokens import Doc

from vnerrant.model.edit import Edit


class BaseMerger(ABC):
    """
    Base class for all merging classes.
    """

    def __init__(self):
        pass

    @staticmethod
    def merge_edits(edits: list[tuple]) -> list[tuple]:
        """
        Merge a list of edits into a single edit.
        :param edits: A list of edits to merge.
        :return: A single merged edit.
        """
        if not edits:
            return edits
        return [("X", edits[0][1], edits[-1][2], edits[0][3], edits[-1][4])]

    @abstractmethod
    def get_all_rule_merge_edits(self, *args, **kwargs):
        """
        Get all edits from the alignment sequence. Each edit is a span of
        tokens from the original and corrected sentences.
        """
        raise NotImplementedError

    def get_all_split_edits(
        self,
        orig: Doc,
        corr: Doc,
        align_edits: list[tuple],
    ) -> list[Edit]:
        """
        Get all edits from the alignment sequence. Each edit is a span of
        tokens from the original and corrected sentences.
        :param orig: The original sentence parsed by spacy.
        :param corr: The corrected sentence parsed by spacy.
        :param align_edits: A list of edits from the alignment sequence.
        :return: A list of Edit objects.
        """

        edits = []
        for align in align_edits:
            if align[0] != "M":
                edits.append(Edit.from_original_and_correction(orig, corr, align[1:]))
        return edits

    def get_all_merge_edits(
        self,
        orig: Doc,
        corr: Doc,
        align_edits: list[tuple],
    ) -> list[Edit]:
        """
        Merge all adjacent non-match operations in the alignment sequence.
        :param orig: The original sentence parsed by spacy.
        :param corr: The corrected sentence parsed by spacy.
        :param align_edits: A list of edits from the alignment sequence.
        :return: A list of Edit objects.
        """
        edits = []
        for op, group in itertools.groupby(
            align_edits,
            lambda x: True if x[0] != "M" else False,
        ):
            if op:
                merged = self.merge_edits(list(group))
                edits.append(
                    Edit.from_original_and_correction(orig, corr, merged[0][1:])
                )
        return edits

    def get_all_equal_edits(
        self,
        orig: Doc,
        corr: Doc,
        align_edits: list[tuple],
    ) -> list[Edit]:
        """
        Merge all adjacent same operations in the alignment sequence.
        :param orig: The original sentence parsed by spacy.
        :param corr: The corrected sentence parsed by spacy.
        :param align_edits: A list of edits from the alignment sequence.
        :return: A list of Edit objects.
        """

        edits = []
        for op, group in itertools.groupby(align_edits, lambda x: x[0]):
            if op != "M":
                merged = self.merge_edits(list(group))
                edits.append(
                    Edit.from_original_and_correction(orig, corr, merged[0][1:])
                )
        return edits
