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

class SVGAngle(SVGValueType):
    '''The SVGAngle interface corresponds to the angle basic data type.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def new_value_specified_units(self, new_unit_type : int, value_in_specified_units : float):
        '''Reset the value as a number with an associated unitType, thereby replacing the values for all of the attributes on the object.
        
        :param new_unit_type: The unit type for the value (e.g., SVG_ANGLETYPE_DEG).
        :param value_in_specified_units: The angle value.'''
        ...
    
    def convert_to_specified_units(self, unit_type : int):
        '''Preserve the same underlying stored value, but reset the stored unit identifier to the given unitType. Object attributes unitType, valueInSpecifiedUnits and valueAsString might be modified as a result of this method.
        
        :param unit_type: The unit type to switch to (e.g., SVG_ANGLETYPE_DEG).'''
        ...
    
    @property
    def unit_type(self) -> int:
        ...
    
    @property
    def value(self) -> float:
        '''The angle value as a floating point value, in degrees. Setting this attribute will cause valueInSpecifiedUnits and valueAsString to be updated automatically to reflect this setting.'''
        ...
    
    @value.setter
    def value(self, value : float):
        '''The angle value as a floating point value, in degrees. Setting this attribute will cause valueInSpecifiedUnits and valueAsString to be updated automatically to reflect this setting.'''
        ...
    
    @property
    def value_in_specified_units(self) -> float:
        ...
    
    @value_in_specified_units.setter
    def value_in_specified_units(self, value : float):
        ...
    
    @property
    def value_as_string(self) -> str:
        ...
    
    @value_as_string.setter
    def value_as_string(self, value : str):
        ...
    
    @classmethod
    @property
    def SVG_ANGLETYPE_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined unit types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def SVG_ANGLETYPE_UNSPECIFIED(cls) -> int:
        '''No unit type was provided (i.e., a unitless value was specified). For angles, a unitless value is treated the same as if degrees were specified.'''
        ...
    
    @classmethod
    @property
    def SVG_ANGLETYPE_DEG(cls) -> int:
        '''The unit type was explicitly set to degrees.'''
        ...
    
    @classmethod
    @property
    def SVG_ANGLETYPE_RAD(cls) -> int:
        '''The unit type is radians.'''
        ...
    
    @classmethod
    @property
    def SVG_ANGLETYPE_GRAD(cls) -> int:
        '''The unit type is radians.'''
        ...
    
    ...

class SVGAnimatedAngle(SVGValueType):
    '''Used for attributes of basic data type angle that can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> aspose.html.dom.svg.datatypes.SVGAngle:
        ...
    
    @base_val.setter
    def base_val(self, value : aspose.html.dom.svg.datatypes.SVGAngle):
        ...
    
    @property
    def anim_val(self) -> aspose.html.dom.svg.datatypes.SVGAngle:
        ...
    
    ...

class SVGAnimatedBoolean(SVGValueType):
    '''Used for attributes of type boolean which can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> bool:
        ...
    
    @base_val.setter
    def base_val(self, value : bool):
        ...
    
    @property
    def anim_val(self) -> bool:
        ...
    
    ...

class SVGAnimatedEnumeration(SVGValueType):
    '''Used for attributes whose value must be a constant from a particular enumeration and which can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> int:
        ...
    
    @base_val.setter
    def base_val(self, value : int):
        ...
    
    @property
    def anim_val(self) -> int:
        ...
    
    ...

class SVGAnimatedInteger(SVGValueType):
    '''Used for attributes of basic type integer which can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> int:
        ...
    
    @base_val.setter
    def base_val(self, value : int):
        ...
    
    @property
    def anim_val(self) -> int:
        ...
    
    ...

class SVGAnimatedLength(SVGValueType):
    '''Used for attributes of basic type length which can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> aspose.html.dom.svg.datatypes.SVGLength:
        ...
    
    @base_val.setter
    def base_val(self, value : aspose.html.dom.svg.datatypes.SVGLength):
        ...
    
    @property
    def anim_val(self) -> aspose.html.dom.svg.datatypes.SVGLength:
        ...
    
    ...

