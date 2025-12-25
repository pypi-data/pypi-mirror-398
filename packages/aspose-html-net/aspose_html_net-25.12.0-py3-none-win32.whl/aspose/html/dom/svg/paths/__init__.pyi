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

class ISVGAnimatedPathData:
    '''he SVGAnimatedPathData interface supports elements which have a ‘d’ attribute which holds SVG path data, and supports the ability to animate that attribute.'''
    
    @property
    def path_seg_list(self) -> aspose.html.dom.svg.paths.SVGPathSegList:
        ...
    
    @property
    def animated_path_seg_list(self) -> aspose.html.dom.svg.paths.SVGPathSegList:
        ...
    
    ...

class SVGPathSeg(aspose.html.dom.svg.datatypes.SVGValueType):
    '''The SVGPathSeg interface is a base interface that corresponds to a single command within a path data specification.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    ...

class SVGPathSegArcAbs(SVGPathSeg):
    '''The SVGPathSegArcAbs interface corresponds to an "absolute arcto" (A) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @property
    def r1(self) -> float:
        '''The x-axis radius for the ellipse (i.e., r1).'''
        ...
    
    @r1.setter
    def r1(self, value : float):
        '''The x-axis radius for the ellipse (i.e., r1).'''
        ...
    
    @property
    def r2(self) -> float:
        '''The y-axis radius for the ellipse (i.e., r2).'''
        ...
    
    @r2.setter
    def r2(self, value : float):
        '''The y-axis radius for the ellipse (i.e., r2).'''
        ...
    
    @property
    def angle(self) -> float:
        '''The rotation angle in degrees for the ellipse's x-axis relative to the x-axis of the user coordinate system.'''
        ...
    
    @angle.setter
    def angle(self, value : float):
        '''The rotation angle in degrees for the ellipse's x-axis relative to the x-axis of the user coordinate system.'''
        ...
    
    @property
    def large_arc_flag(self) -> bool:
        ...
    
    @large_arc_flag.setter
    def large_arc_flag(self, value : bool):
        ...
    
    @property
    def sweep_flag(self) -> bool:
        ...
    
    @sweep_flag.setter
    def sweep_flag(self, value : bool):
        ...
    
    ...

class SVGPathSegArcRel(SVGPathSeg):
    '''The SVGPathSegArcRel interface corresponds to a "relative arcto" (a) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @property
    def r1(self) -> float:
        '''The x-axis radius for the ellipse (i.e., r1).'''
        ...
    
    @r1.setter
    def r1(self, value : float):
        '''The x-axis radius for the ellipse (i.e., r1).'''
        ...
    
    @property
    def r2(self) -> float:
        '''The y-axis radius for the ellipse (i.e., r2).'''
        ...
    
    @r2.setter
    def r2(self, value : float):
        '''The y-axis radius for the ellipse (i.e., r2).'''
        ...
    
    @property
    def angle(self) -> float:
        '''The rotation angle in degrees for the ellipse's x-axis relative to the x-axis of the user coordinate system.'''
        ...
    
    @angle.setter
    def angle(self, value : float):
        '''The rotation angle in degrees for the ellipse's x-axis relative to the x-axis of the user coordinate system.'''
        ...
    
    @property
    def large_arc_flag(self) -> bool:
        ...
    
    @large_arc_flag.setter
    def large_arc_flag(self, value : bool):
        ...
    
    @property
    def sweep_flag(self) -> bool:
        ...
    
    @sweep_flag.setter
    def sweep_flag(self, value : bool):
        ...
    
    ...

class SVGPathSegClosePath(SVGPathSeg):
    '''he SVGPathSegClosePath interface corresponds to a "closepath" (z) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    ...

class SVGPathSegCurvetoCubicAbs(SVGPathSeg):
    '''The SVGPathSegCurvetoCubicAbs interface corresponds to an "absolute cubic Bézier curveto" (C) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @property
    def x1(self) -> float:
        '''The absolute X coordinate for the first control point.'''
        ...
    
    @x1.setter
    def x1(self, value : float):
        '''The absolute X coordinate for the first control point.'''
        ...
    
    @property
    def y1(self) -> float:
        '''The absolute Y coordinate for the first control point.'''
        ...
    
    @y1.setter
    def y1(self, value : float):
        '''The absolute Y coordinate for the first control point.'''
        ...
    
    @property
    def x2(self) -> float:
        '''The absolute X coordinate for the second control point.'''
        ...
    
    @x2.setter
    def x2(self, value : float):
        '''The absolute X coordinate for the second control point.'''
        ...
    
    @property
    def y2(self) -> float:
        '''The absolute Y coordinate for the second control point.'''
        ...
    
    @y2.setter
    def y2(self, value : float):
        '''The absolute Y coordinate for the second control point.'''
        ...
    
    ...

