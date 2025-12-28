"""
Base XML Streaming Utilities

Memory-efficient XML parsing using iterparse with automatic cleanup.
"""

from typing import Iterator, Set
from pathlib import Path
import xml.etree.ElementTree as ET


def stream_xml(
    xml_file: str | Path,
    tags_of_interest: Set[str] | None = None,
) -> Iterator[tuple[str, ET.Element]]:
    """
    Stream XML elements with automatic memory cleanup.
    
    This is the core streaming primitive for EasyRL. It uses ElementTree's
    iterparse to process XML files without loading the entire document
    into memory.
    
    Args:
        xml_file: Path to the XML file to parse
        tags_of_interest: Optional set of qualified tag names to yield.
                         If None, yields all elements.
                         Use qname() to build qualified names.
    
    Yields:
        Tuple of (tag, element) for each matching element.
        Elements are cleared from memory after yielding.
    
    Examples:
        >>> from easyrl.core.namespaces import qname
        >>> 
        >>> # Stream only specific tags
        >>> tags = {qname('link', 'loc'), qname('link', 'label')}
        >>> for tag, elem in stream_xml('labels.xml', tags):
        ...     print(tag, elem.get(qname('xlink', 'label')))
        
        >>> # Stream all elements
        >>> for tag, elem in stream_xml('document.xml'):
        ...     print(tag)
    
    Note:
        Elements are cleared after yielding to keep memory usage low.
        Do not store references to yielded elements - extract needed
        data immediately.
    """
    context = ET.iterparse(xml_file, events=('end',))
    
    for event, elem in context:
        # Skip if not in our interest set
        if tags_of_interest is not None and elem.tag not in tags_of_interest:
            elem.clear()
            continue
        
        yield elem.tag, elem
        
        # Clear element to free memory
        elem.clear()


def stream_xml_with_ancestors(
    xml_file: str | Path,
    tags_of_interest: Set[str] | None = None,
) -> Iterator[tuple[str, ET.Element, list[ET.Element]]]:
    """
    Stream XML elements while tracking ancestor path.
    
    Useful when you need context about where an element appears
    in the document hierarchy.
    
    Args:
        xml_file: Path to the XML file
        tags_of_interest: Optional set of tags to yield
    
    Yields:
        Tuple of (tag, element, ancestors) where ancestors is a list
        of parent elements from root to immediate parent.
    
    Examples:
        >>> for tag, elem, ancestors in stream_xml_with_ancestors('doc.xml'):
        ...     depth = len(ancestors)
        ...     parent_tag = ancestors[-1].tag if ancestors else None
        ...     print(f"{'  ' * depth}{tag} (parent: {parent_tag})")
    """
    # Track the element stack
    path: list[ET.Element] = []
    
    context = ET.iterparse(xml_file, events=('start', 'end'))
    
    for event, elem in context:
        if event == 'start':
            path.append(elem)
        else:  # event == 'end'
            # Remove self from path
            path.pop()
            
            if tags_of_interest is None or elem.tag in tags_of_interest:
                # Yield with copy of current ancestor path
                yield elem.tag, elem, list(path)
            
            elem.clear()