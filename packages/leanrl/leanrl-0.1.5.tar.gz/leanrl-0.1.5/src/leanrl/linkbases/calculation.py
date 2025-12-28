"""
Calculation Linkbase Parser

Extract calculation relationships from XBRL calculation linkbases.
Calculation linkbases define summation relationships with weights.
"""

from typing import Dict, List, Set, Any
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET

from ..core.namespaces import qname, ArcRoles
from ..utils import extract_concept_from_href


@dataclass
class CalculationRelationship:
    """
    A single calculation relationship (parent sums children).
    
    Attributes:
        parent: The summing concept (e.g., 'us-gaap_OperatingExpenses')
        child: A contributing concept (e.g., 'us-gaap_ResearchAndDevelopmentExpense')
        weight: 1.0 (adds) or -1.0 (subtracts)
        order: Sort order among siblings
    """
    parent: str
    child: str
    weight: float = 1.0
    order: float = 0.0
    
    def __repr__(self) -> str:
        sign = '+' if self.weight >= 0 else '-'
        return f"{self.parent} {sign}= {self.child}"


@dataclass
class CalculationNode:
    """
    A node in the calculation tree.
    
    Attributes:
        concept: The concept name
        parent: Parent concept (the sum)
        weight: Weight in parent's calculation (1.0 or -1.0)
        children: List of (child_concept, weight) tuples
        order: Sort order among siblings
    """
    concept: str
    parent: str | None = None
    weight: float = 1.0
    children: List[tuple[str, float]] = field(default_factory=list)
    order: float = 0.0


@dataclass
class CalculationTree:
    """
    A tree structure representing calculation relationships.
    
    In a calculation tree:
    - Parent = Sum of (children * weights)
    - Weight is typically 1.0 (add) or -1.0 (subtract)
    
    Example:
        NetIncome = Revenues * 1.0 + Expenses * (-1.0)
        OperatingExpenses = R&D * 1.0 + SG&A * 1.0 + D&A * 1.0
    """
    nodes: Dict[str, CalculationNode] = field(default_factory=dict)
    roots: List[str] = field(default_factory=list)
    
    def __contains__(self, concept: str) -> bool:
        """Check if a concept exists in the tree."""
        return concept in self.nodes
    
    def __len__(self) -> int:
        """Return the number of concepts in the tree."""
        return len(self.nodes)
    
    def get(self, concept: str) -> CalculationNode | None:
        """Get the node for a concept, or None if not found."""
        return self.nodes.get(concept)
    
    def get_parent(self, concept: str) -> str | None:
        """Get the parent (sum) that this concept contributes to."""
        if concept in self.nodes:
            return self.nodes[concept].parent
        return None
    
    def get_weight(self, concept: str) -> float | None:
        """Get the weight of this concept in its parent's calculation."""
        if concept in self.nodes:
            return self.nodes[concept].weight
        return None
    
    def get_children(self, concept: str) -> List[tuple[str, float]]:
        """
        Get children (components) of a concept with their weights.
        
        Returns:
            List of (child_concept, weight) tuples, sorted by order.
            Empty list if concept not found or has no children.
        """
        if concept in self.nodes:
            children = self.nodes[concept].children
            # Sort by order
            return sorted(
                children,
                key=lambda c: self.nodes[c[0]].order if c[0] in self.nodes else 0
            )
        return []
    
    def get_components(self, concept: str) -> Dict[str, float] | None:
        """
        Get the calculation components as a dict.
        
        Returns:
            Dict mapping child concepts to weights.
            None if concept not found.
            
        Example:
            >>> tree.get_components('us-gaap_NetIncomeLoss')
            {'us-gaap_Revenues': 1.0, 'us-gaap_OperatingExpenses': -1.0}
        """
        if concept not in self.nodes:
            return None
        
        return {child: weight for child, weight in self.nodes[concept].children}
    
    def get_formula(self, concept: str) -> str | None:
        """
        Get a human-readable formula for a calculation.
        
        Returns:
            String formula like "A = B + C - D"
            None if concept not found or has no children.
        """
        if concept not in self.nodes:
            return None
        
        children = self.get_children(concept)
        if not children:
            return None
        
        parts = []
        for i, (child, weight) in enumerate(children):
            # Simplify concept names
            short_name = child.split('_')[-1] if '_' in child else child
            
            if i == 0:
                if weight < 0:
                    parts.append(f"-{short_name}")
                else:
                    parts.append(short_name)
            else:
                if weight < 0:
                    parts.append(f"- {short_name}")
                else:
                    parts.append(f"+ {short_name}")
        
        parent_short = concept.split('_')[-1] if '_' in concept else concept
        return f"{parent_short} = {' '.join(parts)}"
    
    def validate_calculation(
        self, 
        concept: str, 
        values: Dict[str, float]
    ) -> tuple[bool, float, float] | None:
        """
        Validate a calculation given fact values.
        
        Args:
            concept: The parent (sum) concept
            values: Dict of concept -> numeric value
        
        Returns:
            Tuple of (is_valid, expected_sum, actual_value) or None if can't validate.
            
        Example:
            >>> values = {
            ...     'us-gaap_NetIncomeLoss': 100,
            ...     'us-gaap_Revenues': 500,
            ...     'us-gaap_OperatingExpenses': 400,
            ... }
            >>> tree.validate_calculation('us-gaap_NetIncomeLoss', values)
            (True, 100.0, 100.0)
        """
        if concept not in self.nodes:
            return None
        
        children = self.get_children(concept)
        if not children:
            return None
        
        # Calculate expected sum
        expected = 0.0
        for child, weight in children:
            if child not in values:
                return None  # Can't validate without all values
            expected += values[child] * weight
        
        # Get actual value
        if concept not in values:
            return None
        
        actual = values[concept]
        is_valid = abs(expected - actual) < 0.01  # Allow small rounding diff
        
        return (is_valid, expected, actual)
    
    def print_tree(self, concept: str | None = None, indent: str = "  ") -> str:
        """
        Print the calculation tree with weights.
        
        Args:
            concept: Starting node (None = print all roots)
            indent: Indentation string
        """
        lines = []
        
        def _print_node(c: str, level: int, weight: float = 1.0):
            prefix = indent * level
            sign = '+' if weight >= 0 else '-'
            weight_str = f" ({sign}{abs(weight):.1f})" if level > 0 else ""
            lines.append(f"{prefix}{c}{weight_str}")
            
            for child, w in self.get_children(c):
                _print_node(child, level + 1, w)
        
        if concept:
            if concept in self.nodes:
                _print_node(concept, 0)
            else:
                return f"<concept '{concept}' not found>"
        else:
            for r in self.roots:
                _print_node(r, 0)
        
        return "\n".join(lines)


