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

class SourceText:
    '''Base class implements the SourceText.'''
    
    @overload
    @staticmethod
    def from_address(text : str) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Define the interface for get SourceText from string.
        
        :param text: The string text.
        :returns: The SourceText.'''
        ...
    
    @overload
    @staticmethod
    def from_address(text : strencoding : System.Text.Encoding) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Define the interface for get SourceText from string and encoding.
        
        :param text: The string text.
        :param encoding: The encoding.
        :returns: The SourceText.'''
        ...
    
    @overload
    @staticmethod
    def from_address(source : List[aspose.html.toolkit.markdown.syntax.text.SourceText]) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Define the interface for get SourceText from array of the source.
        
        :param source: The SourceText.
        :returns: The SourceText.'''
        ...
    
    @overload
    def get_text(self) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Define the interface for get Text.
        
        :returns: The SourceText.'''
        ...
    
    @overload
    def get_text(self, span : aspose.html.toolkit.markdown.syntax.text.TextSpan) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Define the interface for get Text.
        
        :param span: The TextSpan.
        :returns: The SourceText.'''
        ...
    
    @overload
    def get_text(self, start : int) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Define the interface for get Text.
        
        :param start: The int start.
        :returns: The SourceText.'''
        ...
    
    @overload
    def to_string(self, start : int) -> str:
        '''Override the ToString() method.
        
        :param start: The integer start value.
        :returns: The string result.'''
        ...
    
    @overload
    def to_string(self, start : int, length : int) -> str:
        '''Defines the interface ToString()
        
        :param start: The start position.
        :param length: The length.
        :returns: The string.'''
        ...
    
    @overload
    def to_string(self, span : aspose.html.toolkit.markdown.syntax.text.TextSpan) -> str:
        '''Defines the interface ToString()
        
        :param span: The TextSpan.
        :returns: The string.'''
        ...
    
    def copy_to(self, source_index : int, destination : List[char], destination_index : int, count : int):
        '''Define the interface for get SourceText from array of the source.
        
        :param source_index: The sourceIndex.
        :param destination: The destination.
        :param destination_index: The destinationIndex.
        :param count: The integer count.'''
        ...
    
    @property
    def encoding(self) -> System.Text.Encoding:
        '''Get encoding.'''
        ...
    
    @property
    def length(self) -> int:
        '''Get the length.'''
        ...
    
    @property
    def span(self) -> aspose.html.toolkit.markdown.syntax.text.TextSpan:
        '''Get the span.'''
        ...
    
    @property
    def lines(self) -> aspose.html.toolkit.markdown.syntax.text.TextLineCollection:
        '''Get the Lines collection.'''
        ...
    
    def __getitem__(self, key : int) -> char:
        '''Gets  the value at the given index.'''
        ...
    
    ...

class SourceTextReader:
    '''Represents the SourceTextReader.'''
    
    @overload
    def advance(self):
        '''Increment the position.'''
        ...
    
    @overload
    def advance(self, n : int):
        '''The increment position on N
        
        :param n: The number.'''
        ...
    
    @overload
    def peek(self) -> char:
        '''Get the character on position or Character.Null
        
        :returns: the character on position or Character.Null'''
        ...
    
    @overload
    def peek(self, delta : int) -> char:
        '''Get the char.
        
        :param delta: The delta.
        :returns: The char at the positon + delta or Character.Null'''
        ...
    
    @overload
    def get_line_reader(self) -> aspose.html.toolkit.markdown.syntax.text.SourceTextReader:
        '''Get the SourceTextReader
        
        :returns: The SourceTextReader.'''
        ...
    
    @overload
    def get_line_reader(self, auto_sync : bool) -> aspose.html.toolkit.markdown.syntax.text.SourceTextReader:
        '''Get the SourceTextReader
        
        :param auto_sync: The autosync.
        :returns: The SourceTextReader.'''
        ...
    
    def back(self):
        '''The decrement position.'''
        ...
    
    def next(self) -> char:
        '''Get the next character and advance position.
        
        :returns: The character value.'''
        ...
    
    def reset(self, index : int):
        '''Reset position to index
        
        :param index: The index.'''
        ...
    
    @property
    def source(self) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Get rhe source.'''
        ...
    
    @property
    def position(self) -> int:
        '''Get the position.'''
        ...
    
    ...

class TextLine:
    '''Represent the TextLine.'''
    
    @property
    def text(self) -> aspose.html.toolkit.markdown.syntax.text.SourceText:
        '''Get the Text.'''
        ...
    
    @property
    def line_number(self) -> int:
        ...
    
    @property
    def start(self) -> int:
        '''Get the start position.'''
        ...
    
    @property
    def end(self) -> int:
        '''Get the end position.'''
        ...
    
    @property
    def line_break_length(self) -> int:
        ...
    
    ...

class TextLineCollection:
    '''Represents the TextLineCollection.'''
    
    def index_of(self, position : int) -> int:
        '''Gets the index of the given position.
        
        :param position: The position
        :returns: The index of the collection in the dictionary -or- -1 if the position is not found.'''
        ...
    
    ...

class TextSpan:
    '''Represents the text span.'''
    
    @overload
    @staticmethod
    def create_empty() -> aspose.html.toolkit.markdown.syntax.text.TextSpan:
        '''Create the empty text span.
        
        :returns: The TextSpan.'''
        ...
    
    @overload
    @staticmethod
    def create_empty(start : int) -> aspose.html.toolkit.markdown.syntax.text.TextSpan:
        '''Create empty TextSpan from start position.
        
        :param start: The start position.
        :returns: The TextSpan.'''
        ...
    
    def is_empty(self) -> bool:
        '''Return true if length ==0.
        
        :returns: The boolean value.'''
        ...
    
    @staticmethod
    def combine(left : aspose.html.toolkit.markdown.syntax.text.TextSpanright : aspose.html.toolkit.markdown.syntax.text.TextSpan) -> aspose.html.toolkit.markdown.syntax.text.TextSpan:
        '''Combines the text spans
        
        :param left: The left text span.
        :param right: The right text span.
        :returns: Combined the text span.'''
        ...
    
    @staticmethod
    def create(start : intlength : int) -> aspose.html.toolkit.markdown.syntax.text.TextSpan:
        '''Create the TextSpan
        
        :param start: The start position.
        :param length: The length.
        :returns: The TextSpan.'''
        ...
    
    @staticmethod
    def create_from_start_end(start : intend : int) -> aspose.html.toolkit.markdown.syntax.text.TextSpan:
        '''Create the TextSpan
        
        :param start: The start position.
        :param end: The end position.
        :returns: The TextSpan.'''
        ...
    
    def compare_to(self, other : aspose.html.toolkit.markdown.syntax.text.TextSpan) -> int:
        '''Compare with other TextSpan
        
        :param other: The other TextSpan.
        :returns: The start position of difference.'''
        ...
    
    def equals(self, other : aspose.html.toolkit.markdown.syntax.text.TextSpan) -> bool:
        '''Compare with other TextSpan
        
        :param other: The other TextSpan
        :returns: The if both TextSpan are equal.'''
        ...
    
    @property
    def start(self) -> int:
        '''Get the Start index.'''
        ...
    
    @property
    def end(self) -> int:
        '''Get the End index.'''
        ...
    
    @property
    def length(self) -> int:
        '''Get the length.'''
        ...
    
    ...

