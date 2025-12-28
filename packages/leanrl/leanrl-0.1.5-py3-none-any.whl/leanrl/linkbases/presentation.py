"""
Presentation Linkbase Parser

Extract hierarchical display relationships from XBRL presentation linkbases.
"""

from typing import Dict, List, Set
import xml.etree.ElementTree as ET

from ..core.namespaces import qname, ArcRoles
from ..utils import extract_concept_from_href
from .hierarchy import ConceptNode, ConceptTree


def parse_presentation_linkbase(xml_file: str) -> ConceptTree:
    """
    Parse a presentation linkbase and build a concept hierarchy tree.
    
    Presentation linkbases use parent-child arcs to define how
    concepts should be displayed hierarchically in reports.
    
    Args:
        xml_file: Path to the presentation linkbase XML file
    
    Returns:
        ConceptTree with the parsed hierarchy
    
    Examples:
        >>> tree = parse_presentation_linkbase('us-gaap-stm-soi-pre-2020.xml')
        >>> 
        >>> # Get display hierarchy
        >>> tree.get_children('us-gaap_IncomeStatementAbstract')
        >>> 
        >>> # Print tree
        >>> print(tree.print_tree())
    """
    # Pre-compute qualified names
    TAG_LOC = qname('link', 'loc')
    TAG_ARC = qname('link', 'presentationArc')
    
    ATTR_LABEL = qname('xlink', 'label')
    ATTR_HREF = qname('xlink', 'href')
    ATTR_ARCROLE = qname('xlink', 'arcrole')
    ATTR_FROM = qname('xlink', 'from')
    ATTR_TO = qname('xlink', 'to')
    
    # Storage
    loc_map: Dict[str, str] = {}
    arcs: List[tuple[str, str, float]] = []
    
    context = ET.iterparse(xml_file, events=('end',))
    
    for event, elem in context:
        tag = elem.tag
        
        if tag == TAG_LOC:
            label_id = elem.get(ATTR_LABEL)
            href = elem.get(ATTR_HREF)
            if label_id and href:
                loc_map[label_id] = extract_concept_from_href(href)
        
        elif tag == TAG_ARC:
            # Presentation linkbases use parent-child arcrole
            arc_role = elem.get(ATTR_ARCROLE)
            if arc_role == ArcRoles.PARENT_CHILD:
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
        
        if parent_concept not in tree.nodes:
            tree.nodes[parent_concept] = ConceptNode(concept=parent_concept)
        
        if child_concept not in tree.nodes:
            tree.nodes[child_concept] = ConceptNode(concept=child_concept)
        
        tree.nodes[child_concept].parent = parent_concept
        tree.nodes[child_concept].order = order
        
        if child_concept not in tree.nodes[parent_concept].children:
            tree.nodes[parent_concept].children.append(child_concept)
        
        has_parent.add(child_concept)
    
    for concept in tree.nodes:
        if concept not in has_parent:
            tree.roots.append(concept)
    
    tree.roots.sort(key=lambda c: tree.nodes[c].order if c in tree.nodes else 0)
    
    def _set_depth(concept: str, depth: int):
        if concept in tree.nodes:
            tree.nodes[concept].depth = depth
            for child in tree.nodes[concept].children:
                _set_depth(child, depth + 1)
    
    for root in tree.roots:
        _set_depth(root, 0)
    
    return tree