class SVGPathSegCurvetoCubicRel(SVGPathSeg):
    '''The SVGPathSegCurvetoCubicRel interface corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @property
    def x1(self) -> float:
        '''The relative X coordinate for the first control point.'''
        ...
    
    @x1.setter
    def x1(self, value : float):
        '''The relative X coordinate for the first control point.'''
        ...
    
    @property
    def y1(self) -> float:
        '''The relative Y coordinate for the first control point.'''
        ...
    
    @y1.setter
    def y1(self, value : float):
        '''The relative Y coordinate for the first control point.'''
        ...
    
    @property
    def x2(self) -> float:
        '''The relative X coordinate for the second control point.'''
        ...
    
    @x2.setter
    def x2(self, value : float):
        '''The relative X coordinate for the second control point.'''
        ...
    
    @property
    def y2(self) -> float:
        '''The relative Y coordinate for the second control point.'''
        ...
    
    @y2.setter
    def y2(self, value : float):
        '''The relative Y coordinate for the second control point.'''
        ...
    
    ...

class SVGPathSegCurvetoCubicSmoothAbs(SVGPathSeg):
    '''The SVGPathSegCurvetoCubicSmoothAbs interface corresponds to an "absolute smooth cubic curveto" (S) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @property
    def x2(self) -> float:
        '''The absolute X coordinate for the second control point.'''
        ...
    
    @x2.setter
    def x2(self, value : float):
        '''The absolute X coordinate for the second control point.'''
        ...
    
    @property
    def y2(self) -> float:
        '''The absolute Y coordinate for the second control point.'''
        ...
    
    @y2.setter
    def y2(self, value : float):
        '''The absolute Y coordinate for the second control point.'''
        ...
    
    ...

class SVGPathSegCurvetoCubicSmoothRel(SVGPathSeg):
    '''The SVGPathSegCurvetoCubicSmoothRel interface corresponds to a "relative smooth cubic curveto" (s) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @property
    def x2(self) -> float:
        '''The relative X coordinate for the second control point.'''
        ...
    
    @x2.setter
    def x2(self, value : float):
        '''The relative X coordinate for the second control point.'''
        ...
    
    @property
    def y2(self) -> float:
        '''The relative Y coordinate for the second control point.'''
        ...
    
    @y2.setter
    def y2(self, value : float):
        '''The relative Y coordinate for the second control point.'''
        ...
    
    ...

class SVGPathSegCurvetoQuadraticAbs(SVGPathSeg):
    '''The SVGPathSegCurvetoQuadraticAbs interface corresponds to an "absolute quadratic Bézier curveto" (Q) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @property
    def x1(self) -> float:
        '''The absolute X coordinate for the first control point.'''
        ...
    
    @x1.setter
    def x1(self, value : float):
        '''The absolute X coordinate for the first control point.'''
        ...
    
    @property
    def y1(self) -> float:
        '''The absolute Y coordinate for the first control point.'''
        ...
    
    @y1.setter
    def y1(self, value : float):
        '''The absolute Y coordinate for the first control point.'''
        ...
    
    ...

class SVGPathSegCurvetoQuadraticRel(SVGPathSeg):
    '''The SVGPathSegCurvetoQuadraticRel interface corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @property
    def x1(self) -> float:
        '''The relative X coordinate for the first control point.'''
        ...
    
    @x1.setter
    def x1(self, value : float):
        '''The relative X coordinate for the first control point.'''
        ...
    
    @property
    def y1(self) -> float:
        '''The relative Y coordinate for the first control point.'''
        ...
    
    @y1.setter
    def y1(self, value : float):
        '''The relative Y coordinate for the first control point.'''
        ...
    
    ...

class SVGPathSegCurvetoQuadraticSmoothAbs(SVGPathSeg):
    '''The SVGPathSegCurvetoQuadraticSmoothAbs interface corresponds to an "absolute smooth cubic curveto" (T) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    ...

class SVGPathSegCurvetoQuadraticSmoothRel(SVGPathSeg):
    '''The SVGPathSegCurvetoQuadraticSmoothRel interface corresponds to a "relative smooth cubic curveto" (t) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    ...

class SVGPathSegLinetoAbs(SVGPathSeg):
    '''The SVGPathSegLinetoAbs interface corresponds to an "absolute lineto" (L) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    ...

class SVGPathSegLinetoHorizontalAbs(SVGPathSeg):
    '''The SVGPathSegLinetoHorizontalAbs interface corresponds to an "absolute horizontal lineto" (H) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    ...

class SVGPathSegLinetoHorizontalRel(SVGPathSeg):
    '''The SVGPathSegLinetoHorizontalRel interface corresponds to a "relative horizontal lineto" (h) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    ...

