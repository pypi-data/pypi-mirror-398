"""
XBRL Linkbase Parsers

Parsers for the various XBRL linkbase types:
- Label linkbase: Human-readable labels and documentation
- Reference linkbase: Links to authoritative literature
- Presentation linkbase: Hierarchical display structure
- Calculation linkbase: Mathematical relationships
- Definition linkbase: Dimensional relationships
"""

from .label import parse_label_linkbase, parse_all_labels
from .reference import (
    Reference,
    parse_reference_linkbase,
    parse_reference_linkbase_flat,
)
from .definition import (
    ConceptNode,
    ConceptTree,
    parse_definition_linkbase,
    parse_presentation_linkbase,
    get_hierarchy_dataframe,
)

__all__ = [
    # Label
    'parse_label_linkbase',
    'parse_all_labels',
    # Reference
    'Reference',
    'parse_reference_linkbase',
    'parse_reference_linkbase_flat',
    # Definition
    'ConceptNode',
    'ConceptTree',
    'parse_definition_linkbase',
    'parse_presentation_linkbase',
    'get_hierarchy_dataframe',
]