class SVGAnimatedLengthList(SVGValueType):
    '''Used for attributes of type SVGLengthList which can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> aspose.html.dom.svg.datatypes.SVGLengthList:
        ...
    
    @base_val.setter
    def base_val(self, value : aspose.html.dom.svg.datatypes.SVGLengthList):
        ...
    
    @property
    def anim_val(self) -> aspose.html.dom.svg.datatypes.SVGLengthList:
        ...
    
    ...

class SVGAnimatedNumber(SVGValueType):
    '''Used for attributes of basic type number which can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> float:
        ...
    
    @base_val.setter
    def base_val(self, value : float):
        ...
    
    @property
    def anim_val(self) -> float:
        ...
    
    ...

class SVGAnimatedNumberList(SVGValueType):
    '''Used for attributes which take a list of numbers and which can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> aspose.html.dom.svg.datatypes.SVGNumberList:
        ...
    
    @base_val.setter
    def base_val(self, value : aspose.html.dom.svg.datatypes.SVGNumberList):
        ...
    
    @property
    def anim_val(self) -> aspose.html.dom.svg.datatypes.SVGNumberList:
        ...
    
    ...

class SVGAnimatedPreserveAspectRatio(SVGValueType):
    '''Used for attributes of type SVGPreserveAspectRatio which can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> aspose.html.dom.svg.datatypes.SVGPreserveAspectRatio:
        ...
    
    @base_val.setter
    def base_val(self, value : aspose.html.dom.svg.datatypes.SVGPreserveAspectRatio):
        ...
    
    @property
    def anim_val(self) -> aspose.html.dom.svg.datatypes.SVGPreserveAspectRatio:
        ...
    
    ...

class SVGAnimatedRect(SVGValueType):
    '''Used for attributes of type SVGRect which can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> aspose.html.dom.svg.datatypes.SVGRect:
        ...
    
    @base_val.setter
    def base_val(self, value : aspose.html.dom.svg.datatypes.SVGRect):
        ...
    
    @property
    def anim_val(self) -> aspose.html.dom.svg.datatypes.SVGRect:
        ...
    
    ...

class SVGAnimatedString(SVGValueType):
    '''Used for attributes of type DOMString which can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> str:
        ...
    
    @base_val.setter
    def base_val(self, value : str):
        ...
    
    @property
    def anim_val(self) -> str:
        ...
    
    ...

