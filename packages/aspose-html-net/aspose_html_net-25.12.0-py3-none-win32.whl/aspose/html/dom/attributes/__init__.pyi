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

class DOMConstructorAttribute:
    '''Specifies a constructor that is defined by the W3C.'''
    
    ...

class DOMNameAttribute:
    '''Specifies the official DOM object name as it defined by the W3C.'''
    
    @property
    def name(self) -> str:
        '''Gets the DOM name.'''
        ...
    
    ...

class DOMNamedPropertyGetterAttribute:
    '''Specifies that the method will be used as named property getter.'''
    
    ...

class DOMNoInterfaceObjectAttribute:
    '''If the [NoInterfaceObject] extended attribute appears on an interface, it indicates that an interface object will not exist for the interface in the ECMAScript binding.'''
    
    ...

class DOMNullableAttribute:
    '''Specifies a DOM object can be assigned null value.'''
    
    ...

class DOMObjectAttribute:
    '''Specifies that object is marked with this attribute is defined by the W3C.'''
    
    ...

class DOMTreatNullAsAttribute:
    '''Indicates that null of the member value will be treated as specified value.'''
    
    @property
    def type(self) -> Type:
        '''Gets value the type.'''
        ...
    
    @type.setter
    def type(self, value : Type):
        '''Sets value the type.'''
        ...
    
    @property
    def value(self) -> any:
        '''Gets the value.'''
        ...
    
    @value.setter
    def value(self, value : any):
        '''Sets the value.'''
        ...
    
    ...

class Accessors:
    '''Represents the enumeration of member accessors that is defined by the W3C.'''
    
    @classmethod
    @property
    def NONE(cls) -> Accessors:
        '''Specifies that the property does not have any special meaning.'''
        ...
    
    @classmethod
    @property
    def GETTER(cls) -> Accessors:
        '''Specifies that the property or method should be handled as a getter.'''
        ...
    
    @classmethod
    @property
    def SETTER(cls) -> Accessors:
        '''Specifies that the property or method should be handled as a setter.'''
        ...
    
    @classmethod
    @property
    def DELETER(cls) -> Accessors:
        '''Specifies that the property or method should be handled by delete.'''
        ...
    
    ...

