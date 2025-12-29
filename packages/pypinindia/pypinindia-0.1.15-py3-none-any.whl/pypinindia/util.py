#!/usr/bin/env python3
"""
Legacy utility module for backward compatibility.

This module provides backward compatibility with the old pypinindia API
while redirecting to the new modern implementation.
"""

import warnings
from .core import get_state as new_get_state, get_district as new_get_district


def get_state(pin: str) -> str:
    """
    Legacy function for backward compatibility.
    
    Args:
        pin: The pincode to lookup
        
    Returns:
        State name or 'Not Found' if not found
        
    Note:
        This function is deprecated. Use pinin.get_state() instead.
    """
    warnings.warn(
        "pinin.util.get_state() is deprecated. Use pinin.get_state() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        return new_get_state(pin)
    except Exception:
        return 'Not Found'


def get_location(pin: str) -> str:
    """
    Legacy function for backward compatibility.
    
    Args:
        pin: The pincode to lookup
        
    Returns:
        District name or 'Not Found' if not found
        
    Note:
        This function is deprecated. Use pinin.get_district() instead.
    """
    warnings.warn(
        "pinin.util.get_location() is deprecated. Use pinin.get_district() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        return new_get_district(pin)
    except Exception:
        return 'Not Found'
