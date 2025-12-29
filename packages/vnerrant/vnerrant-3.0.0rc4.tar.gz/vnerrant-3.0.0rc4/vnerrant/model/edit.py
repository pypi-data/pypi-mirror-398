from __future__ import annotations

from typing import Any, List

from spacy.tokens import Doc


def noop_edit(index: int = 0) -> str:
    """
    Create a noop edit string.
    :param index: The id number of the annotation.
    :return: A noop edit string.
    """
    return "A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||" + str(index)


def convert_edits_to_dict(edits: list[str]) -> dict:
    """
    Convert a list of edit strings to a dictionary of edits.
    :param edits: A list of edit strings.
    :return: A dictionary of edits.
    """
    edit_dict = {}
    for edit in edits:
        edit = edit.split("|||")
        span = edit[0][2:].split()  # [2:] ignore the leading "A "
        start = int(span[0])
        end = int(span[1])
        cat = edit[1]
        cor = edit[2]
        index = edit[-1]
        # Save the useful info as a list
        proc_edit = [start, end, cat, cor]
        # Save the proc_edit inside the edit_dict using coder id
        if index in edit_dict.keys():
            edit_dict[index].append(proc_edit)
        else:
            edit_dict[index] = [proc_edit]
    return edit_dict


def convert_m2_to_edits(sent: str) -> list:
    """
    Convert a m2 string to a list of edit strings.
    :param sent: A m2 string.
    :return: A list of edit strings.
    """
    out_edits = []
    # Get the edit lines from a m2 block.
    edits = sent.split("\n")[1:]
    # Loop through the edits
    for edit in edits:
        # Preprocessing
        edit = edit[2:].split("|||")  # Ignore "A " then split.
        span = edit[0].split()
        start = int(span[0])
        end = int(span[1])
        cat = edit[1]
        cor = edit[2]
        coder = int(edit[-1])
        out_edit = [start, end, cat, cor, coder]
        out_edits.append(out_edit)
    return out_edits


def get_corrected_text_and_edits(
    orig_text: str,
    edits: list,
) -> tuple[str, list]:
    """
    Apply the edits to the original text to generate the corrected text.
    :param orig_text: The original text string.
    :param edits: A list of edit strings.
    :return: The corrected text and a list of edit strings.
    """
    # Copy orig_text; we will apply edits to it to make cor
    corr_text = orig_text.split()
    new_edits = []
    offset = 0
    # Sort the edits by offsets before processing them
    edits = sorted(edits, key=lambda e: (e[0], e[1]))
    # Loop through edits: [o_start, o_end, cat, cor_str]
    for edit in edits:
        o_start = edit[0]
        o_end = edit[1]
        cat = edit[2]
        cor_toks = edit[3].split()
        # Detection edits
        if cat in {"Um", "UNK"}:
            # Save the pseudo correction
            det_toks = cor_toks[:]
            # But temporarily overwrite it to be the same as orig
            cor_toks = orig_text.split()[o_start:o_end]
        # Apply the edits
        corr_text[o_start + offset : o_end + offset] = cor_toks
        # Get the cor token start and end offsets in cor
        c_start = o_start + offset
        c_end = c_start + len(cor_toks)
        # Keep track of how this affects orig edit offsets
        offset = offset - (o_end - o_start) + len(cor_toks)
        # Detection edits: Restore the pseudo correction
        if cat in {"Um", "UNK"}:
            cor_toks = det_toks
        # Update the edit with cor span and save
        new_edit = [o_start, o_end, c_start, c_end, cat, " ".join(cor_toks)]
        new_edits.append(new_edit)
    return " ".join(corr_text), new_edits


class EditElement:
    def __init__(
        self,
        start_token: int,
        end_token: int,
        start_char: int,
        end_char: int,
        tokens: Any,
        text: str,
    ):
        self.start_token = start_token
        self.end_token = end_token
        self.start_char = start_char
        self.end_char = end_char
        self.tokens = tokens
        self.text = text

    def copy(self) -> EditElement:
        return EditElement(
            start_token=self.start_token,
            end_token=self.end_token,
            start_char=self.start_char,
            end_char=self.end_char,
            tokens=self.tokens,
            text=self.text,
        )

    def reset_by_tokens(self):
        self.text = self.tokens.text
        self.start_char = self.tokens.start_char
        self.end_char = self.tokens.end_char

    def lstrip(self):
        while self.tokens and self.tokens[0].is_space:
            self.tokens = self.tokens[1:]
            self.start_token += 1
            self.start_char = self.tokens.start_char

        self.text = self.tokens.text if self.tokens else ""

    def rstrip(self):
        while self.tokens and self.tokens[-1].is_space:
            self.tokens = self.tokens[:-1]
            self.end_token -= 1
            self.end_char = self.tokens.end_char

        self.text = self.tokens.text if self.tokens else ""

    def strip(self):
        self.lstrip()
        self.rstrip()


