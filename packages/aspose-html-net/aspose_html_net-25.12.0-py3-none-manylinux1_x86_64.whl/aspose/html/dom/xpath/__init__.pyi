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

class IXPathEvaluator:
    '''The evaluation of XPath expressions is provided by :py:class:`aspose.html.dom.xpath.IXPathEvaluator`.'''
    
    def create_expression(self, expression : str, resolver : aspose.html.dom.xpath.IXPathNSResolver) -> aspose.html.dom.xpath.IXPathExpression:
        '''Creates a parsed XPath expression with resolved namespaces. This is useful
        when an expression will be reused in an application since it makes it possible
        to compile the expression string into a more efficient internal form and
        preresolve all namespace prefixes which occur within the expression.
        
        :param expression: The XPath expression string to be parsed.
        :param resolver: The ``resolver`` permits translation of all prefixes,
        including the ``xml`` namespace prefix, within the XPath expression into
        appropriate namespace URIs. If this is specified as ``null``, any namespace
        prefix within the expression will result in :py:class:`aspose.html.dom.DOMException` being
        thrown with the code ``NAMESPACE_ERR``.
        :returns: The compiled form of the XPath expression.'''
        ...
    
    def create_ns_resolver(self, node_resolver : aspose.html.dom.Node) -> aspose.html.dom.xpath.IXPathNSResolver:
        '''Adapts any DOM node to resolve namespaces so that an XPath expression can be easily evaluated
        relative to the context of the node where it appeared within the document. This adapter works
        like the DOM Level 3 method ``lookupNamespaceURI`` on nodes in resolving the namespaceURI
        from a given prefix using the current information available in the node's hierarchy at the time
        lookupNamespaceURI is called, also correctly resolving the implicit xml prefix.
        
        :param node_resolver: The node to be used as a context for namespace resolution.
        :returns: :py:class:`aspose.html.dom.xpath.IXPathNSResolver` which resolves namespaces with respect to the definitions
        in scope for a specified node.'''
        ...
    
    def evaluate(self, expression : str, context_node : aspose.html.dom.Node, resolver : aspose.html.dom.xpath.IXPathNSResolver, type : aspose.html.dom.xpath.XPathResultType, result : any) -> aspose.html.dom.xpath.IXPathResult:
        '''Evaluates an XPath expression string and returns a result of the specified type if possible.
        
        :param expression: The XPath expression string to be parsed and evaluated.
        :param context_node: The ``context`` is context node for the evaluation of this
        XPath expression. If the :py:class:`aspose.html.dom.xpath.IXPathEvaluator` was obtained by casting the
        :py:class:`aspose.html.dom.Document` then this must be owned by the same document and must be a
        :py:class:`aspose.html.dom.Document`, :py:class:`aspose.html.dom.Element`, :py:class:`aspose.html.dom.Attr`, :py:class:`aspose.html.dom.Text`,
        :py:class:`aspose.html.dom.CDATASection`, :py:class:`aspose.html.dom.Comment`, :py:class:`aspose.html.dom.ProcessingInstruction`,
        or :py:class:`Aspose.Html.Dom.XPath.XPathNamespace` node. If the context node is a :py:class:`aspose.html.dom.Text` or a
        :py:class:`aspose.html.dom.CDATASection`, then the context is interpreted as the whole logical text node
        as seen by XPath, unless the node is empty in which case it may not serve as the XPath context.
        :param resolver: The ``resolver`` permits translation of all prefixes, including
        the ``xml`` namespace prefix, within the XPath expression into appropriate namespace URIs.
        If this is specified as ``null``, any namespace prefix within the expression will result
        in :py:class:`aspose.html.dom.DOMException` being thrown with the code ``NAMESPACE_ERR``.
        :param type: If a specific ``type`` is specified, then the result will be returned as
        the corresponding type. For XPath 1.0 results, this must be one of the values of the
        :py:class:`aspose.html.dom.xpath.XPathResultType` enum.
        :param result: The ``result`` specifies a specific result object which may be reused
        and returned by this method. If this is specified as ``null`` or the implementation does not
        reuse the specified result, a new result object will be constructed and returned. For XPath 1.0
        results, this object will be of type :py:class:`aspose.html.dom.xpath.IXPathResult`.
        :returns: The result of the evaluation of the XPath expression. For XPath 1.0 results, this object
        will be of type :py:class:`aspose.html.dom.xpath.IXPathResult`.'''
        ...
    
    ...

