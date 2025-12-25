"""Data model that defines the data fully qualified name"""
from abc import ABC
from typing import List
from opsorchestrator.core.data_model.data_element import DataElement

class DataModel(ABC):
    """Abstract base class for DataModel"""
    def __init__(self, required_data, \
                 output_data, preconditions = None):
        if isinstance(required_data, list):
            for data_element in required_data:
                if not isinstance(data_element, DataElement):
                    raise TypeError("Required data has to contain data elements")
        else:
            raise TypeError("Output data has to be a list")

        if isinstance(output_data, list):
            for data_element in output_data:
                if not isinstance(data_element, DataElement):
                    raise TypeError("Output data has to contain data elements")
        else:
            raise TypeError("Output data has to be a list")

        self._required_data_list = required_data
        self._output_data_list = output_data
        self._preconditions = preconditions if preconditions else []

    @property
    def required_data(self) -> List[DataElement]:
        return self._required_data_list
    @property
    def output_data(self) -> List[DataElement]:
        return self._output_data_list

    def is_valid(self, operation_id, user_session_id) -> bool:
        return all([condtion.check(operation_id, user_session_id) \
                    for condtion in self._preconditions]) \
                        if self._preconditions else True