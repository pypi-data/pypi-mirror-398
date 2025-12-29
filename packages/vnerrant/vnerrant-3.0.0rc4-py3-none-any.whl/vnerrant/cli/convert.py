from __future__ import annotations

from contextlib import ExitStack
from warnings import filterwarnings

import click
from loguru import logger

import vnerrant
from vnerrant.model.edit import (
    convert_edits_to_dict,
    get_corrected_text_and_edits,
    noop_edit,
)

filterwarnings("ignore")


def validate_merge(ctx, param, value):
    """
    Validate the merge option.
    """
    allowed_choices = ["rules", "all-split", "all-merge", "all-equal"]
    if value not in allowed_choices:
        raise click.BadParameter(
            f"Invalid choice: {value}. (Choose from {', '.join(allowed_choices)})",
        )
    return value


@click.group()
def convert():
    pass


@convert.command()
@click.option(
    "--orig_file",
    "-o",
    help="The path of original file",
    type=str,
    required=True,
)
@click.option(
    "--corr_files",
    "-c",
    help="The path of corrected file",
    type=str,
    multiple=True,
    required=True,
)
@click.option(
    "--output",
    "-out",
    help="The path of output file",
    type=str,
    required=True,
)
@click.option(
    "--tok",
    help="Word tokenise type, ['spacy', 'split', 'string'] (default: spacy)",
    type=str,
    default="spacy",
)
@click.option(
    "--lev",
    help="Align using standard Levenshtein (default: False)",
    type=bool,
    default=False,
)
@click.option(
    "--merge",
    help="Choose a merging strategy for automatic alignment.\n"
    "rules: Use a rule-based merging strategy (default)\n"
    "all-split: Merge nothing: MSSDI -> M, S, S, D, I\n"
    "all-merge: Merge adjacent non-matches: MSSDI -> M, SSDI\n"
    "all-equal: Merge adjacent same-type non-matches: MSSDI -> M, SS, D, I",
    callback=validate_merge,
    default="rules",
    show_default=True,
)
def parallel_to_m2(
    orig_file: str,
    corr_files: str,
    output: str,
    tok: str,
    lev: bool,
    merge: str,
):
    """
    Convert parallel files to m2 format.
    :param orig: The path of original file
    :param corr: The path of corrected files
    :param output: The path of output file
    :param tok: Word tokenise the text using spacy (default: False)
    :param lev: Align using standard Levenshtein (default: False)
    :param merge: Choose a merging strategy for automatic alignment.
    """
    logger.info("Loading resources...")
    annotator = vnerrant.load("en")
    logger.info("Processing parallel files...")
    with ExitStack() as stack, open(output, "w", encoding="utf-8") as out_m2:
        in_files = [
            stack.enter_context(open(i)) for i in [orig_file] + list(corr_files)
        ]
        # Process each line of all input files
        for line in zip(*in_files):
            # Get the original and all the corrected texts
            orig_text = line[0].strip()
            # TODO: preprocess to remove space errors, must implement optional for this function
            orig_text, _ = annotator.preprocess(orig_text)

            corr_texts = line[1:]
            # Skip the line if orig is empty
            if not orig_text:
                continue
            # Parse orig with spacy
            orig_text = annotator.parse(orig_text, tok)
            # Write orig to the output m2 file
            out_m2.write(
                " ".join(["S"] + [token.text for token in orig_text]) + "\n",
            )
            # Loop through the corrected texts
            for cor_id, cor_text in enumerate(corr_texts):
                cor_text = cor_text.strip()
                # TODO: preprocess to remove space errors, must implement optional for this function
                cor_text, _ = annotator.preprocess(cor_text)

                # If the texts are the same, write a noop edit
                if orig_text.text.strip() == cor_text:
                    out_m2.write(noop_edit(cor_id) + "\n")
                # Otherwise, do extra processing
                else:
                    # Parse cor with spacy
                    cor_text = annotator.parse(cor_text, tok)
                    # Align the texts and extract and classify the edits
                    edits = annotator.annotate_raw(
                        orig_text.text, cor_text.text, lev, merge
                    )
                    # Loop through the edits
                    for edit in edits:
                        # Write the edit to the output m2 file
                        out_m2.write(edit.to_m2(cor_id) + "\n")
            # Write a newline when we have processed all corrections for each line
            out_m2.write("\n")


