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

class ICanvasDrawingStyles:
    '''The ICanvasDrawingStyles interface provides methods and properties control how lines are drawn and how text is laid out.'''
    
    def set_line_dash(self, segments : List[float]):
        '''Sets the current line dash pattern.
        
        :param segments: An Array of numbers which specify distances to alternately draw a line and a gap (in coordinate space units)'''
        ...
    
    def get_line_dash(self) -> List[float]:
        '''Returns the current line dash pattern array containing an even number of non-negative numbers.
        
        :returns: An Array. A list of numbers that specifies distances to alternately draw a line and a gap (in coordinate space units).'''
        ...
    
    @property
    def line_width(self) -> float:
        ...
    
    @line_width.setter
    def line_width(self, value : float):
        ...
    
    @property
    def line_cap(self) -> str:
        ...
    
    @line_cap.setter
    def line_cap(self, value : str):
        ...
    
    @property
    def line_join(self) -> str:
        ...
    
    @line_join.setter
    def line_join(self, value : str):
        ...
    
    @property
    def miter_limit(self) -> float:
        ...
    
    @miter_limit.setter
    def miter_limit(self, value : float):
        ...
    
    @property
    def line_dash_offset(self) -> float:
        ...
    
    @line_dash_offset.setter
    def line_dash_offset(self, value : float):
        ...
    
    @property
    def font(self) -> str:
        '''Font setting. Default value 10px sans-serif'''
        ...
    
    @font.setter
    def font(self, value : str):
        '''Font setting. Default value 10px sans-serif'''
        ...
    
    @property
    def text_align(self) -> str:
        ...
    
    @text_align.setter
    def text_align(self, value : str):
        ...
    
    @property
    def text_baseline(self) -> str:
        ...
    
    @text_baseline.setter
    def text_baseline(self, value : str):
        ...
    
    ...

class ICanvasGradient:
    '''Represents an opaque object describing a gradient.'''
    
    def add_color_stop(self, offset : float, color : str):
        '''Adds a new stop, defined by an offset and a color, to the gradient.
        
        :param offset: A number between 0 and 1.
        :param color: A CSS color'''
        ...
    
    ...

class ICanvasPathMethods:
    '''The ICanvasPathMethods interface is used to manipulate paths of objects.'''
    
    @overload
    def arc(self, x : float, y : float, radius : float, start_angle : float, end_angle : float):
        '''Adds an arc to the path which is centered at (x, y) position with radius r starting at startAngle and ending at endAngle going in the given direction by anticlockwise (defaulting to clockwise).
        
        :param x: The x coordinate of the arc's center.
        :param y: The y coordinate of the arc's center.
        :param radius: The arc's radius.
        :param start_angle: The angle at which the arc starts, measured clockwise from the positive x axis and expressed in radians.
        :param end_angle: The angle at which the arc ends, measured clockwise from the positive x axis and expressed in radians.'''
        ...
    
    @overload
    def arc(self, x : float, y : float, radius : float, start_angle : float, end_angle : float, counterclockwise : bool):
        '''Adds an arc to the path which is centered at (x, y) position with radius r starting at startAngle and ending at endAngle going in the given direction by anticlockwise (defaulting to clockwise).
        
        :param x: The x coordinate of the arc's center.
        :param y: The y coordinate of the arc's center.
        :param radius: The arc's radius.
        :param start_angle: The angle at which the arc starts, measured clockwise from the positive x axis and expressed in radians.
        :param end_angle: The angle at which the arc ends, measured clockwise from the positive x axis and expressed in radians.
        :param counterclockwise: Causes the arc to be drawn counter-clockwise between the two angles. By default it is drawn clockwise.'''
        ...
    
    @overload
    def ellipse(self, x : float, y : float, radius_x : float, radius_y : float, rotation : float, start_angle : float, end_angle : float):
        '''Adds an ellipse to the path which is centered at (x, y) position with the radii radiusX and radiusY starting at startAngle
        and ending at endAngle going in the given direction by anticlockwise (defaulting to clockwise).
        
        :param x: The x axis of the coordinate for the ellipse's center.
        :param y: The y axis of the coordinate for the ellipse's center.
        :param radius_x: The ellipse's major-axis radius.
        :param radius_y: The ellipse's minor-axis radius.
        :param rotation: The rotation for this ellipse, expressed in radians.
        :param start_angle: The starting point, measured from the x axis, from which it will be drawn, expressed in radians.
        :param end_angle: The end ellipse's angle to which it will be drawn, expressed in radians.'''
        ...
    
    @overload
    def ellipse(self, x : float, y : float, radius_x : float, radius_y : float, rotation : float, start_angle : float, end_angle : float, anticlockwise : bool):
        '''Adds an ellipse to the path which is centered at (x, y) position with the radii radiusX and radiusY starting at startAngle
        and ending at endAngle going in the given direction by anticlockwise (defaulting to clockwise).
        
        :param x: The x axis of the coordinate for the ellipse's center.
        :param y: The y axis of the coordinate for the ellipse's center.
        :param radius_x: The ellipse's major-axis radius.
        :param radius_y: The ellipse's minor-axis radius.
        :param rotation: The rotation for this ellipse, expressed in radians.
        :param start_angle: The starting point, measured from the x axis, from which it will be drawn, expressed in radians.
        :param end_angle: The end ellipse's angle to which it will be drawn, expressed in radians.
        :param anticlockwise: An optional boolean which, if true, draws the ellipse anticlockwise (counter-clockwise), otherwise in a clockwise direction.'''
        ...
    
    def close_path(self):
        '''Causes the point of the pen to move back to the start of the current sub-path.
        It tries to draw a straight line from the current point to the start.
        If the shape has already been closed or has only one point, this function does nothing.'''
        ...
    
    def move_to(self, x : float, y : float):
        '''Moves the starting point of a new sub-path to the (x, y) coordinates.
        
        :param x: The x axis of the point
        :param y: The y axis of the point'''
        ...
    
    def line_to(self, x : float, y : float):
        '''Connects the last point in the subpath to the x, y coordinates with a straight line.
        
        :param x: The x axis of the coordinate for the end of the line.
        :param y: The y axis of the coordinate for the end of the line.'''
        ...
    
    def quadratic_curve_to(self, cpx : float, cpy : float, x : float, y : float):
        '''Adds a quadratic Bézier curve to the current path.
        
        :param cpx: The x axis of the coordinate for the control point.
        :param cpy: The y axis of the coordinate for the control point.
        :param x: The x axis of the coordinate for the end point.
        :param y: The y axis of the coordinate for the end point.'''
        ...
    
    def bezier_curve_to(self, cp_1x : float, cp_1y : float, cp_2x : float, cp_2y : float, x : float, y : float):
        '''Adds a cubic Bézier curve to the path. It requires three points.
        The first two points are control points and the third one is the end point.
        The starting point is the last point in the current path,
        which can be changed using moveTo() before creating the Bézier curve.
        
        :param cp_1x: The x axis of the coordinate for the first control point.
        :param cp_1y: The y axis of the coordinate for the first control point.
        :param cp_2x: The x axis of the coordinate for the second control point.
        :param cp_2y: The y axis of the coordinate for the second control point.
        :param x: The x axis of the coordinate for the end point.
        :param y: The y axis of the coordinate for the end point.'''
        ...
    
    def arc_to(self, x1 : float, y1 : float, x2 : float, y2 : float, radius : float):
        '''Adds an arc to the path with the given control points and radius, connected to the previous point by a straight line.
        
        :param x1: x-axis coordinates for the first control point.
        :param y1: y-axis coordinates for the first control point.
        :param x2: x-axis coordinates for the second control point.
        :param y2: y-axis coordinates for the second control point.
        :param radius: The arc's radius.'''
        ...
    
    def rect(self, x : float, y : float, w : float, h : float):
        '''Creates a path for a rectangle at position (x, y) with a size that is determined by width and height.
        
        :param x: The x axis of the coordinate for the rectangle starting point.
        :param y: The y axis of the coordinate for the rectangle starting point.
        :param w: The rectangle's width.
        :param h: The rectangle's height.'''
        ...
    
    ...

