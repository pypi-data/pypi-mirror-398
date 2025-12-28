"""XML file handler module."""

from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, ElementTree

from codec_cub.general.base_file_handler import BaseFileHandler
from codec_cub.text.file_handler import TextFileHandler
from funcy_bear.constants.type_constants import StrPath

from .base_worker import BaseXMLWorker

if TYPE_CHECKING:
    Tree = ElementTree[Element]
else:
    Tree = ElementTree


class XMLFileHandler(BaseFileHandler[Tree]):
    """A simple XML file handler."""

    def __init__(
        self,
        file: StrPath,
        mode: str = "r+",
        encoding: str = "utf-8",
        touch: bool = False,
    ) -> None:
        """Initialize XML file handler.

        Args:
            file: Path to the XML file
            mode: File mode for opening (default: "r+" for read/write)
            encoding: Text encoding to use (default: "utf-8")
            touch: Whether to create the file if it doesn't exist (default: False)
        """
        super().__init__(file, mode=mode, encoding=encoding, touch=touch)
        self._txt_handler = None

    @property
    def txt_handler(self) -> TextFileHandler:
        """Get a text file handler for reading/writing XML content."""
        if self._txt_handler is None:
            self._txt_handler = TextFileHandler(
                self.file,
                mode=self._mode,
                encoding=self.encoding or "utf-8",
                touch=self.touch,
            )
        return self._txt_handler

    def read(self, **_) -> Tree | None:
        """Convert the XML content to an ElementTree."""
        data: str = self.txt_handler.read()
        if not data:
            return None
        with BaseXMLWorker(data=data) as worker:
            return worker.tree

    def write(self, data: Tree, **kwargs) -> None:
        """Write an ElementTree back to the XML file.

        Args:
            tree: The ElementTree to write
            pretty: Whether to pretty-print the XML (default: False)
        """
        with BaseXMLWorker(tree=data) as worker:
            xml_string: str = worker.to_string(pretty=kwargs.pop("pretty", False))
            self.txt_handler.write(xml_string)

    def clear(self) -> None:
        """Clear the XML file content."""
        self.txt_handler.clear()

    def close(self) -> None:
        """Close the XML file handler and associated text handler."""
        super().close()
        if self._txt_handler is not None:
            self._txt_handler.close()
