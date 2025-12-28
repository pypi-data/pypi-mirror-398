"""
Definition and Presentation Linkbase Parser

Extract hierarchical relationships from XBRL definition and presentation linkbases.
These linkbases define parent-child relationships forming tree structures.
"""

from typing import Dict, List, Set, Any
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
import pandas as pd
from ..core.namespaces import qname, ArcRoles
from ..utils import extract_concept_from_href



@dataclass
class ConceptNode:
    """
    A node in the concept hierarchy tree.
    
    Attributes:
        concept: The concept name (e.g., 'us-gaap_Assets')
        parent: Parent concept name (None if root)
        children: List of child concept names
        order: Numeric order for sorting siblings
        depth: Depth in the tree (0 = root)
    """
    concept: str
    parent: str | None = None
    children: List[str] = field(default_factory=list)
    order: float = 0.0
    depth: int = 0
    
    def __repr__(self) -> str:
        return f"ConceptNode({self.concept}, children={len(self.children)})"


@dataclass 
class ConceptTree:
    """
    A tree structure representing concept hierarchies.
    
    Provides methods for traversing the tree, finding ancestors,
    descendants, and paths between concepts.
    """
    nodes: Dict[str, ConceptNode] = field(default_factory=dict)
    roots: List[str] = field(default_factory=list)
    
    def get_parent(self, concept: str) -> str | None:
        """Get the parent of a concept."""
        if concept in self.nodes:
            return self.nodes[concept].parent
        return None
    
    def get_children(self, concept: str) -> List[str]:
        """Get children of a concept, sorted by order."""
        if concept in self.nodes:
            children = self.nodes[concept].children
            # Sort by order
            return sorted(children, key=lambda c: self.nodes[c].order if c in self.nodes else 0)
        return []
    
    def get_ancestors(self, concept: str) -> List[str]:
        """
        Get all ancestors from concept to root.
        
        Returns list from immediate parent to root.
        Example: ['Parent', 'Grandparent', 'Root']
        """
        ancestors = []
        current = concept
        seen = set()  # Prevent infinite loops
        
        while current in self.nodes and current not in seen:
            seen.add(current)
            parent = self.nodes[current].parent
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
        
        return ancestors
    
    def get_ancestor_path(self, concept: str) -> List[str]:
        """
        Get path from root to concept.
        
        Returns list from root to concept (inclusive).
        Example: ['Root', 'Grandparent', 'Parent', 'Concept']
        """
        ancestors = self.get_ancestors(concept)
        return list(reversed(ancestors)) + [concept]
    
    def get_descendants(self, concept: str, max_depth: int | None = None) -> List[str]:
        """
        Get all descendants of a concept.
        
        Args:
            concept: Starting concept
            max_depth: Maximum depth to traverse (None = unlimited)
        
        Returns:
            List of all descendant concepts (breadth-first order)
        """
        descendants = []
        queue = [(c, 1) for c in self.get_children(concept)]
        
        while queue:
            child, depth = queue.pop(0)
            if max_depth is not None and depth > max_depth:
                continue
            descendants.append(child)
            for grandchild in self.get_children(child):
                queue.append((grandchild, depth + 1))
        
        return descendants
    
    def get_siblings(self, concept: str) -> List[str]:
        """Get siblings of a concept (same parent)."""
        parent = self.get_parent(concept)
        if parent:
            return [c for c in self.get_children(parent) if c != concept]
        return []
    
    def get_depth(self, concept: str) -> int:
        """Get depth of a concept in the tree."""
        if concept in self.nodes:
            return self.nodes[concept].depth
        return -1
    
    def find_common_ancestor(self, concept1: str, concept2: str) -> str | None:
        """Find the lowest common ancestor of two concepts."""
        ancestors1 = set(self.get_ancestors(concept1))
        ancestors1.add(concept1)
        
        current = concept2
        while current:
            if current in ancestors1:
                return current
            current = self.get_parent(current)
        
        return None
    
    def print_tree(self, root: str | None = None, indent: str = "  ") -> str:
        """
        Print the tree structure as a string.
        
        Args:
            root: Starting node (None = print all roots)
            indent: Indentation string
        
        Returns:
            String representation of the tree
        """
        lines = []
        
        def _print_node(concept: str, level: int):
            prefix = indent * level
            lines.append(f"{prefix}{concept}")
            for child in self.get_children(concept):
                _print_node(child, level + 1)
        
        if root:
            _print_node(root, 0)
        else:
            for r in self.roots:
                _print_node(r, 0)
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tree to nested dictionary."""
        def _node_to_dict(concept: str) -> Dict[str, Any]:
            return {
                'concept': concept,
                'children': [_node_to_dict(c) for c in self.get_children(concept)]
            }
        
        return {
            'roots': [_node_to_dict(r) for r in self.roots]
        }


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
    
    tags = {TAG_LOC, TAG_ARC}
    
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
    tree = ConceptTree()
    
    # Track which concepts have parents
    has_parent: Set[str] = set()
    
    # First pass: create all nodes and relationships
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


def parse_presentation_linkbase(
    xml_file: str,
) -> ConceptTree:
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
    
    tags = {TAG_LOC, TAG_ARC}
    
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
    
    # Build the tree (same logic as definition)
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


def get_hierarchy_dataframe(tree: ConceptTree):
    """
    Convert a ConceptTree to a pandas DataFrame.
    
    Returns DataFrame with columns:
    - concept: Concept name
    - parent: Parent concept name
    - depth: Depth in tree
    - order: Sort order among siblings
    - path: Full path from root as string
    
    Example:
        >>> tree = parse_definition_linkbase('def.xml')
        >>> df = get_hierarchy_dataframe(tree)
        >>> df[df['concept'].str.contains('Research')]
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for get_hierarchy_dataframe()")
    
    rows = []
    for concept, node in tree.nodes.items():
        path = ' > '.join(tree.get_ancestor_path(concept))
        rows.append({
            'concept': concept,
            'parent': node.parent,
            'depth': node.depth,
            'order': node.order,
            'path': path,
        })
    
    return pd.DataFrame(rows)