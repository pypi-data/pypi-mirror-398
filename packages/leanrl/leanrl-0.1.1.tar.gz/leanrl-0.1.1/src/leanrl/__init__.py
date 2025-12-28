"""
EasyRL - Easy (non-XML) approach to process XBRL

A lightweight, memory-efficient Python library for extracting
specific information from XBRL filings and taxonomies.
"""

__version__ = "0.1.0"

# Core: Namespaces and streaming
from .core.namespaces import (
    Namespaces,
    Roles,
    ArcRoles,
    qname,
    NS_LINK,
    NS_XLINK,
    NS_XBRLI,
)
from .core.streaming import stream_xml

# Linkbase parsers
from .linkbases import (
    parse_label_linkbase,
    parse_all_labels,
    Reference,
    parse_reference_linkbase,
    parse_reference_linkbase_flat,
    ConceptNode,
    ConceptTree,
    parse_definition_linkbase,
    parse_presentation_linkbase,
    get_hierarchy_dataframe,
)

# Utilities
from .utils import extract_concept_from_href

__all__ = [
    '__version__',
    # Core
    'Namespaces',
    'Roles',
    'ArcRoles',
    'qname',
    'NS_LINK',
    'NS_XLINK',
    'NS_XBRLI',
    'stream_xml',
    # Linkbases - Label
    'parse_label_linkbase',
    'parse_all_labels',
    # Linkbases - Reference
    'Reference',
    'parse_reference_linkbase',
    'parse_reference_linkbase_flat',
    # Linkbases - Definition/Presentation
    'ConceptNode',
    'ConceptTree',
    'parse_definition_linkbase',
    'parse_presentation_linkbase',
    'get_hierarchy_dataframe',
    # Utils
    'extract_concept_from_href',
]