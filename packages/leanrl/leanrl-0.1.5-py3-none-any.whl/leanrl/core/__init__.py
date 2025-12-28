"""
EasyRL Core Module

Provides base classes and constants for XBRL processing.
"""

from .namespaces import (
    # Namespace class and collection
    Namespace,
    Namespaces,
    # qname helper
    qname,
    # Convenience constants
    NS_LINK,
    NS_XLINK,
    NS_XBRLI,
    NS_XBRLDI,
    NS_XBRLDT,
    NS_XS,
    NS_XSD,
    NS_XSI,
    NS_US_GAAP,
    NS_DEI,
    NS_SRT,
    NS_IFRS,
    NS_ISO4217,
    NS_XML,
    # Role constants
    Roles,
    ArcRoles,
)

from .streaming import (
    stream_xml,
    stream_xml_with_ancestors,
)

__all__ = [
    # Namespaces
    'Namespace',
    'Namespaces',
    'qname',
    'NS_LINK',
    'NS_XLINK',
    'NS_XBRLI',
    'NS_XBRLDI',
    'NS_XBRLDT',
    'NS_XS',
    'NS_XSD',
    'NS_XSI',
    'NS_US_GAAP',
    'NS_DEI',
    'NS_SRT',
    'NS_IFRS',
    'NS_ISO4217',
    'NS_XML',
    'Roles',
    'ArcRoles',
    # Streaming
    'stream_xml',
    'stream_xml_with_ancestors',
]