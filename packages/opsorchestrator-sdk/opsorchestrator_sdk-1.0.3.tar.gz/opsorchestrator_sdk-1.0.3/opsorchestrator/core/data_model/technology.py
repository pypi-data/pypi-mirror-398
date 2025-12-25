"""Data model technology interface"""
from abc import ABC
from opsorchestrator.core.decorator.class_decorators import classproperty

class Technology(ABC):
    @classproperty
    def name(self) -> str:
        """Each subclass must provide a name"""
        return self.__name__
