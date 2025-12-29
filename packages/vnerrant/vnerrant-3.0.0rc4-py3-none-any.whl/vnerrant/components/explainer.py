from abc import ABC, abstractmethod

from vnerrant.model.edit import Edit


class BaseExplainer(ABC):

    @abstractmethod
    def explain(self, edit: Edit) -> Edit:
        raise NotImplementedError
