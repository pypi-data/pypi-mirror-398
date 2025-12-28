# src/easyrl/core/parser.py
from abc import ABC, abstractmethod
from typing import Iterator, Any
import xml.etree.ElementTree as ET
from pathlib import Path

#This is an abstract base class (ABC) — it cannot be instantiated directly. Subclasses must implement the parse() method.
class StreamingParser(ABC):
    """Base class for memory-efficient XML parsing."""
    
    def __init__(self, source: str | Path):
        self.source = Path(source)
    
    def _iter_elements(self, tags: set[str]) -> Iterator[ET.Element]:
        """Stream elements, clearing memory after each."""
        try:        
            context = ET.iterparse(self.source, events=('end',))
            for event, elem in context:
                if elem.tag in tags:
                    yield elem
                    elem.clear()
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML in {self.source}: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing {self.source}: {e}")
    @abstractmethod
    def parse(self) -> Any:
        """Subclasses implement specific parsing logic."""
        pass

