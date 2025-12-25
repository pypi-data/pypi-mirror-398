# pylint: disable=no-self-argument
"""
Operation Interface
"""
from abc import ABC, abstractmethod
from opsorchestrator.core.decorator.class_decorators import classproperty
from opsorchestrator.core.data_model import DataModel

class Operation(ABC):
    """Abstract base class defining the interface for an Operation."""
    @classproperty
    @abstractmethod
    def name(cls) -> str:
        raise NotImplementedError("Subclasses must define .name")

    @classproperty
    @abstractmethod
    def title(cls) -> str:
        raise NotImplementedError("Subclasses must define .title")

    @classproperty
    @abstractmethod
    def description(cls) -> str:
        raise NotImplementedError("Subclasses must define .description")

    @classproperty
    @abstractmethod
    def timeout(cls) -> int:
        raise NotImplementedError("Subclasses must define .timeout")

    @classproperty
    @abstractmethod
    def result_expiration_period(cls) -> int:
        raise NotImplementedError("Subclasses must define .result_expiration_period")

    @classproperty
    @abstractmethod
    def data_model(self) -> DataModel:
        raise NotImplementedError("Subclasses must define .data_model")
