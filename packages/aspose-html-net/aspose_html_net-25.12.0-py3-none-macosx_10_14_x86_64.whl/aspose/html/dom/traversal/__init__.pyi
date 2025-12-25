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

class IDocumentTraversal:
    '''DocumentTraversal contains methods that create iterators and
    tree-walkers to traverse a node and its children in document order (depth
    first, pre-order traversal, which is equivalent to the order in which the
    start tags occur in the text representation of the document). In DOMs
    which support the Traversal feature, DocumentTraversal will
    be implemented by the same objects that implement the Document interface.
    
    See also the `Document object Model (DOM) Level 2 Traversal and Range Specification <http://www.w3.org/TR/2000/REC-DOM-Level-2-Traversal-Range-20001113>`.
    @since DOM Level 2'''
    
    @overload
    def create_node_iterator(self, root : aspose.html.dom.Node) -> aspose.html.dom.traversal.INodeIterator:
        '''Create a new NodeIterator over the subtree rooted at the
        specified node.
        
        :param root: node which will be iterated together with its children.
        The iterator is initially positioned just before this node. The
        whatToShow flags and the filter, if any, are not
        considered when setting this position. The root must not be
        null.
        :returns: The newly created NodeIterator.'''
        ...
    
    @overload
    def create_node_iterator(self, root : aspose.html.dom.Node, what_to_show : int) -> aspose.html.dom.traversal.INodeIterator:
        '''Create a new NodeIterator over the subtree rooted at the
        specified node.
        
        :param root: node which will be iterated together with its children.
        The iterator is initially positioned just before this node. The
        whatToShow flags and the filter, if any, are not
        considered when setting this position. The root must not be
        null.
        :param what_to_show: flag specifies which node types may appear in
        the logical view of the tree presented by the iterator. See the
        description of NodeFilter for the set of possible
        SHOW_ values.These flags can be combined using
        OR.
        :returns: The newly created NodeIterator.'''
        ...
    
    @overload
    def create_node_iterator(self, root : aspose.html.dom.Node, what_to_show : int, filter : aspose.html.dom.traversal.INodeFilter) -> aspose.html.dom.traversal.INodeIterator:
        '''Create a new NodeIterator over the subtree rooted at the
        specified node.
        
        :param root: node which will be iterated together with its children.
        The iterator is initially positioned just before this node. The
        whatToShow flags and the filter, if any, are not
        considered when setting this position. The root must not be
        null.
        :param what_to_show: flag specifies which node types may appear in
        the logical view of the tree presented by the iterator. See the
        description of NodeFilter for the set of possible
        SHOW_ values.These flags can be combined using
        OR.
        :param filter: NodeFilter to be used with this
        TreeWalker, or null to indicate no filter.
        :returns: The newly created NodeIterator.'''
        ...
    
    @overload
    def create_tree_walker(self, root : aspose.html.dom.Node) -> aspose.html.dom.traversal.ITreeWalker:
        '''Create a new TreeWalker over the subtree rooted at the
        specified node.
        
        :param root: node which will serve as the root for the
        TreeWalker. The whatToShow flags and the
        NodeFilter are not considered when setting this value;
        any node type will be accepted as the root. The
        currentNode of the TreeWalker is
        initialized to this node, whether or not it is visible. The
        root functions as a stopping point for traversal
        methods that look upward in the document structure, such as
        parentNode and nextNode. The root must
        not be null.
        :returns: The newly created TreeWalker.'''
        ...
    
    @overload
    def create_tree_walker(self, root : aspose.html.dom.Node, what_to_show : int) -> aspose.html.dom.traversal.ITreeWalker:
        '''Create a new TreeWalker over the subtree rooted at the
        specified node.
        
        :param root: node which will serve as the root for the
        TreeWalker. The whatToShow flags and the
        NodeFilter are not considered when setting this value;
        any node type will be accepted as the root. The
        currentNode of the TreeWalker is
        initialized to this node, whether or not it is visible. The
        root functions as a stopping point for traversal
        methods that look upward in the document structure, such as
        parentNode and nextNode. The root must
        not be null.
        :param what_to_show: flag specifies which node types may appear in
        the logical view of the tree presented by the tree-walker. See the
        description of NodeFilter for the set of possible
        SHOW_ values.These flags can be combined using OR.
        :returns: The newly created TreeWalker.'''
        ...
    
    @overload
    def create_tree_walker(self, root : aspose.html.dom.Node, what_to_show : int, filter : aspose.html.dom.traversal.INodeFilter) -> aspose.html.dom.traversal.ITreeWalker:
        '''Create a new TreeWalker over the subtree rooted at the
        specified node.
        
        :param root: node which will serve as the root for the
        TreeWalker. The whatToShow flags and the
        NodeFilter are not considered when setting this value;
        any node type will be accepted as the root. The
        currentNode of the TreeWalker is
        initialized to this node, whether or not it is visible. The
        root functions as a stopping point for traversal
        methods that look upward in the document structure, such as
        parentNode and nextNode. The root must
        not be null.
        :param what_to_show: flag specifies which node types may appear in
        the logical view of the tree presented by the tree-walker. See the
        description of NodeFilter for the set of possible
        SHOW_ values.These flags can be combined using OR.
        :param filter: NodeFilter to be used with this
        TreeWalker, or null to indicate no filter.
        :returns: The newly created TreeWalker.'''
        ...
    
    ...

