"""A set of helpers for XML file handling."""

from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, ElementTree

if TYPE_CHECKING:
    Tree = ElementTree[Element]
else:
    Tree = ElementTree


from .file_handler import XMLFileHandler
from .helpers import to_elem

__all__ = [
    "Element",
    "ElementTree",
    "Tree",
    "XMLFileHandler",
    "to_elem",
]
