"""
Label Linkbase Parser

Extract labels and documentation from XBRL label linkbase files.
"""

from typing import Dict
from ..core.namespaces import qname, Roles
from ..core.streaming import stream_xml
from ..utils import extract_concept_from_href


def parse_label_linkbase(
    xml_file: str,
    role: str = Roles.DOCUMENTATION,
) -> Dict[str, str]:
    """
    Extract labels from a label linkbase file.
    
    Parses an XBRL label linkbase and returns a mapping of concept names
    to their label text for the specified role.
    
    Args:
        xml_file: Path to the label linkbase XML file
        role: The label role URI to extract. Defaults to documentation role.
              Common roles:
              - Roles.DOCUMENTATION: Detailed concept descriptions
              - Roles.LABEL: Standard display labels
              - Roles.TERSE_LABEL: Short labels
              - Roles.VERBOSE_LABEL: Extended labels
    
    Returns:
        Dict mapping concept names to label text.
        Example: {'us-gaap_Assets': 'Sum of the carrying amounts...'}
    
    Examples:
        >>> # Get documentation for all concepts
        >>> docs = parse_label_linkbase('us-gaap-doc-2023.xml')
        >>> print(docs.get('us-gaap_Assets'))
        
        >>> # Get display labels instead
        >>> from easyrl.core.namespaces import Roles
        >>> labels = parse_label_linkbase('us-gaap-lab-2023.xml', role=Roles.LABEL)
    """
    # Pre-compute qualified names for speed
    TAG_LOC = qname('link', 'loc')
    TAG_LABEL = qname('link', 'label')
    TAG_ARC = qname('link', 'labelArc')
    
    ATTR_LABEL = qname('xlink', 'label')
    ATTR_HREF = qname('xlink', 'href')
    ATTR_ROLE = qname('xlink', 'role')
    ATTR_FROM = qname('xlink', 'from')
    ATTR_TO = qname('xlink', 'to')
    
    # Storage
    loc_map: Dict[str, str] = {}    # label_id -> concept_name
    label_map: Dict[str, str] = {}  # label_id -> text
    arc_links: list[tuple[str, str]] = []  # (from_id, to_id)
    
    # Tags we care about
    tags = {TAG_LOC, TAG_LABEL, TAG_ARC}
    
    for tag, elem in stream_xml(xml_file, tags_of_interest=tags):
        
        if tag == TAG_LOC:
            label_id = elem.get(ATTR_LABEL)
            href = elem.get(ATTR_HREF)
            if label_id and href:
                loc_map[label_id] = extract_concept_from_href(href)
        
        elif tag == TAG_LABEL:
            elem_role = elem.get(ATTR_ROLE)
            label_id = elem.get(ATTR_LABEL)
            if elem_role == role and label_id:
                label_map[label_id] = elem.text or ''
        
        elif tag == TAG_ARC:
            from_id = elem.get(ATTR_FROM)
            to_id = elem.get(ATTR_TO)
            if from_id and to_id:
                arc_links.append((from_id, to_id))
    
    # Resolution Phase: join locators with labels via arcs
    return {
        loc_map[loc]: label_map[lbl]
        for loc, lbl in arc_links
        if loc in loc_map and lbl in label_map
    }


def parse_all_labels(xml_file: str) -> Dict[str, Dict[str, str]]:
    """
    Extract all label types from a label linkbase.
    
    Unlike parse_label_linkbase which extracts a single role,
    this function extracts all available label roles.
    
    Args:
        xml_file: Path to the label linkbase XML file
    
    Returns:
        Nested dict: {concept_name: {role: text, ...}, ...}
    
    Examples:
        >>> all_labels = parse_all_labels('us-gaap-lab-2023.xml')
        >>> concept = all_labels['us-gaap_Assets']
        >>> print(concept[Roles.LABEL])        # "Assets"
        >>> print(concept[Roles.DOCUMENTATION]) # "Sum of the carrying..."
    """
    TAG_LOC = qname('link', 'loc')
    TAG_LABEL = qname('link', 'label')
    TAG_ARC = qname('link', 'labelArc')
    
    ATTR_LABEL = qname('xlink', 'label')
    ATTR_HREF = qname('xlink', 'href')
    ATTR_ROLE = qname('xlink', 'role')
    ATTR_FROM = qname('xlink', 'from')
    ATTR_TO = qname('xlink', 'to')
    
    loc_map: Dict[str, str] = {}
    label_map: Dict[str, tuple[str, str]] = {}  # label_id -> (role, text)
    arc_links: list[tuple[str, str]] = []
    
    tags = {TAG_LOC, TAG_LABEL, TAG_ARC}
    
    for tag, elem in stream_xml(xml_file, tags_of_interest=tags):
        
        if tag == TAG_LOC:
            label_id = elem.get(ATTR_LABEL)
            href = elem.get(ATTR_HREF)
            if label_id and href:
                loc_map[label_id] = extract_concept_from_href(href)
        
        elif tag == TAG_LABEL:
            role = elem.get(ATTR_ROLE)
            label_id = elem.get(ATTR_LABEL)
            if role and label_id:
                label_map[label_id] = (role, elem.text or '')
        
        elif tag == TAG_ARC:
            from_id = elem.get(ATTR_FROM)
            to_id = elem.get(ATTR_TO)
            if from_id and to_id:
                arc_links.append((from_id, to_id))
    
    # Build nested result
    result: Dict[str, Dict[str, str]] = {}
    
    for loc_id, label_id in arc_links:
        if loc_id in loc_map and label_id in label_map:
            concept = loc_map[loc_id]
            role, text = label_map[label_id]
            
            if concept not in result:
                result[concept] = {}
            result[concept][role] = text
    
    return result