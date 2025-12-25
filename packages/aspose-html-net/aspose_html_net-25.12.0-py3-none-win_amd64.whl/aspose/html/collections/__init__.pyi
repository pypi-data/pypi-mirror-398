from typing import List, Optional, Dict, Iterable
import aspose.pycore
import aspose.pydrawing
import aspose.html
import aspose.html.accessibility
import aspose.html.accessibility.results
import aspose.html.accessibility.saving
import aspose.html.collections
import aspose.html.converters
import aspose.html.diagnostics
import aspose.html.dom
import aspose.html.dom.attributes
import aspose.html.dom.canvas
import aspose.html.dom.css
import aspose.html.dom.events
import aspose.html.dom.mutations
import aspose.html.dom.svg
import aspose.html.dom.svg.datatypes
import aspose.html.dom.svg.events
import aspose.html.dom.svg.filters
import aspose.html.dom.svg.paths
import aspose.html.dom.svg.saving
import aspose.html.dom.traversal
import aspose.html.dom.traversal.filters
import aspose.html.dom.views
import aspose.html.dom.xpath
import aspose.html.drawing
import aspose.html.forms
import aspose.html.io
import aspose.html.loading
import aspose.html.net
import aspose.html.net.headers
import aspose.html.net.messagefilters
import aspose.html.net.messagehandlers
import aspose.html.rendering
import aspose.html.rendering.doc
import aspose.html.rendering.fonts
import aspose.html.rendering.image
import aspose.html.rendering.pdf
import aspose.html.rendering.pdf.encryption
import aspose.html.rendering.xps
import aspose.html.saving
import aspose.html.saving.resourcehandlers
import aspose.html.services
import aspose.html.toolkit
import aspose.html.toolkit.markdown
import aspose.html.toolkit.markdown.syntax
import aspose.html.toolkit.markdown.syntax.extensions
import aspose.html.toolkit.markdown.syntax.parser
import aspose.html.toolkit.markdown.syntax.parser.extensions
import aspose.html.toolkit.markdown.syntax.parser.extensions.gfm
import aspose.html.toolkit.markdown.syntax.text
import aspose.html.toolkit.optimizers
import aspose.html.window

class DOMTokenList(aspose.html.dom.DOMObject):
    '''The DOMTokenList class represents a set of space-separated tokens. It is indexed beginning with 0 as with JavaScript Array objects. DOMTokenList is always case-sensitive.'''
    
    @overload
    def toggle(self, token : str) -> bool:
        '''Removes the token from the list if it exists, or adds the token to the list if it doesn't.
        
        :param token: The token you want to toggle.
        :returns: A Boolean indicating whether token is in the list after the call.'''
        ...
    
    @overload
    def toggle(self, token : str, force : bool) -> bool:
        '''Removes the token from the list if it exists, or adds the token to the list if it doesn't.
        
        :param token: The token you want to toggle.
        :param force: A Boolean that, if included, turns the toggle into a one way-only operation. If set to false, then token will only be removed, but not added. If set to true, then token will only be added, but not removed.
        :returns: A Boolean indicating whether token is in the list after the call.'''
        ...
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def contains(self, token : str) -> bool:
        '''Returns true if the list contains the given token, otherwise false.
        
        :param token: The token to locate in the list.
        :returns: A Boolean, which is true if the calling list contains token, otherwise false.'''
        ...
    
    def add(self, tokens : List[str]):
        '''Adds the specified token(s) to the list.
        
        :param tokens: Representing the token (or tokens) to add to the tokenList.'''
        ...
    
    def remove(self, tokens : List[str]):
        '''Removes the specified token(s) from the list.
        
        :param tokens: Represents the token(s) you want to remove from the list.'''
        ...
    
    def replace(self, token : str, new_token : str) -> bool:
        '''Replaces an existing token with a new token. Does nothing if the first token doesn't exist.
        
        :param token: The token you want to replace.
        :param new_token: The token you want to replace the old token with.
        :returns: Boolean ``true`` if the token was found and replaced, ``false`` otherwise.'''
        ...
    
    def supports(self, token : str) -> bool:
        '''Returns true if a given token is in the associated attribute's supported tokens.
        
        :param token: The token to query for.
        :returns: A Boolean indicating whether the token was found.'''
        ...
    
    @property
    def length(self) -> int:
        '''Returns an ulong which represents the number of tokens stored in this list.'''
        ...
    
    @property
    def value(self) -> str:
        '''Gets the value of a corresponding attribute.'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''Sets the value of a corresponding attribute.'''
        ...
    
    def __getitem__(self, key : int) -> str:
        ...
    
    ...

