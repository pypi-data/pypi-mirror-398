from __future__ import annotations

import spacy.parts_of_speech as POS
from rapidfuzz.distance import Indel
from spacy.tokens import Doc
from spacy.tokens.token import Token

# Protected class resource
OPEN_POS = {POS.ADJ, POS.ADV, POS.NOUN, POS.VERB}


class Alignment:
    """
    A class to represent a sentence alignment between an original and a
    corrected sentence. The alignment is computed using a custom
    Damerau-Levenshtein algorithm that incorporates linguistic features
    such as POS and lemma. The alignment is represented as a sequence of
    edit operations (insertions, deletions, substitutions, and
    transpositions) that can be used to generate an edit script.
    """

    def __init__(self, orig: Doc, cor: Doc, lev: bool = False):
        """
        Create an Alignment object from an original and corrected spacy
        Doc object. The alignment is computed using a custom
        Damerau-Levenshtein algorithm that incorporates linguistic features
        such as POS and lemma. The alignment is represented as a sequence of
        edit operations (insertions, deletions, substitutions, and
        transpositions) that can be used to generate an edit script.
        :param orig: An original spacy Doc object.
        :param cor: A corrected spacy Doc object.
        :param lev: A flag for standard Levenshtein alignment.
        """
        # Set orig and cor
        self.orig = orig
        self.cor = cor
        # Align orig and cor and get the cost and op matrices
        self.cost_matrix, self.op_matrix = self.align(lev)
        # Get the cheapest align sequence from the op matrix
        self.align_seq = self.get_cheapest_align_seq()

    def align(self, lev: bool) -> tuple:
        """
        Align the original and corrected sentences using a custom
        Damerau-Levenshtein algorithm that incorporates linguistic features
        such as POS and lemma. The alignment is represented as a sequence of
        edit operations (insertions, deletions, substitutions, and
        transpositions) that can be used to generate an edit script.
        :param lev: A flag for standard Levenshtein alignment.
        :return: The cost matrix and the operation matrix of the alignment.
        Examples:
        >>> orig = nlp("I like cats")
        >>> cor = nlp("I like dogs")
        >>> align = Alignment(orig, cor)
        >>> align.align_seq
        [('M', 0, 1, 0, 1), ('M', 1, 2, 1, 2), ('S', 2, 3, 2, 3)]
        """
        # Sentence lengths
        o_len = len(self.orig)
        c_len = len(self.cor)
        # Lower case token IDs (for transpositions)
        o_low = [o.lower for o in self.orig]
        c_low = [c.lower for c in self.cor]
        # Create the cost_matrix and the op_matrix
        cost_matrix = [[0.0 for j in range(c_len + 1)] for i in range(o_len + 1)]
        op_matrix = [["O" for j in range(c_len + 1)] for i in range(o_len + 1)]
        # Fill in the edges
        for i in range(1, o_len + 1):
            cost_matrix[i][0] = cost_matrix[i - 1][0] + 1
            op_matrix[i][0] = "D"
        for j in range(1, c_len + 1):
            cost_matrix[0][j] = cost_matrix[0][j - 1] + 1
            op_matrix[0][j] = "I"

        # Loop through the cost_matrix
        for i in range(o_len):
            for j in range(c_len):
                # Matches
                if (
                    self.orig[i].orth == self.cor[j].orth
                ):  # check spacy.tokens.token.Token
                    cost_matrix[i + 1][j + 1] = cost_matrix[i][j]
                    op_matrix[i + 1][j + 1] = "M"
                # Non-matches
                else:
                    del_cost = cost_matrix[i][j + 1] + 1
                    ins_cost = cost_matrix[i + 1][j] + 1
                    trans_cost = float("inf")
                    # Standard Levenshtein (S = 1)
                    if lev:
                        sub_cost = cost_matrix[i][j] + 1
                    # Linguistic Damerau-Levenshtein
                    else:
                        # Custom substitution
                        sub_cost = cost_matrix[i][j] + self.get_sub_cost(
                            self.orig[i],
                            self.cor[j],
                        )
                        # Transpositions require >=2 tokens
                        # Traverse the diagonal while there is not a Match.
                        k = 1
                        while (
                            i - k >= 0
                            and j - k >= 0
                            and cost_matrix[i - k + 1][j - k + 1]
                            != cost_matrix[i - k][j - k]
                        ):
                            if sorted(o_low[i - k : i + 1]) == sorted(
                                c_low[j - k : j + 1],
                            ):
                                trans_cost = cost_matrix[i - k][j - k] + k
                                break
                            k += 1
                    # Costs
                    costs = [trans_cost, sub_cost, ins_cost, del_cost]
                    # Get the index of the cheapest (first cheapest if tied)
                    l = costs.index(min(costs))
                    # Save the cost and the op in the matrices
                    cost_matrix[i + 1][j + 1] = costs[l]
                    if l == 0:
                        op_matrix[i + 1][j + 1] = "T" + str(k + 1)
                    elif l == 1:
                        op_matrix[i + 1][j + 1] = "S"
                    elif l == 2:
                        op_matrix[i + 1][j + 1] = "I"
                    else:
                        op_matrix[i + 1][j + 1] = "D"
        # Return the matrices
        return cost_matrix, op_matrix

    @staticmethod
    def get_sub_cost(o: Token, c: Token) -> float:
        """
        Get the substitution cost between two tokens based on their
        linguistic features. The cost is a float between 0 and 2.
        :param o: A spacy orig Token.
        :param c: A spacy cor Token.
        :return: A float between 0 and 2.
        Examples:
        >>> orig = nlp("I like cats")
        >>> cor = nlp("I likes cats")
        >>> align = Alignment(orig, cor)
        >>> align.get_sub_cost(orig[2], cor[2])
        1.249
        """
        # Short circuit if the only difference is case
        if o.lower == c.lower:
            return 0
        # Lemma cost
        if o.lemma == c.lemma:
            lemma_cost = 0
        else:
            lemma_cost = 0.499
        # POS cost
        if o.pos == c.pos:
            pos_cost = 0
        elif o.pos in OPEN_POS and c.pos in OPEN_POS:
            pos_cost = 0.25
        else:
            pos_cost = 0.5
        # Char cost
        if o.text == "that" and c.text == "anti":
            char_cost = 1.0
        else:
            char_cost = Indel.normalized_distance(o.text, c.text)
        # Combine the costs
        return lemma_cost + pos_cost + char_cost

    def get_cheapest_align_seq(self) -> list[tuple]:
        """
        Get the cheapest alignment sequence from the operation matrix.
        :return: A list of alignment tuples. Each tuple is of the form
        (op, o_start, o_end, c_start, c_end) where op is the edit
        operation, o_start and o_end are the start and end indices of the
        original span, and c_start and c_end are the start and end indices
        of the corrected span.
        """
        i = len(self.op_matrix) - 1
        j = len(self.op_matrix[0]) - 1
        align_seq = []
        # Work backwards from bottom right until we hit top left
        while i + j != 0:
            # Get the edit operation in the current cell
            op = self.op_matrix[i][j]
            # Matches and substitutions
            if op in {"M", "S"}:
                align_seq.append((op, i - 1, i, j - 1, j))
                i -= 1
                j -= 1
            # Deletions
            elif op == "D":
                align_seq.append((op, i - 1, i, j, j))
                i -= 1
            # Insertions
            elif op == "I":
                align_seq.append((op, i, i, j - 1, j))
                j -= 1
            # Transpositions
            else:
                # Get the size of the transposition
                k = int(op[1:])
                align_seq.append((op, i - k, i, j - k, j))
                i -= k
                j -= k
        # Reverse the list to go from left to right and return
        align_seq.reverse()
        return align_seq

    def __str__(self):
        """
        String representation of an Alignment object.
        """
        orig = " ".join(["Orig:"] + [tok.text for tok in self.orig])
        cor = " ".join(["Cor:"] + [tok.text for tok in self.cor])
        cost_matrix = "\n".join(
            ["Cost Matrix:"] + [str(row) for row in self.cost_matrix],
        )
        op_matrix = "\n".join(
            ["Operation Matrix:"] + [str(row) for row in self.op_matrix],
        )
        seq = "Best alignment: " + str([a[0] for a in self.align_seq])
        return "\n".join([orig, cor, cost_matrix, op_matrix, seq])