class SVGAnimatedTransformList(SVGValueType):
    '''Used for the various attributes which specify a set of transformations, such as the ‘transform’ attribute which is available for many of SVG's elements, and which can be animated.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def base_val(self) -> aspose.html.dom.svg.datatypes.SVGTransformList:
        ...
    
    @base_val.setter
    def base_val(self, value : aspose.html.dom.svg.datatypes.SVGTransformList):
        ...
    
    @property
    def anim_val(self) -> aspose.html.dom.svg.datatypes.SVGTransformList:
        ...
    
    ...

class SVGLength(SVGValueType):
    '''The SVGLength interface corresponds to the length basic data type.
    An SVGLength object can be designated as read only, which means that attempts to modify the object will result in an exception being thrown, as described below.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def new_value_specified_units(self, unit_type : int, value_in_specified_units : float):
        '''Reset the value as a number with an associated unitType, thereby replacing the values for all of the attributes on the object.
        
        :param unit_type: The unit type for the value.
        :param value_in_specified_units: The new value..'''
        ...
    
    def convert_to_specified_units(self, unit_type : int):
        '''Preserve the same underlying stored value, but reset the stored unit identifier to the given unitType. Object attributes unitType, valueInSpecifiedUnits and valueAsString might be modified as a result of this method. For example, if the original value were "0.5cm" and the method was invoked to convert to millimeters, then the unitType would be changed to SVG_LENGTHTYPE_MM, valueInSpecifiedUnits would be changed to the numeric value 5 and valueAsString would be changed to "5mm".
        
        :param unit_type: The unit type to switch to (e.g., SVG_LENGTHTYPE_MM).'''
        ...
    
    @property
    def unit_type(self) -> int:
        ...
    
    @property
    def value(self) -> float:
        '''The value as a floating point value, in user units. Setting this attribute will cause valueInSpecifiedUnits and valueAsString to be updated automatically to reflect this setting.'''
        ...
    
    @value.setter
    def value(self, value : float):
        '''The value as a floating point value, in user units. Setting this attribute will cause valueInSpecifiedUnits and valueAsString to be updated automatically to reflect this setting.'''
        ...
    
    @property
    def value_in_specified_units(self) -> float:
        ...
    
    @value_in_specified_units.setter
    def value_in_specified_units(self, value : float):
        ...
    
    @property
    def value_as_string(self) -> str:
        ...
    
    @value_as_string.setter
    def value_as_string(self, value : str):
        ...
    
    @classmethod
    @property
    def SVG_LENGTHTYPE_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined unit types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def SVG_LENGTHTYPE_NUMBER(cls) -> int:
        '''No unit type was provided (i.e., a unitless value was specified), which indicates a value in user units.'''
        ...
    
    @classmethod
    @property
    def SVG_LENGTHTYPE_PERCENTAGE(cls) -> int:
        '''A percentage value was specified.'''
        ...
    
    @classmethod
    @property
    def SVG_LENGTHTYPE_EMS(cls) -> int:
        '''A value was specified using the em units defined in CSS2.'''
        ...
    
    @classmethod
    @property
    def SVG_LENGTHTYPE_EXS(cls) -> int:
        '''A value was specified using the ex units defined in CSS2.'''
        ...
    
    @classmethod
    @property
    def SVG_LENGTHTYPE_PX(cls) -> int:
        '''A value was specified using the px units defined in CSS2.'''
        ...
    
    @classmethod
    @property
    def SVG_LENGTHTYPE_CM(cls) -> int:
        '''A value was specified using the cm units defined in CSS2.'''
        ...
    
    @classmethod
    @property
    def SVG_LENGTHTYPE_MM(cls) -> int:
        '''A value was specified using the mm units defined in CSS2.'''
        ...
    
    @classmethod
    @property
    def SVG_LENGTHTYPE_IN(cls) -> int:
        '''A value was specified using the in units defined in CSS2.'''
        ...
    
    @classmethod
    @property
    def SVG_LENGTHTYPE_PT(cls) -> int:
        '''A value was specified using the pt units defined in CSS2.'''
        ...
    
    @classmethod
    @property
    def SVG_LENGTHTYPE_PC(cls) -> int:
        '''A value was specified using the pc units defined in CSS2.'''
        ...
    
    ...

