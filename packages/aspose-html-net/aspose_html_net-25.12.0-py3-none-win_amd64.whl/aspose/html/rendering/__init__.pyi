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

class CssOptions:
    '''Represents css rendering options.'''
    
    @property
    def media_type(self) -> aspose.html.rendering.MediaType:
        ...
    
    @media_type.setter
    def media_type(self, value : aspose.html.rendering.MediaType):
        ...
    
    ...

class Device:
    '''Represents a base class for implementing rendering devices that are used to draw graphics in various formats and environments.'''
    
    ...

class EpubRenderer(Renderer):
    '''Represents a EPub document renderer.'''
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, timeout : TimeSpan, sources : List[io.RawIOBase]):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : io.RawIOBase, configuration : aspose.html.Configuration):
        '''Renders EPub document into specified :py:class:`aspose.html.rendering.IDevice`.
        
        :param device: The device.
        :param source: The EPub document.
        :param configuration: The configuration.'''
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : io.RawIOBase, configuration : aspose.html.Configuration, timeout : TimeSpan):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, sources : List[io.RawIOBase], configuration : aspose.html.Configuration):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, sources : List[io.RawIOBase], configuration : aspose.html.Configuration, timeout : TimeSpan):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : io.RawIOBase):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : io.RawIOBase, timeout : TimeSpan):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : io.RawIOBase, timeout : int):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, sources : List[io.RawIOBase]):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, timeout : int, sources : List[io.RawIOBase]):
        ...
    
    ...

class GlyphInfo:
    '''Contains glyph related information.'''
    
    @property
    def width(self) -> float:
        '''Gets the width of the glyph, in points.'''
        ...
    
    @property
    def offset(self) -> float:
        '''Gets the offset to the next glyph in points.'''
        ...
    
    @property
    def index(self) -> int:
        '''Gets the index of this glyph in the font.'''
        ...
    
    @property
    def string_representation(self) -> str:
        ...
    
    ...

class GraphicContext:
    '''Holds current graphics control parameters.
    These parameters define the global framework within which the graphics operators execute.'''
    
    def transform(self, matrix : aspose.html.drawing.IMatrix):
        '''Modify the current transformation matrix by multiplying the specified matrix.
        
        :param matrix: Transformation matrix.'''
        ...
    
    def clone(self) -> aspose.html.rendering.GraphicContext:
        '''Creates a new instance of a GraphicContext class with the same property values as an existing instance.
        
        :returns: Instance of a GraphicContext'''
        ...
    
    @property
    def current_element(self) -> aspose.html.dom.Element:
        ...
    
    @property
    def line_cap(self) -> aspose.html.rendering.StrokeLineCap:
        ...
    
    @line_cap.setter
    def line_cap(self, value : aspose.html.rendering.StrokeLineCap):
        ...
    
    @property
    def line_dash_offset(self) -> float:
        ...
    
    @line_dash_offset.setter
    def line_dash_offset(self, value : float):
        ...
    
    @property
    def line_dash_pattern(self) -> List[float]:
        ...
    
    @line_dash_pattern.setter
    def line_dash_pattern(self, value : List[float]):
        ...
    
    @property
    def line_join(self) -> aspose.html.rendering.StrokeLineJoin:
        ...
    
    @line_join.setter
    def line_join(self, value : aspose.html.rendering.StrokeLineJoin):
        ...
    
    @property
    def line_width(self) -> float:
        ...
    
    @line_width.setter
    def line_width(self, value : float):
        ...
    
    @property
    def miter_limit(self) -> float:
        ...
    
    @miter_limit.setter
    def miter_limit(self, value : float):
        ...
    
    @property
    def fill_brush(self) -> aspose.html.drawing.IBrush:
        ...
    
    @fill_brush.setter
    def fill_brush(self, value : aspose.html.drawing.IBrush):
        ...
    
    @property
    def stroke_brush(self) -> aspose.html.drawing.IBrush:
        ...
    
    @stroke_brush.setter
    def stroke_brush(self, value : aspose.html.drawing.IBrush):
        ...
    
    @property
    def font(self) -> aspose.html.drawing.ITrueTypeFont:
        '''Sets or gets the true type font object that is used for rendering text.'''
        ...
    
    @font.setter
    def font(self, value : aspose.html.drawing.ITrueTypeFont):
        '''Sets or gets the true type font object that is used for rendering text.'''
        ...
    
    @property
    def font_size(self) -> float:
        ...
    
    @font_size.setter
    def font_size(self, value : float):
        ...
    
    @property
    def font_style(self) -> aspose.html.drawing.WebFontStyle:
        ...
    
    @font_style.setter
    def font_style(self, value : aspose.html.drawing.WebFontStyle):
        ...
    
    @property
    def character_spacing(self) -> float:
        ...
    
    @character_spacing.setter
    def character_spacing(self, value : float):
        ...
    
    @property
    def transformation_matrix(self) -> aspose.html.drawing.IMatrix:
        ...
    
    @transformation_matrix.setter
    def transformation_matrix(self, value : aspose.html.drawing.IMatrix):
        ...
    
    @property
    def text_info(self) -> aspose.html.rendering.TextInfo:
        ...
    
    ...

