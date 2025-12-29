#!/usr/bin/env python3
"""
Legacy main module for backward compatibility.

This module provides backward compatibility with the old pypinindia API
while redirecting to the new modern implementation.
"""

import warnings
from .core import get_state as new_get_state, get_district as new_get_district


def main() -> None:
    """Legacy main function - now redirects to CLI."""
    warnings.warn(
        "The main() function is deprecated. Use 'pypinindia' command or import functions directly.",
        DeprecationWarning,
        stacklevel=2
    )
    from .cli import main as cli_main
    cli_main()


# Legacy function for backward compatibility
def get_state(pincode: str) -> str:
    """
    Legacy function for backward compatibility.
    
    Args:
        pincode: The pincode to lookup
        
    Returns:
        State name or 'Not Found' if not found
        
    Note:
        This function is deprecated. Use pinin.get_state() instead.
    """
    warnings.warn(
        "pinin.main.get_state() is deprecated. Use pinin.get_state() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        return new_get_state(pincode)
    except Exception:
        return 'Not Found'


def run() -> None:
    """Legacy run function for backward compatibility."""
    warnings.warn(
        "The run() function is deprecated. Use 'pypinindia' command instead.",
        DeprecationWarning,
        stacklevel=2
    )
    main()


if __name__ == '__main__':
    main()