class SVGLengthList(SVGValueType):
    '''This interface defines a list of SVGLength objects.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def clear(self):
        ...
    
    def initialize(self, new_item : aspose.html.dom.svg.datatypes.SVGLength) -> aspose.html.dom.svg.datatypes.SVGLength:
        ...
    
    def get_item(self, index : int) -> aspose.html.dom.svg.datatypes.SVGLength:
        ...
    
    def insert_item_before(self, new_item : aspose.html.dom.svg.datatypes.SVGLength, index : int) -> aspose.html.dom.svg.datatypes.SVGLength:
        ...
    
    def replace_item(self, new_item : aspose.html.dom.svg.datatypes.SVGLength, index : int) -> aspose.html.dom.svg.datatypes.SVGLength:
        ...
    
    def remove_item(self, index : int) -> aspose.html.dom.svg.datatypes.SVGLength:
        ...
    
    def append_item(self, new_item : aspose.html.dom.svg.datatypes.SVGLength) -> aspose.html.dom.svg.datatypes.SVGLength:
        ...
    
    @property
    def length(self) -> int:
        ...
    
    @property
    def number_of_items(self) -> int:
        ...
    
    def __getitem__(self, key : int) -> aspose.html.dom.svg.datatypes.SVGLength:
        ...
    
    def __setitem__(self, key : int, value : aspose.html.dom.svg.datatypes.SVGLength):
        ...
    
    ...

class SVGMatrix(SVGValueType):
    '''Many of SVG's graphics operations utilize 2x3 matrices of the form:
    [a c e]
    [b d f]
    which, when expanded into a 3x3 matrix for the purposes of matrix arithmetic, become:
    [a c e]
    [b d f]
    [0 0 1]'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def multiply(self, second_matrix : aspose.html.dom.svg.datatypes.SVGMatrix) -> aspose.html.dom.svg.datatypes.SVGMatrix:
        '''Performs matrix multiplication. This matrix is post-multiplied by another matrix, returning the resulting new matrix.
        
        :param second_matrix: The matrix which is post-multiplied to this matrix.
        :returns: The resulting matrix.'''
        ...
    
    def translate(self, x : float, y : float) -> aspose.html.dom.svg.datatypes.SVGMatrix:
        '''Post-multiplies a translation transformation on the current matrix and returns the resulting matrix.
        
        :param x: The distance to translate along the x-axis.
        :param y: The distance to translate along the y-axis.
        :returns: The resulting matrix.'''
        ...
    
    def scale(self, scale_factor : float) -> aspose.html.dom.svg.datatypes.SVGMatrix:
        '''Post-multiplies a uniform scale transformation on the current matrix and returns the resulting matrix.
        
        :param scale_factor: Scale factor in both X and Y.
        :returns: The resulting matrix.'''
        ...
    
    def scale_non_uniform(self, scale_factor_x : float, scale_factor_y : float) -> aspose.html.dom.svg.datatypes.SVGMatrix:
        '''Post-multiplies a non-uniform scale transformation on the current matrix and returns the resulting matrix.
        
        :param scale_factor_x: Scale factor in X.
        :param scale_factor_y: Scale factor in Y.
        :returns: The resulting matrix.'''
        ...
    
    def rotate(self, angle : float) -> aspose.html.dom.svg.datatypes.SVGMatrix:
        '''Post-multiplies a rotation transformation on the current matrix and returns the resulting matrix.
        
        :param angle: Rotation angle.
        :returns: The resulting matrix.'''
        ...
    
    def skew_x(self, angle : float) -> aspose.html.dom.svg.datatypes.SVGMatrix:
        '''Post-multiplies a skewX transformation on the current matrix and returns the resulting matrix.
        
        :param angle: Skew angle.
        :returns: The resulting matrix.'''
        ...
    
    def skew_y(self, angle : float) -> aspose.html.dom.svg.datatypes.SVGMatrix:
        '''Post-multiplies a skewY transformation on the current matrix and returns the resulting matrix.
        
        :param angle: The angle.
        :returns: Skew angle.'''
        ...
    
    @property
    def a(self) -> float:
        '''The A component of the matrix.'''
        ...
    
    @a.setter
    def a(self, value : float):
        '''The A component of the matrix.'''
        ...
    
    @property
    def b(self) -> float:
        '''The B component of the matrix.'''
        ...
    
    @b.setter
    def b(self, value : float):
        '''The B component of the matrix.'''
        ...
    
    @property
    def c(self) -> float:
        '''The C component of the matrix.'''
        ...
    
    @c.setter
    def c(self, value : float):
        '''The C component of the matrix.'''
        ...
    
    @property
    def d(self) -> float:
        '''The D component of the matrix.'''
        ...
    
    @d.setter
    def d(self, value : float):
        '''The D component of the matrix.'''
        ...
    
    @property
    def e(self) -> float:
        '''The E component of the matrix.'''
        ...
    
    @e.setter
    def e(self, value : float):
        '''The E component of the matrix.'''
        ...
    
    @property
    def f(self) -> float:
        '''The F component of the matrix.'''
        ...
    
    @f.setter
    def f(self, value : float):
        '''The F component of the matrix.'''
        ...
    
    ...

