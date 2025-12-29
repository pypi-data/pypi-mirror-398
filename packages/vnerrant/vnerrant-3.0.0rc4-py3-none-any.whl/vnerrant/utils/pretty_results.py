from __future__ import annotations

from vnerrant.metrics.criteria import computeFScore
from vnerrant.metrics.stats import meanScore


def processCategories(cat_dict: dict, setting: int) -> dict:
    """
    Process the category dictionary to combine categories.
    :param cat_dict: The category dictionary.
    :param setting: The category setting.
    :return: The processed category dictionary.
    """
    # Otherwise, do some processing.
    proc_cat_dict = {}
    for cat, cnt in cat_dict.items():
        if cat == "UNK":
            proc_cat_dict[cat] = cnt
            continue
        # M, U, R or UNK combined only.
        if setting == 1:
            if cat[0] in proc_cat_dict.keys():
                proc_cat_dict[cat[0]] = [
                    x + y for x, y in zip(proc_cat_dict[cat[0]], cnt)
                ]
            else:
                proc_cat_dict[cat[0]] = cnt
        # Everything without M, U or R.
        elif setting == 2:
            if cat[2:] in proc_cat_dict.keys():
                proc_cat_dict[cat[2:]] = [
                    x + y for x, y in zip(proc_cat_dict[cat[2:]], cnt)
                ]
            else:
                proc_cat_dict[cat[2:]] = cnt
        # All error category combinations
        else:
            return cat_dict
    return proc_cat_dict


def print_results(
    best: dict,
    best_cats: dict,
    dt: bool = False,
    ds: bool = False,
    cse: bool = False,
    cat: int = 1,
    beta: float = 0.5,
):
    """
    Print the results of the annotation process.
    :param best: The best scores.
    :param best_cats: The best category scores.
    :param dt: Whether to print token-based detection scores.
    :param ds: Whether to print span-based detection scores.
    :param cse: Whether to print span-based correction + classification scores.
    :param cat: The category setting.
    :param beta: The beta value for f-score.
    :return: The results dictionary.
    """
    # Prepare output title.
    title = ""
    if dt:
        title = " Token-Based Detection "
    elif ds:
        title = " Span-Based Detection "
    elif cse:
        title = " Span-Based Correction + Classification "
    else:
        title = " Span-Based Correction "

    result = {}

    # Category Scores
    if cat:
        best_cats = processCategories(best_cats, cat)
        print("")
        print(f"{title:=^66}")
        print(
            "Category".ljust(14),
            "TP".ljust(8),
            "FP".ljust(8),
            "FN".ljust(8),
            "P".ljust(8),
            "R".ljust(8),
            "F" + str(beta),
        )
        for cat, cnts in sorted(best_cats.items()):
            cat_p, cat_r, cat_f = computeFScore(cnts[0], cnts[1], cnts[2], beta)
            print(
                cat.ljust(14),
                str(cnts[0]).ljust(8),
                str(cnts[1]).ljust(8),
                str(cnts[2]).ljust(8),
                str(cat_p).ljust(8),
                str(cat_r).ljust(8),
                cat_f,
            )

            result[cat] = [cnts[0], cnts[1], cnts[2], cat_p, cat_r, cat_f]

        mic_p = meanScore([s[3] for s in result.values()])
        mic_r = meanScore([s[4] for s in result.values()])
        mic_f = meanScore([s[5] for s in result.values()])

        result["Marco Avg"] = [
            None,
            None,
            None,
            round(mic_p, 4),
            round(mic_r, 4),
            round(mic_f, 4),
        ]

        mac_p, mac_r, mac_f = computeFScore(best["tp"], best["fp"], best["fn"], beta)
        result["Micro Avg"] = [
            best["tp"],
            best["fp"],
            best["fn"],
            mac_p,
            mac_r,
            mac_f,
        ]

    # Print the overall results.
    print("")
    print(f"{title:=^46}")
    print("\t".join(["TP", "FP", "FN", "Prec", "Rec", "F" + str(beta)]))
    print(
        "\t".join(
            map(
                str,
                [best["tp"], best["fp"], best["fn"]]
                + list(computeFScore(best["tp"], best["fp"], best["fn"], beta)),
            ),
        ),
    )
    print("{:=^46}".format(""))
    print("")

    return result


def print_table(table):
    """
    Print a table in a readable format.
    """
    longest_cols = [
        (max([len(str(row[i])) for row in table]) + 3) for i in range(len(table[0]))
    ]
    row_format = "".join(
        ["{:>" + str(longest_col) + "}" for longest_col in longest_cols],
    )
    for row in table:
        print(row_format.format(*row))