class HtmlRenderer(Renderer):
    '''Represents an HTML document renderer.'''
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, timeout : TimeSpan, sources : List[aspose.html.HTMLDocument]):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : aspose.html.HTMLDocument):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : aspose.html.HTMLDocument, timeout : TimeSpan):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : aspose.html.HTMLDocument, timeout : int):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, sources : List[aspose.html.HTMLDocument]):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, timeout : int, sources : List[aspose.html.HTMLDocument]):
        ...
    
    ...

class IDevice:
    '''Defines methods and properties that support custom rendering of the graphic elements like paths, text and images.'''
    
    def save_graphic_context(self):
        '''Pushes a copy of the entire graphics context onto the stack.'''
        ...
    
    def restore_graphic_context(self):
        '''Restores the entire graphics context to its former value by popping it from the stack.'''
        ...
    
    def begin_document(self, document : aspose.html.dom.Document):
        '''Begins rendering of the document.
        
        :param document: The document.'''
        ...
    
    def end_document(self):
        '''Ends rendering of the document.'''
        ...
    
    def begin_page(self, size : aspose.pydrawing.SizeF):
        '''Begins rendering of the new page.
        
        :param size: Size of the page.'''
        ...
    
    def end_page(self):
        '''Ends rendering of the current page.'''
        ...
    
    def begin_element(self, element : aspose.html.dom.Element, rect : aspose.pydrawing.RectangleF) -> bool:
        '''Begins rendering of the element.
        
        :param element: The :py:class:`aspose.html.dom.Element`.
        :param rect: Bounding box of the node.
        :returns: Returns [true] if element should be processed.'''
        ...
    
    def end_element(self, element : aspose.html.dom.Element):
        '''Ends rendering of the element.
        
        :param element: The :py:class:`aspose.html.dom.Element`.'''
        ...
    
    def close_path(self):
        '''Closes the current subpath by appending a straight line segment from the current point to the starting point of the subpath.
        If the current subpath is already closed, "ClosePath" does nothing.
        This operator terminates the current subpath. Appending another segment to the current path begins a new subpath,
        even if the new segment begins at the endpoint reached by the "ClosePath" method.'''
        ...
    
    def move_to(self, pt : aspose.pydrawing.PointF):
        '''Begins a new subpath by moving the current point to coordinates of the parameter pt, omitting any connecting line segment.
        If the previous path construction method in the current path was also "MoveTo", the new "MoveTo" overrides it;
        no vestige of the previous "MoveTo" operation remains in the path.
        
        :param pt: Point of where to move the path to.'''
        ...
    
    def line_to(self, pt : aspose.pydrawing.PointF):
        '''Appends a straight line segment from the current point to the point (pt). The new current point is pt.
        
        :param pt: Point of where to create the line to.'''
        ...
    
    def add_rect(self, rect : aspose.pydrawing.RectangleF):
        '''Appends a rectangle to the current path as a complete subpath.
        
        :param rect: A rectangle to draw.'''
        ...
    
    def cubic_bezier_to(self, pt1 : aspose.pydrawing.PointF, pt2 : aspose.pydrawing.PointF, pt3 : aspose.pydrawing.PointF):
        '''Appends a cubic Bézier curve to the current path. The curve extends from the current point to the point pt3,
        using pt1 and pt2 as the Bézier control points. The new current point is pt3.
        
        :param pt1: Coordinates of first point
        :param pt2: Coordinates of second point
        :param pt3: Coordinates of third point'''
        ...
    
    def stroke(self):
        '''Strokes a line along the current path. The stroked line follows each straight or curved segment in the path,
        centered on the segment with sides parallel to it. Each of the path’s subpaths is treated separately.
        This method terminates current path.'''
        ...
    
    def fill(self, rule : aspose.html.rendering.FillRule):
        '''Fills the entire region enclosed by the current path.
        If the path consists of several disconnected subpaths, it fills the insides of all subpaths,
        considered together.
        This method terminates current path.
        
        :param rule: Filling rule specifies how the interior of a closed path is filled'''
        ...
    
    def clip(self, rule : aspose.html.rendering.FillRule):
        '''Modifies the current clipping path by intersecting it with the current path, using the FillRule to determine the region to fill.
        This method terminates current path.
        
        :param rule: Filling rule specifies how the interior of a closed path is clipped'''
        ...
    
    def stroke_and_fill(self, rule : aspose.html.rendering.FillRule):
        '''Strokes and fill current path.
        This method terminates current path.
        
        :param rule: Filling rule specifies how the interior of a closed path is filled.'''
        ...
    
    def fill_text(self, text : str, pt : aspose.pydrawing.PointF):
        '''Fills the specified text string at the specified location.
        
        :param text: String to fill.
        :param pt: Point that specifies the coordinates of the text.'''
        ...
    
    def stroke_text(self, text : str, pt : aspose.pydrawing.PointF):
        '''Strokes the specified text string at the specified location.
        
        :param text: String to stroke.
        :param pt: Point that specifies the coordinates where to start the text.'''
        ...
    
    def draw_image(self, data : bytes, image_format : aspose.html.drawing.WebImageFormat, rect : aspose.pydrawing.RectangleF):
        '''Draws the specified image.
        
        :param data: An array of bytes representing the image.
        :param image_format: Image format.
        :param rect: A rectangle which determines position and size to draw.'''
        ...
    
    def flush(self):
        '''Flushes all data to output stream.'''
        ...
    
    @property
    def options(self) -> aspose.html.rendering.RenderingOptions:
        '''Gets rendering options.'''
        ...
    
    @property
    def graphic_context(self) -> aspose.html.rendering.GraphicContext:
        ...
    
    ...