class ICanvasPattern:
    '''Represents an opaque object describing a pattern, based on an image, a canvas or a video.'''
    
    def set_transform(self, transform : aspose.html.dom.svg.datatypes.SVGMatrix):
        '''Applies an SVGMatrix representing a linear transform to the pattern.
        
        :param transform: An SVGMatrix to use as the pattern's transformation matrix.'''
        ...
    
    ...

class ICanvasRenderingContext2D(ICanvasDrawingStyles):
    '''The ICanvasRenderingContext2D interface is used for drawing rectangles, text, images and other objects onto the canvas element. It provides the 2D rendering context for the drawing surface of a canvas element.'''
    
    @overload
    def create_pattern(self, image : aspose.html.HTMLImageElement, repetition : str) -> aspose.html.dom.canvas.ICanvasPattern:
        '''Creates a pattern using the specified image (a CanvasImageSource).
        It repeats the source in the directions specified by the repetition argument.
        
        :param image: A HTMLImageElement to be used as the image to repeat
        :param repetition: A string indicating how to repeat the image.
        :returns: An opaque object describing a pattern.'''
        ...
    
    @overload
    def create_pattern(self, image : aspose.html.HTMLCanvasElement, repetition : str) -> aspose.html.dom.canvas.ICanvasPattern:
        '''Creates a pattern using the specified image (a CanvasImageSource).
        It repeats the source in the directions specified by the repetition argument.
        
        :param image: A HTMLCanvasElement to be used as the image to repeat
        :param repetition: A string indicating how to repeat the image.
        :returns: An opaque object describing a pattern.'''
        ...
    
    @overload
    def fill(self):
        '''Fills the subpaths with the current fill style and default algorithm CanvasFillRule.Nonzero.'''
        ...
    
    @overload
    def fill(self, fill_rule : aspose.html.dom.canvas.CanvasFillRule):
        '''Fills the subpaths with the current fill style.
        
        :param fill_rule: The algorithm by which to determine if a point is inside a path or outside a path.'''
        ...
    
    @overload
    def fill(self, path : aspose.html.dom.canvas.Path2D):
        '''Fills the subpaths with the current fill style and default algorithm CanvasFillRule.Nonzero.
        
        :param path: A Path2D path to fill.'''
        ...
    
    @overload
    def fill(self, path : aspose.html.dom.canvas.Path2D, fill_rule : aspose.html.dom.canvas.CanvasFillRule):
        '''Fills the subpaths with the current fill style.
        
        :param path: A Path2D path to fill.
        :param fill_rule: The algorithm by which to determine if a point is inside a path or outside a path.'''
        ...
    
    @overload
    def stroke(self):
        '''Strokes the subpaths with the current stroke style.'''
        ...
    
    @overload
    def stroke(self, path : aspose.html.dom.canvas.Path2D):
        '''Strokes the subpaths with the current stroke style.
        
        :param path: A Path2D path to stroke.'''
        ...
    
    @overload
    def clip(self):
        '''Creates a new clipping region by calculating the intersection of the current clipping region and the area described by the path, using the non-zero winding number rule.
        Open subpaths must be implicitly closed when computing the clipping region, without affecting the actual subpaths.
        The new clipping region replaces the current clipping region.'''
        ...
    
    @overload
    def clip(self, fill_rule : aspose.html.dom.canvas.CanvasFillRule):
        '''Creates a new clipping region by calculating the intersection of the current clipping region and the area described by the path, using the non-zero winding number rule.
        Open subpaths must be implicitly closed when computing the clipping region, without affecting the actual subpaths.
        The new clipping region replaces the current clipping region.
        
        :param fill_rule: The algorithm by which to determine if a point is inside a path or outside a path'''
        ...
    
    @overload
    def clip(self, path : aspose.html.dom.canvas.Path2D, fill_rule : aspose.html.dom.canvas.CanvasFillRule):
        '''Creates a new clipping region by calculating the intersection of the current clipping region and the area described by the path, using the non-zero winding number rule.
        Open subpaths must be implicitly closed when computing the clipping region, without affecting the actual subpaths.
        The new clipping region replaces the current clipping region.
        
        :param path: A Path2D path to clip.
        :param fill_rule: The algorithm by which to determine if a point is inside a path or outside a path.'''
        ...
    
    @overload
    def is_point_in_path(self, x : float, y : float) -> bool:
        '''Reports whether or not the specified point is contained in the current path.
        
        :param x: The X coordinate of the point to check.
        :param y: The Y coordinate of the point to check.
        :returns: Returns true if the point is inside the area contained by the filling of a path, otherwise false.'''
        ...
    
    @overload
    def is_point_in_path(self, x : float, y : float, fill_rule : aspose.html.dom.canvas.CanvasFillRule) -> bool:
        '''Reports whether or not the specified point is contained in the current path.
        
        :param x: The X coordinate of the point to check.
        :param y: The Y coordinate of the point to check.
        :param fill_rule: The algorithm by which to determine if a point is inside a path or outside a path.
        :returns: Returns true if the point is inside the area contained by the filling of a path, otherwise false.'''
        ...
    
    @overload
    def is_point_in_path(self, path : aspose.html.dom.canvas.Path2D, x : float, y : float) -> bool:
        '''Reports whether or not the specified point is contained in the current path.
        
        :param path: A Path2D path to check.
        :param x: The X coordinate of the point to check.
        :param y: The Y coordinate of the point to check.
        :returns: Returns true if the point is inside the area contained by the filling of a path, otherwise false.'''
        ...
    
    @overload
    def is_point_in_path(self, path : aspose.html.dom.canvas.Path2D, x : float, y : float, fill_rule : aspose.html.dom.canvas.CanvasFillRule) -> bool:
        '''Reports whether or not the specified point is contained in the current path.
        
        :param path: A Path2D path to check.
        :param x: The X coordinate of the point to check.
        :param y: The Y coordinate of the point to check.
        :param fill_rule: The algorithm by which to determine if a point is inside a path or outside a path.
        :returns: Returns true if the point is inside the area contained by the filling of a path, otherwise false.'''
        ...
    
    @overload
    def is_point_in_stroke(self, x : float, y : float) -> bool:
        '''Reports whether or not the specified point is inside the area contained by the stroking of a path.
        
        :param x: The X coordinate of the point to check.
        :param y: The Y coordinate of the point to check.
        :returns: Returns true if the point is inside the area contained by the stroking of a path, otherwise false.'''
        ...
    
    @overload
    def is_point_in_stroke(self, path : aspose.html.dom.canvas.Path2D, x : float, y : float) -> bool:
        '''Reports whether or not the specified point is inside the area contained by the stroking of a path.
        
        :param path: A Path2D path to check.
        :param x: The X coordinate of the point to check.
        :param y: The Y coordinate of the point to check.
        :returns: Returns true if the point is inside the area contained by the stroking of a path, otherwise false.'''
        ...
    
    @overload
    def fill_text(self, text : str, x : float, y : float):
        '''Draws (fills) a given text at the given (x,y) position.
        
        :param text: The text to draw using the current font, textAlign, textBaseline, and direction values.
        :param x: The x axis of the coordinate for the text starting point.
        :param y: The y axis of the coordinate for the text starting point.'''
        ...
    
    @overload
    def fill_text(self, text : str, x : float, y : float, max_width : float):
        '''Draws (fills) a given text at the given (x,y) position.
        
        :param text: The text to draw using the current font, textAlign, textBaseline, and direction values.
        :param x: The x axis of the coordinate for the text starting point.
        :param y: The y axis of the coordinate for the text starting point.
        :param max_width: The maximum width to draw. If specified, and the string is computed to be wider than this width, the font is adjusted to use a more horizontally condensed font (if one is available or if a reasonably readable one can be synthesized by scaling the current font horizontally) or a smaller font.'''
        ...
    
    @overload
    def stroke_text(self, text : str, x : float, y : float):
        '''Draws (strokes) a given text at the given (x, y) position.
        
        :param text: The text to draw using the current font, textAlign, textBaseline, and direction values.
        :param x: The x axis of the coordinate for the text starting point.
        :param y: The y axis of the coordinate for the text starting point.'''
        ...
    
    @overload
    def stroke_text(self, text : str, x : float, y : float, max_width : Optional[float]):
        ...
    
    @overload
    def draw_image(self, image : aspose.html.HTMLImageElement, dx : float, dy : float):
        '''Draws the specified image.
        
        :param image: The HTMLImageElement to draw into the context.
        :param dx: The X coordinate in the destination canvas at which to place the top-left corner of the source image.
        :param dy: The Y coordinate in the destination canvas at which to place the top-left corner of the source image.'''
        ...
    
    @overload
    def draw_image(self, image : aspose.html.HTMLCanvasElement, dx : float, dy : float):
        '''Draws the specified image.
        
        :param image: The HTMLCanvasElement to draw into the context.
        :param dx: The X coordinate in the destination canvas at which to place the top-left corner of the source image.
        :param dy: The Y coordinate in the destination canvas at which to place the top-left corner of the source image.'''
        ...
    
    @overload
    def draw_image(self, image : aspose.html.HTMLImageElement, dx : float, dy : float, dw : float, dh : float):
        '''Draws the specified image.
        
        :param image: The HTMLImageElement to draw into the context.
        :param dx: The X coordinate in the destination canvas at which to place the top-left corner of the source image.
        :param dy: The Y coordinate in the destination canvas at which to place the top-left corner of the source image.
        :param dw: The width to draw the image in the destination canvas. This allows scaling of the drawn image. If not specified, the image is not scaled in width when drawn.
        :param dh: The height to draw the image in the destination canvas. This allows scaling of the drawn image. If not specified, the image is not scaled in height when drawn.'''
        ...
    
    @overload
    def draw_image(self, image : aspose.html.HTMLCanvasElement, dx : float, dy : float, dw : float, dh : float):
        '''Draws the specified image.
        
        :param image: The HTMLCanvasElement to draw into the context.
        :param dx: The X coordinate in the destination canvas at which to place the top-left corner of the source image.
        :param dy: The Y coordinate in the destination canvas at which to place the top-left corner of the source image.
        :param dw: The width to draw the image in the destination canvas. This allows scaling of the drawn image. If not specified, the image is not scaled in width when drawn.
        :param dh: The height to draw the image in the destination canvas. This allows scaling of the drawn image. If not specified, the image is not scaled in height when drawn.'''
        ...
    
    @overload
    def draw_image(self, image : aspose.html.HTMLImageElement, sx : float, sy : float, sw : float, sh : float, dx : float, dy : float, dw : float, dh : float):
        '''Draws the specified image.
        
        :param image: The HTMLImageElement to draw into the context.
        :param sx: The X coordinate of the top left corner of the sub-rectangle of the source image to draw into the destination context.
        :param sy: The Y coordinate of the top left corner of the sub-rectangle of the source image to draw into the destination context.
        :param sw: The width of the sub-rectangle of the source image to draw into the destination context. If not specified, the entire rectangle from the coordinates specified by sx and sy to the bottom-right corner of the image is used.
        :param sh: The height of the sub-rectangle of the source image to draw into the destination context.
        :param dx: The X coordinate in the destination canvas at which to place the top-left corner of the source image.
        :param dy: The Y coordinate in the destination canvas at which to place the top-left corner of the source image.
        :param dw: The width to draw the image in the destination canvas. This allows scaling of the drawn image. If not specified, the image is not scaled in width when drawn.
        :param dh: The height to draw the image in the destination canvas. This allows scaling of the drawn image. If not specified, the image is not scaled in height when drawn.'''
        ...
    
    @overload
    def draw_image(self, image : aspose.html.HTMLCanvasElement, sx : float, sy : float, sw : float, sh : float, dx : float, dy : float, dw : float, dh : float):
        '''Draws the specified image.
        
        :param image: The HTMLCanvasElement to draw into the context.
        :param sx: The X coordinate of the top left corner of the sub-rectangle of the source image to draw into the destination context.
        :param sy: The Y coordinate of the top left corner of the sub-rectangle of the source image to draw into the destination context.
        :param sw: The width of the sub-rectangle of the source image to draw into the destination context. If not specified, the entire rectangle from the coordinates specified by sx and sy to the bottom-right corner of the image is used.
        :param sh: The height of the sub-rectangle of the source image to draw into the destination context.
        :param dx: The X coordinate in the destination canvas at which to place the top-left corner of the source image.
        :param dy: The Y coordinate in the destination canvas at which to place the top-left corner of the source image.
        :param dw: The width to draw the image in the destination canvas. This allows scaling of the drawn image. If not specified, the image is not scaled in width when drawn.
        :param dh: The height to draw the image in the destination canvas. This allows scaling of the drawn image. If not specified, the image is not scaled in height when drawn.'''
        ...
    
    @overload
    def create_image_data(self, sw : float, sh : float) -> aspose.html.dom.canvas.IImageData:
        '''Creates a new, blank ImageData object with the specified dimensions.
        All of the pixels in the new object are transparent black.
        
        :param sw: The width to give the new ImageData object.
        :param sh: The height to give the new ImageData object.
        :returns: A new ImageData object with the specified width and height. The new object is filled with transparent black pixels.'''
        ...
    
    @overload
    def create_image_data(self, imagedata : aspose.html.dom.canvas.IImageData) -> aspose.html.dom.canvas.IImageData:
        '''Creates a new, blank ImageData object with the specified dimensions.
        All of the pixels in the new object are transparent black.
        
        :param imagedata: An existing ImageData object from which to copy the width and height. The image itself is not copied.
        :returns: A new ImageData object with the specified width and height. The new object is filled with transparent black pixels.'''
        ...
    
    @overload
    def put_image_data(self, imagedata : aspose.html.dom.canvas.IImageData, dx : float, dy : float):
        '''Paints data from the given ImageData object onto the bitmap.
        If a dirty rectangle is provided, only the pixels from that rectangle are painted.
        This method is not affected by the canvas transformation matrix.
        
        :param imagedata: An ImageData object containing the array of pixel values.
        :param dx: Horizontal position (x-coordinate) at which to place the image data in the destination canvas.
        :param dy: Vertical position (y-coordinate) at which to place the image data in the destination canvas.'''
        ...
    
    @overload
    def put_image_data(self, imagedata : aspose.html.dom.canvas.IImageData, dx : float, dy : float, dirty_x : float, dirty_y : float, dirty_width : float, dirty_height : float):
        '''Paints data from the given ImageData object onto the bitmap.
        If a dirty rectangle is provided, only the pixels from that rectangle are painted.
        This method is not affected by the canvas transformation matrix.
        
        :param imagedata: An ImageData object containing the array of pixel values.
        :param dx: Horizontal position (x-coordinate) at which to place the image data in the destination canvas.
        :param dy: Vertical position (y-coordinate) at which to place the image data in the destination canvas.
        :param dirty_x: Horizontal position (x-coordinate). The x coordinate of the top left hand corner of your Image data. Defaults to 0.
        :param dirty_y: Vertical position (y-coordinate). The y coordinate of the top left hand corner of your Image data. Defaults to 0.
        :param dirty_width: Width of the rectangle to be painted. Defaults to the width of the image data.
        :param dirty_height: Height of the rectangle to be painted. Defaults to the height of the image data.'''
        ...
    
    @overload
    def arc(self, x : float, y : float, radius : float, start_angle : float, end_angle : float):
        ...
    
    @overload
    def arc(self, x : float, y : float, radius : float, start_angle : float, end_angle : float, counterclockwise : bool):
        ...
    
    @overload
    def ellipse(self, x : float, y : float, radius_x : float, radius_y : float, rotation : float, start_angle : float, end_angle : float):
        ...
    
    @overload
    def ellipse(self, x : float, y : float, radius_x : float, radius_y : float, rotation : float, start_angle : float, end_angle : float, anticlockwise : bool):
        ...
    
    def save(self):
        '''Saves the current drawing style state using a stack so you can revert any change you make to it using restore().'''
        ...
    
    def restore(self):
        '''Restores the drawing style state to the last element on the 'state stack' saved by save().'''
        ...
    
    def scale(self, x : float, y : float):
        '''Adds a scaling transformation to the canvas units by x horizontally and by y vertically.
        
        :param x: Scaling factor in the horizontal direction.
        :param y: Scaling factor in the vertical direction.'''
        ...
    
    def rotate(self, angle : float):
        '''Adds a rotation to the transformation matrix. The angle argument represents a clockwise rotation angle and is expressed in radians.
        
        :param angle: Represents a clockwise rotation angle expressed in radians.'''
        ...
    
    def translate(self, x : float, y : float):
        '''Adds a translation transformation by moving the canvas and its origin x horzontally and y vertically on the grid.
        
        :param x: Distance to move in the horizontal direction.
        :param y: Distance to move in the vertical direction.'''
        ...
    
    def transform(self, a : float, b : float, c : float, d : float, e : float, f : float):
        '''Multiplies the current transformation matrix with the matrix described by its arguments.
        
        :param a: Horizontal scaling.
        :param b: Horizontal skewing.
        :param c: Vertical skewing.
        :param d: Vertical scaling.
        :param e: Horizontal moving.
        :param f: Vertical moving.'''
        ...
    
    def set_transform(self, a : float, b : float, c : float, d : float, e : float, f : float):
        '''Resets the current transform to the identity matrix, and then invokes the transform() method with the same arguments.
        
        :param a: Horizontal scaling.
        :param b: Horizontal skewing.
        :param c: Vertical skewing.
        :param d: Vertical scaling.
        :param e: Horizontal moving.
        :param f: Vertical moving.'''
        ...
    
    def reset_transform(self):
        '''Resets the current transform by the identity matrix.'''
        ...
    
    def create_linear_gradient(self, x0 : float, y0 : float, x1 : float, y1 : float) -> aspose.html.dom.canvas.ICanvasGradient:
        '''Creates a linear gradient along the line given by the coordinates represented by the parameters.
        
        :param x0: The x axis of the coordinate of the start point.
        :param y0: The y axis of the coordinate of the start point.
        :param x1: The x axis of the coordinate of the end point.
        :param y1: The y axis of the coordinate of the end point.
        :returns: The linear CanvasGradient.'''
        ...
    
    def create_radial_gradient(self, x0 : float, y0 : float, r0 : float, x1 : float, y1 : float, r1 : float) -> aspose.html.dom.canvas.ICanvasGradient:
        '''Creates a radial gradient given by the coordinates of the two circles represented by the parameters.
        
        :param x0: The x axis of the coordinate of the start circle.
        :param y0: The y axis of the coordinate of the start circle
        :param r0: The radius of the start circle.
        :param x1: The x axis of the coordinate of the end circle.
        :param y1: The y axis of the coordinate of the end circle.
        :param r1: The radius of the end circle.
        :returns: A radial CanvasGradient initialized with the two specified circles.'''
        ...
    
    def clear_rect(self, x : float, y : float, w : float, h : float):
        '''Sets all pixels in the rectangle defined by starting point (x, y) and size (width, height) to transparent black, erasing any previously drawn content.
        
        :param x: The x axis of the coordinate for the rectangle starting point.
        :param y: The y axis of the coordinate for the rectangle starting point.
        :param w: The rectangle's width.
        :param h: The rectangle's height.'''
        ...
    
    def fill_rect(self, x : float, y : float, w : float, h : float):
        '''Draws a filled rectangle at (x, y) position whose size is determined by width and height.
        
        :param x: The x axis of the coordinate for the rectangle starting point.
        :param y: The y axis of the coordinate for the rectangle starting point.
        :param w: The rectangle's width.
        :param h: The rectangle's height.'''
        ...
    
    def stroke_rect(self, x : float, y : float, w : float, h : float):
        '''Paints a rectangle which has a starting point at (x, y) and has a w width and an h height onto the canvas, using the current stroke style.
        
        :param x: The x axis of the coordinate for the rectangle starting point.
        :param y: The y axis of the coordinate for the rectangle starting point.
        :param w: The rectangle's width.
        :param h: The rectangle's height.'''
        ...
    
    def begin_path(self):
        '''Starts a new path by emptying the list of sub-paths. Call this method when you want to create a new path.'''
        ...
    
    def draw_focus_if_needed(self, element : aspose.html.dom.Element):
        '''If a given element is focused, this method draws a focus ring around the current path.
        
        :param element: The element to check whether it is focused or not.'''
        ...
    
    def measure_text(self, text : str) -> aspose.html.dom.canvas.ITextMetrics:
        '''Returns a TextMetrics object.
        
        :param text: The text to measure.
        :returns: A TextMetrics object.'''
        ...
    
    def remove_hit_region(self, id : str):
        '''Removes the hit region with the specified id from the canvas.
        
        :param id: A string representing the id of the region that is to be removed.'''
        ...
    
    def clear_hit_regions(self):
        '''Removes all hit regions from the canvas.'''
        ...
    
    def get_image_data(self, sx : float, sy : float, sw : float, sh : float) -> aspose.html.dom.canvas.IImageData:
        '''Returns an ImageData object representing the underlying pixel data for the area of the canvas denoted by the rectangle which starts at (sx, sy) and has an sw width and sh height.
        This method is not affected by the canvas transformation matrix.
        
        :param sx: The x coordinate of the upper left corner of the rectangle from which the ImageData will be extracted.
        :param sy: The y coordinate of the upper left corner of the rectangle from which the ImageData will be extracted.
        :param sw: The width of the rectangle from which the ImageData will be extracted.
        :param sh: The height of the rectangle from which the ImageData will be extracted.
        :returns: An ImageData object containing the image data for the given rectangle of the canvas.'''
        ...
    
    def set_line_dash(self, segments : List[float]):
        '''Sets the current line dash pattern.
        
        :param segments: An Array of numbers which specify distances to alternately draw a line and a gap (in coordinate space units)'''
        ...
    
    def get_line_dash(self) -> List[float]:
        '''Returns the current line dash pattern array containing an even number of non-negative numbers.
        
        :returns: An Array. A list of numbers that specifies distances to alternately draw a line and a gap (in coordinate space units).'''
        ...
    
    def close_path(self):
        ...
    
    def move_to(self, x : float, y : float):
        ...
    
    def line_to(self, x : float, y : float):
        ...
    
    def quadratic_curve_to(self, cpx : float, cpy : float, x : float, y : float):
        ...
    
    def bezier_curve_to(self, cp_1x : float, cp_1y : float, cp_2x : float, cp_2y : float, x : float, y : float):
        ...
    
    def arc_to(self, x1 : float, y1 : float, x2 : float, y2 : float, radius : float):
        ...
    
    def rect(self, x : float, y : float, w : float, h : float):
        ...
    
    @property
    def canvas(self) -> aspose.html.HTMLCanvasElement:
        '''A read-only back-reference to the HTMLCanvasElement. Might be null if it is not associated with a canvas element.'''
        ...
    
    @property
    def global_alpha(self) -> float:
        ...
    
    @global_alpha.setter
    def global_alpha(self, value : float):
        ...
    
    @property
    def global_composite_operation(self) -> str:
        ...
    
    @global_composite_operation.setter
    def global_composite_operation(self, value : str):
        ...
    
    @property
    def stroke_style(self) -> any:
        ...
    
    @stroke_style.setter
    def stroke_style(self, value : any):
        ...
    
    @property
    def fill_style(self) -> any:
        ...
    
    @fill_style.setter
    def fill_style(self, value : any):
        ...
    
    @property
    def image_smoothing_enabled(self) -> bool:
        ...
    
    @image_smoothing_enabled.setter
    def image_smoothing_enabled(self, value : bool):
        ...
    
    @property
    def shadow_offset_x(self) -> float:
        ...
    
    @shadow_offset_x.setter
    def shadow_offset_x(self, value : float):
        ...
    
    @property
    def shadow_offset_y(self) -> float:
        ...
    
    @shadow_offset_y.setter
    def shadow_offset_y(self, value : float):
        ...
    
    @property
    def shadow_blur(self) -> float:
        ...
    
    @shadow_blur.setter
    def shadow_blur(self, value : float):
        ...
    
    @property
    def shadow_color(self) -> str:
        ...
    
    @shadow_color.setter
    def shadow_color(self, value : str):
        ...
    
    @property
    def line_width(self) -> float:
        ...
    
    @line_width.setter
    def line_width(self, value : float):
        ...
    
    @property
    def line_cap(self) -> str:
        ...
    
    @line_cap.setter
    def line_cap(self, value : str):
        ...
    
    @property
    def line_join(self) -> str:
        ...
    
    @line_join.setter
    def line_join(self, value : str):
        ...
    
    @property
    def miter_limit(self) -> float:
        ...
    
    @miter_limit.setter
    def miter_limit(self, value : float):
        ...
    
    @property
    def line_dash_offset(self) -> float:
        ...
    
    @line_dash_offset.setter
    def line_dash_offset(self, value : float):
        ...
    
    @property
    def font(self) -> str:
        '''Font setting. Default value 10px sans-serif'''
        ...
    
    @font.setter
    def font(self, value : str):
        '''Font setting. Default value 10px sans-serif'''
        ...
    
    @property
    def text_align(self) -> str:
        ...
    
    @text_align.setter
    def text_align(self, value : str):
        ...
    
    @property
    def text_baseline(self) -> str:
        ...
    
    @text_baseline.setter
    def text_baseline(self, value : str):
        ...
    
    ...

