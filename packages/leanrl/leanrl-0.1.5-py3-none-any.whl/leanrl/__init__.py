"""
LeanRL - Lean (non-XML) approach to process XBRL

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
    # Label
    parse_label_linkbase,
    parse_all_labels,
    # Reference
    Reference,
    parse_reference_linkbase,
    parse_reference_linkbase_flat,
    # Definition / Presentation
    ConceptNode,
    ConceptTree,
    parse_definition_linkbase,
    parse_presentation_linkbase,
    get_hierarchy_dataframe,
    # Calculation
    CalculationRelationship,
    CalculationNode,
    CalculationTree,
    parse_calculation_linkbase,
    get_calculation_dataframe,
)

# Taxonomy schema parsers
from .taxonomy import (
    ConceptSchema,
    parse_schema,
    parse_schema_to_dict,
    get_concept_types,
    get_schema_dataframe,
    extract_concepts_from_schema,
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
    # Linkbases - Calculation
    'CalculationRelationship',
    'CalculationNode',
    'CalculationTree',
    'parse_calculation_linkbase',
    'get_calculation_dataframe',
    # Taxonomy Schema
    'ConceptSchema',
    'parse_schema',
    'parse_schema_to_dict',
    'get_concept_types',
    'get_schema_dataframe',
    'extract_concepts_from_schema',
    # Utils
    'extract_concept_from_href',
]