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

class ContentDispositionHeaderValue:
    '''Represent Content-Disposition header value.'''
    
    @property
    def disposition_type(self) -> str:
        ...
    
    @disposition_type.setter
    def disposition_type(self, value : str):
        ...
    
    @property
    def parameters(self) -> List[aspose.html.net.headers.NameValueHeaderValue]:
        '''Get collection of paremeters'''
        ...
    
    @property
    def name(self) -> str:
        '''The name for a content body part.'''
        ...
    
    @name.setter
    def name(self, value : str):
        '''The name for a content body part.'''
        ...
    
    @property
    def file_name(self) -> str:
        ...
    
    @file_name.setter
    def file_name(self, value : str):
        ...
    
    ...

class ContentTypeHeaderValue(NameValueHeaderValue):
    '''Represents a Content-Type header value.'''
    
    @property
    def name(self) -> str:
        '''Gets the parameter name.'''
        ...
    
    @property
    def value(self) -> str:
        '''Gets the parameter value.'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''Sets the parameter value.'''
        ...
    
    @property
    def char_set(self) -> str:
        ...
    
    @char_set.setter
    def char_set(self, value : str):
        ...
    
    @property
    def media_type(self) -> aspose.html.MimeType:
        ...
    
    @media_type.setter
    def media_type(self, value : aspose.html.MimeType):
        ...
    
    ...

class NameValueHeaderValue:
    '''Represents a name/value pair that describe a header value.'''
    
    @property
    def name(self) -> str:
        '''Gets the parameter name.'''
        ...
    
    @property
    def value(self) -> str:
        '''Gets the parameter value.'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''Sets the parameter value.'''
        ...
    
    ...