class SVGPathSegLinetoRel(SVGPathSeg):
    '''The SVGPathSegLinetoRel interface corresponds to a "relative lineto" (l) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    ...

class SVGPathSegLinetoVerticalAbs(SVGPathSeg):
    '''The SVGPathSegLinetoVerticalAbs interface corresponds to an "absolute vertical lineto" (V) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def y(self) -> float:
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    ...

class SVGPathSegLinetoVerticalRel(SVGPathSeg):
    '''The SVGPathSegLinetoVerticalRel interface corresponds to a "relative vertical lineto" (v) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def y(self) -> float:
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    ...

class SVGPathSegList(aspose.html.dom.svg.datatypes.SVGValueType):
    '''This interface defines a list of SVGPathSeg objects.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def clear(self):
        ...
    
    def initialize(self, new_item : aspose.html.dom.svg.paths.SVGPathSeg) -> aspose.html.dom.svg.paths.SVGPathSeg:
        ...
    
    def get_item(self, index : int) -> aspose.html.dom.svg.paths.SVGPathSeg:
        ...
    
    def insert_item_before(self, new_item : aspose.html.dom.svg.paths.SVGPathSeg, index : int) -> aspose.html.dom.svg.paths.SVGPathSeg:
        ...
    
    def replace_item(self, new_item : aspose.html.dom.svg.paths.SVGPathSeg, index : int) -> aspose.html.dom.svg.paths.SVGPathSeg:
        ...
    
    def remove_item(self, index : int) -> aspose.html.dom.svg.paths.SVGPathSeg:
        ...
    
    def append_item(self, new_item : aspose.html.dom.svg.paths.SVGPathSeg) -> aspose.html.dom.svg.paths.SVGPathSeg:
        ...
    
    @property
    def length(self) -> int:
        ...
    
    @property
    def number_of_items(self) -> int:
        ...
    
    def __getitem__(self, key : int) -> aspose.html.dom.svg.paths.SVGPathSeg:
        ...
    
    def __setitem__(self, key : int, value : aspose.html.dom.svg.paths.SVGPathSeg):
        ...
    
    ...

class SVGPathSegMovetoAbs(SVGPathSeg):
    '''The SVGPathSegMovetoAbs interface corresponds to an "absolute moveto" (M) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The absolute X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The absolute Y coordinate for the end point of this path segment.'''
        ...
    
    ...

class SVGPathSegMovetoRel(SVGPathSeg):
    '''The SVGPathSegMovetoRel interface corresponds to a "relative moveto" (m) path data command.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def path_seg_type(self) -> int:
        ...
    
    @property
    def path_seg_type_as_letter(self) -> str:
        ...
    
    @classmethod
    @property
    def PATHSEG_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CLOSEPATH(cls) -> int:
        '''Corresponds to a "closepath" (z) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_ABS(cls) -> int:
        '''Corresponds to a "absolute moveto" (M) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_MOVETO_REL(cls) -> int:
        '''Corresponds to a "relative moveto" (m) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_ABS(cls) -> int:
        '''Corresponds to a "absolute lineto" (L) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_REL(cls) -> int:
        '''Corresponds to a "relative lineto" (l) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_ABS(cls) -> int:
        '''Corresponds to a "absolute cubic Bézier curveto" (C) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_REL(cls) -> int:
        '''Corresponds to a "relative cubic Bézier curveto" (c) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_ABS(cls) -> int:
        '''Corresponds to a "absolute quadratic Bézier curveto" (Q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_REL(cls) -> int:
        '''Corresponds to a "relative quadratic Bézier curveto" (q) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_ABS(cls) -> int:
        '''Corresponds to a "absolute arcto" (A) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_ARC_REL(cls) -> int:
        '''Corresponds to a "relative arcto" (a) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_ABS(cls) -> int:
        '''Corresponds to a "absolute horizontal lineto" (H) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_HORIZONTAL_REL(cls) -> int:
        '''Corresponds to a "relative horizontal lineto" (h) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_ABS(cls) -> int:
        '''Corresponds to a "absolute vertical lineto" (V) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_LINETO_VERTICAL_REL(cls) -> int:
        '''Corresponds to a "relative vertical lineto" (v) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth cubic curveto" (S) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_CUBIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth cubic curveto" (s) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS(cls) -> int:
        '''Corresponds to a "absolute smooth quadratic curveto" (T) path data command.'''
        ...
    
    @classmethod
    @property
    def PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL(cls) -> int:
        '''Corresponds to a "relative smooth quadratic curveto" (t) path data command.'''
        ...
    
    @property
    def x(self) -> float:
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The relative X coordinate for the end point of this path segment.'''
        ...
    
    @property
    def y(self) -> float:
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The relative Y coordinate for the end point of this path segment.'''
        ...
    
    ...

