"""This module provides utility functions for working with XML elements, including filtering, updating, and enclosing elements."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING
from xml.dom import minidom
from xml.etree.ElementTree import Element, tostring

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from xml.dom.minidom import Document


class MissingXMLAttributeError(Exception):
    """Custom exception raised when a required XML attribute is missing."""


class MissingNameError(Exception):
    """Custom exception raised when a required name attribute is missing in an XML element."""


class ElementList(list[Element]):
    """A class that extends the built-in list class and is specifically for working with XML elements."""

    def __init__(self, elements: Sequence[Element[str]] | None = None) -> None:
        """Initialize the ElementList with a list of elements or an empty list."""
        super().__init__(elements if elements is not None else [])

    def filter_contains(self, substring: str, tag: str) -> ElementList:
        """Filter the elements in the ElementList based on a substring and a tag."""
        return ElementList([e for e in self if _filter_element_matches(e, substring, tag)])

    def get_names(self) -> list[str]:
        """Get a list of names of the elements in the ElementList."""
        return [e.get("name", "") for e in self]

    def with_tag(self, tag: str) -> ElementList:
        """Get a new ElementList containing only elements with the specified tag."""
        return ElementList([e for e in self if e.tag == tag])


def to_elem(tag: str, **kwargs) -> Element:
    """Helper to create an XML Element with given tag and attributes.

    You would use this function when you need to create a new XML element with specific attributes.

    Args:
        tag: The tag of the XML element to create.
        **kwargs: The attributes of the XML element to create, that will be added as key-value pairs
        in the element's attribute dictionary.

    Returns:
        The created XML element.
    """
    return Element(tag, attrib=kwargs)


def get_value(elem: Element, name: str) -> str:
    """Get the value of an attribute from an XML element.

    You would use this when you need to retrieve an attribute value from an XML element
    and want to ensure that the attribute exists, raising an exception if it does not.

    Args:
        elem: The XML element to retrieve the attribute from.
        name: The name of the attribute to retrieve.

    Returns:
        The value of the attribute.

    Raises:
        Exception: If the attribute does not exist in the XML element.
    """
    value: str | None = elem.get(name)
    if value is None:
        raise MissingXMLAttributeError(f"Cannot find {name} attribute in the XML element")
    return value


def find_value(elem: Element, name: str) -> Element[str]:
    """Find an XML element by its tag name.

    You would use this when you need to retrieve a child element from an XML element
    and want to ensure that the element exists, raising an exception if it does not.

    Args:
        elem: The XML element to search within.
        name: The tag name of the child element to find.

    Returns:
        The XML element with the specified tag name.

    Raises:
        Exception: If the child element with the specified tag name does not exist in the XML element.
    """
    value: Element[str] | None = elem.find(name)
    if value is None:
        raise MissingNameError(f"Cannot find {name} element in the XML element")
    return value


def enclose_element(
    tag: str,
    enclosed_element: Element,
    outer_element: Element,
    index: int,
    remove: bool = False,
    **kwargs,
) -> Element:
    """Enclose an XML element in a new element with a given name and attributes.

    Args:
        tag: The tag of the new element.
        enclosed_element: The element to enclose.
        outer_element: The element to add the new element to.
        index: The index to add the new element at.
        remove: Whether to remove the old element from the list of elements. Optional.
        **kwargs: Additional attributes for the new element.

    Returns:
        Element with the enclosed element.
    """
    enclosing_element: Element = to_elem(tag, **kwargs)
    outer_element.insert(index, enclosing_element)
    enclosing_element.append(enclosed_element)
    if remove:
        outer_element.remove(enclosed_element)
    return enclosing_element


def create_element(
    parent: Element,
    tag: str,
    template: Element | None = None,
    index: int | None = None,
    inner_text: str | None = None,
    **kwargs,
) -> Element:
    """Create a new XML element from a template and add it to a parent element.

    Creates a new element with the specified tag and attributes, optionally populates
    it with child elements copied from a template element, then adds it to the parent.

    Args:
        parent: The parent element to add the new element to.
        tag: The tag name for the new element.
        template: Optional template element whose children will be copied to the new element.
        index: Index where to insert the new element (-1 to append at end).
        inner_text: Optional text content for the new element.
        **kwargs: Additional attributes for the new element.

    Returns:
        The newly created XML element.
    """
    new_element: Element = to_elem(tag, **kwargs)
    if template is not None:
        copy_child_elements(new_element, template)
    if inner_text is not None:
        new_element.text = inner_text
    parent.append(new_element) if index is None else parent.insert(index, new_element)
    return new_element


def copy_child_elements(target: Element[str], source: Element[str]) -> None:
    """Copy all child elements from source element to target element.

    Args:
        target: The target XML element to add children to.
        source: The source element whose child elements will be copied.
    """
    for child in source:
        target.append(child)


def update_element(element: Element[str], func: Callable[[Element], None | bool]) -> None:
    """Update an XML element using a function that is passed as an argument.

    Args:
        element: The XML element.
        func: The function to apply to the element.
    """
    func(element)


def update_elements(elements: list[Element[str]], func: Callable[[Element], None | bool]) -> None:
    """Update a list of XML elements using a function that is passed as an argument.

    Args:
        elements: The list of XML elements.
        func: The function to update the elements with.
    """
    for element in elements:
        update_element(element=element, func=func)


def _filter_element_matches(elem: Element[str], sub: str, tag: str) -> bool:
    """Check if an XML element contains a specific substring in a given tag."""
    tag_value: str | None = elem.get(tag)
    return tag_value is not None and sub in tag_value


def filter_elements_split(elements: list[Element[str]], substring: str, tag: str) -> tuple[ElementList, ElementList]:
    """Filter a list of XML elements based on a string and return two lists.

    One with elements that contain the string and one with elements that do not.

    Args:
        elements: The list of XML elements.
        substring: The string to filter by.
        tag: The tag to look for the filter in.

    Returns:
        A tuple of (matching_elements, non_matching_elements).
    """
    return (
        ElementList([e for e in elements if _filter_element_matches(e, substring, tag)]),
        ElementList([e for e in elements if not _filter_element_matches(e, substring, tag)]),
    )


def filter_elements(elements: list[Element[str]], substring: str, tag: str) -> ElementList:
    """Filter a list of XML elements based on a string, i.e. only keep elements that contain the string.

    Args:
        elements: The list of XML elements.
        substring: The string to filter by.
        tag: The tag to look for the filter in.

    Returns:
        The filtered list of elements.
    """
    return ElementList([e for e in elements if _filter_element_matches(e, substring, tag)])


def filter_out_elements(elements: list[Element[str]], substring: str, tag: str) -> ElementList:
    """Filter out a list of XML elements based on a string, i.e. remove elements that contain the string.

    Args:
        elements: The list of XML elements.
        substring: The string to filter out.
        tag: The tag to look for the filter in.

    Returns:
        The filtered list of elements.
    """
    return ElementList([e for e in elements if not _filter_element_matches(e, substring, tag)])


def filter_out_elements_by_tag(elements: list[Element[str]], tag_name: str) -> ElementList:
    """Filter out a list of XML elements based on a tag, i.e. remove elements that do have the tag (ie, it is not None).

    Args:
        elements: The list of XML elements.
        tag_name: The tag to filter out.

    Returns:
        The filtered list of elements.
    """
    return ElementList([e for e in elements if e.get(tag_name) is None])


def find_and_remove(element: Element, tag: str) -> bool:
    """Find and remove an XML element from a parent element based on the element's tag.

    If the element is not found, this function does nothing.

    Args:
        element: The parent XML element.
        tag: The tag of the XML element to remove.

    Returns:
        bool: True if the element was found and removed, False otherwise.
    """
    tag_to_find: Element[str] | None = element.find(tag)
    if tag_to_find is not None:
        element.remove(tag_to_find)
        return True
    return False


def get_element_and_index(elements: Element, tag: str) -> tuple[Element[str], int]:
    """Get an XML element and its index in a list of XML elements based on the element's tag.

    Args:
        elements: The list of XML elements.
        tag: The tag of the XML element to find.

    Returns:
        The XML element and its index in the list.
    """
    for index, element in enumerate(elements):
        if tag == element.tag:
            return element, index
    raise ValueError(f"No element with tag {tag} found in the list of elements.")


def get_element_and_index_by_name(elements: list[Element[str]], name: str) -> tuple[Element[str], int]:
    """Get an XML element and its index in a list of XML elements based on the name attribute.

    Args:
        elements: The list of XML elements.
        name: The name of the XML element to find.

    Returns:
        The XML element and its index in the list.
    """
    for index, element in enumerate(elements):
        if name == element.get("name"):
            return element, index
    raise ValueError(f"No element with name {name} found in the list of elements.")


def has_tag(elements: list[Element[str]], tag: str) -> bool:
    """Check if all elements in a list of XML elements have a specific tag.

    Args:
        elements: A list of elements to check.
        tag: The tag to check for.

    Returns:
        True if all elements have the tag, False otherwise.
    """
    return not [e for e in elements if e.find(tag) is None]


def write_xml_pretty(output_path: Path, isp_root: Element, basic: bool = True) -> None:
    """Write an XML file to disk and format it nicely.

    Args:
        output_path: The path to write the XML file to.
        isp_root: The root element of the XML tree.
        basic: If True, format the string without the document element, this will retain
        the xml declaration and doctype if present.
    """
    xml_str: str = pretty_string(tostring(isp_root, encoding="unicode"), basic=basic)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(xml_str, encoding="utf-8")


def pretty_string(string: str, basic: bool = True) -> str:
    """Function is used to format XML strings and will make them look pretty.

    You might use this function without basic if you want to strip out XML declaration and doctype.
    For example when you are working with individual elements and do not want the document element.

    Args:
        string: The string to format.
        basic: If True, format the string without the document element, this will retain
        the xml declaration and doctype if present.

    Returns:
        The formatted string.

    Raises:
        ValueError: If the provided string does not contain a valid XML document.
    """
    if basic:
        string = minidom.parseString(string).toprettyxml(indent="  ")  # noqa: S318
    else:
        dom: Document = minidom.parseString(string)  # noqa: S318
        if dom.documentElement is None:
            raise ValueError("The provided string does not contain a valid XML document.")
        string = dom.documentElement.toprettyxml(indent="  ")
    return "\n".join([line for line in string.split("\n") if line.strip()]) + "\n"
