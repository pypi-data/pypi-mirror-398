"""
Reference Linkbase Parser

Extract references from XBRL reference linkbase files.
References link concepts to authoritative literature (FASB, SEC, IFRS, etc.)
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from ..core.namespaces import qname, Roles
from ..core.streaming import stream_xml
from ..utils import extract_concept_from_href


# Reference part namespace
NS_REF = '{http://www.xbrl.org/2006/ref}'


@dataclass
class Reference:
    """
    A single reference to authoritative literature.
    
    Attributes:
        role: The reference role URI (e.g., Roles.REFERENCE)
        parts: Dict of reference parts (Publisher, Name, Topic, Section, etc.)
    """
    role: str
    parts: Dict[str, str] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        publisher = self.parts.get('Publisher', '')
        name = self.parts.get('Name', '')
        topic = self.parts.get('Topic', '')
        section = self.parts.get('Section', '')
        return f"Reference({publisher} {name} Topic {topic} Section {section})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'role': self.role,
            **self.parts
        }
    
    def format_citation(self) -> str:
        """
        Format as a human-readable citation string.
        
        Example: "FASB ASC 210-10-S99-1"
        """
        parts = []
        
        # Publisher abbreviation
        publisher = self.parts.get('Publisher', '')
        if publisher:
            parts.append(publisher)
        
        # Name abbreviation
        name = self.parts.get('Name', '')
        if 'Codification' in name:
            parts.append('ASC')
        elif 'Regulation' in name:
            parts.append(name)
        elif name:
            parts.append(name)
        
        # Topic-SubTopic-Section-Paragraph
        topic = self.parts.get('Topic', '')
        subtopic = self.parts.get('SubTopic', '')
        section = self.parts.get('Section', '')
        paragraph = self.parts.get('Paragraph', '')
        
        ref_parts = []
        if topic:
            ref_parts.append(topic)
        if subtopic:
            ref_parts.append(subtopic)
        if section:
            ref_parts.append(section)
        if paragraph:
            ref_parts.append(paragraph)
        
        if ref_parts:
            parts.append('-'.join(ref_parts))
        
        return ' '.join(parts)


def parse_reference_linkbase(
    xml_file: str,
    role: str | None = None,
    ) -> Dict[str, List[Reference]]:
    """
    Extract references from a reference linkbase file.
    
    Reference linkbases link concepts to authoritative literature
    (FASB ASC, SEC Regulation S-X, IFRS standards, etc.)
    
    Unlike labels which contain text, references contain structured
    child elements like Publisher, Name, Topic, Section, Paragraph.
    
    Args:
        xml_file: Path to the reference linkbase XML file
        role: Optional role URI to filter by (e.g., Roles.REFERENCE).
              If None, returns all references.
    
    Returns:
        Dict mapping concept names to lists of Reference objects.
        A concept can have multiple references.
        Example: {
            'us-gaap_Assets': [Reference(...), Reference(...)],
            'us-gaap_Cash': [Reference(...)]
        }
    
    Examples:
        >>> refs = parse_reference_linkbase('us-gaap-ref-2023.xml')
        >>> for ref in refs.get('us-gaap_Assets', []):
        ...     print(ref.format_citation())
        FASB ASC 210-10-S99-1
        FASB ASC 210-10-45-1
        
        >>> # Filter by role
        >>> disclosure_refs = parse_reference_linkbase(
        ...     'us-gaap-ref-2023.xml',
        ...     role=Roles.DISCLOSURE_REF
        ... )
    """
    import xml.etree.ElementTree as ET
    
    # Pre-compute qualified names
    TAG_LOC = qname('link', 'loc')
    TAG_REFERENCE = qname('link', 'reference')
    TAG_ARC = qname('link', 'referenceArc')
    
    ATTR_LABEL = qname('xlink', 'label')
    ATTR_HREF = qname('xlink', 'href')
    ATTR_ROLE = qname('xlink', 'role')
    ATTR_FROM = qname('xlink', 'from')
    ATTR_TO = qname('xlink', 'to')
    
    # Storage
    loc_map: Dict[str, str] = {}           # label_id -> concept_name
    ref_map: Dict[str, Reference] = {}      # label_id -> Reference
    arc_links: List[tuple[str, str]] = []   # (from_id, to_id)
    
    # For reference linkbases, we need to capture child elements.
    # Use iterparse with start/end to track when we're inside a reference element
    current_ref_label: str | None = None
    current_ref_role: str | None = None
    current_ref_parts: Dict[str, str] = {}
    
    context = ET.iterparse(xml_file, events=('start', 'end'))
    
    for event, elem in context:
        tag = elem.tag
        
        if event == 'start':
            if tag == TAG_REFERENCE:
                # Starting a reference element - capture its attributes
                current_ref_label = elem.get(ATTR_LABEL)
                current_ref_role = elem.get(ATTR_ROLE)
                current_ref_parts = {}
        
        elif event == 'end':
            if tag == TAG_LOC:
                label_id = elem.get(ATTR_LABEL)
                href = elem.get(ATTR_HREF)
                if label_id and href:
                    loc_map[label_id] = extract_concept_from_href(href)
                elem.clear()
            
            elif tag == TAG_REFERENCE:
                # Ending a reference element - store it if it passes filters
                if current_ref_label:
                    # Filter by role if specified
                    if role is None or current_ref_role == role:
                        ref_map[current_ref_label] = Reference(
                            role=current_ref_role or '',
                            parts=current_ref_parts.copy()
                        )
                
                current_ref_label = None
                current_ref_role = None
                current_ref_parts = {}
                elem.clear()
            
            elif tag == TAG_ARC:
                from_id = elem.get(ATTR_FROM)
                to_id = elem.get(ATTR_TO)
                if from_id and to_id:
                    arc_links.append((from_id, to_id))
                elem.clear()
            
            elif current_ref_label is not None:
                # We're inside a reference element - this is a child part
                local_name = tag.split('}')[-1] if '}' in tag else tag
                if elem.text:
                    current_ref_parts[local_name] = elem.text.strip()
                elem.clear()
            
            else:
                # Some other element - just clear it
                elem.clear()
    
    # Resolution Phase: join locators with references via arcs
    result: Dict[str, List[Reference]] = {}
    
    for loc_id, ref_id in arc_links:
        if loc_id in loc_map and ref_id in ref_map:
            concept = loc_map[loc_id]
            ref = ref_map[ref_id]
            
            if concept not in result:
                result[concept] = []
            result[concept].append(ref)
    
    return result


def parse_reference_linkbase_flat(
    xml_file: str,
    role: str | None = None,
    ) -> Dict[str, List[Dict[str, str]]]:
    """
    Extract references as flat dictionaries (for pandas/JSON).
    
    Same as parse_reference_linkbase but returns dicts instead of
    Reference objects.
    
    Args:
        xml_file: Path to the reference linkbase XML file
        role: Optional role URI to filter by
    
    Returns:
        Dict mapping concept names to lists of reference dicts.
        Example: {
            'us-gaap_Assets': [
                {'role': '...', 'Publisher': 'FASB', 'Topic': '210', ...},
                ...
            ]
        }
    """
    refs = parse_reference_linkbase(xml_file, role=role)
    return {
        concept: [ref.to_dict() for ref in ref_list]
        for concept, ref_list in refs.items()
    }