import os

from vnerrant.utils import io_utils


class WordListAdapter:
    """
    Adapter is used in front of the system to check if a word is in the wordlist or not.

    The wordlist can be loaded from a txt or json file.
    The adapter can check if a word is in the wordlist and add or remove words from it.
    """

    def __init__(self, adapter_wordlist_path: str):
        self.wordlist = {}

        if os.path.isfile(adapter_wordlist_path):
            self._load_wordlist(adapter_wordlist_path)
        elif os.path.isdir(adapter_wordlist_path):
            all_files = io_utils.get_all_files_in_directory(adapter_wordlist_path)
            for file_path in all_files:
                self._load_wordlist(file_path)
        else:
            raise ValueError(
                f"System does not support type of this path, please try txt or json"
            )

    def _load_wordlist(self, path: str) -> None:
        """
        Load a wordlist from a file. Now, the system supports txt and json files.

        Args:
            path (str): path to the file containing the wordlist

        Returns: None

        """

        if path.endswith(".txt"):
            self._load_txt_wordlist(path)
        elif path.endswith(".json"):
            self._load_json_wordlist(path)
        else:
            raise ValueError(
                f"System does not support type of this path, please try txt or json"
            )

    def _load_txt_wordlist(self, path: str) -> None:
        """
        Load a wordlist from a text file. The file should contain one word per line.

        Args:
            path (str): path to the file containing the wordlist

        Returns: None

        """

        with open(path, "r") as file:
            wordlist = file.readlines()
        wordlist = [word.strip() for word in wordlist if word.strip()]
        wordlist = [word for word in wordlist if not word.startswith("#")]
        self.wordlist.update(dict.fromkeys(wordlist))

    def _load_json_wordlist(self, path: str) -> None:
        """
        Load a wordlist from a json file. The file should contain a dictionary with words as keys and values as True.

        Args:
            path (str): path to the file containing the wordlist

        Returns: None

        """

        self.wordlist.update(io_utils.load_json(path))

    def check(self, word: str) -> bool:
        """
        Check if the word is in dictionary of adapter and, if it is, report whether it is correct or not

        Args:
            word (str): word to check

        Returns (bool): True if word is in dictionary, False otherwise

        """
        changed_words = [word, word.lower(), word.capitalize()]
        for changed_word in changed_words:
            if changed_word in self.wordlist:
                return True
        return False

    def add(self, word: str) -> None:
        """
        Add a word to the wordlist

        Args:
            word (str): word to add to the wordlist

        Returns: None

        """
        self.wordlist[word] = True

    def remove(self, word: str) -> None:
        """
        Remove a word from the wordlist. The word is removed in both lower and upper case.

        Args:
            word (str): word to remove from the wordlist

        Returns (None): None

        """
        lowered = word.lower()
        if word in self.wordlist:
            self.wordlist.pop(word)
        if lowered in self.wordlist:
            self.wordlist.pop(lowered)