class SVGNumber(SVGValueType):
    '''Used for attributes of basic type number.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def value(self) -> float:
        '''The value of the given attribute.'''
        ...
    
    @value.setter
    def value(self, value : float):
        '''The value of the given attribute.'''
        ...
    
    ...

class SVGNumberList(SVGValueType):
    '''This interface defines a list of SVGNumber objects.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def clear(self):
        ...
    
    def initialize(self, new_item : aspose.html.dom.svg.datatypes.SVGNumber) -> aspose.html.dom.svg.datatypes.SVGNumber:
        ...
    
    def get_item(self, index : int) -> aspose.html.dom.svg.datatypes.SVGNumber:
        ...
    
    def insert_item_before(self, new_item : aspose.html.dom.svg.datatypes.SVGNumber, index : int) -> aspose.html.dom.svg.datatypes.SVGNumber:
        ...
    
    def replace_item(self, new_item : aspose.html.dom.svg.datatypes.SVGNumber, index : int) -> aspose.html.dom.svg.datatypes.SVGNumber:
        ...
    
    def remove_item(self, index : int) -> aspose.html.dom.svg.datatypes.SVGNumber:
        ...
    
    def append_item(self, new_item : aspose.html.dom.svg.datatypes.SVGNumber) -> aspose.html.dom.svg.datatypes.SVGNumber:
        ...
    
    @property
    def length(self) -> int:
        ...
    
    @property
    def number_of_items(self) -> int:
        ...
    
    def __getitem__(self, key : int) -> aspose.html.dom.svg.datatypes.SVGNumber:
        ...
    
    def __setitem__(self, key : int, value : aspose.html.dom.svg.datatypes.SVGNumber):
        ...
    
    ...

class SVGPoint(SVGValueType):
    '''Many of the SVG DOM interfaces refer to objects of class SVGPoint. An SVGPoint is an (x, y) coordinate pair. When used in matrix operations, an SVGPoint is treated as a vector of the form:
    [x]
    [y]
    [1]
    If an SVGRect object is designated as read only, then attempting to assign to one of its attributes will result in an exception being thrown.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def matrix_transform(self, matrix : aspose.html.dom.svg.datatypes.SVGMatrix) -> aspose.html.dom.svg.datatypes.SVGPoint:
        '''Applies a 2x3 matrix transformation on this SVGPoint object and returns a new, transformed SVGPoint object:
        newpoint = matrix* thispoint
        
        :param matrix: he matrix which is to be applied to this SVGPoint object.
        :returns: A new SVGPoint object.'''
        ...
    
    @property
    def x(self) -> float:
        '''The X coordinate.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The X coordinate.'''
        ...
    
    @property
    def y(self) -> float:
        '''The Y coordinate.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The Y coordinate.'''
        ...
    
    ...

class SVGPointList(SVGValueType):
    '''This interface defines a list of SVGPoint objects.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def clear(self):
        ...
    
    def initialize(self, new_item : aspose.html.dom.svg.datatypes.SVGPoint) -> aspose.html.dom.svg.datatypes.SVGPoint:
        ...
    
    def get_item(self, index : int) -> aspose.html.dom.svg.datatypes.SVGPoint:
        ...
    
    def insert_item_before(self, new_item : aspose.html.dom.svg.datatypes.SVGPoint, index : int) -> aspose.html.dom.svg.datatypes.SVGPoint:
        ...
    
    def replace_item(self, new_item : aspose.html.dom.svg.datatypes.SVGPoint, index : int) -> aspose.html.dom.svg.datatypes.SVGPoint:
        ...
    
    def remove_item(self, index : int) -> aspose.html.dom.svg.datatypes.SVGPoint:
        ...
    
    def append_item(self, new_item : aspose.html.dom.svg.datatypes.SVGPoint) -> aspose.html.dom.svg.datatypes.SVGPoint:
        ...
    
    @property
    def length(self) -> int:
        ...
    
    @property
    def number_of_items(self) -> int:
        ...
    
    def __getitem__(self, key : int) -> aspose.html.dom.svg.datatypes.SVGPoint:
        ...
    
    def __setitem__(self, key : int, value : aspose.html.dom.svg.datatypes.SVGPoint):
        ...
    
    ...