class IElementTraversal:
    '''The ElementTraversal interface is a set of read-only attributes which allow an author to easily navigate between elements in a document. In conforming implementations of Element Traversal, all objects that implement Element must also implement the ElementTraversal interface.'''
    
    @property
    def first_element_child(self) -> aspose.html.dom.Element:
        ...
    
    @property
    def last_element_child(self) -> aspose.html.dom.Element:
        ...
    
    @property
    def previous_element_sibling(self) -> aspose.html.dom.Element:
        ...
    
    @property
    def next_element_sibling(self) -> aspose.html.dom.Element:
        ...
    
    @property
    def child_element_count(self) -> int:
        ...
    
    ...

class INodeFilter:
    '''Filters are objects that know how to "filter out" nodes. If a
    NodeIterator or TreeWalker is given a
    NodeFilter, it applies the filter before it returns the next
    node. If the filter says to accept the node, the traversal logic returns
    it; otherwise, traversal looks for the next node and pretends that the
    node that was rejected was not there.
    
    The DOM does not provide any filters. NodeFilter is just an
    interface that users can implement to provide their own filters.
    
    
    NodeFilters do not need to know how to traverse from node
    to node, nor do they need to know anything about the data structure that
    is being traversed. This makes it very easy to write filters, since the
    only thing they have to know how to do is evaluate a single node. One
    filter may be used with a number of different kinds of traversals,
    encouraging code reuse.
    
    
    See also the `Document object Model (DOM) Level 2 Traversal and Range Specification <http://www.w3.org/TR/2000/REC-DOM-Level-2-Traversal-Range-20001113>`.
    @since DOM Level 2'''
    
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
    
    ...

class INodeIterator(ITraversal):
    '''Iterators are used to step through a set of nodes, e.g. the
    set of nodes in a NodeList, the document subtree governed by
    a particular Node, the results of a query, or any other set
    of nodes. The set of nodes to be iterated is determined by the
    implementation of the NodeIterator. DOM Level 2 specifies a
    single NodeIterator implementation for document-order
    traversal of a document subtree. Instances of these iterators are created
    by calling DocumentTraversal
    .createNodeIterator().
    
    See also the `Document object Model (DOM) Level 2 Traversal and Range Specification <http://www.w3.org/TR/2000/REC-DOM-Level-2-Traversal-Range-20001113>`.
    @since DOM Level 2'''
    
    def next_node(self) -> aspose.html.dom.Node:
        '''Returns the next node in the set and advances the position of the
        iterator in the set. After a NodeIterator is created,
        the first call to nextNode() returns the first node in
        the set.
        
        :returns: The next Node in the set being iterated over, or
        null if there are no more members in that set.'''
        ...
    
    def previous_node(self) -> aspose.html.dom.Node:
        '''Returns the previous node in the set and moves the position of the
        NodeIterator backwards in the set.
        
        :returns: The previous Node in the set being iterated over,
        or null if there are no more members in that set.'''
        ...
    
    def detach(self):
        '''Detaches the NodeIterator from the set which it iterated
        over, releasing any computational resources and placing the iterator
        in the INVALID state. After detach has been invoked,
        calls to nextNode or previousNode will
        raise the exception INVALID_STATE_ERR.'''
        ...
    
    @property
    def reference_node(self) -> aspose.html.dom.Node:
        ...
    
    @property
    def pointer_before_reference_node(self) -> bool:
        ...
    
    @property
    def root(self) -> aspose.html.dom.Node:
        '''The root node of the NodeIterator, as specified when it
        was created.'''
        ...
    
    @property
    def what_to_show(self) -> int:
        ...
    
    @property
    def filter(self) -> aspose.html.dom.traversal.INodeFilter:
        '''The NodeFilter used to screen nodes.'''
        ...
    
    ...

