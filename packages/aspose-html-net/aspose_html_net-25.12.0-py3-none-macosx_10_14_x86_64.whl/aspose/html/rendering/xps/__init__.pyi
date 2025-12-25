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

class XpsDevice(aspose.html.rendering.Device):
    '''Represents rendering to a xps document.'''
    
    def save_graphic_context(self):
        ...
    
    def restore_graphic_context(self):
        ...
    
    def begin_document(self, document : aspose.html.dom.Document):
        ...
    
    def end_document(self):
        ...
    
    def begin_page(self, size : aspose.pydrawing.SizeF):
        ...
    
    def end_page(self):
        ...
    
    def flush(self):
        ...
    
    def begin_element(self, element : aspose.html.dom.Element, rect : aspose.pydrawing.RectangleF) -> bool:
        ...
    
    def end_element(self, element : aspose.html.dom.Element):
        ...
    
    def close_path(self):
        ...
    
    def move_to(self, pt : aspose.pydrawing.PointF):
        ...
    
    def line_to(self, pt : aspose.pydrawing.PointF):
        ...
    
    def add_rect(self, rect : aspose.pydrawing.RectangleF):
        ...
    
    def cubic_bezier_to(self, pt1 : aspose.pydrawing.PointF, pt2 : aspose.pydrawing.PointF, pt3 : aspose.pydrawing.PointF):
        ...
    
    def stroke(self):
        ...
    
    def fill(self, rule : aspose.html.rendering.FillRule):
        ...
    
    def clip(self, rule : aspose.html.rendering.FillRule):
        ...
    
    def stroke_and_fill(self, rule : aspose.html.rendering.FillRule):
        ...
    
    def fill_text(self, text : str, pt : aspose.pydrawing.PointF):
        ...
    
    def stroke_text(self, text : str, pt : aspose.pydrawing.PointF):
        ...
    
    def draw_image(self, data : bytes, image_format : aspose.html.drawing.WebImageFormat, rect : aspose.pydrawing.RectangleF):
        ...
    
    @property
    def options(self) -> aspose.html.rendering.xps.XpsRenderingOptions:
        ...
    
    @property
    def graphic_context(self) -> XpsDevice.XpsGraphicContext:
        ...
    
    ...

class XpsRenderingOptions(aspose.html.rendering.RenderingOptions):
    '''Represents rendering options for :py:class:`aspose.html.rendering.xps.XpsDevice`.'''
    
    @property
    def css(self) -> aspose.html.rendering.CssOptions:
        '''Gets a :py:class:`aspose.html.rendering.CssOptions` object which is used for configuration of css properties processing.'''
        ...
    
    @property
    def page_setup(self) -> aspose.html.rendering.PageSetup:
        ...
    
    @property
    def horizontal_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    @property
    def background_color(self) -> aspose.pydrawing.Color:
        ...
    
    @background_color.setter
    def background_color(self, value : aspose.pydrawing.Color):
        ...
    
    @property
    def vertical_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    ...