class SVGPreserveAspectRatio(SVGValueType):
    '''The SVGPreserveAspectRatio interface corresponds to the ‘preserveAspectRatio’ attribute, which is available for some of SVG's elements.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def align(self) -> int:
        '''The type of the alignment value as specified by one of the SVG_PRESERVEASPECTRATIO_* constants defined on this interface.'''
        ...
    
    @align.setter
    def align(self, value : int):
        '''The type of the alignment value as specified by one of the SVG_PRESERVEASPECTRATIO_* constants defined on this interface.'''
        ...
    
    @property
    def meet_or_slice(self) -> int:
        ...
    
    @meet_or_slice.setter
    def meet_or_slice(self, value : int):
        ...
    
    @classmethod
    @property
    def SVG_PRESERVEASPECTRATIO_UNKNOWN(cls) -> int:
        '''The enumeration was set to a value that is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def SVG_PRESERVEASPECTRATIO_NONE(cls) -> int:
        '''Corresponds to value 'none' for attribute ‘preserveAspectRatio’.'''
        ...
    
    @classmethod
    @property
    def SVG_PRESERVEASPECTRATIO_XMINYMIN(cls) -> int:
        '''Corresponds to value 'xMinYMin' for attribute ‘preserveAspectRatio’.'''
        ...
    
    @classmethod
    @property
    def SVG_PRESERVEASPECTRATIO_XMIDYMIN(cls) -> int:
        '''Corresponds to value 'xMidYMin' for attribute ‘preserveAspectRatio’.'''
        ...
    
    @classmethod
    @property
    def SVG_PRESERVEASPECTRATIO_XMAXYMIN(cls) -> int:
        '''Corresponds to value 'xMaxYMin' for attribute ‘preserveAspectRatio’.'''
        ...
    
    @classmethod
    @property
    def SVG_PRESERVEASPECTRATIO_XMINYMID(cls) -> int:
        '''Corresponds to value 'XMinYMid' for attribute ‘preserveAspectRatio’.'''
        ...
    
    @classmethod
    @property
    def SVG_PRESERVEASPECTRATIO_XMIDYMID(cls) -> int:
        '''Corresponds to value 'xMidYMid' for attribute ‘preserveAspectRatio’.'''
        ...
    
    @classmethod
    @property
    def SVG_PRESERVEASPECTRATIO_XMAXYMID(cls) -> int:
        '''Corresponds to value 'xMaxYMid' for attribute ‘preserveAspectRatio’.'''
        ...
    
    @classmethod
    @property
    def SVG_PRESERVEASPECTRATIO_XMINYMAX(cls) -> int:
        '''Corresponds to value 'xMinYMax' for attribute ‘preserveAspectRatio’.'''
        ...
    
    @classmethod
    @property
    def SVG_PRESERVEASPECTRATIO_XMIDYMAX(cls) -> int:
        '''Corresponds to value 'xMidYMax' for attribute ‘preserveAspectRatio’.'''
        ...
    
    @classmethod
    @property
    def SVG_PRESERVEASPECTRATIO_XMAXYMAX(cls) -> int:
        '''Corresponds to value 'xMaxYMax' for attribute ‘preserveAspectRatio’.'''
        ...
    
    @classmethod
    @property
    def SVG_MEETORSLICE_UNKNOWN(cls) -> int:
        '''The enumeration was set to a value that is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def SVG_MEETORSLICE_MEET(cls) -> int:
        '''Corresponds to value 'meet' for attribute ‘preserveAspectRatio’.'''
        ...
    
    @classmethod
    @property
    def SVG_MEETORSLICE_SLICE(cls) -> int:
        '''Corresponds to value 'slice' for attribute ‘preserveAspectRatio’.'''
        ...
    
    ...

class SVGRect(SVGValueType):
    '''Represents rectangular geometry. Rectangles are defined as consisting of a (x,y) coordinate pair identifying a minimum X value, a minimum Y value, and a width and height, which are usually constrained to be non-negative.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def x(self) -> float:
        '''The X coordinate of the rectangle, in user units.'''
        ...
    
    @x.setter
    def x(self, value : float):
        '''The X coordinate of the rectangle, in user units.'''
        ...
    
    @property
    def y(self) -> float:
        '''The Y coordinate of the rectangle, in user units.'''
        ...
    
    @y.setter
    def y(self, value : float):
        '''The Y coordinate of the rectangle, in user units.'''
        ...
    
    @property
    def width(self) -> float:
        '''The Width coordinate of the rectangle, in user units.'''
        ...
    
    @width.setter
    def width(self, value : float):
        '''The Width coordinate of the rectangle, in user units.'''
        ...
    
    @property
    def height(self) -> float:
        '''The Height coordinate of the rectangle, in user units.'''
        ...
    
    @height.setter
    def height(self, value : float):
        '''The Height coordinate of the rectangle, in user units.'''
        ...
    
    ...

