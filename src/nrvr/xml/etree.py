#!/usr/bin/python

"""nrvr.xml.etree - Utilities for xml.etree.ElementTree

The main class provided by this module is ElementTreeUtil.

To be expanded as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2015.
Simplified BSD License"""

import copy
import xml.etree.ElementTree

class ElementTreeUtil(object):
    """Utilities for xml.etree.ElementTree.
    
    Written for Python 2.6."""
    @classmethod
    def indent(cls, element, indent="  ", level=0):
        """Set whitespace for indentation.
        
        element
            an xml.etree.ElementTree.Element instance.
        
        indent
            the additional indent for each level down.
        
        level
            increases on recursive calls.
            Need not be set on regular use."""
        levelIndent = "\n" + level * indent
        if len(element):
            # element has child element
            if not element.text or not element.text.strip():
                # element has no text or text is only whitespace
                element.text = levelIndent + indent
            for child in element:
                # child indented one level more
                cls.indent(child, indent=indent, level=level + 1)
            if not child.tail or not child.tail.strip():
                # last child has no tail or tail is only whitespace
                child.tail = levelIndent
        if level > 0:
            # any level except top level
            if not element.tail or not element.tail.strip():
                # element has no tail or tail is only whitespace
                element.tail = levelIndent
        else:
            # top level
            element.tail = ""

    @classmethod
    def unindent(cls, element):
        """Remove whitespace from indentation.
        
        element
            an xml.etree.ElementTree.Element instance."""
        if len(element):
            # element has child element
            if not element.text or not element.text.strip():
                # element has no text or text is only whitespace
                element.text = ""
            for child in element:
                # child indented one level more
                cls.unindent(child)
        if not element.tail or not element.tail.strip():
            # element has no tail or tail is only whitespace
            element.tail = ""

    @classmethod
    def tostring(cls, element, indent="  ", xml_declaration=True, encoding="utf-8"):
        """Generate a string representation.
        
        element
            an xml.etree.ElementTree.Element instance.
            
            Tolerates xml.etree.ElementTree.ElementTree.
        
        indent
            the additional indent for each level down.
            
            If None then unindented.
        
        xml_declaration
            whether with XML declaration <?xml version="1.0" encoding="utf-8"?>."""
        # tolerate tree instead of element
        if isinstance(element, xml.etree.ElementTree.ElementTree):
            # if given a tree
            element = element.getroot()
        element = copy.deepcopy(element)
        if indent is not None:
            cls.indent(element, indent)
        else:
            cls.unindent(element)
        string = xml.etree.ElementTree.tostring(element, encoding=encoding)
        if xml_declaration:
            string = '<?xml version="1.0" encoding="{0}"?>\n'.format(encoding) + string
        return string

    @classmethod
    def simpledict(cls, element):
        """Generate a dictionary from child element tags and text.
        
        element
            an xml.etree.ElementTree.Element instance."""
        children = element.findall('*')
        dictionary = {}
        for child in children:
            dictionary[child.tag] = child.text
        return dictionary

if __name__ == "__main__":
    import sys
    tree = xml.etree.ElementTree.ElementTree(xml.etree.ElementTree.XML \
                                             ("""<e1 a1="A1">
                                             <e2 a2="A2">E2</e2>
                                             <e3 a3="A3">E3</e3>
                                             <e4><e5/></e4>
                                             <e6/></e1>"""))
    tree.write(sys.stdout)
    print # a newline after the write of unindented XML
    ElementTreeUtil.indent(tree.getroot())
    tree.write(sys.stdout)
    print # a newline after the write of unindented XML
    print xml.etree.ElementTree.tostring(tree.getroot())
    ElementTreeUtil.unindent(tree.getroot())
    tree.write(sys.stdout)
    print # a newline after the write of unindented XML
    print ElementTreeUtil.tostring(tree)
    print ElementTreeUtil.tostring(tree.getroot())
    print ElementTreeUtil.tostring(tree, indent=None)