class MhtmlRenderer(Renderer):
    '''Represents a MHTML document renderer.'''
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, timeout : TimeSpan, sources : List[io.RawIOBase]):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : io.RawIOBase, configuration : aspose.html.Configuration):
        '''Renders MHTML document into specified :py:class:`aspose.html.rendering.IDevice`.
        
        :param device: The device.
        :param source: The MHTML document.
        :param configuration: The configuration.'''
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : io.RawIOBase, configuration : aspose.html.Configuration, timeout : TimeSpan):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, sources : List[io.RawIOBase], configuration : aspose.html.Configuration):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, sources : List[io.RawIOBase], configuration : aspose.html.Configuration, timeout : TimeSpan):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : io.RawIOBase):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : io.RawIOBase, timeout : TimeSpan):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : io.RawIOBase, timeout : int):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, sources : List[io.RawIOBase]):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, timeout : int, sources : List[io.RawIOBase]):
        ...
    
    ...

class PageSetup:
    '''Represents a page setup object is used for configuration output page-set.'''
    
    def set_left_right_page(self, left_page : aspose.html.drawing.Page, right_page : aspose.html.drawing.Page):
        '''Sets the Left/Right page configuration.
        
        :param left_page: The left page.
        :param right_page: The right page.'''
        ...
    
    @property
    def at_page_priority(self) -> aspose.html.rendering.AtPagePriority:
        ...
    
    @at_page_priority.setter
    def at_page_priority(self, value : aspose.html.rendering.AtPagePriority):
        ...
    
    @property
    def page_layout_options(self) -> aspose.html.rendering.PageLayoutOptions:
        ...
    
    @page_layout_options.setter
    def page_layout_options(self, value : aspose.html.rendering.PageLayoutOptions):
        ...
    
    @property
    def adjust_to_widest_page(self) -> bool:
        ...
    
    @adjust_to_widest_page.setter
    def adjust_to_widest_page(self, value : bool):
        ...
    
    @property
    def scale_limit(self) -> float:
        ...
    
    @scale_limit.setter
    def scale_limit(self, value : float):
        ...
    
    @property
    def left_page(self) -> aspose.html.drawing.Page:
        ...
    
    @property
    def right_page(self) -> aspose.html.drawing.Page:
        ...
    
    @property
    def any_page(self) -> aspose.html.drawing.Page:
        ...
    
    @any_page.setter
    def any_page(self, value : aspose.html.drawing.Page):
        ...
    
    @property
    def first_page(self) -> aspose.html.drawing.Page:
        ...
    
    @first_page.setter
    def first_page(self, value : aspose.html.drawing.Page):
        ...
    
    ...

