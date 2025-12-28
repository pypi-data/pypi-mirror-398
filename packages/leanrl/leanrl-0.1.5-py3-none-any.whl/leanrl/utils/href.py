"""
XBRL Href and Concept Utilities

Functions for parsing XBRL href attributes and extracting concept identifiers.
"""

import re
from functools import lru_cache


def extract_concept_from_href(href: str) -> str:
    """
    Extract the concept name from an xlink:href attribute.
    
    XBRL locators use href attributes like:
        - "us-gaap-2023.xsd#us-gaap_Assets"
        - "../elts/us-gaap-2023.xsd#us-gaap_CashAndCashEquivalents"
        - "#dei_EntityRegistrantName"
    
    This function extracts just the concept identifier after the '#'.
    
    Args:
        href: The full href string from an xlink:href attribute
    
    Returns:
        The concept name (fragment identifier after '#')
    
    Examples:
        >>> extract_concept_from_href('us-gaap-2023.xsd#us-gaap_Assets')
        'us-gaap_Assets'
        
        >>> extract_concept_from_href('#dei_EntityRegistrantName')
        'dei_EntityRegistrantName'
        
        >>> extract_concept_from_href('no-fragment')
        'no-fragment'
    """
    if '#' in href:
        return href.split('#', 1)[-1]
    return href


def parse_href(href: str) -> tuple[str, str]:
    """
    Parse an href into (file_path, fragment) components.
    
    Args:
        href: The full href string
    
    Returns:
        Tuple of (file_path, fragment). Fragment is empty string if not present.
    
    Examples:
        >>> parse_href('us-gaap-2023.xsd#us-gaap_Assets')
        ('us-gaap-2023.xsd', 'us-gaap_Assets')
        
        >>> parse_href('#LocalElement')
        ('', 'LocalElement')
        
        >>> parse_href('schema.xsd')
        ('schema.xsd', '')
    """
    if '#' in href:
        parts = href.split('#', 1)
        return parts[0], parts[1]
    return href, ''


@lru_cache(maxsize=256)
def parse_concept_name(concept: str) -> tuple[str, str]:
    """
    Parse a concept name into (prefix, local_name) components.
    
    XBRL concept names typically use underscore as separator:
        - "us-gaap_Assets" -> ("us-gaap", "Assets")
        - "dei_EntityRegistrantName" -> ("dei", "EntityRegistrantName")
    
    Args:
        concept: The concept identifier (e.g., "us-gaap_Assets")
    
    Returns:
        Tuple of (prefix, local_name)
    
    Examples:
        >>> parse_concept_name('us-gaap_Assets')
        ('us-gaap', 'Assets')
        
        >>> parse_concept_name('Assets')
        ('', 'Assets')
    """
    if '_' in concept:
        parts = concept.split('_', 1)
        return parts[0], parts[1]
    return '', concept


def normalize_concept_name(concept: str) -> str:
    """
    Normalize a concept name for consistent lookup.
    
    Handles variations in how concepts might be referenced:
        - Strips whitespace
        - Handles both underscore and colon separators
    
    Args:
        concept: Raw concept name
    
    Returns:
        Normalized concept name using underscore separator
    
    Examples:
        >>> normalize_concept_name('us-gaap:Assets')
        'us-gaap_Assets'
        
        >>> normalize_concept_name('  us-gaap_Assets  ')
        'us-gaap_Assets'
    """
    concept = concept.strip()
    # Some systems use colon instead of underscore
    if ':' in concept and '_' not in concept:
        concept = concept.replace(':', '_', 1)
    return concept


# Regex for matching concept patterns
_CONCEPT_PATTERN = re.compile(
    r'^(?:(?P<prefix>[a-zA-Z][a-zA-Z0-9-]*)_)?(?P<name>[a-zA-Z][a-zA-Z0-9]*)$'
)


def is_valid_concept_name(concept: str) -> bool:
    """
    Check if a string is a valid XBRL concept name.
    
    Valid patterns:
        - "Assets" (no prefix)
        - "us-gaap_Assets" (with prefix)
    
    Args:
        concept: String to validate
    
    Returns:
        True if valid concept name pattern
    """
    return _CONCEPT_PATTERN.match(concept) is not None