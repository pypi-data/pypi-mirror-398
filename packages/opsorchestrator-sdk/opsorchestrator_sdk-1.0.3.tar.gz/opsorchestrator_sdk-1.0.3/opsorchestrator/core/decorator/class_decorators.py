"""General file to define custom decorators within classes"""
from functools import update_wrapper
class classproperty:
    """Decorator to allow treating a property as classproperty mimcing classmethod"""
    def __init__(self, fget):
        self.fget = fget
        update_wrapper(self, fget)
    def __get__(self, _, owner=None):
        return self.fget(owner)