class Renderer:
    '''Represents a base class for all renderers and implemnts IDisposable interface.'''
    
    ...

class RenderingOptions:
    '''Represents rendering options.'''
    
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

class SvgRenderer(Renderer):
    '''Represents SVG document renderer.'''
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, timeout : TimeSpan, sources : List[aspose.html.dom.svg.SVGDocument]):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : aspose.html.dom.svg.SVGDocument):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : aspose.html.dom.svg.SVGDocument, timeout : TimeSpan):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, source : aspose.html.dom.svg.SVGDocument, timeout : int):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, sources : List[aspose.html.dom.svg.SVGDocument]):
        ...
    
    @overload
    def render(self, device : aspose.html.rendering.IDevice, timeout : int, sources : List[aspose.html.dom.svg.SVGDocument]):
        ...
    
    ...

class TextInfo:
    '''Contains information about rendered text.'''
    
    @property
    def glyph_infos(self) -> List[aspose.html.rendering.GlyphInfo]:
        ...
    
    ...

class AtPagePriority:
    '''Specifies possible orders of applying page size declarations.'''
    
    @classmethod
    @property
    def OPTIONS_PRIORITY(cls) -> AtPagePriority:
        '''Specifies that :py:class:`aspose.html.rendering.PageSetup` values declared in :py:class:`aspose.html.rendering.RenderingOptions` will override values defined in css by ``@page`` rules :link:`https://www.w3.org/TR/CSS2/page.html#page-selectors`.'''
        ...
    
    @classmethod
    @property
    def CSS_PRIORITY(cls) -> AtPagePriority:
        '''Specifies that ``@page`` rules :link:`https://www.w3.org/TR/CSS2/page.html#page-selectors` defined in css will override values defined in :py:class:`aspose.html.rendering.PageSetup`.'''
        ...
    
    ...

class FillRule:
    '''Specifies the fill rule used in rendering SVG and HTML.'''
    
    @classmethod
    @property
    def EVEN_ODD(cls) -> FillRule:
        '''Determines the fill area using the even-odd rule. The behavior corresponds to System.Drawing.Drawing2D.FillMode.Alternate.'''
        ...
    
    @classmethod
    @property
    def NONZERO(cls) -> FillRule:
        '''Determines the fill area using the non-zero rule. The behavior corresponds to System.Drawing.Drawing2D.FillMode.Winding.'''
        ...
    
    ...

