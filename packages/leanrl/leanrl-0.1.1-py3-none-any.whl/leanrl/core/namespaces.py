"""
XBRL Namespace Constants

This module centralizes all XML namespace URIs and their ElementTree-formatted
versions (with curly braces) used throughout XBRL processing.

Usage:
    from easyrl.core.namespaces import NS_LINK, NS_XLINK, Namespaces, qname

    # Direct usage for ElementTree tag matching
    tag == f'{NS_LINK}loc'

    # Or use qname() for cleaner code
    tag == qname('link', 'loc')

    # Or use the Namespaces class for more context
    Namespaces.LINK.uri  # Raw URI
    Namespaces.LINK.tag  # {uri} formatted for ElementTree
"""

from dataclasses import dataclass
from typing import ClassVar
from functools import lru_cache


@dataclass(frozen=True)
class Namespace:
    """Represents an XML namespace with both URI and ElementTree tag format."""
    
    prefix: str
    uri: str
    
    @property
    def tag(self) -> str:
        """Return namespace formatted for ElementTree: {uri}"""
        return f'{{{self.uri}}}'
    
    def __str__(self) -> str:
        return self.tag


class Namespaces:
    """
    Collection of all XBRL-related namespaces.
    
    Each namespace is available as a Namespace object with:
    - .prefix: The common prefix (e.g., 'link')
    - .uri: The full URI (e.g., 'http://www.xbrl.org/2003/linkbase')
    - .tag: ElementTree format (e.g., '{http://www.xbrl.org/2003/linkbase}')
    """
    
    # Core XBRL Namespaces
    LINK: ClassVar[Namespace] = Namespace(
        prefix='link',
        uri='http://www.xbrl.org/2003/linkbase'
    )
    
    XLINK: ClassVar[Namespace] = Namespace(
        prefix='xlink',
        uri='http://www.w3.org/1999/xlink'
    )
    
    XBRLI: ClassVar[Namespace] = Namespace(
        prefix='xbrli',
        uri='http://www.xbrl.org/2003/instance'
    )
    
    XBRLDI: ClassVar[Namespace] = Namespace(
        prefix='xbrldi',
        uri='http://xbrl.org/2006/xbrldi'
    )
    
    XBRLDT: ClassVar[Namespace] = Namespace(
        prefix='xbrldt',
        uri='http://xbrl.org/2005/xbrldt'
    )
    
    # XML Schema Namespaces
    XS: ClassVar[Namespace] = Namespace(
        prefix='xs',
        uri='http://www.w3.org/2001/XMLSchema'
    )
    
    XSD: ClassVar[Namespace] = Namespace(
        prefix='xsd',
        uri='http://www.w3.org/2001/XMLSchema'
    )
    
    XSI: ClassVar[Namespace] = Namespace(
        prefix='xsi',
        uri='http://www.w3.org/2001/XMLSchema-instance'
    )
    
    # US GAAP / SEC Namespaces
    US_GAAP: ClassVar[Namespace] = Namespace(
        prefix='us-gaap',
        uri='http://fasb.org/us-gaap/2023'
    )
    
    DEI: ClassVar[Namespace] = Namespace(
        prefix='dei',
        uri='http://xbrl.sec.gov/dei/2023'
    )
    
    SRT: ClassVar[Namespace] = Namespace(
        prefix='srt',
        uri='http://fasb.org/srt/2023'
    )
    
    # IFRS Namespace
    IFRS: ClassVar[Namespace] = Namespace(
        prefix='ifrs-full',
        uri='http://xbrl.ifrs.org/taxonomy/2023-03-23/ifrs-full'
    )
    
    # Generic / ISO Namespaces
    ISO4217: ClassVar[Namespace] = Namespace(
        prefix='iso4217',
        uri='http://www.xbrl.org/2003/iso4217'
    )
    
    XML: ClassVar[Namespace] = Namespace(
        prefix='xml',
        uri='http://www.w3.org/XML/1998/namespace'
    )
    
    @classmethod
    def as_dict(cls) -> dict[str, str]:
        """
        Return namespace mapping for use with ElementTree findall().
        
        Example:
            tree.findall('.//link:loc', Namespaces.as_dict())
        """
        return {
            ns.prefix: ns.uri
            for name, ns in vars(cls).items()
            if isinstance(ns, Namespace)
        }
    
    @classmethod
    def from_prefix(cls, prefix: str) -> Namespace | None:
        """Look up a namespace by its prefix."""
        for name, ns in vars(cls).items():
            if isinstance(ns, Namespace) and ns.prefix == prefix:
                return ns
        return None


# =============================================================================
# Convenience Constants (for direct import)
# =============================================================================

NS_LINK = Namespaces.LINK.tag
NS_XLINK = Namespaces.XLINK.tag
NS_XBRLI = Namespaces.XBRLI.tag
NS_XBRLDI = Namespaces.XBRLDI.tag
NS_XBRLDT = Namespaces.XBRLDT.tag
NS_XS = Namespaces.XS.tag
NS_XSD = Namespaces.XSD.tag
NS_XSI = Namespaces.XSI.tag
NS_US_GAAP = Namespaces.US_GAAP.tag
NS_DEI = Namespaces.DEI.tag
NS_SRT = Namespaces.SRT.tag
NS_IFRS = Namespaces.IFRS.tag
NS_ISO4217 = Namespaces.ISO4217.tag
NS_XML = Namespaces.XML.tag


