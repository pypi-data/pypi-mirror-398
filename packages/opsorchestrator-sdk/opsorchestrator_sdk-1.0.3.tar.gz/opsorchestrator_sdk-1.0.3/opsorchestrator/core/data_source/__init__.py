"""Blueprint for state registry and its scopes"""
from enum import Enum

class DataSourceScope(Enum):
    OPERATION = 0
    USER = 1
    SHARED = 2
