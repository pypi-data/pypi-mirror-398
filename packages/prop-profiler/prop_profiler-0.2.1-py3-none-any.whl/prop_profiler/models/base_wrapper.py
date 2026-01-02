from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar


InputT = TypeVar("InputT", contravariant=True)
OutputT = TypeVar("OutputT", covariant=True)


class BaseWrapper(ABC, Generic[InputT, OutputT]):
    """
        Abstract base for all model-like wrappers.
    """
    @abstractmethod
    def predict(self, input_data: InputT) -> OutputT:
        """
            Compute predictions for a sequence of model inputs.
        """
        pass

    
