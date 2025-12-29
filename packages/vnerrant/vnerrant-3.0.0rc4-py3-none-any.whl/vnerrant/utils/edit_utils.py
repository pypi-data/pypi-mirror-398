from itertools import groupby
from typing import List

from vnerrant.components.en.constants import dependency_resources
from vnerrant.model import Edit, EditCollection, EditElement


def get_match_edits(alignment):
    """
    Get the match edits from an alignment.
    Args:
        alignment (Alignment): An Alignment object

    Returns: A list of match edits
    """
    orig, corr, align_edits = alignment.orig, alignment.cor, alignment.align_seq
    edits = []
    # Split alignment into groups of M, T and rest. (T has a number after it)
    for op, group in groupby(
        align_edits, lambda x: x[0][0] if x[0][0] in {"M", "T"} else False
    ):
        group = list(group)
        if op == "M":
            for seq in group:
                edits.append(Edit.from_original_and_correction(orig, corr, seq[1:]))
    return edits


def update_edits(orig_doc, cor_doc, edits):
    """
    Postprocess the edits by updating text, the start and end character indices.
    Args:
        orig_doc (Doc): An original spacy Doc object
        cor_doc (Doc): A corrected spacy Doc object
        edits (list[Edit]): A list of Edit objects
    """
    orig_tokens = [token._.full_text for token in orig_doc]
    cor_tokens = [token._.full_text for token in cor_doc]
    for edit in edits:
        edit.original.text = "".join(
            [token._.full_text for token in edit.original.tokens]
        )
        edit.corrected.text = "".join(
            [token._.full_text for token in edit.corrected.tokens]
        )

        if edit.original.start_token != 0:
            edit.original.start_char = len(
                "".join(orig_tokens[: edit.original.start_token])
            )
        if edit.original.end_token != 0:
            edit.original.end_char = len(
                "".join(orig_tokens[: edit.original.end_token])
            )

        if edit.corrected.start_token != 0:
            edit.corrected.start_char = len(
                "".join(cor_tokens[: edit.corrected.start_token])
            )
        if edit.corrected.end_token != 0:
            edit.corrected.end_char = len(
                "".join(cor_tokens[: edit.corrected.end_token])
            )


def _merge_edit_elements(
    text: str, first: EditElement, second: EditElement, inplace: str = "first"
) -> None:
    """
    Merge two Edit Elements objects.

    Args:
        text (str): The text of the EditElement objects
        first (EditElement): An EditElement object
        second (EditElement): An EditElement object
        inplace (str): The object to be updated. Default is "first".

    Returns: None
    """
    if inplace not in ["first", "second"]:
        raise ValueError("inplace should be either 'first' or 'second'.")

    if inplace == "second":
        first, second = second, first

    first.start_token = min(first.start_token, second.start_token)
    first.start_char = min(first.start_char, second.start_char)
    first.end_token = max(first.end_token, second.end_token)
    first.end_char = max(first.end_char, second.end_char)
    first.text = text[first.start_char : first.end_char]


def merge_edit_collection_with_space_edits(
    edit_collection: EditCollection, space_edits: List[Edit]
):
    """
    Merge the space edits to the edit collection.
    Args:
        edit_collection (EditCollection): An EditCollection object
        space_edits (list[Edit]): A list of Edit objects
    """
    # Merge SPACE with PUNCTUATION
    remained_edits = []
    for space_edit in space_edits:
        for edit in edit_collection.edits:
            if space_edit.original.end_char == edit.original.start_char:
                _merge_edit_elements(
                    edit_collection.orig, edit.original, space_edit.original
                )
                _merge_edit_elements(
                    edit_collection.cor, edit.corrected, space_edit.corrected
                )
                break

        else:
            remained_edits.append(space_edit)

    edit_collection.edits.extend(remained_edits)


def update_operator(edits: List[Edit]):
    """
    Update the operator of the edits.
    Args:
        edits (list[Edit]): A list of Edit objects to be updated.
    """
    for edit in edits:
        orig_text = edit.original.text
        cor_text = edit.corrected.text
        if orig_text and cor_text:
            edit.edit_type = "R" + edit.edit_type[1:]
        elif not orig_text and cor_text:
            edit.edit_type = "M" + edit.edit_type[1:]
        else:
            edit.edit_type = "U" + edit.edit_type[1:]