class IXPathExpression:
    '''The ``XPathExpression`` interface represents a parsed and resolved XPath expression.'''
    
    def evaluate(self, context_node : aspose.html.dom.Node, type : aspose.html.dom.xpath.XPathResultType, result : any) -> aspose.html.dom.xpath.IXPathResult:
        '''Evaluates this XPath expression and returns a result.
        
        :param context_node: The ``context`` is context node for the evaluation of this XPath expression.
        If the :py:class:`aspose.html.dom.xpath.IXPathEvaluator` was obtained by casting the :py:class:`aspose.html.dom.Document` then this must be
        owned by the same document and must be a :py:class:`aspose.html.dom.Document`, :py:class:`aspose.html.dom.Element`, :py:class:`aspose.html.dom.Attr`,
        :py:class:`aspose.html.dom.Text`, :py:class:`aspose.html.dom.CDATASection`, :py:class:`aspose.html.dom.Comment`, :py:class:`aspose.html.dom.ProcessingInstruction`,
        or :py:class:`Aspose.Html.Dom.XPath.XPathNamespace` node. If the context node is a :py:class:`aspose.html.dom.Text` or a :py:class:`aspose.html.dom.CDATASection`,
        then the context is interpreted as the whole logical text node as seen by XPath, unless the node is empty
        in which case it may not serve as the XPath context.
        :param type: If a specific ``type`` is specified, then the result will be coerced to return the
        specified type relying on XPath conversions and fail if the desired coercion is not possible. This must
        be one of the values of :py:class:`aspose.html.dom.xpath.XPathResultType`.
        :param result: The ``result`` specifies a specific result object which may be reused and returned
        by this method. If this is specified as ``null`` or the implementation does not reuse the specified
        result, a new result object will be constructed and returned. For XPath 1.0 results, this object will be
        of type :py:class:`aspose.html.dom.xpath.IXPathResult`.
        :returns: The result of the evaluation of the XPath expression. For XPath 1.0 results, this object will be
        of type :py:class:`aspose.html.dom.xpath.IXPathResult`.'''
        ...
    
    ...

class IXPathNSResolver:
    '''The ``XPathNSResolver`` interface permit ``prefix`` strings in
    the expression to be properly bound to ``namespaceURI`` strings.
    :py:class:`aspose.html.dom.xpath.IXPathEvaluator` can construct an implementation of
    :py:class:`aspose.html.dom.xpath.IXPathNSResolver` from a node, or the interface may be
    implemented by any application.'''
    
    def lookup_namespace_uri(self, prefix : str) -> str:
        '''Look up the namespace URI associated to the given namespace prefix.
        The XPath evaluator must never call this with a ``null`` or empty
        argument, because the result of doing this is undefined.
        
        :param prefix: The prefix to look for.
        :returns: Returns the associated namespace URI or ``null`` if none
        is found.'''
        ...
    
    ...

class IXPathNamespace:
    '''The XPathNamespace interface is returned by XPathResult interfaces to represent the XPath namespace node type that DOM lacks.'''
    
    @property
    def owner_element(self) -> aspose.html.dom.Element:
        ...
    
    ...

class IXPathResult:
    '''The ``XPathResult`` interface represents the result of the evaluation of an
    XPath 1.0 expression within the context of a particular node. Since evaluation
    of an XPath expression can result in various result types, this object makes it
    possible to discover and manipulate the type and value of the result.'''
    
    def iterate_next(self) -> aspose.html.dom.Node:
        '''Iterates and returns the next node from the node set or ``null`` if there are no more nodes.
        
        :returns: Returns the next node.'''
        ...
    
    def snapshot_item(self, index : int) -> aspose.html.dom.Node:
        '''Returns the ``index``th item in the snapshot collection. If ``index`` is greater than
        or equal to the number of nodes in the list, this method returns ``null``. Unlike the
        iterator result, the snapshot does not become invalid, but may not correspond to the current
        document if it is mutated.
        
        :param index: Index into the snapshot collection.
        :returns: The node at the ``index``th position in the ``NodeList``, or ``null`` if
        that is not a valid index.'''
        ...
    
    @property
    def result_type(self) -> aspose.html.dom.xpath.XPathResultType:
        ...
    
    @property
    def number_value(self) -> float:
        ...
    
    @property
    def string_value(self) -> str:
        ...
    
    @property
    def boolean_value(self) -> bool:
        ...
    
    @property
    def single_node_value(self) -> aspose.html.dom.Node:
        ...
    
    @property
    def invalid_iterator_state(self) -> bool:
        ...
    
    @property
    def snapshot_length(self) -> int:
        ...
    
    ...

