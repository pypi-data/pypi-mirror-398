"""
Helper functions for local services.
"""

from typing import List


def SplitStrings(typeString: str) -> List[str]:
    """
    Split a type string into its component parts at the last underscore.

    Used for hierarchical type processing where compound types like
    "the_person_email" are split into ["the_person", "email"].

    Args:
        typeString: The type string to split (e.g., "the_person_email")

    Returns:
        List with two elements [prefix, suffix] if underscore found,
        or single element [typeString] if no underscore.

    Example:
        >>> SplitStrings("the_person_email")
        ['the_person', 'email']
        >>> SplitStrings("the_status")
        ['the', 'status']
        >>> SplitStrings("status")
        ['status']
    """
    pos = typeString.rfind("_")

    if pos > 0:
        rest = typeString[:pos]
        last = typeString[pos + 1:]
        return [rest, last]
    else:
        return [typeString]