class SVGStringList(SVGValueType):
    '''SVGStringList has the same attributes and methods as other SVGxxxList interfaces. Implementers may consider using a single base class to implement the various SVGxxxList interfaces.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def clear(self):
        ...
    
    def initialize(self, new_item : str) -> str:
        ...
    
    def get_item(self, index : int) -> str:
        ...
    
    def insert_item_before(self, new_item : str, index : int) -> str:
        ...
    
    def replace_item(self, new_item : str, index : int) -> str:
        ...
    
    def remove_item(self, index : int) -> str:
        ...
    
    def append_item(self, new_item : str) -> str:
        ...
    
    @property
    def length(self) -> int:
        ...
    
    @property
    def number_of_items(self) -> int:
        ...
    
    def __getitem__(self, key : int) -> str:
        ...
    
    def __setitem__(self, key : int, value : str):
        ...
    
    ...

class SVGTransform(SVGValueType):
    '''SVGTransform is the interface for one of the component transformations within an SVGTransformList; thus, an SVGTransform object corresponds to a single component (e.g., 'scale(…)' or 'matrix(…)') within a ‘transform’ attribute specification.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def set_matrix(self, matrix : aspose.html.dom.svg.datatypes.SVGMatrix):
        '''Sets the transform type to SVG_TRANSFORM_MATRIX, with parameter matrix defining the new transformation. The values from the parameter matrix are copied, the matrix parameter does not replace SVGTransform::matrix.
        
        :param matrix: The new matrix for the transformation.'''
        ...
    
    def set_translate(self, tx : float, ty : float):
        '''Sets the transform type to SVG_TRANSFORM_TRANSLATE, with parameters tx and ty defining the translation amounts.
        
        :param tx: The translation amount in X.
        :param ty: The translation amount in Y.'''
        ...
    
    def set_scale(self, sx : float, sy : float):
        '''Sets the transform type to SVG_TRANSFORM_SCALE, with parameters sx and sy defining the scale amounts.
        
        :param sx: The scale amount in X.
        :param sy: The scale amount in Y.'''
        ...
    
    def set_rotate(self, angle : float, cx : float, cy : float):
        '''Sets the transform type to SVG_TRANSFORM_ROTATE, with parameter angle defining the rotation angle and parameters cx and cy defining the optional center of rotation.
        
        :param angle: The rotation angle.
        :param cx: The x coordinate of center of rotation.
        :param cy: The y coordinate of center of rotation.'''
        ...
    
    def set_skew_x(self, angle : float):
        '''Sets the transform type to SVG_TRANSFORM_SKEWX, with parameter angle defining the amount of skew.
        
        :param angle: The skew angle.'''
        ...
    
    def set_skew_y(self, angle : float):
        '''Sets the transform type to SVG_TRANSFORM_SKEWY, with parameter angle defining the amount of skew.
        
        :param angle: The skew angle.'''
        ...
    
    @property
    def type(self) -> int:
        '''The type of the value as specified by one of the SVG_TRANSFORM_* constants defined on this interface.'''
        ...
    
    @property
    def matrix(self) -> aspose.html.dom.svg.datatypes.SVGMatrix:
        '''The matrix that represents this transformation. The matrix object is live, meaning that any changes made to the SVGTransform object are immediately reflected in the matrix object and vice versa. In case the matrix object is changed directly (i.e., without using the methods on the SVGTransform interface itself) then the type of the SVGTransform changes to SVG_TRANSFORM_MATRIX.
        For SVG_TRANSFORM_MATRIX, the matrix contains the a, b, c, d, e, f values supplied by the user.
        For SVG_TRANSFORM_TRANSLATE, e and f represent the translation amounts(a= 1, b= 0, c= 0 and d = 1).
        For SVG_TRANSFORM_SCALE, a and d represent the scale amounts(b= 0, c= 0, e= 0 and f = 0).
        For SVG_TRANSFORM_SKEWX and SVG_TRANSFORM_SKEWY, a, b, c and d represent the matrix which will result in the given skew(e= 0 and f = 0).
        For SVG_TRANSFORM_ROTATE, a, b, c, d, e and f together represent the matrix which will result in the given rotation.When the rotation is around the center point(0, 0), e and f will be zero.'''
        ...
    
    @property
    def angle(self) -> float:
        '''A convenience attribute for SVG_TRANSFORM_ROTATE, SVG_TRANSFORM_SKEWX and SVG_TRANSFORM_SKEWY. It holds the angle that was specified.
        For SVG_TRANSFORM_MATRIX, SVG_TRANSFORM_TRANSLATE and SVG_TRANSFORM_SCALE, angle will be zero.'''
        ...
    
    @classmethod
    @property
    def SVG_TRANSFORM_UNKNOWN(cls) -> int:
        '''The unit type is not one of predefined types. It is invalid to attempt to define a new value of this type or to attempt to switch an existing value to this type.'''
        ...
    
    @classmethod
    @property
    def SVG_TRANSFORM_MATRIX(cls) -> int:
        '''A 'matrix(…)' transformation.'''
        ...
    
    @classmethod
    @property
    def SVG_TRANSFORM_TRANSLATE(cls) -> int:
        '''A 'translate(…)' transformation.'''
        ...
    
    @classmethod
    @property
    def SVG_TRANSFORM_SCALE(cls) -> int:
        '''A 'scale(…)' transformation.'''
        ...
    
    @classmethod
    @property
    def SVG_TRANSFORM_ROTATE(cls) -> int:
        '''A 'rotate(…)' transformation.'''
        ...
    
    @classmethod
    @property
    def SVG_TRANSFORM_SKEWX(cls) -> int:
        '''A 'skewX(…)' transformation.'''
        ...
    
    @classmethod
    @property
    def SVG_TRANSFORM_SKEWY(cls) -> int:
        '''A 'skewY(…)' transformation.'''
        ...
    
    ...

