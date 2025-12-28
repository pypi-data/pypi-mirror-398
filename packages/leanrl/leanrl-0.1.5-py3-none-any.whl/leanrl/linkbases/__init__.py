"""
XBRL Linkbase Parsers

Parsers for the various XBRL linkbase types:
- Label linkbase: Human-readable labels and documentation
- Reference linkbase: Links to authoritative literature
- Definition linkbase: Hierarchical/dimensional relationships
- Presentation linkbase: Display hierarchy
- Calculation linkbase: Mathematical summation relationships
"""

# Shared hierarchy structures
from .hierarchy import (
    ConceptNode,
    ConceptTree,
    get_hierarchy_dataframe,
)

# Individual linkbase parsers
from .label import parse_label_linkbase, parse_all_labels
from .reference import (
    Reference,
    parse_reference_linkbase,
    parse_reference_linkbase_flat,
)
from .definition import parse_definition_linkbase
from .presentation import parse_presentation_linkbase
from .calculation import (
    CalculationRelationship,
    CalculationNode,
    CalculationTree,
    parse_calculation_linkbase,
    get_calculation_dataframe,
)

__all__ = [
    # Shared hierarchy structures
    'ConceptNode',
    'ConceptTree',
    'get_hierarchy_dataframe',
    # Label
    'parse_label_linkbase',
    'parse_all_labels',
    # Reference
    'Reference',
    'parse_reference_linkbase',
    'parse_reference_linkbase_flat',
    # Definition
    'parse_definition_linkbase',
    # Presentation
    'parse_presentation_linkbase',
    # Calculation
    'CalculationRelationship',
    'CalculationNode',
    'CalculationTree',
    'parse_calculation_linkbase',
    'get_calculation_dataframe',
]