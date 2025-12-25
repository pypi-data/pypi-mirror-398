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

class BlockSyntaxDescriptor:
    '''Defines the BlockSyntaxDescriptor.'''
    
    def has_attribute(self, name : str) -> bool:
        '''Defines the interface for check Has Attribute
        
        :param name: The string name.
        :returns: The boolean.'''
        ...
    
    def append_inline(self, text : aspose.html.toolkit.markdown.syntax.text.SourceText) -> aspose.html.toolkit.markdown.syntax.parser.BlockSyntaxDescriptor:
        '''Defines the interface for Append Inline.
        
        :param text: The SourceText.
        :returns: The BlockSyntaxDescriptor.'''
        ...
    
    def get_content(self) -> List[aspose.html.toolkit.markdown.syntax.text.SourceText]:
        '''Defines the interface for get content.
        
        :returns: The ICollection.'''
        ...
    
    def delete(self):
        '''Defines the interface for Delete.'''
        ...
    
    def close(self):
        '''Defines the interface for Close.'''
        ...
    
    @property
    def block(self) -> aspose.html.toolkit.markdown.syntax.BlockSyntaxNode:
        '''Get the Block'''
        ...
    
    @property
    def parser(self) -> aspose.html.toolkit.markdown.syntax.parser.MarkdownBlockParser:
        '''Get the Parser.'''
        ...
    
    ...

class DelimiterRun:
    '''Defines the DelimiterRun'''
    
    @property
    def state(self) -> aspose.html.toolkit.markdown.syntax.parser.DelimiterState:
        '''Get and set the State.'''
        ...
    
    @state.setter
    def state(self, value : aspose.html.toolkit.markdown.syntax.parser.DelimiterState):
        '''Get and set the State.'''
        ...
    
    @property
    def length(self) -> int:
        '''Get the Length.'''
        ...
    
    @property
    def source(self) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Get the Source.'''
        ...
    
    @property
    def span(self) -> aspose.html.toolkit.markdown.syntax.text.TextSpan:
        '''Get and Set the Span.'''
        ...
    
    @span.setter
    def span(self, value : aspose.html.toolkit.markdown.syntax.text.TextSpan):
        '''Get and Set the Span.'''
        ...
    
    @property
    def text(self) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Get the Text.'''
        ...
    
    ...