class SVGTransformList(SVGValueType):
    '''This interface defines a list of SVGTransform objects.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def clear(self):
        ...
    
    def initialize(self, new_item : aspose.html.dom.svg.datatypes.SVGTransform) -> aspose.html.dom.svg.datatypes.SVGTransform:
        ...
    
    def get_item(self, index : int) -> aspose.html.dom.svg.datatypes.SVGTransform:
        ...
    
    def insert_item_before(self, new_item : aspose.html.dom.svg.datatypes.SVGTransform, index : int) -> aspose.html.dom.svg.datatypes.SVGTransform:
        ...
    
    def replace_item(self, new_item : aspose.html.dom.svg.datatypes.SVGTransform, index : int) -> aspose.html.dom.svg.datatypes.SVGTransform:
        ...
    
    def remove_item(self, index : int) -> aspose.html.dom.svg.datatypes.SVGTransform:
        ...
    
    def append_item(self, new_item : aspose.html.dom.svg.datatypes.SVGTransform) -> aspose.html.dom.svg.datatypes.SVGTransform:
        ...
    
    @property
    def length(self) -> int:
        ...
    
    @property
    def number_of_items(self) -> int:
        ...
    
    def __getitem__(self, key : int) -> aspose.html.dom.svg.datatypes.SVGTransform:
        ...
    
    def __setitem__(self, key : int, value : aspose.html.dom.svg.datatypes.SVGTransform):
        ...
    
    ...

class SVGValueType(aspose.html.dom.DOMObject):
    '''The SVGValueType type is used to represent an base SVG value type.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    ...

