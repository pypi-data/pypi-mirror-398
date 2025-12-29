from __future__ import annotations

from vnerrant.metrics.criteria import compareEdits, computeFScore
from vnerrant.utils.pretty_results import print_table


def process_token_based_detection(coder_dict, coder, start, end, cat):
    """
    Process a token based detection edit.
    :param coder_dict: The coder dictionary.
    :param coder: The coder.
    :param start: The start index.
    :param end: The end index.
    :param cat: The category.
    :return: None
    """
    if start == -1:
        # Preserve noop edits.
        coder_dict[coder].setdefault((start, start), []).append(cat)
    elif start == end and start >= 0:
        # Insertions defined as affecting the token on the right
        coder_dict[coder].setdefault((start, start + 1), []).append(cat)
    else:
        # Edit spans are split for each token in the range.
        for tok_id in range(start, end):
            coder_dict[coder].setdefault((tok_id, tok_id + 1), []).append(cat)


def process_span_based_detection(coder_dict, coder, start, end, cat):
    """
    Process a span based detection edit.
    :param coder_dict: The coder dictionary.
    :param coder: The coder.
    :param start: The start index.
    :param end: The end index.
    :param cat: The category.
    :return: None
    """
    coder_dict[coder].setdefault((start, end), []).append(cat)


def process_span_based_correction(coder_dict, coder, start, end, cat, cor, cse):
    """
    Process a span based correction edit.
    :param coder_dict: The coder dictionary.
    :param coder: The coder.
    :param start: The start index.
    :param end: The end index.
    :param cat: The category.
    :param cor: The correction.
    :param cse: Whether to evaluate correction in terms of error types.
    :return: None
    """
    key = (start, end, cat, cor) if cse else (start, end, cor)
    coder_dict[coder].setdefault(key, []).append(cat)


def process_edits(
    edits,
    dt: bool = False,
    ds: bool = False,
    single: bool = False,
    multi: bool = False,
    filt: bool = None,
    cse: bool = False,
):
    """
    Process the edits for detection/correction based on args.
    :param edits: The edits.
    :param dt: Whether to evaluate detection in terms of tokens.
    :param ds: Whether to evaluate detection in terms of spans.
    :param single: Whether to only evaluate single token edits.
    :param multi: Whether to only evaluate multi token edits.
    :param filt: Whether to not evaluate the specified error types.
    :param cse: Whether to evaluate correction in terms of error types.
    :return: The coder dictionary.
    """
    coder_dict = {}

    # Add an explicit noop edit if there are no edits.
    if not edits:
        edits = [[-1, -1, "noop", "-NONE-", 0]]

    # Loop through the edits
    for edit in edits:
        start, end, cat, cor, coder = edit

        # Add the coder to the coder_dict if necessary
        coder_dict.setdefault(coder, {})

        # Apply filters
        # Optionally apply filters based on args
        # 1. UNK type edits are only useful for detection, not correction.
        if cat == "UNK" and not dt and not ds:
            continue
        # 2. Only evaluate single token edits; i.e. 0:1, 1:0 or 1:1
        if single and (end - start >= 2 or len(cor.split()) >= 2):
            continue
        # 3. Only evaluate multi token edits; i.e. 2+:n or n:2+
        if multi and end - start < 2 and len(cor.split()) < 2:
            continue
        # 4. If there is a filter, ignore the specified error types
        if filt and cat in filt:
            continue

        # Token Based Detection
        if dt:
            process_token_based_detection(coder_dict, coder, start, end, cat)

        # Span Based Detection
        elif ds:
            process_span_based_detection(coder_dict, coder, start, end, cat)

        # Span Based Correction
        else:
            process_span_based_correction(
                coder_dict,
                coder,
                start,
                end,
                cat,
                cor,
                cse,
            )

    return coder_dict


