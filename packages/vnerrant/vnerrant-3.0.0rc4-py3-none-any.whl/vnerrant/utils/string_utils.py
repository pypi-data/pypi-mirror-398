from typing import List, Optional

from vnerrant.constants import ENGLISH_TOKENIZING_CHARACTERS


class Character:
    MIN_SUPPLEMENTARY_CODE_POINT = 0x010000
    MIN_HIGH_SURROGATE = "\ud800"
    MAX_LOW_SURROGATE = "\udfff"

    @classmethod
    def char_count(cls, code_point: int) -> int:
        return 2 if code_point >= cls.MIN_SUPPLEMENTARY_CODE_POINT else 1


class StringTokenizer:
    """
    The string tokenizer class allows an application to break a string into tokens.
    The StringTokenizer methods do not distinguish among identifiers, numbers, and
    quoted strings, nor do they recognize and skip comments.

    The set of delimiters (the characters that separate tokens) may be specified either
    at creation time or on a per-token basis.

    An instance of StringTokenizer behaves in one of two ways, depending on whether it
    was created with the return_delimiter flag having the value true or false:
    - If the flag is False, delimiter characters serve to separate tokens.
      A token is a maximal sequence of consecutive characters that are not delimiters.
    - If the flag is true, delimiter characters are themselves considered to be tokens.
      A token is thus either one delimiter character, or a maximal sequence of consecutive
      characters that are not delimiters.

    A StringTokenizer object internally maintains a current position within the string to be tokenized.
    Some operations advance this current position past the characters processed.

    A token is returned by taking a substring of the string that was used to create the StringTokenizer object.
    """

    def __init__(
        self, text: str, delimiter: str = " \t\n\r\f", return_delimiter: bool = False
    ):
        self.current_position: int = 0
        self.new_position: int = -1
        self.max_position: int = len(text)
        self.text: str = text
        self.delimiter: str = delimiter
        self.return_delimiter: bool = return_delimiter
        self.delimiter_changed: bool = False

        self.max_delimiter_code_point: int = 0
        self.has_surrogates: bool = False
        self.delimiter_code_point: List[int] = []

        self._set_max_delimiter_code_point()

    def _set_max_delimiter_code_point(self):
        """
        Set max_delimiter_code_point to the highest char in the delimiter set.
        """
        m, count, index = 0, 0, 0
        while index < len(self.delimiter):
            c = self.delimiter[index]
            if Character.MIN_HIGH_SURROGATE <= c <= Character.MAX_LOW_SURROGATE:
                c = ord(c)
                self.has_surrogates = True

            c = ord(c)
            if m < c:
                m = c
            count += 1
            index += Character.char_count(c)

        self.max_delimiter_code_point = m
        if self.has_surrogates:
            self.delimiter_code_point = []
            i, j = 0, 0
            while i < count:
                c = ord(self.delimiter[j])
                self.delimiter_code_point[i] = c
                i += 1
                j += Character.char_count(c)

    def is_delimiter(self, code_point):
        for delimiter_code_point in self.delimiter_code_point:
            if delimiter_code_point == code_point:
                return True
        return False

    def skip_delimiter(self, start_pos: int):
        """
        Skips delimiters starting from the specified position. If return_delimiter is false,
        returns the index of the first non-delimiter character at or after startPos.
        If return_delimiter is true, startPos is returned.
        """
        position = start_pos
        while not self.return_delimiter and position < self.max_position:
            if not self.has_surrogates:
                c = self.text[position]
                if ord(c) > self.max_delimiter_code_point or c not in self.delimiter:
                    break
                position += 1
            else:
                c = ord(self.text[position])
                if c > self.max_delimiter_code_point or not self.is_delimiter(c):
                    break
                position += Character.char_count(c)

        return position

    def scan_token(self, start_pos):
        """
        Skips ahead from start_pos and returns the index of the next delimiter
        character encountered, or max_position if no such delimiter is found.
        """
        position = start_pos
        while position < self.max_position:
            if not self.has_surrogates:
                c = self.text[position]
                if ord(c) <= self.max_delimiter_code_point and c in self.delimiter:
                    break
                position += 1
            else:
                c = ord(self.text[position])
                if c <= self.max_delimiter_code_point and self.is_delimiter(c):
                    break
                position += Character.char_count(c)

        if self.return_delimiter and start_pos == position:
            if not self.has_surrogates:
                c = self.text[position]
                if ord(c) <= self.max_delimiter_code_point and c in self.delimiter:
                    position += 1
            else:
                c = ord(self.text[position])
                if c <= self.max_position and self.is_delimiter(c):
                    position += Character.char_count(c)

        return position

    def has_more_tokens(self):
        """
        Temporarily store this position and use it in the following
        next_token() method only if the delimiters haven't been changed in
        that next_token() invocation.
        """
        self.new_position = self.skip_delimiter(self.current_position)
        return self.new_position < self.max_position

    def next_token(self, delimiter: Optional[str] = None):
        """
        If the next position has already been computed in has_more_tokens() and
        delimiters have not changed between the computation and this invocation,
        then use the computed value.
        """
        if delimiter is not None:
            self.delimiter = delimiter
            self.delimiter_changed = True
            self._set_max_delimiter_code_point()
            return self.next_token()

        if self.new_position >= 0 and not self.delimiter_changed:
            self.current_position = self.new_position
        else:
            self.skip_delimiter(self.current_position)

        # Reset these anyway
        self.delimiter_changed = False
        self.new_position = -1

        if self.current_position >= self.max_position:
            raise ValueError("NoSuchElementException")

        start = self.current_position
        self.current_position = self.scan_token(self.current_position)
        return self.text[start : self.current_position]

    def count_tokens(self):
        """
        Calculates the number of times that this tokenizer's nextToken method can be called
        before it generates an exception. The current position is not advanced.
        Returns: the number of tokens remaining in the string using the current delimiter set.
        """
        count = 0
        current_position = self.current_position
        while current_position < self.max_position:
            current_position = self.skip_delimiter(current_position)
            if current_position >= self.max_position:
                break
            current_position = self.scan_token(current_position)
            count += 1
        return count


def get_string_tokenizer(text: str, language: str = "en") -> StringTokenizer:
    if language == "en":
        return StringTokenizer(text, ENGLISH_TOKENIZING_CHARACTERS, True)
    else:
        raise ValueError(f"Language {language} is not supported")
