"""
Custom exceptions for the pypinindia library.
"""

from typing import List, Optional


class PininError(Exception):
    """Base exception class for pypinindia library."""
    pass


class InvalidPincodeError(PininError):
    """Raised when an invalid pincode is provided."""
    
    def __init__(self, pincode: str, message: Optional[str] = None):
        self.pincode = pincode
        
        if message:
            full_message = message
        else:
            full_message = f"Invalid pincode: '{pincode}'. Pincode must be a 6-digit number."
        
        super().__init__(full_message)


class DataNotFoundError(PininError):
    """Raised when pincode data is not found."""
    
    def __init__(self, pincode: str, message: Optional[str] = None):
        self.pincode = pincode
        
        if message:
            full_message = message
        else:
            full_message = f"No data found for pincode: '{pincode}'"
        
        super().__init__(full_message)


class DataLoadError(PininError):
    """Raised when pincode data fails to load."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, original_exception: Optional[Exception] = None):
        self.file_path = file_path
        self.original_exception = original_exception
        
        full_message = f"Failed to load pincode data: {message}"
        if file_path:
            full_message += f" from file: '{file_path}'"
        if original_exception:
            full_message += f"\nOriginal Exception: {type(original_exception).__name__}: {original_exception}"
        
        super().__init__(full_message)
    

    
class SummaryError(PininError):
    """Raised when a summary operation fails."""

    def __init__(self, pincode: Optional[str] = None, message: Optional[str] = None):
        self.pincode = pincode

        if message:
            full_message = message
        elif pincode:
            full_message = f"Summary unavailable for pincode: '{pincode}'"
        else:
            full_message = "Summary operation failed."

        super().__init__(full_message)