class MediaType:
    '''Specifies possible media types used during rendering.'''
    
    @classmethod
    @property
    def PRINT(cls) -> MediaType:
        '''The ``Print`` media is used during rendering.'''
        ...
    
    @classmethod
    @property
    def SCREEN(cls) -> MediaType:
        '''The ``Screen`` media is used during rendering.'''
        ...
    
    ...

class PageLayoutOptions:
    '''Specifies flags that together with other PageSetup options determine sizes and layouts of pages.
    These flags can be combined together according to their descriptions.'''
    
    @classmethod
    @property
    def NONE(cls) -> PageLayoutOptions:
        '''Default value which indicates that the PageLayoutOptions will not affect the sizes and layouts of pages.'''
        ...
    
    @classmethod
    @property
    def FIT_TO_CONTENT_WIDTH(cls) -> PageLayoutOptions:
        '''This flag indicates that the width of the pages is determined from the content size itself, not from the specified page width.
        The width of content is calculated individually for every page.'''
        ...
    
    @classmethod
    @property
    def USE_WIDEST_PAGE(cls) -> PageLayoutOptions:
        '''When combined with :py:attr:`aspose.html.rendering.PageLayoutOptions.FIT_TO_CONTENT_WIDTH` indicates that the width of every page will be the same and will be equal to the widest content size among all pages.'''
        ...
    
    @classmethod
    @property
    def FIT_TO_WIDEST_CONTENT_WIDTH(cls) -> PageLayoutOptions:
        '''This flag indicates that the width of the page is determined from the content size itself, not from the specified page width.
        The width of every page will be the same and will be equal to the widest content size among all pages.'''
        ...
    
    @classmethod
    @property
    def FIT_TO_CONTENT_HEIGHT(cls) -> PageLayoutOptions:
        '''This flag indicates that the height of the page is determined from the content size itself, not from the specified page height.
        All the documents content will be located on the single page if this flag is specified.'''
        ...
    
    @classmethod
    @property
    def SCALE_TO_PAGE_WIDTH(cls) -> PageLayoutOptions:
        '''This flag indicates that the content of the document will be scaled to fit the page where the difference between the available page width and the overlapping content is greatest.
        It collides with :py:attr:`aspose.html.rendering.PageLayoutOptions.FIT_TO_CONTENT_WIDTH` flag and if both flags are specified only :py:attr:`aspose.html.rendering.PageLayoutOptions.SCALE_TO_PAGE_WIDTH` will take affect.'''
        ...
    
    @classmethod
    @property
    def SCALE_TO_PAGE_HEIGHT(cls) -> PageLayoutOptions:
        '''This flag indicates that the content of the document will be scaled to fit the height of the first page.
        It collides with :py:attr:`aspose.html.rendering.PageLayoutOptions.FIT_TO_CONTENT_HEIGHT` flag and if both flags are specified only :py:attr:`aspose.html.rendering.PageLayoutOptions.SCALE_TO_PAGE_HEIGHT` will take affect.
        All document content will be placed on the single page only.'''
        ...
    
    ...

class StrokeLineCap:
    '''Specifies the line cap used in rendering SVG and HTML.'''
    
    @classmethod
    @property
    def BUTT(cls) -> StrokeLineCap:
        '''The stroke ends with a flat edge.'''
        ...
    
    @classmethod
    @property
    def SQUARE(cls) -> StrokeLineCap:
        '''The stroke ends with a square projection beyond the endpoint.'''
        ...
    
    @classmethod
    @property
    def ROUND(cls) -> StrokeLineCap:
        '''The stroke ends with a rounded cap.'''
        ...
    
    ...

class StrokeLineJoin:
    '''Specifies the line join style used in rendering SVG and HTML.'''
    
    @classmethod
    @property
    def MITER(cls) -> StrokeLineJoin:
        '''The line joins with a sharp point, extending beyond the endpoints.'''
        ...
    
    @classmethod
    @property
    def ROUND(cls) -> StrokeLineJoin:
        '''The line joins with a rounded corner.'''
        ...
    
    @classmethod
    @property
    def BEVEL(cls) -> StrokeLineJoin:
        '''The line joins with a beveled corner.'''
        ...
    
    ...

