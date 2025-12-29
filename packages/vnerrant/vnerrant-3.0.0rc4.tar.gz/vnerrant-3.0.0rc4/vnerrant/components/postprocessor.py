from abc import ABC, abstractmethod


class BasePostprocessor(ABC):
    """
    Base class for all post-processing classes.
    """

    @abstractmethod
    def process(self, *args, **kwargs):
        """
        Post-process the edits.
        """
        raise NotImplementedError
