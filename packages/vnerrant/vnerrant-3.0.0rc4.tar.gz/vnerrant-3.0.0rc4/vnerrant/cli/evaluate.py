from __future__ import annotations

from collections import Counter
from typing import Any
from warnings import filterwarnings

import click
from loguru import logger

from vnerrant.components.evaluater import evaluate_edits, process_edits
from vnerrant.model.edit import convert_m2_to_edits
from vnerrant.utils.helper import merge_dict
from vnerrant.utils.pretty_results import print_results

filterwarnings("ignore")


def validate_cat(ctx, param, value):
    """
    Validate the cat option.
    """
    if value not in [1, 2, 3]:
        raise click.BadParameter("Invalid choice: {value}. (Choose from 1, 2, 3)")
    return value


@click.group()
def evaluate():
    pass


@evaluate.command()
@click.option("-hyp", help="A hypothesis M2 file.", required=True)
@click.option("-ref", help="A reference M2 file.", required=True)
@click.option(
    "-b",
    "--beta",
    help="Value of beta in F-score. (default: 0.5)",
    default=0.5,
    type=float,
)
@click.option(
    "-v",
    "--verbose",
    help="Print verbose output.",
    is_flag=True,
)
@click.option(
    "-dt",
    help="Evaluate Detection in terms of Tokens.",
    is_flag=True,
)
@click.option(
    "-ds",
    help="Evaluate Detection in terms of Spans.",
    is_flag=True,
)
@click.option(
    "-cse",
    help="Evaluate Correction in terms of Spans and Error types.",
    is_flag=True,
)
@click.option(
    "-single",
    help="Only evaluate single token edits; i.e. 0:1, 1:0 or 1:1",
    is_flag=True,
)
@click.option(
    "-multi",
    help="Only evaluate multi token edits; i.e. 2+:n or n:2+",
    is_flag=True,
)
@click.option(
    "-filt",
    help="Do not evaluate the specified error types.",
    multiple=True,
)
@click.option(
    "-cat",
    help="Show error category scores.\n"
    "1: Only show operation tier scores; e.g. R.\n"
    "2: Only show main tier scores; e.g. NOUN.\n"
    "3: Show all category scores; e.g. R:NOUN.",
    callback=validate_cat,
    type=int,
)
def m2(
    hyp: str,
    ref: str,
    dt: bool,
    ds: bool,
    single: bool,
    multi: bool,
    filt: Any,
    cse: bool,
    cat: int,
    beta: float,
    verbose: bool,
):
    """
    Evaluate the hypothesis M2 file against the reference M2 file.
    :param hyp: A hypothesis M2 file.
    :param ref: A reference M2 file.
    :param dt: Evaluate Detection in terms of Tokens.
    :param ds: Evaluate Detection in terms of Spans.
    :param single: Only evaluate single token edits; i.e. 0:1, 1:0 or 1:1.
    :param multi: Only evaluate multi token edits; i.e. 2+:n or n:2+.
    :param filt: Do not evaluate the specified error types.
    :param cse: Evaluate Correction in terms of Spans and Error types.
    :param cat: Show error category scores.
    :param beta: Value of beta in F-score. (default: 0.5)
    :param verbose: Print verbose output.
    """
    # Parse command line args
    # Open hypothesis and reference m2 files and split into chunks
    hyp_m2 = open(hyp).read().strip().split("\n\n")
    ref_m2 = open(ref).read().strip().split("\n\n")
    # Make sure they have the same number of sentences
    assert len(hyp_m2) == len(ref_m2)

    # Store global corpus level best counts here
    best_dict = Counter({"tp": 0, "fp": 0, "fn": 0})
    best_cats = {}
    # Process each sentence
    sents = zip(hyp_m2, ref_m2)
    for sent_id, sent in enumerate(sents):
        # Simplify the edits into lists of lists
        hyp_edits = convert_m2_to_edits(sent[0])
        ref_edits = convert_m2_to_edits(sent[1])
        # Process the edits for detection/correction based on args
        hyp_dict = process_edits(hyp_edits, dt, ds, single, multi, filt, cse)
        ref_dict = process_edits(ref_edits, dt, ds, single, multi, filt, cse)
        # original sentence for logging
        original_sentence = sent[0][2:].split("\nA")[0]
        # Evaluate edits and get best TP, FP, FN hyp+ref combo.
        count_dict, cat_dict = evaluate_edits(
            hyp_dict,
            ref_dict,
            best_dict,
            sent_id,
            original_sentence,
            verbose,
            beta,
        )
        # Merge these dicts with best_dict and best_cats
        best_dict += Counter(count_dict)
        best_cats = merge_dict(best_cats, cat_dict)
    logger.info("Systematic Evaluate based on VNERRANT tags")
    print_results(best_dict, best_cats, dt, ds, cse, cat, beta)