# =============================================================================
# qname() Helper Function
# =============================================================================

# Build prefix -> URI lookup once at module load
_PREFIX_TO_URI: dict[str, str] = {
    ns.prefix: ns.uri
    for name, ns in vars(Namespaces).items()
    if isinstance(ns, Namespace)
}


@lru_cache(maxsize=128)
def qname(prefix: str, local_name: str) -> str:
    """
    Build a qualified name (QName) for ElementTree tag/attribute matching.
    
    This is the preferred way to construct namespace-qualified names
    for use with ElementTree's iterparse.
    
    Args:
        prefix: Namespace prefix (e.g., 'link', 'xlink', 'xbrli')
        local_name: Local element/attribute name (e.g., 'loc', 'label', 'href')
    
    Returns:
        ElementTree-formatted QName: '{namespace_uri}local_name'
    
    Raises:
        KeyError: If prefix is not registered in Namespaces
    
    Examples:
        >>> qname('link', 'loc')
        '{http://www.xbrl.org/2003/linkbase}loc'
        
        >>> qname('xlink', 'href')
        '{http://www.w3.org/1999/xlink}href'
        
        >>> # Use in parsing
        >>> TAG_LOC = qname('link', 'loc')
        >>> ATTR_HREF = qname('xlink', 'href')
        >>> if elem.tag == TAG_LOC:
        ...     href = elem.get(ATTR_HREF)
    """
    if prefix not in _PREFIX_TO_URI:
        available = ', '.join(sorted(_PREFIX_TO_URI.keys()))
        raise KeyError(
            f"Unknown namespace prefix: {prefix!r}. "
            f"Available prefixes: {available}"
        )
    return f'{{{_PREFIX_TO_URI[prefix]}}}{local_name}'


# =============================================================================
# XBRL Role URIs
# =============================================================================

class Roles:
    """Standard XBRL role URIs used in linkbases."""
    
    # Label roles
    LABEL = 'http://www.xbrl.org/2003/role/label'
    TERSE_LABEL = 'http://www.xbrl.org/2003/role/terseLabel'
    VERBOSE_LABEL = 'http://www.xbrl.org/2003/role/verboseLabel'
    DOCUMENTATION = 'http://www.xbrl.org/2003/role/documentation'
    PERIOD_START_LABEL = 'http://www.xbrl.org/2003/role/periodStartLabel'
    PERIOD_END_LABEL = 'http://www.xbrl.org/2003/role/periodEndLabel'
    TOTAL_LABEL = 'http://www.xbrl.org/2003/role/totalLabel'
    NEGATED_LABEL = 'http://www.xbrl.org/2009/role/negatedLabel'
    
    # Reference roles
    REFERENCE = 'http://www.xbrl.org/2003/role/reference'
    DEFINITION_REF = 'http://www.xbrl.org/2003/role/definitionRef'
    DISCLOSURE_REF = 'http://www.xbrl.org/2003/role/disclosureRef'
    
    # Link roles
    LINK = 'http://www.xbrl.org/2003/role/link'
    PRESENTATION_LINK = 'http://www.xbrl.org/2003/role/presentationLinkbaseRef'
    CALCULATION_LINK = 'http://www.xbrl.org/2003/role/calculationLinkbaseRef'
    DEFINITION_LINK = 'http://www.xbrl.org/2003/role/definitionLinkbaseRef'
    LABEL_LINK = 'http://www.xbrl.org/2003/role/labelLinkbaseRef'
    REFERENCE_LINK = 'http://www.xbrl.org/2003/role/referenceLinkbaseRef'


class ArcRoles:
    """Standard XBRL arc role URIs."""
    
    PARENT_CHILD = 'http://www.xbrl.org/2003/arcrole/parent-child'
    SUMMATION_ITEM = 'http://www.xbrl.org/2003/arcrole/summation-item'
    HYPERCUBE_DIMENSION = 'http://xbrl.org/int/dim/arcrole/hypercube-dimension'
    DIMENSION_DOMAIN = 'http://xbrl.org/int/dim/arcrole/dimension-domain'
    DOMAIN_MEMBER = 'http://xbrl.org/int/dim/arcrole/domain-member'
    ALL = 'http://xbrl.org/int/dim/arcrole/all'
    NOT_ALL = 'http://xbrl.org/int/dim/arcrole/notAll'
    CONCEPT_LABEL = 'http://www.xbrl.org/2003/arcrole/concept-label'
    CONCEPT_REFERENCE = 'http://www.xbrl.org/2003/arcrole/concept-reference'
    FACT_FOOTNOTE = 'http://www.xbrl.org/2003/arcrole/fact-footnote'
    GENERAL_SPECIAL = 'http://www.xbrl.org/2003/arcrole/general-special'
    ESSENCE_ALIAS = 'http://www.xbrl.org/2003/arcrole/essence-alias'
    SIMILAR_TUPLES = 'http://www.xbrl.org/2003/arcrole/similar-tuples'
    REQUIRES_ELEMENT = 'http://www.xbrl.org/2003/arcrole/requires-element'