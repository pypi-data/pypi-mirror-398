from __future__ import annotations


def merge_dict(dict1: dict[str, list], dict2: dict[str, list]) -> dict[str, list]:
    """
    Merge two dictionaries. If a key is present in both dictionaries, the values are
    added together.
    :param dict1: The first dictionary.
    :param dict2: The second dictionary.
    :return: The merged dictionary.
    Examples:
    >>> merge_dict({"a": [1, 2, 3]}, {"a": [4, 5, 6]})
    {"a": [5, 7, 9]}
    """
    for cat, stats in dict2.items():
        if cat in dict1.keys():
            dict1[cat] = [x + y for x, y in zip(dict1[cat], stats)]
        else:
            dict1[cat] = stats
    return dict1
