"""
Execution unit interface
with Execution Unit Execution parameters and Validation Result
"""
from abc import ABC, abstractmethod
from opsorchestrator.core.data_model import DataModel
from opsorchestrator.core.decorator.class_decorators import classproperty

class ExecutionUnit(ABC):
    """
    Execution Unit Interface
    """
    _operation_id = None
    _user_session_id = None
    _operation_name = None

    @classproperty
    def name(cls) -> str:
        """The name of an execution unit"""
        raise NotImplementedError("Name was never defined")

    @classproperty
    def data_model(cls) -> DataModel:
        raise NotImplementedError("Subclasses must define .data_model")

    @classproperty
    def unique_name(self) -> str:
        return self.__name__ if isinstance(self,type) else self.__class__.__name__


    @classmethod
    def emit(cls, message):
        """Emit a message"""
        print(message)


    @classmethod
    @abstractmethod
    def execute(
        cls,
        operation_name : str,
        operation_id : str,
        user_session_id : str,
        required_data : dict
        ): #to be done; Arguments has to be passed from upper layer not accessed via sub_operation or operation
        """Should provide concrete implementation for execution"""
        raise NotImplementedError("Execution unit has to implement execute method")