class ITraversal:
    '''Iterators are used to step through a set of nodes, e.g. the
    set of nodes in a NodeList, the document subtree governed by
    a particular Node, the results of a query, or any other set
    of nodes. The set of nodes to be iterated is determined by the
    implementation of the NodeIterator. DOM Level 2 specifies a
    single NodeIterator implementation for document-order
    traversal of a document subtree. Instances of these iterators are created
    by calling DocumentTraversal
    .createNodeIterator().
    
    See also the `Document object Model (DOM) Level 2 Traversal and Range Specification <http://www.w3.org/TR/2000/REC-DOM-Level-2-Traversal-Range-20001113>`.
    @since DOM Level 2'''
    
    @property
    def root(self) -> aspose.html.dom.Node:
        '''The root node of the NodeIterator, as specified when it
        was created.'''
        ...
    
    @property
    def what_to_show(self) -> int:
        ...
    
    @property
    def filter(self) -> aspose.html.dom.traversal.INodeFilter:
        '''The NodeFilter used to screen nodes.'''
        ...
    
    ...

class ITreeWalker(ITraversal):
    '''TreeWalker objects are used to navigate a document tree or
    subtree using the view of the document defined by their
    whatToShow flags and filter (if any). Any function which
    performs navigation using a TreeWalker will automatically
    support any view defined by a TreeWalker.
    
    Omitting nodes from the logical view of a subtree can result in a
    structure that is substantially different from the same subtree in the
    complete, unfiltered document. Nodes that are siblings in the
    TreeWalker view may be children of different, widely
    separated nodes in the original view. For instance, consider a
    NodeFilter that skips all nodes except for Text nodes and
    the root node of a document. In the logical view that results, all text
    nodes will be siblings and appear as direct children of the root node, no
    matter how deeply nested the structure of the original document.
    
    
    See also the `Document object Model (DOM) Level 2 Traversal and Range Specification <http://www.w3.org/TR/2000/REC-DOM-Level-2-Traversal-Range-20001113>`.
    @since DOM Level 2'''
    
    def parent_node(self) -> aspose.html.dom.Node:
        '''Moves to and returns the closest visible ancestor node of the current
        node. If the search for parentNode attempts to step
        upward from the TreeWalker's root node, or
        if it fails to find a visible ancestor node, this method retains the
        current position and returns null.
        
        :returns: The new parent node, or null if the current node
        has no parent  in the TreeWalker's logical view.'''
        ...
    
    def first_child(self) -> aspose.html.dom.Node:
        '''Moves the TreeWalker to the first visible child of the
        current node, and returns the new node. If the current node has no
        visible children, returns null, and retains the current
        node.
        
        :returns: The new node, or null if the current node has no
        visible children  in the TreeWalker's logical view.'''
        ...
    
    def last_child(self) -> aspose.html.dom.Node:
        '''Moves the TreeWalker to the last visible child of the
        current node, and returns the new node. If the current node has no
        visible children, returns null, and retains the current
        node.
        
        :returns: The new node, or null if the current node has no
        children  in the TreeWalker's logical view.'''
        ...
    
    def previous_sibling(self) -> aspose.html.dom.Node:
        '''Moves the TreeWalker to the previous sibling of the
        current node, and returns the new node. If the current node has no
        visible previous sibling, returns null, and retains the
        current node.
        
        :returns: The new node, or null if the current node has no
        previous sibling.  in the TreeWalker's logical view.'''
        ...
    
    def next_sibling(self) -> aspose.html.dom.Node:
        '''Moves the TreeWalker to the next sibling of the current
        node, and returns the new node. If the current node has no visible
        next sibling, returns null, and retains the current node.
        
        :returns: The new node, or null if the current node has no
        next sibling.  in the TreeWalker's logical view.'''
        ...
    
    def previous_node(self) -> aspose.html.dom.Node:
        '''Moves the TreeWalker to the previous visible node in
        document order relative to the current node, and returns the new
        node. If the current node has no previous node,  or if the search for
        previousNode attempts to step upward from the
        TreeWalker's root node,  returns
        null, and retains the current node.
        
        :returns: The new node, or null if the current node has no
        previous node  in the TreeWalker's logical view.'''
        ...
    
    def next_node(self) -> aspose.html.dom.Node:
        '''Moves the TreeWalker to the next visible node in document
        order relative to the current node, and returns the new node. If the
        current node has no next node, or if the search for nextNode attempts
        to step upward from the TreeWalker's root
        node, returns null, and retains the current node.
        
        :returns: The new node, or null if the current node has no
        next node  in the TreeWalker's logical view.'''
        ...
    
    @property
    def current_node(self) -> aspose.html.dom.Node:
        ...
    
    @current_node.setter
    def current_node(self, value : aspose.html.dom.Node):
        ...
    
    @property
    def root(self) -> aspose.html.dom.Node:
        '''The root node of the NodeIterator, as specified when it
        was created.'''
        ...
    
    @property
    def what_to_show(self) -> int:
        ...
    
    @property
    def filter(self) -> aspose.html.dom.traversal.INodeFilter:
        '''The NodeFilter used to screen nodes.'''
        ...
    
    ...