def update_span_edit(edits: List[Edit]):  # noqa D103
    """
    Update the replace operator of the edits by trimming matching leading
    and trailing spaces in both original and corrected text of each edit.

    Args:
        edits (list): A list of Edit objects to be updated.
    """

    for edit in edits:
        if edit.edit_type[0] == "R":
            orig_text, start_orig, end_orig = (
                edit.original.text,
                edit.original.start_char,
                edit.original.end_char,
            )
            corr_text, start_corr, end_corr = (
                edit.corrected.text,
                edit.corrected.start_char,
                edit.corrected.end_char,
            )

            # Remove trailing spaces if both original and corrected texts end with them
            while orig_text.endswith(" ") and corr_text.endswith(" "):
                orig_text = orig_text[:-1]
                corr_text = corr_text[:-1]
                end_orig -= 1
                end_corr -= 1

            # Remove leading spaces if both original and corrected texts start with them
            while orig_text.startswith(" ") and corr_text.startswith(" "):
                orig_text = orig_text[1:]
                corr_text = corr_text[1:]
                start_orig += 1
                start_corr += 1

            # Except for the case where the original text is empty
            if not orig_text and start_orig == end_orig:
                edit.edit_type = "M" + edit.edit_type[1:]

            # Update the texts and character positions back to the Edit objects
            edit.original.text = orig_text
            edit.corrected.text = corr_text
            edit.original.start_char = start_orig
            edit.original.end_char = end_orig
            edit.corrected.start_char = start_corr
            edit.corrected.end_char = end_corr


def process_space_edit(edit: Edit) -> Edit:
    """
    Process the space edit.
    Args:
        edit (Edit): An Edit object to be processed.

    Returns: An Edit object after processing.
    """
    space_edit = edit.copy()
    align = len(edit.original.text.strip())

    new_orig_text = space_edit.original.text[align:]
    new_cor_text = space_edit.corrected.text[align:]

    while new_orig_text and new_cor_text:
        if new_orig_text[0] != new_cor_text[0]:
            break
        new_orig_text = new_orig_text[1:]
        new_cor_text = new_cor_text[1:]
        align += 1

    space_edit.original.start_char += align
    space_edit.original.text = new_orig_text

    space_edit.corrected.start_char += align
    space_edit.corrected.text = new_cor_text

    if new_orig_text and new_cor_text:
        space_edit.edit_type = "R:SPACE"
    elif not new_orig_text and new_cor_text:
        space_edit.edit_type = "M:SPACE"
    else:
        space_edit.edit_type = "U:SPACE"

    space_edit.is_space = True
    return space_edit


def merge_contraction_with_aux(collection: EditCollection) -> EditCollection:
    """
    Merge contraction edits with auxiliary edits in the edit collection.
    Examples:
    orig = "this is wrong sentence. there aren't wrong sentences"
    cor = "this are wrong sentences. there are not wrong sentences"

    -> Orig: [6, 8, 30, 36, "aren't"], Cor: [6, 8, 32, 39, 'are not'], Type: 'R:CONTR'

    Args:
        collection (EditCollection): An EditCollection object containing edits.

    """
    orig_doc = collection.orig_doc
    cor_doc = collection.cor_doc

    orig_text = orig_doc.text
    cor_text = cor_doc.text

    edits_: List[Edit] = []

    for idx, edit in enumerate(collection.edits):

        edit_ = edit.copy()

        edit_type = edit.edit_type[2:]

        corr_start_char = edit.corrected.start_char
        corr_end_char = edit.corrected.end_char

        orig_start_char = edit.original.start_char
        orig_end_char = edit.original.end_char

        # Get start and text for full AUX +contraction
        if (
            edit_type == "CONTR"
            and orig_text[orig_start_char - 1 : orig_start_char]
            and orig_start_char != 0
        ):
            while (
                orig_text[orig_start_char - 1 : orig_start_char] != " "
                and orig_start_char != 0
            ):
                orig_start_char -= 1
            while (
                cor_text[corr_start_char - 1 : corr_start_char] != " "
                and corr_start_char != 0
            ):
                corr_start_char -= 1
            edit_.original.text = orig_text[orig_start_char:orig_end_char]
            edit_.corrected.text = cor_text[corr_start_char:corr_end_char]

            edit_.original.start_char = orig_start_char
            edit_.corrected.start_char = corr_start_char

        # Merge contraction with auxiliary edits
        if idx != 0 and (
            collection.edits[idx - 1].original.end_char >= orig_start_char
        ):
            if collection.edits[idx - 1].edit_type[2:] == "ORTH" or (
                collection.edits[idx - 1].original.text.lower()
                in dependency_resources.aux_conts
                or collection.edits[idx - 1].original.text.lower()
                in dependency_resources.mapping_conts
                or collection.edits[idx - 1].corrected.text.lower()
                in dependency_resources.aux_conts
                or collection.edits[idx - 1].corrected.text.lower()
                in dependency_resources.mapping_conts
            ):
                edits_[-1] = edit_
            else:
                edits_.append(edit)
        else:
            edits_.append(edit_)

    collection.edits = edits_
