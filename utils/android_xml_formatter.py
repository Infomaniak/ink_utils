"""
Android XML strings formatting utilities.
Provides indentation and blank line preservation for Android strings.xml files.
"""

from dataclasses import dataclass


def indent_android_strings_xml(root_elem):
    """
    Format Android strings.xml with preserved blank lines.

    Args:
        root_elem: Root Element of the XML tree
    """
    context = _remember_blank_lines(root_elem)
    _apply_standard_indent(root_elem)
    _apply_blank_lines(root_elem, context)


def _remember_blank_lines(root):
    """Extract blank line formatting from XML tree."""
    element_names = set()
    has_leading = False
    root_text = root.text or ''

    if root_text.count('\n') > 1:
        has_leading = True

    for elem in root:
        tail = elem.tail or ''
        if '\n\n' in tail:
            name = elem.get('name')
            if name:
                element_names.add(name)

    return BlankLineContext(
        element_names_with_blank_after=element_names,
        has_leading_blank_line=has_leading
    )


def _apply_standard_indent(root_elem, level=0):
    """Standard XML indentation without blank lines."""
    i = "\n" + level * "    "

    if len(root_elem):
        if not root_elem.text or not root_elem.text.strip():
            root_elem.text = i + "    "

        for elem in root_elem:
            _apply_standard_indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i

    if level and (not root_elem.tail or not root_elem.tail.strip()):
        root_elem.tail = i


def _apply_blank_lines(root, context, level=0):
    """Apply preserved blank line formatting to XML tree."""
    indent_str = (level + 1) * "    "

    if level == 0 and context.has_leading_blank_line:
        current_text = root.text or ''
        if not current_text.endswith('\n\n'):
            root.text = current_text.rstrip() + '\n\n' + "    "

    for elem in root:
        name = elem.get('name')
        if name and name in context.element_names_with_blank_after:
            current_tail = elem.tail or ''
            if not current_tail.endswith('\n\n'):
                elem.tail = current_tail.rstrip() + '\n\n' + indent_str

        if len(elem) > 0:
            _apply_blank_lines(elem, context, level + 1)


@dataclass
class BlankLineContext:
    """Holds information about blank line formatting in an XML file."""
    element_names_with_blank_after: set
    has_leading_blank_line: bool
