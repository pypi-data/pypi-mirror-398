from __future__ import annotations


def load_text_file(path: str) -> set[str]:
    """
    Load a text file.
    :param path: The path to the file.
    :return: The contents of the file as a string.
    """
    data = set()
    with open(path, encoding="utf-8") as text_file:
        for line in text_file:
            line = line.strip()
            if line:
                data.add(line)
    return data


def load_word_list(path: str) -> set:
    """
    Load a list of words from a file.
    :param path: The path to the file.
    :return: A set of words.
    """
    with open(path, encoding="utf-8") as word_list:
        return {word.strip() for word in word_list}


# Load Universal Dependency POS Tags map file.
# https://universaldependencies.org/tagset-conversion/en-penn-uposf.html
def load_pos_map(path: str) -> dict:
    """
    Load a mapping of PTB tags to UD tags from a file.
    :param path: The path to the file.
    :return: A dictionary of tags.
    """
    map_dict = {}
    with open(path, encoding="utf-8") as map_file:
        for line in map_file:
            line = line.strip().split("\t")
            # Change ADP to PREP for readability
            if line[1] == "ADP":
                map_dict[line[0]] = "PREP"
            # Change PROPN to NOUN; we don't need a prop noun tag
            elif line[1] == "PROPN":
                map_dict[line[0]] = "NOUN"
            # Change CCONJ to CONJ
            elif line[1] == "CCONJ":
                map_dict[line[0]] = "CONJ"
            # Otherwise
            else:
                map_dict[line[0]] = line[1].strip()
        # Add some spacy PTB tags not in the original mapping.
        map_dict['""'] = "PUNCT"
        map_dict["SP"] = "SPACE"
        map_dict["_SP"] = "SPACE"
        map_dict["BES"] = "VERB"
        map_dict["HVS"] = "VERB"
        map_dict["ADD"] = "X"
        map_dict["GW"] = "X"
        map_dict["NFP"] = "X"
        map_dict["XX"] = "X"
    return map_dict
