from __future__ import annotations


def computeFScore(tp: int, fp: int, fn: int, beta: float = 0.5) -> tuple:
    """
    Compute the F-score given the TP, FP, and FN counts.
    :param tp: The number of true positives.
    :param fp: The number of false positives.
    :param fn: The number of false negatives.
    :param beta: The beta value for the F-score.
    :return: The precision, recall, and F-score.
    """
    p = float(tp) / (tp + fp) if fp else 1.0
    r = float(tp) / (tp + fn) if fn else 1.0
    f = float((1 + (beta**2)) * p * r) / (((beta**2) * p) + r) if p + r else 0.0
    return round(p, 4), round(r, 4), round(f, 4)


def compareEdits(hyp_edits: dict, ref_edits: dict) -> tuple[int, int, int, dict]:
    """
    Compare two sets of edits and return the TP, FP, FN, and category counts.
    :param hyp_edits: The hypothesis edits.
    :param ref_edits: The reference edits.
    :return: The TP, FP, FN, and category counts.
    """
    tp = 0  # True Positives
    fp = 0  # False Positives
    fn = 0  # False Negatives
    cat_dict = {}  # {cat: [tp, fp, fn], ...}

    for h_edit, h_cats in hyp_edits.items():
        # noop hyp edits cannot be TP or FP
        if h_cats[0] == "noop":
            continue
        # TRUE POSITIVES
        if h_edit in ref_edits.keys():
            # On occasion, multiple tokens at same span.
            for h_cat in ref_edits[h_edit]:  # Use ref dict for TP
                tp += 1
                # Each dict value [TP, FP, FN]
                if h_cat in cat_dict.keys():
                    cat_dict[h_cat][0] += 1
                else:
                    cat_dict[h_cat] = [1, 0, 0]
        # FALSE POSITIVES
        else:
            # On occasion, multiple tokens at same span.
            for h_cat in h_cats:
                fp += 1
                # Each dict value [TP, FP, FN]
                if h_cat in cat_dict.keys():
                    cat_dict[h_cat][1] += 1
                else:
                    cat_dict[h_cat] = [0, 1, 0]
    for r_edit, r_cats in ref_edits.items():
        # noop ref edits cannot be FN
        if r_cats[0] == "noop":
            continue
        # FALSE NEGATIVES
        if r_edit not in hyp_edits.keys():
            # On occasion, multiple tokens at same span.
            for r_cat in r_cats:
                fn += 1
                # Each dict value [TP, FP, FN]
                if r_cat in cat_dict.keys():
                    cat_dict[r_cat][2] += 1
                else:
                    cat_dict[r_cat] = [0, 0, 1]
    return tp, fp, fn, cat_dict
