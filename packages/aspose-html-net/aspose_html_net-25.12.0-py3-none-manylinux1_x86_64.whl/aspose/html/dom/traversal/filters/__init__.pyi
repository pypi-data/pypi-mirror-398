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

class NodeFilter(aspose.html.dom.DOMObject):
    '''Filters are objects that know how to "filter out" nodes.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object :py:class:`System.Type`.'''
        ...
    
    def accept_node(self, n : aspose.html.dom.Node) -> int:
        '''Test whether a specified node is visible in the logical view of a
        TreeWalker or NodeIterator. This function
        will be called by the implementation of TreeWalker and
        NodeIterator; it is not normally called directly from
        user code. (Though you could do so if you wanted to use the same
        filter to guide your own application logic.)
        
        :param n: node to check to see if it passes the filter or not.
        :returns: a constant to determine whether the node is accepted,
        rejected, or skipped, as defined above.'''
        ...
    
    @classmethod
    @property
    def FILTER_ACCEPT(cls) -> int:
        '''Accept the node. Navigation methods defined for
        NodeIterator or TreeWalker will return this
        node.'''
        ...
    
    @classmethod
    @property
    def FILTER_REJECT(cls) -> int:
        '''Reject the node. Navigation methods defined for
        NodeIterator or TreeWalker will not return
        this node. For TreeWalker, the children of this node
        will also be rejected. NodeIterators treat this as a
        synonym for FILTER_SKIP.'''
        ...
    
    @classmethod
    @property
    def FILTER_SKIP(cls) -> int:
        '''Skip this single node. Navigation methods defined for
        NodeIterator or TreeWalker will not return
        this node. For both NodeIterator and
        TreeWalker, the children of this node will still be
        considered.'''
        ...
    
    @classmethod
    @property
    def SHOW_ALL(cls) -> int:
        '''Show all Nodes.'''
        ...
    
    @classmethod
    @property
    def SHOW_ELEMENT(cls) -> int:
        '''Show Element nodes.'''
        ...
    
    @classmethod
    @property
    def SHOW_ATTRIBUTE(cls) -> int:
        '''Show Attr nodes. This is meaningful only when creating an
        iterator or tree-walker with an attribute node as its
        root; in this case, it means that the attribute node
        will appear in the first position of the iteration or traversal.
        Since attributes are never children of other nodes, they do not
        appear when traversing over the document tree.'''
        ...
    
    @classmethod
    @property
    def SHOW_TEXT(cls) -> int:
        '''Show Text nodes.'''
        ...
    
    @classmethod
    @property
    def SHOW_CDATA_SECTION(cls) -> int:
        '''Show CDATASection nodes.'''
        ...
    
    @classmethod
    @property
    def SHOW_ENTITY_REFERENCE(cls) -> int:
        '''Show EntityReference nodes.'''
        ...
    
    @classmethod
    @property
    def SHOW_ENTITY(cls) -> int:
        '''Show Entity nodes. This is meaningful only when creating
        an iterator or tree-walker with an Entity node as its
        root; in this case, it means that the Entity
        node will appear in the first position of the traversal. Since
        entities are not part of the document tree, they do not appear when
        traversing over the document tree.'''
        ...
    
    @classmethod
    @property
    def SHOW_PROCESSING_INSTRUCTION(cls) -> int:
        '''Show ProcessingInstruction nodes.'''
        ...
    
    @classmethod
    @property
    def SHOW_COMMENT(cls) -> int:
        '''Show Comment nodes.'''
        ...
    
    @classmethod
    @property
    def SHOW_DOCUMENT(cls) -> int:
        '''Show Document nodes.'''
        ...
    
    @classmethod
    @property
    def SHOW_DOCUMENT_TYPE(cls) -> int:
        '''Show DocumentType nodes.'''
        ...
    
    @classmethod
    @property
    def SHOW_DOCUMENT_FRAGMENT(cls) -> int:
        '''Show DocumentFragment nodes.'''
        ...
    
    @classmethod
    @property
    def SHOW_NOTATION(cls) -> int:
        '''Show Notation nodes. This is meaningful only when creating
        an iterator or tree-walker with a Notation node as its
        root; in this case, it means that the
        Notation node will appear in the first position of the
        traversal. Since notations are not part of the document tree, they do
        not appear when traversing over the document tree.'''
        ...
    
    ...