class IBlockParsingContext:
    '''Defines the IBlockParsingContext interface.'''
    
    @overload
    def close(self, head : aspose.html.toolkit.markdown.syntax.parser.BlockSyntaxDescriptor, reason : aspose.html.toolkit.markdown.syntax.parser.BlockClosingReason):
        '''Defines the Close method.
        
        :param head: The BlockSyntaxDescriptor.
        :param reason: The BlockClosingReason.'''
        ...
    
    @overload
    def close(self, reason : aspose.html.toolkit.markdown.syntax.parser.BlockClosingReason):
        '''Defines the Close method.
        
        :param reason: The BlockClosingReason.'''
        ...
    
    def push(self, block : aspose.html.toolkit.markdown.syntax.BlockSyntaxNode) -> aspose.html.toolkit.markdown.syntax.parser.BlockSyntaxDescriptor:
        '''Defines the Push method.
        
        :param block: The block.
        :returns: The BlockSyntaxDescriptor.'''
        ...
    
    def get_open_blocks(self) -> Iterable[aspose.html.toolkit.markdown.syntax.parser.BlockSyntaxDescriptor]:
        '''Defines the GetOpenBlocks.
        
        :returns: The collection of BlockSyntaxDescriptor.'''
        ...
    
    def peak(self) -> aspose.html.toolkit.markdown.syntax.parser.BlockSyntaxDescriptor:
        '''Defines the Peak method.
        
        :returns: The BlockSyntaxDescriptor.'''
        ...
    
    def delete(self, head : aspose.html.toolkit.markdown.syntax.parser.BlockSyntaxDescriptor):
        '''Defines the Delete method.
        
        :param head: The BlockSyntaxDescriptor.'''
        ...
    
    def get_block_syntax_parsers(self) -> Iterable[aspose.html.toolkit.markdown.syntax.parser.MarkdownBlockParser]:
        '''Defines the GetBlockSyntaxParsers method.
        
        :returns: The IEnumerable.'''
        ...
    
    def get_inline_syntax_parsers(self) -> Iterable[aspose.html.toolkit.markdown.syntax.parser.MarkdownInlineSyntaxParser]:
        '''Defines the GetInlineSyntaxParsers method.
        
        :returns: The IEnumerable.'''
        ...
    
    @property
    def source(self) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Get the Source.'''
        ...
    
    @property
    def reader(self) -> aspose.html.toolkit.markdown.syntax.text.SourceTextReader:
        '''Get the Reader.'''
        ...
    
    @property
    def instruction(self) -> aspose.html.toolkit.markdown.syntax.parser.LineParsingInstruction:
        '''Get the Instruction.'''
        ...
    
    @property
    def syntax_factory(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxFactory:
        ...
    
    ...

class IInlineEmphasisPostProcessing(IInlinePostProcessing):
    '''Defines the IInlineEmphasisPostProcessing interface.'''
    
    def process(self, context : aspose.html.toolkit.markdown.syntax.parser.IInlinePostProcessingContext) -> aspose.html.toolkit.markdown.syntax.parser.InlineParsingInstruction:
        '''Defines the Process method.
        
        :param context: The context.
        :returns: The InlineParsingInstruction.'''
        ...
    
    ...

class IInlineLinkPostProcessing(IInlinePostProcessing):
    '''Defines the IInlineLinkPostProcessing interface.'''
    
    def process(self, context : aspose.html.toolkit.markdown.syntax.parser.IInlinePostProcessingContext) -> aspose.html.toolkit.markdown.syntax.parser.InlineParsingInstruction:
        '''Defines the Process method.
        
        :param context: The context.
        :returns: The InlineParsingInstruction.'''
        ...
    
    ...

class IInlineParsingContext:
    '''Defines the IInlineParsingContext interface.'''
    
    @overload
    def push(self, syntax : aspose.html.toolkit.markdown.syntax.InlineSyntaxNode):
        '''Defines the Push method.
        
        :param syntax: The syntax.'''
        ...
    
    @overload
    def push(self, delimiter : aspose.html.toolkit.markdown.syntax.parser.DelimiterRun):
        '''Defines the Push method.
        
        :param delimiter: The delimiter.'''
        ...
    
    @property
    def source(self) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Get the Source.'''
        ...
    
    @property
    def reader(self) -> aspose.html.toolkit.markdown.syntax.text.SourceTextReader:
        '''Get the Reader.'''
        ...
    
    @property
    def syntax_factory(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxFactory:
        ...
    
    @property
    def owner(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Get the Owner.'''
        ...
    
    ...

class IInlinePostProcessing:
    '''Defines the IInlinePostProcessing interface'''
    
    def process(self, context : aspose.html.toolkit.markdown.syntax.parser.IInlinePostProcessingContext) -> aspose.html.toolkit.markdown.syntax.parser.InlineParsingInstruction:
        '''Defines the Process method.
        
        :param context: The context.
        :returns: The InlineParsingInstruction.'''
        ...
    
    ...

class IInlinePostProcessingContext(IInlineParsingContext):
    '''Defines the interface IInlinePostProcessingContext'''
    
    @overload
    def push(self, syntax : aspose.html.toolkit.markdown.syntax.InlineSyntaxNode):
        '''Defines the Push method.
        
        :param syntax: The syntax.'''
        ...
    
    @overload
    def push(self, delimiter : aspose.html.toolkit.markdown.syntax.parser.DelimiterRun):
        '''Defines the Push method.
        
        :param delimiter: The delimiter.'''
        ...
    
    def contains_link_reference_definition(self, label : str) -> bool:
        '''Defines the ContainsLinkReferenceDefinition
        
        :param label: The label.
        :returns: The boolean.'''
        ...
    
    @property
    def opened_delimiter(self) -> aspose.html.toolkit.markdown.syntax.parser.DelimiterRun:
        ...
    
    @opened_delimiter.setter
    def opened_delimiter(self, value : aspose.html.toolkit.markdown.syntax.parser.DelimiterRun):
        ...
    
    @property
    def closed_delimiter(self) -> aspose.html.toolkit.markdown.syntax.parser.DelimiterRun:
        ...
    
    @closed_delimiter.setter
    def closed_delimiter(self, value : aspose.html.toolkit.markdown.syntax.parser.DelimiterRun):
        ...
    
    @property
    def content(self) -> List[aspose.html.toolkit.markdown.syntax.InlineSyntaxNode]:
        '''Get the Content.'''
        ...
    
    @property
    def source(self) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Get the Source.'''
        ...
    
    @property
    def reader(self) -> aspose.html.toolkit.markdown.syntax.text.SourceTextReader:
        '''Get the Reader.'''
        ...
    
    @property
    def syntax_factory(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxFactory:
        ...
    
    @property
    def owner(self) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode:
        '''Get the Owner.'''
        ...
    
    ...

class IMarkdownParserBuilder:
    '''Defines the base interface IMarkdownParserBuilder'''
    
    ...

class InlineParsingInstruction:
    '''Defines the InlineParsingInstruction struct.'''
    
    def equals(self, other : aspose.html.toolkit.markdown.syntax.parser.InlineParsingInstruction) -> bool:
        '''Compare two InlineParsingInstruction.
        
        :param other: The other.
        :returns: The boolean.'''
        ...
    
    @property
    def instruction(self) -> aspose.html.toolkit.markdown.syntax.parser.ParsingInstruction:
        '''Get the Instruction.'''
        ...
    
    @classmethod
    @property
    def NONE(cls) -> aspose.html.toolkit.markdown.syntax.parser.InlineParsingInstruction:
        '''The ParsingInstruction.None.'''
        ...
    
    @classmethod
    @property
    def HANDLED(cls) -> aspose.html.toolkit.markdown.syntax.parser.InlineParsingInstruction:
        '''The Handled.'''
        ...
    
    ...

class LineParsingInstruction:
    '''Defines the LineParsingInstruction.'''
    
    def with_tabs_reservation(self, value : int) -> aspose.html.toolkit.markdown.syntax.parser.LineParsingInstruction:
        '''Defines the interface for WithTabsReservation
        
        :param value: The int value.
        :returns: The LineParsingInstruction.'''
        ...
    
    def with_content_indentation(self, value : int) -> aspose.html.toolkit.markdown.syntax.parser.LineParsingInstruction:
        '''Defines the interface for get LineParsingInstruction
        
        :param value: The int value.
        :returns: The LineParsingInstruction.'''
        ...
    
    def get_tabs_reservation(self) -> int:
        '''Defines the interface for get TabsReservation
        
        :returns: The reservation.'''
        ...
    
    def get_content_indentation(self) -> int:
        '''Defines the interface for get indentation
        
        :returns: The indentation.'''
        ...
    
    def equals(self, other : aspose.html.toolkit.markdown.syntax.parser.LineParsingInstruction) -> bool:
        '''Compare two LineParsingInstruction
        
        :param other: The LineParsingInstruction.
        :returns: The boolean.'''
        ...
    
    @property
    def instruction(self) -> aspose.html.toolkit.markdown.syntax.parser.ParsingInstruction:
        '''Get the Instruction'''
        ...
    
    @classmethod
    @property
    def NONE(cls) -> aspose.html.toolkit.markdown.syntax.parser.LineParsingInstruction:
        '''The None LineParsingInstruction.'''
        ...
    
    @classmethod
    @property
    def CONTINUE(cls) -> aspose.html.toolkit.markdown.syntax.parser.LineParsingInstruction:
        '''The Continue.'''
        ...
    
    @classmethod
    @property
    def NEXT_LINE(cls) -> aspose.html.toolkit.markdown.syntax.parser.LineParsingInstruction:
        ...
    
    ...

class MarkdownBlockParser:
    '''Defines the base class MarkdownBlockParser'''
    
    def can_parse(self, context : aspose.html.toolkit.markdown.syntax.parser.IBlockParsingContext) -> bool:
        '''Defines interface for get the CanParse value.
        
        :param context: The IBlockParsingContext.
        :returns: The boolean result.'''
        ...
    
    def parse(self, context : aspose.html.toolkit.markdown.syntax.parser.IBlockParsingContext) -> aspose.html.toolkit.markdown.syntax.parser.LineParsingInstruction:
        '''Defines interface for parse ofr the context..
        
        :param context: The context.
        :returns: The LineParsingInstruction.'''
        ...
    
    def on_open(self, descriptor : aspose.html.toolkit.markdown.syntax.parser.BlockSyntaxDescriptor, context : aspose.html.toolkit.markdown.syntax.parser.IBlockParsingContext):
        '''Defines interface for OnOpen method.
        
        :param descriptor: The description.
        :param context: The context.'''
        ...
    
    def can_close(self, descriptor : aspose.html.toolkit.markdown.syntax.parser.BlockSyntaxDescriptor, reason : aspose.html.toolkit.markdown.syntax.parser.BlockClosingReason, context : aspose.html.toolkit.markdown.syntax.parser.IBlockParsingContext) -> bool:
        '''Defines interface for CanClose method.
        
        :param descriptor: The description.
        :param reason: The reason.
        :param context: The context.
        :returns: The boolean result.'''
        ...
    
    def on_close(self, descriptor : aspose.html.toolkit.markdown.syntax.parser.BlockSyntaxDescriptor, parent : aspose.html.toolkit.markdown.syntax.MarkdownSyntaxNode, context : aspose.html.toolkit.markdown.syntax.parser.IBlockParsingContext):
        '''Defines interface for OnClose method.
        
        :param descriptor: The description.
        :param parent: The parent.
        :param context: The context.'''
        ...
    
    def on_process_inline(self, descriptor : aspose.html.toolkit.markdown.syntax.parser.BlockSyntaxDescriptor, context : aspose.html.toolkit.markdown.syntax.parser.IBlockParsingContext):
        '''Defines the interface for OnProcessInline method.
        
        :param descriptor: The description.
        :param context: The context.'''
        ...
    
    ...

class MarkdownInlineSyntaxParser:
    '''Defines the base class MarkdownInlineSyntaxParser'''
    
    def can_parse(self, context : aspose.html.toolkit.markdown.syntax.parser.IInlineParsingContext) -> bool:
        '''Get the can parse boolean value.
        
        :param context: The context.
        :returns: True if can parse.'''
        ...
    
    def parse(self, context : aspose.html.toolkit.markdown.syntax.parser.IInlineParsingContext) -> aspose.html.toolkit.markdown.syntax.parser.InlineParsingInstruction:
        '''Defines the interface for parse.
        
        :param context: The context.
        :returns: The InlineParsingInstruction.'''
        ...
    
    ...

class MarkdownParser:
    '''Represents an MarkDown format document parser.'''
    
    @overload
    def parse(self, stream : io.RawIOBase) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxTree:
        '''Parse from Stream.
        
        :param stream: The Stream.
        :returns: The Markdown syntax tree.'''
        ...
    
    @overload
    def parse(self, content : str) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxTree:
        '''Prase from the string context.
        
        :param content: The string content.
        :returns: The Markdown syntax tree.'''
        ...
    
    def parse_file(self, path : str) -> aspose.html.toolkit.markdown.syntax.MarkdownSyntaxTree:
        '''Parse an file.
        
        :param path: The path to file.
        :returns: The Markdown syntax tree.'''
        ...
    
    ...

class MarkdownSyntaxExtension:
    '''Defines the base class for MarkdownSyntaxExtension'''
    
    def setup(self, builder : aspose.html.toolkit.markdown.syntax.parser.IMarkdownParserBuilder):
        '''Defines the interface for Setup
        
        :param builder: The builder.'''
        ...
    
    ...

class BlockClosingReason:
    '''Defines the BlockClosingReason enum.'''
    
    @classmethod
    @property
    def BLANK_LINE(cls) -> BlockClosingReason:
        '''The BlankLine'''
        ...
    
    @classmethod
    @property
    def FORCE(cls) -> BlockClosingReason:
        '''The Force value'''
        ...
    
    ...

class DelimiterState:
    '''Defines the DelimiterState enum.'''
    
    @classmethod
    @property
    def UNDEFINED(cls) -> DelimiterState:
        '''The Undefined'''
        ...
    
    @classmethod
    @property
    def ACTIVE(cls) -> DelimiterState:
        '''The Active'''
        ...
    
    @classmethod
    @property
    def CLOSER(cls) -> DelimiterState:
        '''The Closer'''
        ...
    
    @classmethod
    @property
    def OPENER(cls) -> DelimiterState:
        '''The Opener'''
        ...
    
    ...

class ParsingInstruction:
    '''The ParsingInstruction enum.'''
    
    @classmethod
    @property
    def NONE(cls) -> ParsingInstruction:
        '''The None = 0'''
        ...
    
    @classmethod
    @property
    def HANDLED(cls) -> ParsingInstruction:
        '''The Handled = 1 << 0'''
        ...
    
    @classmethod
    @property
    def CONTINUE(cls) -> ParsingInstruction:
        '''The Continue = 1 <<'''
        ...
    
    @classmethod
    @property
    def NEXT_LINE(cls) -> ParsingInstruction:
        '''The NextLine = 1 << 2'''
        ...
    
    ...

