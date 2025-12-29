from typing import List


class ReplacingRule:
    """
    Replacing rule class that contains rules for replacing words.
    It replaces incorrect words with correct words using a dictionary.
    The dictionary is a text file where each line contains a list of incorrect words separated by commas
    and a list of correct words separated by commas, with "->" between them.
    """

    def __init__(self, path: str):
        self.rules = {}

        with open(path, "r") as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines if line.strip()]

        for line in lines:
            if line.startswith("#"):
                continue
            incorrect, correct = line.split("->")
            incorrect = incorrect.split(",")
            correct = correct.split(",")
            incorrect = [element.strip() for element in incorrect if element.strip()]
            correct = [element.strip() for element in correct if element.strip()]
            for element in incorrect:
                self.rules[element] = correct

    def check(self, word: str) -> bool:
        """
        Check if the word is in rule dictionary or not. If it is, return INCORRECT, otherwise UNKNOWN.

        Args:
            word (str): word to check

        Returns (RuleResult): result of the check

        """
        if word in self.rules:
            return False
        return True

    def suggest(self, word: str) -> List[str]:
        """
        Suggest corrections for the word based on the replacing dictionary.

        Args:
            word (str): word to suggest corrections for

        Returns (List[str]): list of suggestions

        """
        result = self.rules.get(word, None)
        return self.rules[word].copy() if result is not None else []
