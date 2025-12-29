from __future__ import annotations

import spacy
import yaml


def get_available_spacy_models() -> list[str]:
    """
    Get a list of available spaCy models installed in the current environment.
    :return: A list of spaCy model names.
    """
    installed_models = spacy.info().get("pipelines", "")
    if not installed_models:
        return []
    return list(installed_models.keys())


def get_spacy_models_for_language(lang: str) -> list[str]:
    """
    Get a list of spaCy models that support a specific language.
    :param lang: The language code (e.g. "en", "de", "fr").
    :return: A list of spaCy model names that support the specified language.
    """
    installed_models = get_available_spacy_models()
    if not installed_models:
        return []

    return [
        model_name
        for model_name in installed_models
        if model_name.split("_")[0] == lang
    ]


def load_yml_file(file_path: str) -> dict:
    """
    Load a YAML file from the specified path.
    :param file_path: The path to the YAML file.
    :return: The parsed YAML file.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)
