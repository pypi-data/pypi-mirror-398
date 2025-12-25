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

class IDeviceInformationService:
    '''An interface that is described an environment in which :py:class:`aspose.html.dom.Document` is presented to the user.'''
    
    @property
    def screen_size(self) -> aspose.html.drawing.Size:
        ...
    
    @screen_size.setter
    def screen_size(self, value : aspose.html.drawing.Size):
        ...
    
    @property
    def window_size(self) -> aspose.html.drawing.Size:
        ...
    
    @window_size.setter
    def window_size(self, value : aspose.html.drawing.Size):
        ...
    
    @property
    def horizontal_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    @property
    def vertical_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    ...

class INetworkService:
    '''Provides an interface for the network operations.'''
    
    @property
    def url_resolver(self) -> aspose.html.net.UrlResolver:
        ...
    
    @url_resolver.setter
    def url_resolver(self, value : aspose.html.net.UrlResolver):
        ...
    
    @property
    def message_handlers(self) -> aspose.html.net.MessageHandlerCollection:
        ...
    
    ...

class IRuntimeService:
    '''This service is used to configure runtime related properties.'''
    
    @property
    def java_script_timeout(self) -> TimeSpan:
        ...
    
    @java_script_timeout.setter
    def java_script_timeout(self, value : TimeSpan):
        ...
    
    ...

class IUserAgentService:
    '''An interface that is described a user agent environment.'''
    
    @property
    def language(self) -> str:
        '''The :py:attr:`aspose.html.services.IUserAgentService.language` specifies the primary language for the element's contents and for any of the element's attributes that contain text.
        Its value must be a valid BCP 47 (:link:`http://www.ietf.org/rfc/bcp/bcp47.txt`) language tag, or the empty string. Setting the attribute to the empty string indicates that the primary language is unknown.'''
        ...
    
    @language.setter
    def language(self, value : str):
        '''The :py:attr:`aspose.html.services.IUserAgentService.language` specifies the primary language for the element's contents and for any of the element's attributes that contain text.
        Its value must be a valid BCP 47 (:link:`http://www.ietf.org/rfc/bcp/bcp47.txt`) language tag, or the empty string. Setting the attribute to the empty string indicates that the primary language is unknown.'''
        ...
    
    @property
    def user_style_sheet(self) -> str:
        ...
    
    @user_style_sheet.setter
    def user_style_sheet(self, value : str):
        ...
    
    @property
    def char_set(self) -> str:
        ...
    
    @char_set.setter
    def char_set(self, value : str):
        ...
    
    @property
    def css_engine_mode(self) -> aspose.html.dom.css.CSSEngineMode:
        ...
    
    @css_engine_mode.setter
    def css_engine_mode(self, value : aspose.html.dom.css.CSSEngineMode):
        ...
    
    @property
    def fonts_settings(self) -> aspose.html.FontsSettings:
        ...
    
    @property
    def show_image_placeholders(self) -> bool:
        ...
    
    @show_image_placeholders.setter
    def show_image_placeholders(self, value : bool):
        ...
    
    ...

