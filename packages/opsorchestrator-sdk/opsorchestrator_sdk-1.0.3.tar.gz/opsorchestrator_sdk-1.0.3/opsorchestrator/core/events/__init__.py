"""
This module defines the `EventContract` abstract base class and related
components to represent the outcome of operations in the system.

It provides a standardized structure for capturing:
    - Operation details
    - Execution status (success, partial success, failure, pending)
    - Reason for the status
    - Optional reference to the execution unit that produced the event

Components:
    - StatusCodes: Enum representing possible execution states
    - EventContract: Abstract base class for creating event contracts
      associated with operations.
"""
from typing import TypedDict
from enum import Enum


class StatusCodes(Enum):
    """
    Enumeration of possible status codes for an operation event.

    Attributes:
        SUCCESS (str): The operation was completed successfully.
        PARTIAL_SUCESS (str): The operation was partially successful.
        FAILURE (str): The operation failed.
        PENDING (str): The operation is still pending.
    """
    START = "START"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    PENDING = "pending"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    
class EmittedMessage(TypedDict):
    text: str
    status: StatusCodes