def evaluate_edits(
    hyp_dict: dict,
    ref_dict: dict,
    best: dict,
    sent_id: int,
    original_sentence: str,
    verbose: bool = False,
    beta: float = 0.5,
):
    """
    Evaluate the edits for a sentence and return the best TP, FP, FN hyp+ref combo.
    :param hyp_dict: The hypothesis edits.
    :param ref_dict: The reference edits.
    :param best: The best TP, FP, FN counts so far.
    :param sent_id: The sentence ID.
    :param original_sentence: The original sentence.
    :param verbose: Whether to output verbose information.
    :param beta: The beta value for the F-score.
    :return: The best TP, FP, FN hyp+ref combo.
    """
    # Verbose output: display the original sentence
    if verbose:
        print("{:-^40}".format(""))
        print("Original sentence " + str(sent_id) + ": " + original_sentence)
    # Store the best sentence level scores and hyp+ref combination IDs
    # best_f is initialised as -1 cause 0 is a valid result.
    best_tp, best_fp, best_fn, best_f, best_hyp, best_ref = 0, 0, 0, -1, 0, 0
    best_cat = {}
    # Compare each hyp and ref combination
    for hyp_id in hyp_dict.keys():
        for ref_id in ref_dict.keys():
            # Get the local counts for the current combination.
            tp, fp, fn, cat_dict = compareEdits(
                hyp_dict[hyp_id],
                ref_dict[ref_id],
            )
            # Compute the local sentence scores (for verbose output only)
            loc_p, loc_r, loc_f = computeFScore(tp, fp, fn, beta)
            # Compute the global sentence scores
            p, r, f = computeFScore(
                tp + best["tp"],
                fp + best["fp"],
                fn + best["fn"],
                beta,
            )
            # Save the scores if they are better in terms of:
            # 1. Higher F-score
            # 2. Same F-score, higher TP
            # 3. Same F-score and TP, lower FP
            # 4. Same F-score, TP and FP, lower FN
            if (
                (f > best_f)
                or (f == best_f and tp > best_tp)
                or (f == best_f and tp == best_tp and fp < best_fp)
                or (f == best_f and tp == best_tp and fp == best_fp and fn < best_fn)
            ):
                best_tp, best_fp, best_fn = tp, fp, fn
                best_f, best_hyp, best_ref = f, hyp_id, ref_id
                best_cat = cat_dict
            # Verbose output
            if verbose:
                # Prepare verbose output edits.
                hyp_verb = list(sorted(hyp_dict[hyp_id].keys()))
                ref_verb = list(sorted(ref_dict[ref_id].keys()))
                # add categories
                # hyp_dict[hyp_id] looks like (0, 1, "str")
                # hyp_dict[hyp_id][h] is a list, always length one, of the corresponding category
                hyp_verb = [h + (hyp_dict[hyp_id][h][0],) for h in hyp_verb]
                ref_verb = [r + (ref_dict[ref_id][r][0],) for r in ref_verb]
                # Ignore noop edits
                if not hyp_verb or hyp_verb[0][0] == -1:
                    hyp_verb = []
                if not ref_verb or ref_verb[0][0] == -1:
                    ref_verb = []
                # Print verbose info
                print("{:-^40}".format(""))
                print(
                    "SENTENCE "
                    + str(sent_id)
                    + " - HYP "
                    + str(hyp_id)
                    + " - REF "
                    + str(ref_id),
                )
                print("HYPOTHESIS EDITS :", hyp_verb)
                print("REFERENCE EDITS  :", ref_verb)
                print("Local TP/FP/FN   :", str(tp), str(fp), str(fn))
                print(
                    "Local P/R/F" + str(beta) + "  :",
                    str(loc_p),
                    str(loc_r),
                    str(loc_f),
                )
                print(
                    "Global TP/FP/FN  :",
                    str(tp + best["tp"]),
                    str(fp + best["fp"]),
                    str(fn + best["fn"]),
                )
                print(
                    "Global P/R/F" + str(beta) + "  :",
                    str(p),
                    str(r),
                    str(f),
                )
    # Verbose output: display the best hyp+ref combination
    if verbose:
        print("{:-^40}".format(""))
        print(
            "^^ HYP "
            + str(best_hyp)
            + ", REF "
            + str(best_ref)
            + " chosen for sentence "
            + str(sent_id),
        )
        print("Local results:")
        header = ["Category", "TP", "FP", "FN"]
        body = [[k, *v] for k, v in best_cat.items()]
        print_table([header] + body)
    # Save the best TP, FP and FNs as a dict, and return this and the best_cat dict
    best_dict = {"tp": best_tp, "fp": best_fp, "fn": best_fn}
    return best_dict, best_cat
