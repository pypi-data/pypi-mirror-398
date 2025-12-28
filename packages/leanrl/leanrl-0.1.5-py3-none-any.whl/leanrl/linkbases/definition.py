"""
Definition Linkbase Parser

Extract hierarchical relationships from XBRL definition linkbases.
"""

from typing import Dict, List, Set
import xml.etree.ElementTree as ET

from ..core.namespaces import qname, ArcRoles
from ..utils import extract_concept_from_href
from .hierarchy import ConceptNode, ConceptTree


def parse_definition_linkbase(
    xml_file: str,
    arcrole: str | None = None,
) -> ConceptTree:
    """
    Parse a definition linkbase and build a concept hierarchy tree.
    
    Definition linkbases use arcs like:
    - domain-member: Hierarchical relationships
    - dimension-domain: Dimension to domain
    - hypercube-dimension: Table to dimension
    
    Args:
        xml_file: Path to the definition linkbase XML file
        arcrole: Optional arc role to filter by. If None, uses domain-member.
                Common values:
                - ArcRoles.DOMAIN_MEMBER (default)
                - ArcRoles.DIMENSION_DOMAIN
                - ArcRoles.HYPERCUBE_DIMENSION
    
    Returns:
        ConceptTree with the parsed hierarchy
    
    Examples:
        >>> tree = parse_definition_linkbase('us-gaap-stm-soi-def-2020.xml')
        >>> 
        >>> # Get parent
        >>> tree.get_parent('us-gaap_ResearchAndDevelopmentExpense')
        'us-gaap_ResearchAndDevelopmentExpenseAbstract'
        >>> 
        >>> # Get full ancestor path
        >>> tree.get_ancestors('us-gaap_ResearchAndDevelopmentExpense')
        ['us-gaap_ResearchAndDevelopmentExpenseAbstract', 
         'us-gaap_OperatingCostsAndExpensesAbstract', ...]
        >>> 
        >>> # Print tree
        >>> print(tree.print_tree())
    """
    if arcrole is None:
        arcrole = ArcRoles.DOMAIN_MEMBER
    
    # Pre-compute qualified names
    TAG_LOC = qname('link', 'loc')
    TAG_ARC = qname('link', 'definitionArc')
    
    ATTR_LABEL = qname('xlink', 'label')
    ATTR_HREF = qname('xlink', 'href')
    ATTR_ARCROLE = qname('xlink', 'arcrole')
    ATTR_FROM = qname('xlink', 'from')
    ATTR_TO = qname('xlink', 'to')
    
    # Storage
    loc_map: Dict[str, str] = {}  # label_id -> concept_name
    arcs: List[tuple[str, str, float]] = []  # (parent_label, child_label, order)
    
    context = ET.iterparse(xml_file, events=('end',))
    
    for event, elem in context:
        tag = elem.tag
        
        if tag == TAG_LOC:
            label_id = elem.get(ATTR_LABEL)
            href = elem.get(ATTR_HREF)
            if label_id and href:
                loc_map[label_id] = extract_concept_from_href(href)
        
        elif tag == TAG_ARC:
            arc_role = elem.get(ATTR_ARCROLE)
            if arc_role == arcrole:
                from_id = elem.get(ATTR_FROM)
                to_id = elem.get(ATTR_TO)
                order_str = elem.get('order', '0')
                try:
                    order = float(order_str)
                except ValueError:
                    order = 0.0
                
                if from_id and to_id:
                    arcs.append((from_id, to_id, order))
        
        elem.clear()
    
    # Build the tree
    return _build_tree(loc_map, arcs)


def _build_tree(
    loc_map: Dict[str, str],
    arcs: List[tuple[str, str, float]]
) -> ConceptTree:
    """Build a ConceptTree from locators and arcs."""
    tree = ConceptTree()
    has_parent: Set[str] = set()
    
    for from_label, to_label, order in arcs:
        if from_label not in loc_map or to_label not in loc_map:
            continue
        
        parent_concept = loc_map[from_label]
        child_concept = loc_map[to_label]
        
        # Ensure parent node exists
        if parent_concept not in tree.nodes:
            tree.nodes[parent_concept] = ConceptNode(concept=parent_concept)
        
        # Ensure child node exists
        if child_concept not in tree.nodes:
            tree.nodes[child_concept] = ConceptNode(concept=child_concept)
        
        # Set relationship
        tree.nodes[child_concept].parent = parent_concept
        tree.nodes[child_concept].order = order
        
        if child_concept not in tree.nodes[parent_concept].children:
            tree.nodes[parent_concept].children.append(child_concept)
        
        has_parent.add(child_concept)
    
    # Find roots (nodes without parents)
    for concept in tree.nodes:
        if concept not in has_parent:
            tree.roots.append(concept)
    
    # Sort roots by order if available
    tree.roots.sort(key=lambda c: tree.nodes[c].order if c in tree.nodes else 0)
    
    # Calculate depths
    def _set_depth(concept: str, depth: int):
        if concept in tree.nodes:
            tree.nodes[concept].depth = depth
            for child in tree.nodes[concept].children:
                _set_depth(child, depth + 1)
    
    for root in tree.roots:
        _set_depth(root, 0)
    
    return tree