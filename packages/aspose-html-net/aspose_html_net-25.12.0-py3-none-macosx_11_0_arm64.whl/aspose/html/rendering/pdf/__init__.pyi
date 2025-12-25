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

class PdfDevice(aspose.html.rendering.Device):
    '''Represents rendering to a pdf document.'''
    
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
    def options(self) -> aspose.html.rendering.pdf.PdfRenderingOptions:
        ...
    
    @property
    def graphic_context(self) -> PdfDevice.PdfGraphicContext:
        ...
    
    ...

class PdfDocumentInfo:
    '''Represents the information about the PDF document.'''
    
    @property
    def title(self) -> str:
        '''The document's title.'''
        ...
    
    @title.setter
    def title(self, value : str):
        '''The document's title.'''
        ...
    
    @property
    def author(self) -> str:
        '''The name of the person who created the document.'''
        ...
    
    @author.setter
    def author(self, value : str):
        '''The name of the person who created the document.'''
        ...
    
    @property
    def subject(self) -> str:
        '''The subject of the document.'''
        ...
    
    @subject.setter
    def subject(self, value : str):
        '''The subject of the document.'''
        ...
    
    @property
    def keywords(self) -> str:
        '''Keywords associated with the document.'''
        ...
    
    @keywords.setter
    def keywords(self, value : str):
        '''Keywords associated with the document.'''
        ...
    
    @property
    def creator(self) -> str:
        '''The name of the product that created the original document.'''
        ...
    
    @creator.setter
    def creator(self, value : str):
        '''The name of the product that created the original document.'''
        ...
    
    @property
    def producer(self) -> str:
        '''The name of the product that converted the document.'''
        ...
    
    @producer.setter
    def producer(self, value : str):
        '''The name of the product that converted the document.'''
        ...
    
    @property
    def creation_date(self) -> DateTime:
        ...
    
    @creation_date.setter
    def creation_date(self, value : DateTime):
        ...
    
    @property
    def modification_date(self) -> DateTime:
        ...
    
    @modification_date.setter
    def modification_date(self, value : DateTime):
        ...
    
    ...

class PdfRenderingOptions(aspose.html.rendering.RenderingOptions):
    '''Represents rendering options for :py:class:`aspose.html.rendering.pdf.PdfDevice`.'''
    
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
    
    @property
    def document_info(self) -> aspose.html.rendering.pdf.PdfDocumentInfo:
        ...
    
    @property
    def form_field_behaviour(self) -> aspose.html.rendering.pdf.FormFieldBehaviour:
        ...
    
    @form_field_behaviour.setter
    def form_field_behaviour(self, value : aspose.html.rendering.pdf.FormFieldBehaviour):
        ...
    
    @property
    def jpeg_quality(self) -> int:
        ...
    
    @jpeg_quality.setter
    def jpeg_quality(self, value : int):
        ...
    
    @property
    def encryption(self) -> aspose.html.rendering.pdf.encryption.PdfEncryptionInfo:
        '''Gets a encryption details. If not set, then no encryption will be performed.'''
        ...
    
    @encryption.setter
    def encryption(self, value : aspose.html.rendering.pdf.encryption.PdfEncryptionInfo):
        '''Sets a encryption details. If not set, then no encryption will be performed.'''
        ...
    
    @property
    def is_tagged_pdf(self) -> bool:
        ...
    
    @is_tagged_pdf.setter
    def is_tagged_pdf(self, value : bool):
        ...
    
    ...

class FormFieldBehaviour:
    '''This enumeration is used to specify the behavior of form fields in the output PDF document.'''
    
    @classmethod
    @property
    def INTERACTIVE(cls) -> FormFieldBehaviour:
        '''The output PDF document will contain interactive form fields.'''
        ...
    
    @classmethod
    @property
    def FLATTENED(cls) -> FormFieldBehaviour:
        '''The output PDF document will contain flattened form fields.'''
        ...
    
    ...