@convert.command()
@click.option(
    "--input",
    "-i",
    help="The path to an input that have a m2 format.",
    type=str,
    required=True,
)
@click.option(
    "--output",
    "-o",
    help="The path to an output that have a m2 format.",
    type=str,
    required=True,
)
@click.option(
    "--auto",
    help="Extract edits automatically.",
    is_flag=True,
)
@click.option(
    "--gold",
    help="Use existing edit alignments.",
    is_flag=True,
)
@click.option(
    "--no_min",
    help="Do not minimise edit spans (gold only).",
    is_flag=True,
)
@click.option(
    "--old_cats",
    help="Preserve old error types (gold only); i.e. turn off the classifier.",
    is_flag=True,
)
@click.option(
    "--lev",
    help="Align using standard Levenshtein.",
    is_flag=True,
)
@click.option(
    "--merge",
    help="Choose a merging strategy for automatic alignment.\n"
    "rules: Use a rule-based merging strategy (default)\n"
    "all-split: Merge nothing: MSSDI -> M, S, S, D, I\n"
    "all-merge: Merge adjacent non-matches: MSSDI -> M, SSDI\n"
    "all-equal: Merge adjacent same-type non-matches: MSSDI -> M, SS, D, I",
    callback=validate_merge,
    default="rules",
    show_default=True,
)
def m2_to_m2(
    input: str,
    output: str,
    auto: bool,
    gold: bool,
    no_min: bool,
    old_cats: bool,
    lev: bool,
    merge: str,
):
    """
    Convert m2 files to m2 format.
    :param input: The path to an input that have a m2 format.
    :param output: The path to an output that have a m2 format.
    :param auto: Extract edits automatically.
    :param gold: Use existing edit alignments.
    :param no_min: Do not minimise edit spans (gold only).
    :param old_cats: Preserve old error types (gold only); i.e. turn off the classifier.
    :param lev: Align using standard Levenshtein.
    :param merge: Choose a merging strategy for automatic alignment.
    """
    # Parse command line args
    logger.info("Loading resources...")

    annotator = vnerrant.load("en")

    logger.info("Processing M2 file...")
    # Open the m2 file and split it into text+edits blocks. Also open out_m2.
    with open(input) as m2, open(output, "w") as out_m2:
        # Store the current m2_block here
        m2_block = []
        # Loop through m2 lines
        for line in m2:
            line = line.strip()
            # If the line isn't empty, add it to the m2_block
            if line:
                m2_block.append(line)
            # Otherwise, process the complete blocks
            else:
                # Write the original text to the output M2 file
                out_m2.write(m2_block[0] + "\n")
                # Parse orig with spacy
                orig = annotator.parse(m2_block[0][2:])
                # Simplify the edits and sort by coder id
                edit_dict = convert_edits_to_dict(m2_block[1:])
                # Loop through coder ids
                for id, raw_edits in sorted(edit_dict.items()):
                    # If the first edit is a noop
                    if raw_edits[0][2] == "noop":
                        # Write the noop and continue
                        out_m2.write(noop_edit(id) + "\n")
                        continue
                    # Apply the edits to generate the corrected text
                    # Also redefine the edits as orig and cor token offsets
                    cor, gold_edits = get_corrected_text_and_edits(
                        m2_block[0][2:],
                        raw_edits,
                    )
                    # Parse cor with spacy
                    cor = annotator.parse(cor)
                    # Save detection edits here for auto
                    det_edits = []
                    # Loop through the gold edits
                    for gold_edit in gold_edits:
                        # Do not minimise detection edits
                        if gold_edit[-2] in {"Um", "UNK"}:
                            edit = annotator.import_edit(
                                orig,
                                cor,
                                gold_edit[:-1],
                                min=False,
                                old_cat=old_cats,
                            )
                            # Overwrite the pseudo correction and set it in the edit
                            edit.c_toks = annotator.parse(gold_edit[-1])
                            # Save the edit for auto
                            det_edits.append(edit)
                            # Write the edit for gold
                            if gold:
                                # Write the edit
                                out_m2.write(edit.to_m2(id) + "\n")
                        # Gold annotation
                        elif gold:
                            edit = annotator.import_edit(
                                orig,
                                cor,
                                gold_edit[:-1],
                                not no_min,
                                old_cats,
                            )
                            # Write the edit
                            out_m2.write(edit.to_m2(id) + "\n")
                    # Auto annotations
                    if auto:
                        # Auto edits
                        edits = annotator.annotate(
                            orig,
                            cor,
                            lev,
                            merge,
                        )
                        # Combine detection and auto edits and sort by orig offsets
                        edits = sorted(
                            det_edits + edits,
                            key=lambda e: (e.o_start, e.o_end),
                        )
                        # Write the edits to the output M2 file
                        for edit in edits:
                            out_m2.write(edit.to_m2(id) + "\n")
                # Write a newline when there are no more edits
                out_m2.write("\n")
                # Reset the m2 block
                m2_block = []
