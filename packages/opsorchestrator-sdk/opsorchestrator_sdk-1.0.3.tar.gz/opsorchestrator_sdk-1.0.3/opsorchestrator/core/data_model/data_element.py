"""Data model element"""
import re
from opsorchestrator.core.data_source import DataSourceScope
from opsorchestrator.core.data_model.component import Component
from opsorchestrator.core.data_model.technology import Technology

class DataElement():
    """Data element interface to define a key within a component"""
    def __init__(self, name : str, technology : Technology, component : Component, element_type : type, \
                  is_auth : bool = False, is_optional : bool = False, \
                  scope : DataSourceScope = DataSourceScope.OPERATION, \
                  expiration_period = None, 
                  skip_execution_if_not_found = False): #Justification: Already imported via TYPE_CHECKING, pylint: disable=used-before-assignment
        super().__setattr__("_name", name)
        self._element_type = element_type
        self._is_auth = is_auth
        self._scope = scope
        self.technology = technology
        self.component = component
        self._is_optional = is_optional
        self._expiration_period = expiration_period
        self._skip_execution_if_not_found = skip_execution_if_not_found

    def __setattr__(self, name, value):
        if name == "_technology":
            raise AttributeError("Direct assignment to _technology is forbidden. Use technology only.")
        if name == "_component":
            raise AttributeError("Direct assignment to _component is forbidden. Use component only.")
        if name == "_name":
            raise AttributeError("Direct assignment to _name is forbidden. Use DataElement initializer only.")
        super().__setattr__(name, value)

    @property
    def element_type(self):
        return self._element_type

    @property
    def is_authentication_element(self):
        return self._is_auth

    @property
    def is_optional(self):
        return self._is_optional

    @property
    def skip_execution(self):
        """Skip execution of that execution unit if data is absent."""
        return self._skip_execution_if_not_found

    @property
    def technology(self):
        return self._technology #Justification: element is set directly using __setattr__ pylint: disable=no-member

    @technology.setter
    def technology(self, _technology):
        if  not issubclass(_technology, Technology):
            raise TypeError("Technology has to be of type Technology")
        super().__setattr__("_technology", _technology)

    @property
    def component(self):
        return self._component #Justification: element is set directly using __setattr__ pylint: disable=no-member

    @component.setter
    def component(self, _component):
        if  not issubclass(_component, Component):
            raise TypeError("Component has to be of type Component")
        super().__setattr__("_component", _component)

    @property
    def name(self):
        return self._name #Justification: element is set directly using __setattr__ pylint: disable=no-member

    @name.setter
    def name(self,name):
        """
        Validates that the provided `name` string adheres to specific naming rules:
        - Must be a string.
        - Must be lowercase.
        - Can only contain lowercase letters and underscores.

        Args:
            name (str): The name string to validate.

        Raises:
            TypeError: If `name` is not a string.
            ValueError: If `name` is not lowercase or contains invalid characters.

        Returns:
            bool: True if validation passes.
        """
        # Allowed: lowercase letters, underscore
        name_re = re.compile(r"^[a-z_]+$")
        if not isinstance(name, str):
            raise TypeError(f"name: {name} must be a string")
        if name != name.lower():
            raise ValueError(f"name: {name} must be lowercase")
        if not name_re.fullmatch(name):
            raise ValueError(f"name: {name} may only contain lowercase letters, and underscore")
        super().__setattr__("_name", name)

    @property
    def fully_qualified_name(self):
        return f"{self.technology.__name__.lower()}.{self.component.__name__.lower()}.{self.name}"

    @property
    def unique_name(self):
        return self.fully_qualified_name.replace(".","_")

    @property
    def scope(self) -> DataSourceScope:
        return self._scope

    @scope.setter
    def scope(self, scope):
        self._scope = scope

    @property
    def expiration_period(self):
        return self._expiration_period