class Edit:
    """
    An object representing an edit.
    """

    def __init__(
        self,
        original: EditElement,
        corrected: EditElement,
        edit_type: str = "NA",
        explanation: str = "",
        is_space: bool = False,
    ):
        self.original = original
        self.corrected = corrected
        self.edit_type = edit_type
        self.explanation = explanation
        self.is_space = is_space

    def copy(self) -> Edit:
        return Edit(
            original=self.original.copy(),
            corrected=self.corrected.copy(),
            edit_type=self.edit_type,
            explanation=self.explanation,
            is_space=self.is_space,
        )

    @classmethod
    def from_original_and_correction(
        cls, orig: Doc, cor: Doc, edit: list, edit_type: str = "NA"
    ):
        """
        Initialise the edit object with the orig and cor token spans and
        the error type. If the error type is not known, it is set to "NA".
        :param orig: The original text string parsed by spacy.
        :param cor: The corrected text string parsed by spacy.
        :param edit: A token span edit list: [o_start, o_end, c_start, c_end].
        :param edit_type: The error type string, if known.
        """
        # Orig offsets, spacy tokens and string
        o_start_token, o_end_token = edit[0], edit[1]
        o_tokens = orig[o_start_token:o_end_token]
        o_start_char, o_end_char = o_tokens.start_char, o_tokens.end_char
        o_text = o_tokens.text if o_tokens else ""
        original = EditElement(
            start_token=o_start_token,
            end_token=o_end_token,
            start_char=o_start_char,
            end_char=o_end_char,
            tokens=o_tokens,
            text=o_text,
        )

        # Cor offsets, spacy tokens and string
        c_start_token, c_end_token = edit[2], edit[3]
        c_tokens = cor[c_start_token:c_end_token]
        c_start_char, c_end_char = c_tokens.start_char, c_tokens.end_char
        c_text = c_tokens.text if c_tokens else ""
        corrected = EditElement(
            start_token=c_start_token,
            end_token=c_end_token,
            start_char=c_start_char,
            end_char=c_end_char,
            tokens=c_tokens,
            text=c_text,
        )

        return cls(original=original, corrected=corrected, edit_type=edit_type)

    # Minimise the edit; e.g. [a b -> a c] = [b -> c]
    def minimise(self):
        """
        Minimise the edit by removing common tokens from the start and end of
        the edit spans. This is done by adjusting the start and end offsets
        and removing tokens from the token spans.
        :return: The minimised edit object.
        Examples:
            >>> e = Edit("a b c", "a d c", [0, 3, 0, 3])
            >>> print(e)
            Orig: [0, 3, 'a b c'], Cor: [0, 3, 'a d c'], Type: 'NA'
            >>> e.minimise()
            >>> print(e)
            Orig: [1, 2, 'b'], Cor: [1, 2, 'd'], Type: 'NA'
        """
        # While the first token is the same on both sides
        while (
            self.original.tokens
            and self.corrected.tokens
            and self.original.tokens[0].text == self.corrected.tokens[0].text
        ):
            # Remove that token from the span, and adjust the start offsets
            self.original.tokens = self.original.tokens[1:]
            self.corrected.tokens = self.corrected.tokens[1:]
            self.original.start_token += 1
            self.corrected.start_token += 1

        # Do the same for the last token
        while (
            self.original.tokens
            and self.corrected.tokens
            and self.original.tokens[-1].text == self.corrected.tokens[-1].text
        ):
            self.original.tokens = self.original.tokens[:-1]
            self.corrected.tokens = self.corrected.tokens[:-1]
            self.original.end_token -= 1
            self.corrected.end_token -= 1

        # Update the strings and character indexes
        self.original.reset_by_tokens()
        self.corrected.reset_by_tokens()

        return self

    def to_m2(self, index: int = 0):
        """
        Convert the edit to a m2 string. If the error type is "NA", it is
        converted to "UNK".
        :param index: The id number of the annotation.
        """
        span = " ".join(
            ["A", str(self.original.start_token), str(self.original.end_token)]
        )
        cor_tokens_str = " ".join([token.text for token in self.corrected.tokens])
        return "|||".join(
            [span, self.edit_type, cor_tokens_str, "REQUIRED", "-NONE-", str(index)]
        )

    # Edit object string representation
    def __str__(self):
        """
        Print the edit object in a readable format.
        """
        orig = "Orig: " + str(
            [
                self.original.start_token,
                self.original.end_token,
                self.original.start_char,
                self.original.end_char,
                self.original.text,
            ]
        )
        cor = "Cor: " + str(
            [
                self.corrected.start_token,
                self.corrected.end_token,
                self.corrected.start_char,
                self.corrected.end_char,
                self.corrected.text,
            ]
        )
        edit_type = "Type: " + repr(self.edit_type)
        return ", ".join([orig, cor, edit_type])


class EditCollection:
    def __init__(
        self,
        orig: str,
        cor: str,
        orig_doc: Doc,
        cor_doc: Doc,
        edits: List[Edit],
        match_edits: List[Edit],
    ):
        self.orig = orig
        self.cor = cor
        self.orig_doc = orig_doc
        self.cor_doc = cor_doc
        self.edits = edits
        self.match_edits = match_edits

    def apply_edits(self):
        """
        Apply the edits to the original text to generate the corrected text.
        """
        self.edits.sort(
            key=lambda x: (x.original.start_char, x.original.end_char), reverse=True
        )
        new_text = self.orig
        for edit in self.edits:
            start, end, corrected_text = (
                edit.original.start_char,
                edit.original.end_char,
                edit.corrected.text,
            )
            new_text = new_text[:start] + corrected_text + new_text[end:]
        return new_text
