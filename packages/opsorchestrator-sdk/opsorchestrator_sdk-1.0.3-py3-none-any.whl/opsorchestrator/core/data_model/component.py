"""Data model component"""
from abc import ABC
from opsorchestrator.core.decorator.class_decorators import classproperty

class Component(ABC):
    """Component interface to define a component within a technology"""
    @classproperty
    def name(self) -> str:
        """Each subclass must provide a name"""
        return self.__name__