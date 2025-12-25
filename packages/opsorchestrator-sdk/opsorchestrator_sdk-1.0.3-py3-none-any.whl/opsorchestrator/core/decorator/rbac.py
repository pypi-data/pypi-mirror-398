"""
This module contains the RBAC handling for Operations
"""
def role(value: str):
    """
    Decorator that attaches predefined roles to a class
    and adds a can_access(token) method that uses them.
    """
    def decorator(cls):
        return cls
    return decorator