class XPathResultType:
    '''An unsigned short indicating what type of result this is. If a specific
    ``type`` is specified, then the result will be returned as the corresponding
    type, using XPath type conversions where required and possible.'''
    
    @classmethod
    @property
    def ANY(cls) -> XPathResultType:
        '''This code does not represent a specific type. An evaluation of an XPath expression
        will never produce this type. If this type is requested, then the evaluation returns
        whatever type naturally results from evaluation of the expression. If the natural
        result is a node set when ``Any`` type was requested, then ``UnorderedNodeIterator``
        is always the resulting type. Any other representation of a node set must be
        explicitly requested.'''
        ...
    
    @classmethod
    @property
    def NUMBER(cls) -> XPathResultType:
        '''The result is a number as defined by [XPath 1.0]. Document modification does not
        invalidate the number, but may mean that reevaluation would not yield the same number.'''
        ...
    
    @classmethod
    @property
    def STRING(cls) -> XPathResultType:
        '''The result is a string as defined by [XPath 1.0]. Document modification does not
        invalidate the string, but may mean that the string no longer corresponds to the
        current document.'''
        ...
    
    @classmethod
    @property
    def BOOLEAN(cls) -> XPathResultType:
        '''The result is a boolean as defined by [XPath 1.0]. Document modification does not
        invalidate the boolean, but may mean that reevaluation would not yield the same boolean.'''
        ...
    
    @classmethod
    @property
    def UNORDERED_NODE_ITERATOR(cls) -> XPathResultType:
        '''The result is a node set as defined by [XPath 1.0] that will be accessed iteratively,
        which may not produce nodes in a particular order. Document modification invalidates the
        iteration. This is the default type returned if the result is a node set and ``Any``
        type is requested.'''
        ...
    
    @classmethod
    @property
    def ORDERED_NODE_ITERATOR(cls) -> XPathResultType:
        '''The result is a node set as defined by [XPath 1.0] that will be accessed iteratively,
        which will produce document-ordered nodes. Document modification invalidates the iteration.'''
        ...
    
    @classmethod
    @property
    def UNORDERED_NODE_SNAPSHOT(cls) -> XPathResultType:
        '''The result is a node set as defined by [XPath 1.0] that will be accessed as a snapshot
        list of nodes that may not be in a particular order. Document modification does not
        invalidate the snapshot but may mean that reevaluation would not yield the same snapshot
        and nodes in the snapshot may have been altered, moved, or removed from the document.'''
        ...
    
    @classmethod
    @property
    def ORDERED_NODE_SNAPSHOT(cls) -> XPathResultType:
        '''The result is a node set as defined by [XPath 1.0] that will be accessed as a snapshot
        list of nodes that will be in original document order. Document modification does not
        invalidate the snapshot but may mean that reevaluation would not yield the same snapshot
        and nodes in the snapshot may have been altered, moved, or removed from the document.'''
        ...
    
    @classmethod
    @property
    def ANY_UNORDERED_NODE(cls) -> XPathResultType:
        '''The result is a node set as defined by [XPath 1.0] and will be accessed as a single node,
        which may be ``null`` if the node set is empty. Document modification does not invalidate
        the node, but may mean that the result node no longer corresponds to the current document.
        This is a convenience that permits optimization since the implementation can stop once any
        node in the resulting set has been found. If there is more than one node in the actual result,
        the single node returned might not be the first in document order.'''
        ...
    
    @classmethod
    @property
    def FIRST_ORDERED_NODE(cls) -> XPathResultType:
        '''The result is a node set as defined by [XPath 1.0] and will be accessed as a single node,
        which may be ``null`` if the node set is empty. Document modification does not invalidate
        the node, but may mean that the result node no longer corresponds to the current document.
        This is a convenience that permits optimization since the implementation can stop once the
        first node in document order of the resulting set has been found. If there are more than one
        node in the actual result, the single node returned will be the first in document order.'''
        ...
    
    ...

