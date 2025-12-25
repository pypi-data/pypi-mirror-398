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

class ChildFrontMatterSyntaxNode:
    '''Defines the ChildFrontMatterSyntaxNode'''
    
    ...

class HugoFrontMatterSyntaxNode(aspose.html.toolkit.markdown.syntax.BlockSyntaxNode):
    '''Defines the base class HugoFrontMatterSyntaxNode'''
    
    def get_syntax_tree(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxTree:
        '''Get the syntax tree.
        
        :returns: The MarkdownSyntaxTree.'''
        ...
    
    def child_nodes(self) -> aspose.html.collections.NodeList:
        '''Get the child nodes collection.
        
        :returns: The NodeList.'''
        ...
    
    def get_leading_trivia(self) -> aspose.html.toolkit.markdown.syntax.TriviaCollection:
        '''Get the leading trivia.
        
        :returns: The TriviaCollection.'''
        ...
    
    def get_trailing_trivia(self) -> aspose.html.toolkit.markdown.syntax.TriviaCollection:
        '''Get the Trailing trivia.
        
        :returns: The TriviaCollection.'''
        ...
    
    def append_child(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Append child node.
        
        :param node: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def remove_child(self, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Remove the child.
        
        :param child: The child.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def replace_child(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Replace the child node.
        
        :param node: The MarkdownSyntaxNode.
        :param child: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def insert_before(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Insert before node.
        
        :param node: The MarkdownSyntaxNode.
        :param child: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def accept(self, visitor : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxVisitor):
        '''Defines the interface for accept visitor.
        
        :param visitor: The visitor.'''
        ...
    
    def write_to(self, writer : aspose.html.toolkit.markdown.syntax.MarkdownTextWriter):
        '''Write to MarkdownTextWriter.
        
        :param writer: The MarkdownTextWriter.'''
        ...
    
    def find(self, path : List[str]) -> aspose.html.toolkit.markdown.syntax.extensions.ChildFrontMatterSyntaxNode:
        '''Defines the interface for find BaseSyntaxNode
        
        :param path: The string path.
        :returns: The BaseSyntaxNode.'''
        ...
    
    @property
    def parent(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Get the parent node.'''
        ...
    
    @property
    def first_child(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def last_child(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def previous_sibling(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def next_sibling(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def front_matter_root_node(self) -> aspose.html.toolkit.markdown.syntax.extensions.ChildFrontMatterSyntaxNode:
        ...
    
    ...

class HugoShortCodeSyntaxNode(aspose.html.toolkit.markdown.syntax.InlineContainerSyntaxNode):
    '''Defines the HugoShortCodeSyntaxNode'''
    
    def get_syntax_tree(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxTree:
        '''Get the syntax tree.
        
        :returns: The MarkdownSyntaxTree.'''
        ...
    
    def child_nodes(self) -> aspose.html.collections.NodeList:
        '''Get the child nodes collection.
        
        :returns: The NodeList.'''
        ...
    
    def get_leading_trivia(self) -> aspose.html.toolkit.markdown.syntax.TriviaCollection:
        '''Get the leading trivia.
        
        :returns: The TriviaCollection.'''
        ...
    
    def get_trailing_trivia(self) -> aspose.html.toolkit.markdown.syntax.TriviaCollection:
        '''Get the Trailing trivia.
        
        :returns: The TriviaCollection.'''
        ...
    
    def append_child(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Append child node.
        
        :param node: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def remove_child(self, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Remove the child.
        
        :param child: The child.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def replace_child(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Replace the child node.
        
        :param node: The MarkdownSyntaxNode.
        :param child: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def insert_before(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Insert before node.
        
        :param node: The MarkdownSyntaxNode.
        :param child: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def accept(self, visitor : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxVisitor):
        '''Defines the interface for accept visitor.
        
        :param visitor: The visitor.'''
        ...
    
    def write_to(self, writer : aspose.html.toolkit.markdown.syntax.MarkdownTextWriter):
        '''Write to MarkdownTextWriter.
        
        :param writer: The MarkdownTextWriter.'''
        ...
    
    def is_end_tag(self) -> bool:
        '''Defines the interface for check IsEndTag
        
        :returns: The boolean.'''
        ...
    
    def get_parameters_count(self) -> int:
        '''Defines the GetParametersCount
        
        :returns: Teh count.'''
        ...
    
    def get_parameter(self, index : int) -> aspose.html.toolkit.markdown.syntax.extensions.ShortCodeParameterSyntaxNode:
        '''Defines the GetParameter
        
        :param index: The index.
        :returns: The  ShortCodeParameterSyntax.'''
        ...
    
    @property
    def parent(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Get the parent node.'''
        ...
    
    @property
    def first_child(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def last_child(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def previous_sibling(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def next_sibling(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    ...

class HugoSyntaxExtension(aspose.html.toolkit.markdown.syntax.parser.MarkdownSyntaxExtension):
    '''Defines the HugoSyntaxExtension.'''
    
    def setup(self, builder : aspose.html.toolkit.markdown.syntax.parser.IMarkdownParserBuilder):
        '''Defines the interface for Setup
        
        :param builder: The builder.'''
        ...
    
    ...

class HugoYamlBasedFrontMatterSyntaxNode(HugoFrontMatterSyntaxNode):
    '''Defines the HugoYamlBasedFrontMatterSyntaxNode'''
    
    def get_syntax_tree(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxTree:
        '''Get the syntax tree.
        
        :returns: The MarkdownSyntaxTree.'''
        ...
    
    def child_nodes(self) -> aspose.html.collections.NodeList:
        '''Get the child nodes collection.
        
        :returns: The NodeList.'''
        ...
    
    def get_leading_trivia(self) -> aspose.html.toolkit.markdown.syntax.TriviaCollection:
        '''Get the leading trivia.
        
        :returns: The TriviaCollection.'''
        ...
    
    def get_trailing_trivia(self) -> aspose.html.toolkit.markdown.syntax.TriviaCollection:
        '''Get the Trailing trivia.
        
        :returns: The TriviaCollection.'''
        ...
    
    def append_child(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Append child node.
        
        :param node: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def remove_child(self, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Remove the child.
        
        :param child: The child.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def replace_child(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Replace the child node.
        
        :param node: The MarkdownSyntaxNode.
        :param child: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def insert_before(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Insert before node.
        
        :param node: The MarkdownSyntaxNode.
        :param child: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def accept(self, visitor : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxVisitor):
        '''Defines the interface for accept visitor.
        
        :param visitor: The visitor.'''
        ...
    
    def write_to(self, writer : aspose.html.toolkit.markdown.syntax.MarkdownTextWriter):
        '''Write to MarkdownTextWriter.
        
        :param writer: The MarkdownTextWriter.'''
        ...
    
    def find(self, path : List[str]) -> aspose.html.toolkit.markdown.syntax.extensions.ChildFrontMatterSyntaxNode:
        '''Defines the interface for find BaseSyntaxNode
        
        :param path: The string path.
        :returns: The BaseSyntaxNode.'''
        ...
    
    @property
    def parent(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Get the parent node.'''
        ...
    
    @property
    def first_child(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def last_child(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def previous_sibling(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def next_sibling(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def front_matter_root_node(self) -> aspose.html.toolkit.markdown.syntax.extensions.ChildFrontMatterSyntaxNode:
        ...
    
    ...

class ShortCodeParameterSyntaxNode(aspose.html.toolkit.markdown.syntax.InlineSyntaxNode):
    '''Defines the ShortCodeParameterSyntax.'''
    
    def get_syntax_tree(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxTree:
        '''Get the syntax tree.
        
        :returns: The MarkdownSyntaxTree.'''
        ...
    
    def child_nodes(self) -> aspose.html.collections.NodeList:
        '''Get the child nodes collection.
        
        :returns: The NodeList.'''
        ...
    
    def get_leading_trivia(self) -> aspose.html.toolkit.markdown.syntax.TriviaCollection:
        '''Get the leading trivia.
        
        :returns: The TriviaCollection.'''
        ...
    
    def get_trailing_trivia(self) -> aspose.html.toolkit.markdown.syntax.TriviaCollection:
        '''Get the Trailing trivia.
        
        :returns: The TriviaCollection.'''
        ...
    
    def append_child(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Append child node.
        
        :param node: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def remove_child(self, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Remove the child.
        
        :param child: The child.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def replace_child(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Replace the child node.
        
        :param node: The MarkdownSyntaxNode.
        :param child: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def insert_before(self, node : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode, child : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Insert before node.
        
        :param node: The MarkdownSyntaxNode.
        :param child: The MarkdownSyntaxNode.
        :returns: The MarkdownSyntaxNode.'''
        ...
    
    def accept(self, visitor : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxVisitor):
        '''Defines the interface for accept visitor.
        
        :param visitor: The visitor.'''
        ...
    
    def write_to(self, writer : aspose.html.toolkit.markdown.syntax.MarkdownTextWriter):
        '''Write to MarkdownTextWriter.
        
        :param writer: The MarkdownTextWriter.'''
        ...
    
    def get_name(self) -> str:
        '''Get string name.
        
        :returns: The string result.'''
        ...
    
    def get_value(self) -> str:
        '''Get string Value
        
        :returns: The string result.'''
        ...
    
    def set_value(self, value : str):
        '''Defines the interface for set value.
        
        :param value: The value.'''
        ...
    
    @property
    def parent(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Get the parent node.'''
        ...
    
    @property
    def first_child(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def last_child(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def previous_sibling(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    @property
    def next_sibling(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        ...
    
    ...

class YamlMappingSyntaxNode(ChildFrontMatterSyntaxNode):
    '''Defines the YamlMappingSyntaxNode'''
    
    @property
    def keys(self) -> Iterable[aspose.html.toolkit.markdown.syntax.extensions.ChildFrontMatterSyntaxNode]:
        '''Get all Keys.'''
        ...
    
    @property
    def values(self) -> Iterable[aspose.html.toolkit.markdown.syntax.extensions.ChildFrontMatterSyntaxNode]:
        '''Get all Values.'''
        ...
    
    def __getitem__(self, key : int) -> aspose.html.toolkit.markdown.syntax.extensions.ChildFrontMatterSyntaxNode:
        '''Get the value by index.'''
        ...
    
    ...

class YamlScalarSyntaxNode(ChildFrontMatterSyntaxNode):
    '''Defines the YamlScalarSyntaxNode'''
    
    def get_value(self) -> str:
        '''Defines the interface for get value.
        
        :returns: The string.'''
        ...
    
    def set_value(self, value : str):
        '''Defines the interface for set value.
        
        :param value: The value.'''
        ...
    
    ...

class YamlSequenceSyntaxNode(ChildFrontMatterSyntaxNode):
    '''Defines the YamlSequenceSyntaxNode'''
    
    def count(self) -> int:
        '''Defines the interface for get count.
        
        :returns: The integer result.'''
        ...
    
    def __getitem__(self, key : int) -> aspose.html.toolkit.markdown.syntax.extensions.ChildFrontMatterSyntaxNode:
        '''Get the ChildFrontMatterSyntaxNode by index.'''
        ...
    
    ...

