"""A base class for a class that works with XML configuration files."""

from pathlib import Path
from typing import TYPE_CHECKING, Self, cast
from xml.etree.ElementTree import Element, ElementTree, fromstring, parse, tostring

from funcy_bear.constants.type_constants import StrPath

from .helpers import pretty_string

if TYPE_CHECKING:
    Tree = ElementTree[Element]
else:
    Tree = ElementTree

# ruff:  noqa: S314


class BaseXMLWorker:
    """A base class for working with XML files."""

    def __init__(
        self,
        path: StrPath | None = None,
        data: str | None = None,
        tree: Tree | None = None,
    ) -> None:
        """Initialize the BaseXMLWorker with the path to the XML file."""
        self._path: StrPath | None = path
        self._data: str | None = data
        self._tree: Tree | None = tree
        self._root: Element | None = tree.getroot() if tree is not None else None

    def add_data(self, data: str) -> Self:
        """Add raw XML data as a string."""
        self._data = data
        return self

    def add_path(self, path: StrPath) -> Self:
        """Add the path to the XML file."""
        self._path = Path(path)
        return self

    def add_tree(self, tree: Tree) -> Self:
        """Add an existing ElementTree."""
        self._tree = tree
        self._root = tree.getroot()
        return self

    @property
    def file_path(self) -> Path:
        """Return the path to the XML file."""
        if self._path is None:
            raise ValueError("File path is not set.")
        if isinstance(self._path, str):
            self._path = Path(self._path).expanduser().resolve()
        return cast("Path", self._path)

    @property
    def data(self) -> str:
        """Return the raw XML data as a string."""
        if self._data is not None:
            return self._data
        raise ValueError("XML data is not set.")

    @property
    def tree(self) -> Tree:
        """Return the parsed XML tree."""
        if self._tree is None:
            if self._path is not None:
                self._tree = parse(self.file_path)
            elif self._data is not None:
                self._tree = ElementTree(fromstring(self.data))
            else:
                raise ValueError("Either file path or XML data must be provided.")
        return self._tree

    @property
    def root(self) -> Element:
        """Return the XML tree."""
        if self._root is None:
            self._root = self.tree.getroot()
        return self._root

    def to_string(self, encoding: str = "utf-8", pretty: bool = False) -> str:
        """Convert the XML tree back to a string."""
        if encoding != "unicode":
            string: bytes = tostring(self.root, encoding=encoding)
            output: str = string.decode(encoding)
        else:
            output = tostring(self.root, encoding=encoding)
        return pretty_string(output) if pretty else output

    def __enter__(self) -> Self:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Exit the runtime context related to this object."""
        self.clear()

    def clear(self) -> None:
        """Clear all internal references."""
        self._path = None
        self._data = None
        self._tree = None
        self._root = None