class HTMLCollection(aspose.html.dom.DOMObject):
    '''The :py:class:`aspose.html.collections.HTMLCollection` represents a generic collection of :py:class:`aspose.html.dom.Element`.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object :py:class:`System.Type`.'''
        ...
    
    def named_item(self, name : str) -> aspose.html.dom.Element:
        '''Returns the item in the collection matched specified name.
        
        :param name: The element name.
        :returns: The matched element'''
        ...
    
    @property
    def length(self) -> int:
        '''The number of nodes in the list.'''
        ...
    
    def __getitem__(self, key : int) -> aspose.html.dom.Element:
        '''Returns the index-th item in the collection. If index is greater than or equal to the number of nodes in the list, this returns null.'''
        ...
    
    ...

class NamedNodeMap(aspose.html.dom.DOMObject):
    '''Represents collections of attributes that can be accessed by name.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def get_named_item(self, name : str) -> aspose.html.dom.Attr:
        '''Retrieves a node specified by name.
        
        :param name: The node name.
        :returns: Returns node.'''
        ...
    
    def get_named_item_ns(self, namespace_uri : str, local_name : str) -> aspose.html.dom.Attr:
        '''Retrieves a node specified by local name and namespace URI.
        
        :param namespace_uri: The namespace URI.
        :param local_name: Name of the local.
        :returns: Returns node.'''
        ...
    
    def set_named_item(self, attr : aspose.html.dom.Attr) -> aspose.html.dom.Attr:
        '''Adds a node using its nodeName attribute. If a node with that name is already present in this map, it is replaced by the new one. Replacing a node by itself has no effect.
        
        :param attr: The attribute.
        :returns: Returns node.'''
        ...
    
    def set_named_item_ns(self, attr : aspose.html.dom.Attr) -> aspose.html.dom.Attr:
        '''Adds a node using its namespaceURI and localName. If a node with that namespace URI and that local name is already present in this map, it is replaced by the new one. Replacing a node by itself has no effect.
        
        :param attr: The attribute.
        :returns: Returns node.'''
        ...
    
    def remove_named_item(self, name : str) -> aspose.html.dom.Attr:
        '''Removes a node specified by name.
        
        :param name: The element name.
        :returns: Removed node.'''
        ...
    
    def remove_named_item_ns(self, namespace_uri : str, local_name : str) -> aspose.html.dom.Attr:
        '''Removes a node specified by local name and namespace URI.
        
        :param namespace_uri: The namespace URI.
        :param local_name: Name of the local.
        :returns: Returns node.'''
        ...
    
    @property
    def length(self) -> int:
        '''The number of nodes in this map.'''
        ...
    
    def __getitem__(self, key : int) -> aspose.html.dom.Attr:
        '''Returns the index-th item in the map. If index is greater than or equal to the number of nodes in this map, this returns null.'''
        ...
    
    ...

class NodeList(aspose.html.dom.DOMObject):
    '''The NodeList provides the abstraction of an ordered collection of nodes, without defining or constraining how this collection is implemented.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object :py:class:`System.Type`.'''
        ...
    
    @property
    def length(self) -> int:
        '''The number of nodes in the list.'''
        ...
    
    def __getitem__(self, key : int) -> aspose.html.dom.Node:
        '''Method returns the indexth item in the collection. If index is greater than or equal to the number of nodes in the list, this returns null.'''
        ...
    
    ...