class IImageData:
    '''Creates an ImageData object from a given Uint8ClampedArray and the size of the image it contains.
    If no array is given, it creates an image of a black rectangle.'''
    
    @property
    def width(self) -> int:
        '''Is an unsigned long representing the actual width, in pixels, of the ImageData.'''
        ...
    
    @property
    def height(self) -> int:
        '''Is an unsigned long representing the actual height, in pixels, of the ImageData.'''
        ...
    
    @property
    def data(self) -> aspose.html.Uint8ClampedArray:
        '''Is a Uint8ClampedArray representing a one-dimensional array containing the data in the RGBA order,
        with integer values between 0 and 255 (included).'''
        ...
    
    ...

class ITextMetrics:
    '''Represents the dimension of a text in the canvas.'''
    
    @property
    def width(self) -> float:
        '''Is a double giving the calculated width of a segment of inline text in CSS pixels.'''
        ...
    
    ...

class Path2D(aspose.html.dom.DOMObject):
    '''The Path2D interface of the Canvas 2D API is used to declare paths that are then later used on CanvasRenderingContext2D objects.
    The path methods of the CanvasRenderingContext2D interface are present on this interface as well and are allowing you to create
    paths that you can retain and replay as required on a canvas.'''
    
    @overload
    def add_path(self, path : aspose.html.dom.canvas.Path2D):
        '''Adds to the path the path given by the argument.
        
        :param path: A Path2D path to add.'''
        ...
    
    @overload
    def add_path(self, path : aspose.html.dom.canvas.Path2D, transformation : aspose.html.dom.svg.datatypes.SVGMatrix):
        '''Adds to the path the path given by the argument.
        
        :param path: A Path2D path to add.
        :param transformation: An SVGMatrix to be used as the transformation matrix for the path that is added.'''
        ...
    
    @overload
    def arc(self, x : float, y : float, radius : float, start_angle : float, end_angle : float):
        '''Adds an arc to the path which is centered at (x, y) position with radius r starting at startAngle and ending at endAngle going in the given direction by anticlockwise (defaulting to clockwise).
        
        :param x: The x coordinate of the arc's center.
        :param y: The y coordinate of the arc's center.
        :param radius: The arc's radius.
        :param start_angle: The angle at which the arc starts, measured clockwise from the positive x axis and expressed in radians.
        :param end_angle: The angle at which the arc ends, measured clockwise from the positive x axis and expressed in radians.'''
        ...
    
    @overload
    def arc(self, x : float, y : float, radius : float, start_angle : float, end_angle : float, counterclockwise : bool):
        '''Adds an arc to the path which is centered at (x, y) position with radius r starting at startAngle and ending at endAngle going in the given direction by anticlockwise (defaulting to clockwise).
        
        :param x: The x coordinate of the arc's center.
        :param y: The y coordinate of the arc's center.
        :param radius: The arc's radius.
        :param start_angle: The angle at which the arc starts, measured clockwise from the positive x axis and expressed in radians.
        :param end_angle: The angle at which the arc ends, measured clockwise from the positive x axis and expressed in radians.
        :param counterclockwise: Causes the arc to be drawn counter-clockwise between the two angles. By default it is drawn clockwise.'''
        ...
    
    @overload
    def ellipse(self, x : float, y : float, radius_x : float, radius_y : float, rotation : float, start_angle : float, end_angle : float):
        '''Adds an ellipse to the path which is centered at (x, y) position with the radii radiusX and radiusY starting at startAngle
        and ending at endAngle going in the given direction by anticlockwise (defaulting to clockwise).
        
        :param x: The x axis of the coordinate for the ellipse's center.
        :param y: The y axis of the coordinate for the ellipse's center.
        :param radius_x: The ellipse's major-axis radius.
        :param radius_y: The ellipse's minor-axis radius.
        :param rotation: The rotation for this ellipse, expressed in radians.
        :param start_angle: The starting point, measured from the x axis, from which it will be drawn, expressed in radians.
        :param end_angle: The end ellipse's angle to which it will be drawn, expressed in radians.'''
        ...
    
    @overload
    def ellipse(self, x : float, y : float, radius_x : float, radius_y : float, rotation : float, start_angle : float, end_angle : float, anticlockwise : bool):
        '''Adds an ellipse to the path which is centered at (x, y) position with the radii radiusX and radiusY starting at startAngle
        and ending at endAngle going in the given direction by anticlockwise (defaulting to clockwise).
        
        :param x: The x axis of the coordinate for the ellipse's center.
        :param y: The y axis of the coordinate for the ellipse's center.
        :param radius_x: The ellipse's major-axis radius.
        :param radius_y: The ellipse's minor-axis radius.
        :param rotation: The rotation for this ellipse, expressed in radians.
        :param start_angle: The starting point, measured from the x axis, from which it will be drawn, expressed in radians.
        :param end_angle: The end ellipse's angle to which it will be drawn, expressed in radians.
        :param anticlockwise: An optional boolean which, if true, draws the ellipse anticlockwise (counter-clockwise), otherwise in a clockwise direction.'''
        ...
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def close_path(self):
        '''Causes the point of the pen to move back to the start of the current sub-path.
        It tries to draw a straight line from the current point to the start.
        If the shape has already been closed or has only one point, this function does nothing.'''
        ...
    
    def move_to(self, x : float, y : float):
        '''Moves the starting point of a new sub-path to the (x, y) coordinates.
        
        :param x: The x axis of the point
        :param y: The y axis of the point'''
        ...
    
    def line_to(self, x : float, y : float):
        '''Connects the last point in the subpath to the x, y coordinates with a straight line.
        
        :param x: The x axis of the coordinate for the end of the line.
        :param y: The y axis of the coordinate for the end of the line.'''
        ...
    
    def quadratic_curve_to(self, cpx : float, cpy : float, x : float, y : float):
        '''Adds a quadratic Bézier curve to the current path.
        
        :param cpx: The x axis of the coordinate for the control point.
        :param cpy: The y axis of the coordinate for the control point.
        :param x: The x axis of the coordinate for the end point.
        :param y: The y axis of the coordinate for the end point.'''
        ...
    
    def bezier_curve_to(self, cp_1x : float, cp_1y : float, cp_2x : float, cp_2y : float, x : float, y : float):
        '''Adds a cubic Bézier curve to the path. It requires three points.
        The first two points are control points and the third one is the end point.
        The starting point is the last point in the current path,
        which can be changed using moveTo() before creating the Bézier curve.
        
        :param cp_1x: The x axis of the coordinate for the first control point.
        :param cp_1y: The y axis of the coordinate for the first control point.
        :param cp_2x: The x axis of the coordinate for the second control point.
        :param cp_2y: The y axis of the coordinate for the second control point.
        :param x: The x axis of the coordinate for the end point.
        :param y: The y axis of the coordinate for the end point.'''
        ...
    
    def arc_to(self, x1 : float, y1 : float, x2 : float, y2 : float, radius : float):
        '''Adds an arc to the path with the given control points and radius, connected to the previous point by a straight line.
        
        :param x1: x-axis coordinates for the first control point.
        :param y1: y-axis coordinates for the first control point.
        :param x2: x-axis coordinates for the second control point.
        :param y2: y-axis coordinates for the second control point.
        :param radius: The arc's radius.'''
        ...
    
    def rect(self, x : float, y : float, w : float, h : float):
        '''Creates a path for a rectangle at position (x, y) with a size that is determined by width and height.
        
        :param x: The x axis of the coordinate for the rectangle starting point.
        :param y: The y axis of the coordinate for the rectangle starting point.
        :param w: The rectangle's width.
        :param h: The rectangle's height.'''
        ...
    
    ...

class CanvasFillRule:
    '''This enumeration is used to select the fill rule algorithm by which to determine if a point is inside or outside a path.'''
    
    @classmethod
    @property
    def NON_ZERO(cls) -> CanvasFillRule:
        '''The value "nonzero" value indicates the non-zero winding rule, wherein a point is considered to be outside a
        shape if the number of times a half-infinite straight line drawn from that point crosses the shape's path
        going in one direction is equal to the number of times it crosses the path going in the other direction.'''
        ...
    
    @classmethod
    @property
    def EVEN_ODD(cls) -> CanvasFillRule:
        '''The "evenodd" value indicates the even-odd rule, wherein a point is considered to be outside a shape if the
        number of times a half-infinite straight line drawn from that point crosses the shape's path is even.'''
        ...
    
    ...

