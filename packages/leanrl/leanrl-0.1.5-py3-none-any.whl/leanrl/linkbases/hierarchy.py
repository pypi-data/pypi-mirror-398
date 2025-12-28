"""
Hierarchy Data Structures

Shared data structures for hierarchical linkbases (definition, presentation).
These linkbases define parent-child relationships forming tree structures.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


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
    
    Used by both definition and presentation linkbases.
    """
    nodes: Dict[str, ConceptNode] = field(default_factory=dict)
    roots: List[str] = field(default_factory=list)
    
    def __contains__(self, concept: str) -> bool:
        """Check if a concept exists in the tree."""
        return concept in self.nodes
    
    def __len__(self) -> int:
        """Return the number of concepts in the tree."""
        return len(self.nodes)
    
    def get(self, concept: str) -> ConceptNode | None:
        """Get the node for a concept, or None if not found."""
        return self.nodes.get(concept)
    
    def get_parent(self, concept: str) -> str | None:
        """
        Get the parent of a concept.
        
        Returns None if concept not found or has no parent (is root).
        """
        if concept in self.nodes:
            return self.nodes[concept].parent
        return None
    
    def get_children(self, concept: str) -> List[str]:
        """
        Get children of a concept, sorted by order.
        
        Returns empty list if concept not found or has no children.
        """
        if concept in self.nodes:
            children = self.nodes[concept].children
            # Sort by order
            return sorted(children, key=lambda c: self.nodes[c].order if c in self.nodes else 0)
        return []
    
    def get_ancestors(self, concept: str) -> List[str] | None:
        """
        Get all ancestors from concept to root.
        
        Returns:
            List from immediate parent to root, e.g. ['Parent', 'Grandparent', 'Root']
            None if concept is not in the tree
            Empty list [] if concept is a root (has no ancestors)
        """
        if concept not in self.nodes:
            return None
        
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
    
    def get_ancestor_path(self, concept: str) -> List[str] | None:
        """
        Get path from root to concept.
        
        Returns:
            List from root to concept (inclusive), e.g. ['Root', 'Grandparent', 'Parent', 'Concept']
            None if concept is not in the tree
        """
        if concept not in self.nodes:
            return None
        
        ancestors = self.get_ancestors(concept)
        if ancestors is None:
            return None
        
        return list(reversed(ancestors)) + [concept]
    
    def get_descendants(self, concept: str, max_depth: int | None = None) -> List[str] | None:
        """
        Get all descendants of a concept.
        
        Args:
            concept: Starting concept
            max_depth: Maximum depth to traverse (None = unlimited)
        
        Returns:
            List of all descendant concepts (breadth-first order)
            None if concept is not in the tree
            Empty list [] if concept has no descendants
        """
        if concept not in self.nodes:
            return None
        
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
    
    def get_siblings(self, concept: str) -> List[str] | None:
        """
        Get siblings of a concept (same parent).
        
        Returns:
            List of sibling concepts (excluding self)
            None if concept is not in the tree
            Empty list [] if concept has no siblings
        """
        if concept not in self.nodes:
            return None
        
        parent = self.get_parent(concept)
        if parent:
            return [c for c in self.get_children(parent) if c != concept]
        return []
    
    def get_depth(self, concept: str) -> int | None:
        """
        Get depth of a concept in the tree.
        
        Returns:
            Depth (0 = root)
            None if concept is not in the tree
        """
        if concept in self.nodes:
            return self.nodes[concept].depth
        return None
    
    def find_common_ancestor(self, concept1: str, concept2: str) -> str | None:
        """
        Find the lowest common ancestor of two concepts.
        
        Returns None if either concept is not in the tree or no common ancestor exists.
        """
        if concept1 not in self.nodes or concept2 not in self.nodes:
            return None
        
        ancestors1 = set(self.get_ancestors(concept1) or [])
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
            if root in self.nodes:
                _print_node(root, 0)
            else:
                return f"<concept '{root}' not found>"
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
        path = ' > '.join(tree.get_ancestor_path(concept) or [concept])
        rows.append({
            'concept': concept,
            'parent': node.parent,
            'depth': node.depth,
            'order': node.order,
            'path': path,
        })
    
    return pd.DataFrame(rows)