def parse_calculation_linkbase(xml_file: str) -> CalculationTree:
    """
    Parse a calculation linkbase and build a calculation tree.
    
    Calculation linkbases define summation relationships:
    - Parent concept = Sum of (child * weight)
    - Weight is 1.0 (add) or -1.0 (subtract)
    
    Args:
        xml_file: Path to the calculation linkbase XML file
    
    Returns:
        CalculationTree with the parsed relationships
    
    Examples:
        >>> tree = parse_calculation_linkbase('us-gaap-stm-soi-cal-2020.xml')
        >>> 
        >>> # Get components of a total
        >>> tree.get_components('us-gaap_OperatingCostsAndExpenses')
        {'us-gaap_ResearchAndDevelopmentExpense': 1.0,
         'us-gaap_SellingGeneralAndAdministrativeExpense': 1.0, ...}
        >>> 
        >>> # Get human-readable formula
        >>> tree.get_formula('us-gaap_NetIncomeLoss')
        'NetIncomeLoss = Revenues - CostOfRevenue - OperatingExpenses'
        >>> 
        >>> # Validate a calculation
        >>> values = {'us-gaap_NetIncome': 100, 'us-gaap_Revenue': 500, ...}
        >>> tree.validate_calculation('us-gaap_NetIncome', values)
    """
    # Pre-compute qualified names
    TAG_LOC = qname('link', 'loc')
    TAG_ARC = qname('link', 'calculationArc')
    
    ATTR_LABEL = qname('xlink', 'label')
    ATTR_HREF = qname('xlink', 'href')
    ATTR_ARCROLE = qname('xlink', 'arcrole')
    ATTR_FROM = qname('xlink', 'from')
    ATTR_TO = qname('xlink', 'to')
    
    # Storage
    loc_map: Dict[str, str] = {}  # label_id -> concept_name
    arcs: List[tuple[str, str, float, float]] = []  # (parent, child, weight, order)
    
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
            if arc_role == ArcRoles.SUMMATION_ITEM:
                from_id = elem.get(ATTR_FROM)
                to_id = elem.get(ATTR_TO)
                
                weight_str = elem.get('weight', '1.0')
                order_str = elem.get('order', '0')
                
                try:
                    weight = float(weight_str)
                except ValueError:
                    weight = 1.0
                
                try:
                    order = float(order_str)
                except ValueError:
                    order = 0.0
                
                if from_id and to_id:
                    arcs.append((from_id, to_id, weight, order))
        
        elem.clear()
    
    # Build the tree
    tree = CalculationTree()
    has_parent: Set[str] = set()
    
    for from_label, to_label, weight, order in arcs:
        if from_label not in loc_map or to_label not in loc_map:
            continue
        
        parent_concept = loc_map[from_label]
        child_concept = loc_map[to_label]
        
        # Ensure parent node exists
        if parent_concept not in tree.nodes:
            tree.nodes[parent_concept] = CalculationNode(concept=parent_concept)
        
        # Ensure child node exists
        if child_concept not in tree.nodes:
            tree.nodes[child_concept] = CalculationNode(concept=child_concept)
        
        # Set relationship
        tree.nodes[child_concept].parent = parent_concept
        tree.nodes[child_concept].weight = weight
        tree.nodes[child_concept].order = order
        
        # Add to parent's children
        child_tuple = (child_concept, weight)
        if child_tuple not in tree.nodes[parent_concept].children:
            tree.nodes[parent_concept].children.append(child_tuple)
        
        has_parent.add(child_concept)
    
    # Find roots (concepts that are sums but not components of anything else)
    for concept in tree.nodes:
        if concept not in has_parent:
            tree.roots.append(concept)
    
    # Sort roots by order
    tree.roots.sort(key=lambda c: tree.nodes[c].order if c in tree.nodes else 0)
    
    return tree


def get_calculation_dataframe(tree: CalculationTree):
    """
    Convert a CalculationTree to a pandas DataFrame.
    
    Returns DataFrame with columns:
    - parent: Parent (sum) concept
    - child: Child (component) concept
    - weight: Weight (1.0 or -1.0)
    - order: Sort order
    
    Example:
        >>> tree = parse_calculation_linkbase('cal.xml')
        >>> df = get_calculation_dataframe(tree)
        >>> df[df['parent'].str.contains('OperatingExpenses')]
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for get_calculation_dataframe()")
    
    rows = []
    for concept, node in tree.nodes.items():
        for child, weight in node.children:
            child_node = tree.nodes.get(child)
            rows.append({
                'parent': concept,
                'child': child,
                'weight': weight,
                'order': child_node.order if child_node else 0,
            })
    
    return pd.DataFrame(rows)