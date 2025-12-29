from __future__ import annotations

from abc import ABC, abstractmethod

from vnerrant.model.edit import Edit


class BaseClassifer(ABC):
    """
    Abstract class for a classifier.
    """

    def __init__(self):
        pass

    @abstractmethod
    def classify(self, edit: Edit, **kwargs) -> Edit:
        """
        Classify an edit into a specific error type.
        :param edit: An Edit object.
        :return: The error type of the edit.
        """
        raise NotImplementedError
