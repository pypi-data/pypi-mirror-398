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

class Angle(Dimension):
    '''The angle data type'''
    
    @overload
    def get_value(self) -> float:
        '''Gets the unit value.
        
        :returns: The object value.'''
        ...
    
    @overload
    def get_value(self, unit_type : aspose.html.drawing.UnitType) -> float:
        '''Gets the value converted to the specified :py:class:`aspose.html.drawing.UnitType`.
        
        :param unit_type: Type of the unit.
        :returns: Returns value that is converted to specified type.'''
        ...
    
    def equals(self, other : aspose.html.drawing.Unit) -> bool:
        '''Determines whether the specified :py:class:`aspose.html.drawing.Unit`, is equal to this instance.
        
        :param other: The :py:class:`aspose.html.drawing.Unit` to compare with this instance.
        :returns: ``true`` if the specified :py:class:`aspose.html.drawing.Unit` is equal to this instance; otherwise, ``false``.'''
        ...
    
    @staticmethod
    def from_centimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_quarter_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in quarter-millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_inches(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in inches.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_picas(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in picas.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_points(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in points.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_pixels(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_degrees(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in degrees.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_gradians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in gradians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_radians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in radians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_turns(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in turns.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_seconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in seconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_milliseconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in milliseconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in hertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_kilo_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in kiloHertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_dots_per_inch(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per inch.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_centimeters(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_pixel(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    def compare_to(self, other : aspose.html.drawing.Numeric) -> int:
        '''Compares the current instance with another object of the same type and returns an integer that indicates whether the current instance precedes, follows, or occurs in the same position in the sort order as the other object.
        
        :param other: The other object to compare.
        :returns: A value that indicates the relative order of the objects being compared.'''
        ...
    
    @property
    def unit_type(self) -> aspose.html.drawing.UnitType:
        ...
    
    ...

class Color:
    '''The Color class lets you specify colors as
    Red-Green-Blue (RGB) values,
    Hue-Saturation-Luminosity (HSL) values,
    Hue-Saturation-Value (HSV) values,
    Hue-Whiteness-Blackness (HWB) values,
    lightness-A-B (LAB) values,
    Luminance-Chroma-Hue (LCH) values,
    Cyan-Magenta-Yellow-Key (CMYK) values,
    Natural colors (NCOL) values,
    or with a color name.
    An Alpha channel is also available to indicate transparency.'''
    
    @overload
    @staticmethod
    def from_rgb(red : bytegreen : byte, blue : byte) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested ged, green, blue values.
        All color components must be in the range 0-255.
        
        :param red: A byte that represents the red component of the color.
        :param green: A byte that represents the green component of the color.
        :param blue: A byte that represents the blue component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @overload
    @staticmethod
    def from_rgb(red : intgreen : int, blue : int) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested ged, green, blue values.
        All color components must be in the range 0-255.
        
        :param red: A int that represents the red component of the color.
        :param green: A int that represents the green component of the color.
        :param blue: A int that represents the blue component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @overload
    @staticmethod
    def from_rgb(red : floatgreen : float, blue : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested ged, green, blue values.
        All color components must be in the range 0-1.
        
        :param red: A float that represents the red component of the color.
        :param green: A float that represents the green component of the color.
        :param blue: A float that represents the blue component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @overload
    @staticmethod
    def from_rgba(red : bytegreen : byte, blue : byte, alpha : byte) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested ged, green, blue, alpha values.
        All color components must be in the range 0-255.
        
        :param red: A byte that represents the red component of the color.
        :param green: A byte that represents the green component of the color.
        :param blue: A byte that represents the blue component of the color.
        :param alpha: A byte that represents the alpha component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @overload
    @staticmethod
    def from_rgba(red : intgreen : int, blue : int, alpha : int) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested ged, green, blue, alpha values.
        All color components must be in the range 0-255.
        
        :param red: A int that represents the red component of the color.
        :param green: A int that represents the green component of the color.
        :param blue: A int that represents the blue component of the color.
        :param alpha: A int that represents the alpha component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @overload
    @staticmethod
    def from_rgba(red : floatgreen : float, blue : float, alpha : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested ged, green, blue, alpha values.
        All color components must be in the range 0-1.
        
        :param red: A float that represents the red component of the color.
        :param green: A float that represents the green component of the color.
        :param blue: A float that represents the blue component of the color.
        :param alpha: A float that represents the alpha component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_gray(gray : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested gray value.
        
        :param gray: A float that represents the gray value of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_uint(argb : int) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested ARGB value.
        
        :param argb: A uint that represents the ARGB value of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_int(argb : int) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested ARGB value.
        
        :param argb: A int that represents the ARGB value of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_string(color : str) -> aspose.html.drawing.Color:
        '''Parses string containing the CSS color and returns a new Color.
        
        :param color: A string containing the color in the format RGB, HEX, HSL, HSV, HWB, CMYK, NCOL, LCH, OKLCH, LAB or OKLAB
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_hsl(hue : floatsaturation : float, lightness : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested hue, saturation, saturation values.
        
        :param hue: A float that represents the hue component of the color.
        :param saturation: A float that represents the saturation component of the color.
        :param lightness: A float that represents the lightness component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_hsla(hue : floatsaturation : float, lightness : float, alpha : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested hue, saturation, saturation, alpha values.
        
        :param hue: A float that represents the hue component of the color.
        :param saturation: A float that represents the saturation component of the color.
        :param lightness: A float that represents the lightness component of the color.
        :param alpha: A float that represents the alpha component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_hsv(hue : floatsaturation : float, value : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested hue, saturation, value.
        
        :param hue: A float that represents the hue component of the color.
        :param saturation: A float that represents the saturation component of the color.
        :param value: A float that represents the value component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_hsva(hue : floatsaturation : float, value : float, alpha : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested hue, saturation, value, alpha.
        
        :param hue: A float that represents the hue component of the color.
        :param saturation: A float that represents the saturation component of the color.
        :param value: A float that represents the value component of the color.
        :param alpha: A float that represents the alpha component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_hwb(hue : floatwhiteness : float, blackness : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested hue, whiteness, blackness values.
        
        :param hue: A float that represents the hue component of the color.
        :param whiteness: A float that represents the whiteness component of the color.
        :param blackness: A float that represents the blackness component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_hwba(hue : floatwhiteness : float, blackness : float, alpha : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested hue, whiteness, blackness values.
        
        :param hue: A float that represents the hue component of the color.
        :param whiteness: A float that represents the whiteness component of the color.
        :param blackness: A float that represents the blackness component of the color.
        :param alpha: A float that represents the alpha component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_cmyk(cyan : floatmagenta : float, yellow : float, key : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested cyan, magenta, yellow, key (black) values.
        
        :param cyan: A float that represents the cyan component of the color.
        :param magenta: A float that represents the magenta component of the color.
        :param yellow: A float that represents the yellow component of the color.
        :param key: A float that represents the key component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_cmyka(cyan : floatmagenta : float, yellow : float, key : float, alpha : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested cyan, magenta, yellow, key (black), alpha values.
        
        :param cyan: A float that represents the cyan component of the color.
        :param magenta: A float that represents the magenta component of the color.
        :param yellow: A float that represents the yellow component of the color.
        :param key: A float that represents the key component of the color.
        :param alpha: A float that represents the alpha component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_lab(lightness : floata : float, b : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested lightness, A, B values.
        
        :param lightness: A float that represents the lightness component of the color.
        :param a: A float that represents the A component of the color.
        :param b: A float that represents the B component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_laba(lightness : floata : float, b : float, alpha : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested lightness, A, B, alpha values.
        
        :param lightness: A float that represents the lightness component of the color.
        :param a: A float that represents the A component of the color.
        :param b: A float that represents the B component of the color.
        :param alpha: A float that represents the alpha component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_oklab(lightness : floata : float, b : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested lightness, A, B values for OKLAB model.
        
        :param lightness: A float that represents the lightness component of the color.
        :param a: A float that represents the A component of the color.
        :param b: A float that represents the B component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_oklaba(lightness : floata : float, b : float, alpha : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested lightness, A, B, alpha values for OKLAB model.
        
        :param lightness: A float that represents the lightness component of the color.
        :param a: A float that represents the A component of the color.
        :param b: A float that represents the B component of the color.
        :param alpha: A float that represents the alpha component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_lch(luminance : floatchroma : float, hue : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested luminance, chroma, hue values.
        
        :param luminance: A float that represents the luminance component of the color.
        :param chroma: A float that represents the chroma component of the color.
        :param hue: A float that represents the hue component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_lcha(luminance : floatchroma : float, hue : float, alpha : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested luminance, chroma, hue, alpha values.
        
        :param luminance: A float that represents the luminance component of the color.
        :param chroma: A float that represents the chroma component of the color.
        :param hue: A float that represents the hue component of the color.
        :param alpha: A float that represents the alpha component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_oklch(luminance : floatchroma : float, hue : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested luminance, chroma, hue values for OKLAB model.
        
        :param luminance: A float that represents the luminance component of the color.
        :param chroma: A float that represents the chroma component of the color.
        :param hue: A float that represents the hue component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    @staticmethod
    def from_oklcha(luminance : floatchroma : float, hue : float, alpha : float) -> aspose.html.drawing.Color:
        '''Returns a new Color with the requested luminance, chroma, hue, alpha values for OKLAB model.
        
        :param luminance: A float that represents the luminance component of the color.
        :param chroma: A float that represents the chroma component of the color.
        :param hue: A float that represents the hue component of the color.
        :param alpha: A float that represents the alpha component of the color.
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    def to_rgb_hex_string(self) -> str:
        '''Returns a hexadecimal color is specified with: #RRGGBB.
        
        :returns: A hexadecimal color string.'''
        ...
    
    def to_natural_color_string(self, digits : int) -> str:
        '''Returns a Natural colors (NCol) specified color using a color letter with a number to specify the distance (in percent) from the color.
        
        :param digits: Sets the rounding precision for color components.
        :returns: A Natural colors (NCol) string'''
        ...
    
    def to_name(self) -> str:
        '''Returns the name of the color if it matches a color in the list of CSS named colors, or an empty string.
        
        :returns: A color name.'''
        ...
    
    def convert(self, model : aspose.html.drawing.ColorModel) -> aspose.html.drawing.IColorComponents:
        '''Returns a color components in the format of the specified color model.
        
        :param model: The color model.
        :returns: A new instance of the :py:class:`aspose.html.drawing.IColorComponents` interface'''
        ...
    
    def to_rgb_string(self) -> str:
        '''Returns a string containing the RGB color specified by: rgb(R, G, B).
        
        :returns: A rgb string.'''
        ...
    
    def to_rgba_hex_string(self) -> str:
        '''Returns a Hexadecimal color is specified with: #RRGGBBAA.
        
        :returns: A Hexadecimal color string.'''
        ...
    
    def to_rgba_string(self) -> str:
        '''Returns a string containing the RGBA color specified by: rgba(R, G, B, A).
        
        :returns: A rgba string.'''
        ...
    
    def to_int(self) -> int:
        '''Encodes the Color ARGB components into int.
        
        :returns: Encoded int.'''
        ...
    
    def to_uint(self) -> int:
        '''Encodes the Color ARGB components into unsigned int.
        
        :returns: Encoded unsigned int.'''
        ...
    
    def get_luminosity(self) -> float:
        '''Returns a luminosity of the Color.
        
        :returns: A luminosity of the Color.'''
        ...
    
    def add_luminosity(self, delta : float) -> aspose.html.drawing.Color:
        '''Creates copy of the Color with Sum of its luminosity and the delta value.
        
        :param delta: Value of luminosity
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    def with_luminosity(self, luminosity : float) -> aspose.html.drawing.Color:
        '''Creates copy of the Color with specified luminosity.
        
        :param luminosity: Value of luminosity
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class.'''
        ...
    
    def with_alpha(self, alpha : float) -> aspose.html.drawing.Color:
        '''Creates copy of the Color with specified alpha component.
        
        :param alpha: Value of Alpha component
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    def get_saturation(self) -> float:
        '''Returns a saturation of the Color.
        
        :returns: A saturation of the Color.'''
        ...
    
    def with_saturation(self, saturation : float) -> aspose.html.drawing.Color:
        '''Creates copy of the Color with specified saturation.
        
        :param saturation: Value of saturation.
        :returns: >A new instance of the :py:class:`aspose.html.drawing.Color` class.'''
        ...
    
    def get_hue(self) -> float:
        '''Returns a Hue of the Color.
        
        :returns: A Hue of the Color.'''
        ...
    
    def with_hue(self, hue : float) -> aspose.html.drawing.Color:
        '''Creates copy of the Color with specified Hue.
        
        :param hue: Value of Hue.
        :returns: >A new instance of the :py:class:`aspose.html.drawing.Color` class.'''
        ...
    
    def get_complementary(self) -> aspose.html.drawing.Color:
        '''Returns a new color that is on the opposite side of the color wheel from the original.
        
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class.'''
        ...
    
    @property
    def red(self) -> float:
        '''Represents the red component of the color'''
        ...
    
    @property
    def green(self) -> float:
        '''Represents the green component of the color.'''
        ...
    
    @property
    def blue(self) -> float:
        '''Represents the blue component of the color.'''
        ...
    
    @property
    def alpha(self) -> float:
        '''Represents the alpha component of the color.'''
        ...
    
    ...

class Dimension(Numeric):
    '''Provides the base class for dimensions.
    The general term 'dimension' refers to a number with a unit attached to it, and are denoted by :py:class:`aspose.html.drawing.UnitType`.'''
    
    @overload
    def get_value(self) -> float:
        '''Gets the unit value.
        
        :returns: The object value.'''
        ...
    
    @overload
    def get_value(self, unit_type : aspose.html.drawing.UnitType) -> float:
        '''Gets the value converted to the specified :py:class:`aspose.html.drawing.UnitType`.
        
        :param unit_type: Type of the unit.
        :returns: Returns value that is converted to specified type.'''
        ...
    
    def equals(self, other : aspose.html.drawing.Unit) -> bool:
        '''Determines whether the specified :py:class:`aspose.html.drawing.Unit`, is equal to this instance.
        
        :param other: The :py:class:`aspose.html.drawing.Unit` to compare with this instance.
        :returns: ``true`` if the specified :py:class:`aspose.html.drawing.Unit` is equal to this instance; otherwise, ``false``.'''
        ...
    
    @staticmethod
    def from_centimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_quarter_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in quarter-millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_inches(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in inches.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_picas(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in picas.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_points(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in points.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_pixels(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_degrees(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in degrees.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_gradians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in gradians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_radians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in radians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_turns(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in turns.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_seconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in seconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_milliseconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in milliseconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in hertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_kilo_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in kiloHertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_dots_per_inch(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per inch.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_centimeters(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_pixel(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    def compare_to(self, other : aspose.html.drawing.Numeric) -> int:
        '''Compares the current instance with another object of the same type and returns an integer that indicates whether the current instance precedes, follows, or occurs in the same position in the sort order as the other object.
        
        :param other: The other object to compare.
        :returns: A value that indicates the relative order of the objects being compared.'''
        ...
    
    @property
    def unit_type(self) -> aspose.html.drawing.UnitType:
        ...
    
    ...

class Frequency(Dimension):
    '''The 'frequency' unit.'''
    
    @overload
    def get_value(self) -> float:
        '''Gets the unit value.
        
        :returns: The object value.'''
        ...
    
    @overload
    def get_value(self, unit_type : aspose.html.drawing.UnitType) -> float:
        '''Gets the value converted to the specified :py:class:`aspose.html.drawing.UnitType`.
        
        :param unit_type: Type of the unit.
        :returns: Returns value that is converted to specified type.'''
        ...
    
    def equals(self, other : aspose.html.drawing.Unit) -> bool:
        '''Determines whether the specified :py:class:`aspose.html.drawing.Unit`, is equal to this instance.
        
        :param other: The :py:class:`aspose.html.drawing.Unit` to compare with this instance.
        :returns: ``true`` if the specified :py:class:`aspose.html.drawing.Unit` is equal to this instance; otherwise, ``false``.'''
        ...
    
    @staticmethod
    def from_centimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_quarter_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in quarter-millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_inches(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in inches.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_picas(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in picas.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_points(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in points.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_pixels(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_degrees(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in degrees.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_gradians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in gradians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_radians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in radians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_turns(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in turns.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_seconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in seconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_milliseconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in milliseconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in hertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_kilo_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in kiloHertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_dots_per_inch(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per inch.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_centimeters(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_pixel(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    def compare_to(self, other : aspose.html.drawing.Numeric) -> int:
        '''Compares the current instance with another object of the same type and returns an integer that indicates whether the current instance precedes, follows, or occurs in the same position in the sort order as the other object.
        
        :param other: The other object to compare.
        :returns: A value that indicates the relative order of the objects being compared.'''
        ...
    
    @property
    def unit_type(self) -> aspose.html.drawing.UnitType:
        ...
    
    ...

class IBrush:
    '''Declares method for getting of brush type.'''
    
    @property
    def type(self) -> aspose.html.drawing.BrushType:
        '''Gets type of brush as :py:class:`aspose.html.drawing.BrushType`.'''
        ...
    
    ...

class IColorComponents:
    '''Declares method and properties for processing color components.'''
    
    def to_color(self) -> aspose.html.drawing.Color:
        '''Converts the color components to the Color object.
        
        :returns: A new instance of the :py:class:`aspose.html.drawing.Color` class'''
        ...
    
    def to_string(self, include_alpha : bool, as_decimal : bool, digits : int) -> str:
        '''Converts color components to string representation.
        
        :param include_alpha: Specifies whether to add Alpha component.
        :param as_decimal: Specifies whether color components are preserved as a decimal number or as a percentage.
        :param digits: Sets the rounding precision for color components.
        :returns: String representation of the color components.'''
        ...
    
    @property
    def model(self) -> aspose.html.drawing.ColorModel:
        '''Returns the color model.'''
        ...
    
    @property
    def components(self) -> List[float]:
        '''Returns the color components as float array.'''
        ...
    
    @property
    def alpha(self) -> float:
        '''Returns the alpha component.'''
        ...
    
    ...

class IDrawingFactory:
    '''Represents a factory for creating drawing-related objects.'''
    
    @overload
    def create_matrix(self, matrix : aspose.html.drawing.IMatrix) -> aspose.html.drawing.IMatrix:
        '''Creates a new matrix with the same contents as the specified matrix.
        
        :param matrix: The matrix to copy.
        :returns: The created :py:class:`aspose.html.drawing.IMatrix`.'''
        ...
    
    @overload
    def create_matrix(self, m11 : float, m12 : float, m21 : float, m22 : float, m31 : float, m32 : float) -> aspose.html.drawing.IMatrix:
        '''Creates a new matrix with the specified elements.
        
        :param m11: The value in the first row and first column of the matrix.
        :param m12: The value in the first row and second column of the matrix.
        :param m21: The value in the second row and first column of the matrix.
        :param m22: The value in the second row and second column of the matrix.
        :param m31: The value in the third row and first column of the matrix.
        :param m32: The value in the third row and second column of the matrix.
        :returns: The created :py:class:`aspose.html.drawing.IMatrix`.'''
        ...
    
    @overload
    def create_matrix(self) -> aspose.html.drawing.IMatrix:
        '''Creates a new identity matrix.
        
        :returns: The created :py:class:`aspose.html.drawing.IMatrix`.'''
        ...
    
    def create_solid_brush(self, color : aspose.pydrawing.Color) -> aspose.html.drawing.ISolidBrush:
        '''Creates a solid brush with the specified color.
        
        :param color: The color of the solid brush.
        :returns: The created :py:class:`aspose.html.drawing.ISolidBrush`.'''
        ...
    
    def create_linear_gradient_brush(self, rect : aspose.pydrawing.RectangleF, colors : List[aspose.html.drawing.IInterpolationColor]) -> aspose.html.drawing.ILinearGradientBrush:
        '''Creates a linear gradient brush with the specified parameters.
        
        :param rect: The rectangle defining the gradient bounds.
        :param colors: The interpolation colors for the gradient. See :py:class:`aspose.html.drawing.IInterpolationColor`.
        :returns: The created :py:class:`aspose.html.drawing.ILinearGradientBrush`.'''
        ...
    
    def create_texture_brush(self, image_bytes : bytes) -> aspose.html.drawing.ITextureBrush:
        '''Creates a texture brush with the specified parameters.
        
        :param image_bytes: The byte array containing the image data.
        :returns: The created :py:class:`aspose.html.drawing.ITextureBrush`.'''
        ...
    
    def create_interpolation_color(self, color : aspose.pydrawing.Color, position : float) -> aspose.html.drawing.IInterpolationColor:
        '''Creates an interpolation color with the specified color and position.
        
        :param color: Represents the color that will be used at the corresponding position of the gradient.
        :param position: The position, represented as a percentage from 0 to 1, at which the corresponding gradient color will be used.
        :returns: The created :py:class:`aspose.html.drawing.IInterpolationColor`.'''
        ...
    
    ...

class IGradientBrush(ITransformableBrush):
    '''Declare methods for getting common properties of gradient brushes.'''
    
    @property
    def interpolation_colors(self) -> List[aspose.html.drawing.IInterpolationColor]:
        ...
    
    @interpolation_colors.setter
    def interpolation_colors(self, value : List[aspose.html.drawing.IInterpolationColor]):
        ...
    
    @property
    def blend_positions(self) -> List[float]:
        ...
    
    @blend_positions.setter
    def blend_positions(self, value : List[float]):
        ...
    
    @property
    def blend_factors(self) -> List[float]:
        ...
    
    @blend_factors.setter
    def blend_factors(self, value : List[float]):
        ...
    
    @property
    def transformation_matrix(self) -> aspose.html.drawing.IMatrix:
        ...
    
    @transformation_matrix.setter
    def transformation_matrix(self, value : aspose.html.drawing.IMatrix):
        ...
    
    @property
    def spread_mode(self) -> aspose.html.drawing.SpreadMode:
        ...
    
    @spread_mode.setter
    def spread_mode(self, value : aspose.html.drawing.SpreadMode):
        ...
    
    @property
    def type(self) -> aspose.html.drawing.BrushType:
        '''Gets type of brush as :py:class:`aspose.html.drawing.BrushType`.'''
        ...
    
    ...

class IInterpolationColor:
    '''Desclares methods for getting interpolation color.'''
    
    @property
    def color(self) -> aspose.pydrawing.Color:
        '''Get the color that represents the colors to use at corresponding positions along a gradient.'''
        ...
    
    @color.setter
    def color(self, value : aspose.pydrawing.Color):
        '''Get or sets the color that represents the colors to use at corresponding positions along a gradient.'''
        ...
    
    @property
    def position(self) -> float:
        '''Gets the color position.'''
        ...
    
    @position.setter
    def position(self, value : float):
        '''Sets the color position.'''
        ...
    
    ...

class ILinearGradientBrush(IGradientBrush):
    '''Defines an interface for a brush with a linear gradient.'''
    
    @property
    def rect(self) -> aspose.pydrawing.RectangleF:
        '''Gets the rectangular region that defines the starting and ending points of the gradient.'''
        ...
    
    @rect.setter
    def rect(self, value : aspose.pydrawing.RectangleF):
        '''Sets the rectangular region that defines the starting and ending points of the gradient.'''
        ...
    
    @property
    def angle(self) -> float:
        '''Gets the angle, measured in degrees clockwise from the x-axis, of the gradient's orientation line.'''
        ...
    
    @angle.setter
    def angle(self, value : float):
        '''Sets the angle, measured in degrees clockwise from the x-axis, of the gradient's orientation line.'''
        ...
    
    @property
    def interpolation_colors(self) -> List[aspose.html.drawing.IInterpolationColor]:
        ...
    
    @interpolation_colors.setter
    def interpolation_colors(self, value : List[aspose.html.drawing.IInterpolationColor]):
        ...
    
    @property
    def blend_positions(self) -> List[float]:
        ...
    
    @blend_positions.setter
    def blend_positions(self, value : List[float]):
        ...
    
    @property
    def blend_factors(self) -> List[float]:
        ...
    
    @blend_factors.setter
    def blend_factors(self, value : List[float]):
        ...
    
    @property
    def transformation_matrix(self) -> aspose.html.drawing.IMatrix:
        ...
    
    @transformation_matrix.setter
    def transformation_matrix(self, value : aspose.html.drawing.IMatrix):
        ...
    
    @property
    def spread_mode(self) -> aspose.html.drawing.SpreadMode:
        ...
    
    @spread_mode.setter
    def spread_mode(self, value : aspose.html.drawing.SpreadMode):
        ...
    
    @property
    def type(self) -> aspose.html.drawing.BrushType:
        '''Gets type of brush as :py:class:`aspose.html.drawing.BrushType`.'''
        ...
    
    ...

class IMatrix:
    '''Represents a matrix used for transformations.'''
    
    @overload
    def scale(self, scale_x : float, scale_y : float, order : aspose.html.drawing.WebMatrixOrder):
        '''Scales the matrix by the specified scale factors in the specified order.
        
        :param scale_x: The scale factor along the x-axis.
        :param scale_y: The scale factor along the y-axis.
        :param order: The order in which scaling is applied.'''
        ...
    
    @overload
    def scale(self, scale_x : float, scale_y : float):
        '''Scales the matrix by the specified scale factors uniformly.
        
        :param scale_x: The uniform scale factor.
        :param scale_y: The uniform scale factor.'''
        ...
    
    @overload
    def translate(self, offset_x : float, offset_y : float, order : aspose.html.drawing.WebMatrixOrder):
        '''Translates the matrix by the specified offset values in the specified order.
        
        :param offset_x: The offset value along the x-axis.
        :param offset_y: The offset value along the y-axis.
        :param order: The order in which translation is applied.'''
        ...
    
    @overload
    def translate(self, offset_x : float, offset_y : float):
        '''Translates the matrix by the specified offset values.
        
        :param offset_x: The offset value along the x-axis.
        :param offset_y: The offset value along the y-axis.'''
        ...
    
    @overload
    def multiply(self, matrix : aspose.html.drawing.IMatrix, order : aspose.html.drawing.WebMatrixOrder):
        '''Multiplies this matrix by another matrix in the specified order.
        
        :param matrix: The matrix to multiply by.
        :param order: The order in which multiplication is applied.'''
        ...
    
    @overload
    def multiply(self, matrix : aspose.html.drawing.IMatrix):
        '''Multiplies this matrix by another matrix.
        
        :param matrix: The matrix to multiply by.'''
        ...
    
    @overload
    def rotate(self, angle : float, order : aspose.html.drawing.WebMatrixOrder):
        '''Rotates the matrix by the specified angle in the specified order.
        
        :param angle: The angle of rotation in degrees.
        :param order: The order in which rotation is applied.'''
        ...
    
    @overload
    def rotate(self, angle : float):
        '''Rotates the matrix by the specified angle.
        
        :param angle: The angle of rotation in degrees.'''
        ...
    
    @overload
    def rotate_at(self, angle : float, point : aspose.pydrawing.PointF, order : aspose.html.drawing.WebMatrixOrder):
        '''Rotates the matrix by the specified angle around the specified point in the specified order.
        
        :param angle: The angle of rotation in degrees.
        :param point: The point to rotate around.
        :param order: The order in which rotation is applied.'''
        ...
    
    @overload
    def rotate_at(self, angle : float, point : aspose.pydrawing.PointF):
        '''Rotates the matrix by the specified angle around the specified point.
        
        :param angle: The angle of rotation in degrees.
        :param point: The point to rotate around.'''
        ...
    
    def invert(self):
        '''Inverts this matrix.'''
        ...
    
    def get_elements(self) -> List[float]:
        '''Gets the elements of the matrix as an array.
        
        :returns: The elements of the matrix.'''
        ...
    
    def transform_point(self, point : aspose.pydrawing.PointF) -> aspose.pydrawing.PointF:
        '''Transforms the specified point using this matrix.
        
        :param point: The point to transform.
        :returns: The transformed point.'''
        ...
    
    def transform_points(self, points : aspose.pydrawing.PointF[]):
        '''Transforms an array of points using this matrix.
        
        :param points: The array of points to transform.'''
        ...
    
    def transform_rectangle(self, rect : aspose.pydrawing.RectangleF) -> aspose.pydrawing.RectangleF:
        '''Transforms the specified rectangle using this matrix.
        
        :param rect: The rectangle to transform.
        :returns: The transformed rectangle.'''
        ...
    
    def skew(self, skew_x : float, skew_y : float):
        '''Applies a skew transformation to the matrix.
        
        :param skew_x: The angle by which to skew in the x-axis direction.
        :param skew_y: The angle by which to skew in the y-axis direction.'''
        ...
    
    def reset(self):
        '''Resets the matrix to the identity matrix.'''
        ...
    
    def clone(self) -> aspose.html.drawing.IMatrix:
        '''Creates a copy of this matrix.
        
        :returns: A new instance of :py:class:`aspose.html.drawing.IMatrix` that is a copy of this matrix.'''
        ...
    
    @property
    def is_identity(self) -> bool:
        ...
    
    @property
    def m11(self) -> float:
        '''Gets the value in the first row and first column of the matrix.'''
        ...
    
    @m11.setter
    def m11(self, value : float):
        '''Sets the value in the first row and first column of the matrix.'''
        ...
    
    @property
    def m12(self) -> float:
        '''Gets the value in the first row and second column of the matrix.'''
        ...
    
    @m12.setter
    def m12(self, value : float):
        '''Sets the value in the first row and second column of the matrix.'''
        ...
    
    @property
    def m21(self) -> float:
        '''Gets the value in the second row and first column of the matrix.'''
        ...
    
    @m21.setter
    def m21(self, value : float):
        '''Sets the value in the second row and first column of the matrix.'''
        ...
    
    @property
    def m22(self) -> float:
        '''Gets the value in the second row and second column of the matrix.'''
        ...
    
    @m22.setter
    def m22(self, value : float):
        '''Sets the value in the second row and second column of the matrix.'''
        ...
    
    @property
    def m31(self) -> float:
        '''Gets the value in the third row and first column of the matrix.'''
        ...
    
    @m31.setter
    def m31(self, value : float):
        '''Sets the value in the third row and first column of the matrix.'''
        ...
    
    @property
    def m32(self) -> float:
        '''Gets the value in the third row and second column of the matrix.'''
        ...
    
    @m32.setter
    def m32(self, value : float):
        '''Sets the value in the third row and second column of the matrix.'''
        ...
    
    @property
    def is_invertible(self) -> bool:
        ...
    
    ...

class ISolidBrush(IBrush):
    '''Defines brush interface of a single color'''
    
    @property
    def color(self) -> aspose.pydrawing.Color:
        '''Get color of the brush.'''
        ...
    
    @property
    def type(self) -> aspose.html.drawing.BrushType:
        '''Gets type of brush as :py:class:`aspose.html.drawing.BrushType`.'''
        ...
    
    ...

class ITextureBrush(ITransformableBrush):
    '''Defines brush interface that uses an image to fill the interior of a shape.'''
    
    @property
    def image(self) -> bytes:
        '''Gets the image used by the brush.'''
        ...
    
    @property
    def opacity(self) -> float:
        '''Get opacity value in a color transform matrix.'''
        ...
    
    @opacity.setter
    def opacity(self, value : float):
        '''Get opacity value in a color transform matrix.'''
        ...
    
    @property
    def image_area(self) -> aspose.pydrawing.RectangleF:
        ...
    
    @property
    def color_map(self) -> aspose.pydrawing.Color[]:
        ...
    
    @property
    def transformation_matrix(self) -> aspose.html.drawing.IMatrix:
        ...
    
    @transformation_matrix.setter
    def transformation_matrix(self, value : aspose.html.drawing.IMatrix):
        ...
    
    @property
    def spread_mode(self) -> aspose.html.drawing.SpreadMode:
        ...
    
    @spread_mode.setter
    def spread_mode(self, value : aspose.html.drawing.SpreadMode):
        ...
    
    @property
    def type(self) -> aspose.html.drawing.BrushType:
        '''Gets type of brush as :py:class:`aspose.html.drawing.BrushType`.'''
        ...
    
    ...

class ITransformableBrush(IBrush):
    '''Desclares methods for getting transformation matrix and wrap mode.'''
    
    @property
    def transformation_matrix(self) -> aspose.html.drawing.IMatrix:
        ...
    
    @transformation_matrix.setter
    def transformation_matrix(self, value : aspose.html.drawing.IMatrix):
        ...
    
    @property
    def spread_mode(self) -> aspose.html.drawing.SpreadMode:
        ...
    
    @spread_mode.setter
    def spread_mode(self, value : aspose.html.drawing.SpreadMode):
        ...
    
    @property
    def type(self) -> aspose.html.drawing.BrushType:
        '''Gets type of brush as :py:class:`aspose.html.drawing.BrushType`.'''
        ...
    
    ...

class ITrueTypeFont:
    '''Declares methods for working with TrueType fonts.'''
    
    def get_data(self) -> io.RawIOBase:
        '''Opens the stream with the font data. The caller is responsible for disposing the stream.
        
        :returns: The stream with the font data.'''
        ...
    
    def get_descent(self, font_size : float) -> float:
        '''Gets the descent of the font in points using the specified font size.
        
        :param font_size: The size of the font.
        :returns: The descent of the font in points.'''
        ...
    
    def get_ascent(self, font_size : float) -> float:
        '''Gets the ascent of the font in points using the specified font size.
        
        :param font_size: The size of the font.
        :returns: The ascent of the font in points.'''
        ...
    
    @property
    def family_name(self) -> str:
        ...
    
    @property
    def sub_family_name(self) -> str:
        ...
    
    @property
    def full_font_name(self) -> str:
        ...
    
    @property
    def data_size(self) -> float:
        ...
    
    @property
    def style(self) -> aspose.html.drawing.WebFontStyle:
        '''Get the font style that combines the values of the font-face rule and data from the font.'''
        ...
    
    ...

class Length(Dimension):
    '''Represents a length measurement unit.'''
    
    @overload
    def get_value(self) -> float:
        '''Gets the unit value.
        
        :returns: The object value.'''
        ...
    
    @overload
    def get_value(self, unit_type : aspose.html.drawing.UnitType) -> float:
        '''Gets the value converted to the specified :py:class:`aspose.html.drawing.UnitType`.
        
        :param unit_type: Type of the unit.
        :returns: Returns value that is converted to specified type.'''
        ...
    
    def equals(self, other : aspose.html.drawing.Unit) -> bool:
        '''Determines whether the specified :py:class:`aspose.html.drawing.Unit`, is equal to this instance.
        
        :param other: The :py:class:`aspose.html.drawing.Unit` to compare with this instance.
        :returns: ``true`` if the specified :py:class:`aspose.html.drawing.Unit` is equal to this instance; otherwise, ``false``.'''
        ...
    
    @staticmethod
    def from_centimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_quarter_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in quarter-millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_inches(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in inches.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_picas(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in picas.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_points(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in points.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_pixels(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_degrees(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in degrees.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_gradians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in gradians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_radians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in radians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_turns(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in turns.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_seconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in seconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_milliseconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in milliseconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in hertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_kilo_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in kiloHertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_dots_per_inch(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per inch.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_centimeters(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_pixel(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    def compare_to(self, other : aspose.html.drawing.Numeric) -> int:
        '''Compares the current instance with another object of the same type and returns an integer that indicates whether the current instance precedes, follows, or occurs in the same position in the sort order as the other object.
        
        :param other: The other object to compare.
        :returns: A value that indicates the relative order of the objects being compared.'''
        ...
    
    @property
    def unit_type(self) -> aspose.html.drawing.UnitType:
        ...
    
    ...

class LengthOrAuto(Unit):
    '''Represents a container for storage length or 'auto' units..'''
    
    def equals(self, other : aspose.html.drawing.Unit) -> bool:
        '''Determines whether the specified :py:class:`aspose.html.drawing.Unit`, is equal to this instance.
        
        :param other: The :py:class:`aspose.html.drawing.Unit` to compare with this instance.
        :returns: ``true`` if the specified :py:class:`aspose.html.drawing.Unit` is equal to this instance; otherwise, ``false``.'''
        ...
    
    @staticmethod
    def from_centimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_quarter_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in quarter-millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_inches(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in inches.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_picas(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in picas.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_points(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in points.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_pixels(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_degrees(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in degrees.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_gradians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in gradians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_radians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in radians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_turns(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in turns.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_seconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in seconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_milliseconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in milliseconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in hertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_kilo_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in kiloHertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_dots_per_inch(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per inch.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_centimeters(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_pixel(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    def set_auto(self):
        '''Resets container to state 'auto'.'''
        ...
    
    @property
    def unit_type(self) -> aspose.html.drawing.UnitType:
        ...
    
    @property
    def length(self) -> aspose.html.drawing.Length:
        '''Gets the length.'''
        ...
    
    @length.setter
    def length(self, value : aspose.html.drawing.Length):
        '''Sets the length.'''
        ...
    
    @property
    def is_auto(self) -> bool:
        ...
    
    ...

class Margin:
    '''Represents page margin.'''
    
    @property
    def top(self) -> aspose.html.drawing.LengthOrAuto:
        '''Gets the top.'''
        ...
    
    @top.setter
    def top(self, value : aspose.html.drawing.LengthOrAuto):
        '''Sets the top.'''
        ...
    
    @property
    def right(self) -> aspose.html.drawing.LengthOrAuto:
        '''Gets the right.'''
        ...
    
    @right.setter
    def right(self, value : aspose.html.drawing.LengthOrAuto):
        '''Sets the right.'''
        ...
    
    @property
    def bottom(self) -> aspose.html.drawing.LengthOrAuto:
        '''Gets the bottom.'''
        ...
    
    @bottom.setter
    def bottom(self, value : aspose.html.drawing.LengthOrAuto):
        '''Sets the bottom.'''
        ...
    
    @property
    def left(self) -> aspose.html.drawing.LengthOrAuto:
        '''Gets the left.'''
        ...
    
    @left.setter
    def left(self, value : aspose.html.drawing.LengthOrAuto):
        '''Sets the left.'''
        ...
    
    ...

class Numeric(Unit):
    '''Provides the base class for numeric types.'''
    
    @overload
    def get_value(self) -> float:
        '''Gets the unit value.
        
        :returns: The object value.'''
        ...
    
    @overload
    def get_value(self, unit_type : aspose.html.drawing.UnitType) -> float:
        '''Gets the value converted to the specified :py:class:`aspose.html.drawing.UnitType`.
        
        :param unit_type: Type of the unit.
        :returns: Returns value that is converted to specified type.'''
        ...
    
    def equals(self, other : aspose.html.drawing.Unit) -> bool:
        '''Determines whether the specified :py:class:`aspose.html.drawing.Unit`, is equal to this instance.
        
        :param other: The :py:class:`aspose.html.drawing.Unit` to compare with this instance.
        :returns: ``true`` if the specified :py:class:`aspose.html.drawing.Unit` is equal to this instance; otherwise, ``false``.'''
        ...
    
    @staticmethod
    def from_centimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_quarter_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in quarter-millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_inches(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in inches.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_picas(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in picas.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_points(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in points.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_pixels(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_degrees(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in degrees.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_gradians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in gradians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_radians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in radians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_turns(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in turns.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_seconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in seconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_milliseconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in milliseconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in hertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_kilo_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in kiloHertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_dots_per_inch(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per inch.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_centimeters(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_pixel(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    def compare_to(self, other : aspose.html.drawing.Numeric) -> int:
        '''Compares the current instance with another object of the same type and returns an integer that indicates whether the current instance precedes, follows, or occurs in the same position in the sort order as the other object.
        
        :param other: The other object to compare.
        :returns: A value that indicates the relative order of the objects being compared.'''
        ...
    
    @property
    def unit_type(self) -> aspose.html.drawing.UnitType:
        ...
    
    ...

class Page:
    '''Represents a page object is used for configuration output page.
    The lacuna value for page size is A4(210x297mm)'''
    
    @property
    def size(self) -> aspose.html.drawing.Size:
        '''Gets the page size.'''
        ...
    
    @size.setter
    def size(self, value : aspose.html.drawing.Size):
        '''Sets the page size.'''
        ...
    
    @property
    def margin(self) -> aspose.html.drawing.Margin:
        '''Gets the page margin.'''
        ...
    
    @margin.setter
    def margin(self, value : aspose.html.drawing.Margin):
        '''Sets the page margin.'''
        ...
    
    ...

class Resolution(Dimension):
    '''Represents a resolution unit.'''
    
    @overload
    def get_value(self) -> float:
        '''Gets the unit value.
        
        :returns: The object value.'''
        ...
    
    @overload
    def get_value(self, unit_type : aspose.html.drawing.UnitType) -> float:
        '''Gets the value converted to the specified :py:class:`aspose.html.drawing.UnitType`.
        
        :param unit_type: Type of the unit.
        :returns: Returns value that is converted to specified type.'''
        ...
    
    def equals(self, other : aspose.html.drawing.Unit) -> bool:
        '''Determines whether the specified :py:class:`aspose.html.drawing.Unit`, is equal to this instance.
        
        :param other: The :py:class:`aspose.html.drawing.Unit` to compare with this instance.
        :returns: ``true`` if the specified :py:class:`aspose.html.drawing.Unit` is equal to this instance; otherwise, ``false``.'''
        ...
    
    @staticmethod
    def from_centimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_quarter_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in quarter-millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_inches(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in inches.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_picas(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in picas.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_points(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in points.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_pixels(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_degrees(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in degrees.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_gradians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in gradians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_radians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in radians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_turns(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in turns.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_seconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in seconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_milliseconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in milliseconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in hertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_kilo_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in kiloHertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_dots_per_inch(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per inch.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_centimeters(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_pixel(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    def compare_to(self, other : aspose.html.drawing.Numeric) -> int:
        '''Compares the current instance with another object of the same type and returns an integer that indicates whether the current instance precedes, follows, or occurs in the same position in the sort order as the other object.
        
        :param other: The other object to compare.
        :returns: A value that indicates the relative order of the objects being compared.'''
        ...
    
    @property
    def unit_type(self) -> aspose.html.drawing.UnitType:
        ...
    
    ...

class Size:
    '''Stores a values which specify a Height and Width.'''
    
    @property
    def height(self) -> aspose.html.drawing.Length:
        '''Gets the vertical component of this :py:class:`aspose.html.drawing.Size`.'''
        ...
    
    @height.setter
    def height(self, value : aspose.html.drawing.Length):
        '''Sets the vertical component of this :py:class:`aspose.html.drawing.Size`.'''
        ...
    
    @property
    def width(self) -> aspose.html.drawing.Length:
        '''Gets the horizontal component of this :py:class:`aspose.html.drawing.Size`.'''
        ...
    
    @width.setter
    def width(self, value : aspose.html.drawing.Length):
        '''Sets the horizontal component of this :py:class:`aspose.html.drawing.Size`.'''
        ...
    
    ...

class Time(Dimension):
    '''Represents a time unit.'''
    
    @overload
    def get_value(self) -> float:
        '''Gets the unit value.
        
        :returns: The object value.'''
        ...
    
    @overload
    def get_value(self, unit_type : aspose.html.drawing.UnitType) -> float:
        '''Gets the value converted to the specified :py:class:`aspose.html.drawing.UnitType`.
        
        :param unit_type: Type of the unit.
        :returns: Returns value that is converted to specified type.'''
        ...
    
    def equals(self, other : aspose.html.drawing.Unit) -> bool:
        '''Determines whether the specified :py:class:`aspose.html.drawing.Unit`, is equal to this instance.
        
        :param other: The :py:class:`aspose.html.drawing.Unit` to compare with this instance.
        :returns: ``true`` if the specified :py:class:`aspose.html.drawing.Unit` is equal to this instance; otherwise, ``false``.'''
        ...
    
    @staticmethod
    def from_centimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_quarter_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in quarter-millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_inches(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in inches.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_picas(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in picas.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_points(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in points.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_pixels(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_degrees(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in degrees.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_gradians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in gradians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_radians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in radians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_turns(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in turns.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_seconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in seconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_milliseconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in milliseconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in hertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_kilo_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in kiloHertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_dots_per_inch(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per inch.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_centimeters(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_pixel(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    def compare_to(self, other : aspose.html.drawing.Numeric) -> int:
        '''Compares the current instance with another object of the same type and returns an integer that indicates whether the current instance precedes, follows, or occurs in the same position in the sort order as the other object.
        
        :param other: The other object to compare.
        :returns: A value that indicates the relative order of the objects being compared.'''
        ...
    
    @property
    def unit_type(self) -> aspose.html.drawing.UnitType:
        ...
    
    ...

class Unit:
    '''Provides the base class for units of measurement.'''
    
    def equals(self, other : aspose.html.drawing.Unit) -> bool:
        '''Determines whether the specified :py:class:`aspose.html.drawing.Unit`, is equal to this instance.
        
        :param other: The :py:class:`aspose.html.drawing.Unit` to compare with this instance.
        :returns: ``true`` if the specified :py:class:`aspose.html.drawing.Unit` is equal to this instance; otherwise, ``false``.'''
        ...
    
    @staticmethod
    def from_centimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_quarter_millimeters(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in quarter-millimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_inches(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in inches.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_picas(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in picas.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_points(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in points.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_pixels(value : float) -> aspose.html.drawing.Length:
        '''Returns a :py:class:`aspose.html.drawing.Length` object that is represented in pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Length` object.'''
        ...
    
    @staticmethod
    def from_degrees(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in degrees.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_gradians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in gradians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_radians(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in radians.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_turns(value : float) -> aspose.html.drawing.Angle:
        '''Returns a :py:class:`aspose.html.drawing.Angle` object that is represented in turns.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Angle` object.'''
        ...
    
    @staticmethod
    def from_seconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in seconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_milliseconds(value : float) -> aspose.html.drawing.Time:
        '''Returns a :py:class:`aspose.html.drawing.Time` object that is represented in milliseconds.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Time` object.'''
        ...
    
    @staticmethod
    def from_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in hertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_kilo_hertz(value : float) -> aspose.html.drawing.Frequency:
        '''Returns a :py:class:`aspose.html.drawing.Frequency` object that is represented in kiloHertz.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Frequency` object.'''
        ...
    
    @staticmethod
    def from_dots_per_inch(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per inch.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_centimeters(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per centimeters.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @staticmethod
    def from_dots_per_pixel(value : float) -> aspose.html.drawing.Resolution:
        '''Returns a :py:class:`aspose.html.drawing.Resolution` object that is represented in dots per pixels.
        
        :param value: The value.
        :returns: Returns a :py:class:`aspose.html.drawing.Resolution` object.'''
        ...
    
    @property
    def unit_type(self) -> aspose.html.drawing.UnitType:
        ...
    
    ...

class UnitType:
    '''Specifies the unit of measurement.'''
    
    def equals(self, other : aspose.html.drawing.UnitType) -> bool:
        '''Determines whether the specified :py:class:`aspose.html.drawing.UnitType`, is equal to this instance.
        
        :param other: The :py:class:`aspose.html.drawing.UnitType` to compare with this instance.
        :returns: ``true`` if the specified :py:class:`aspose.html.drawing.UnitType` is equal to this instance; otherwise, ``false``.'''
        ...
    
    @classmethod
    @property
    def EM(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is relative to the height of the parent element's font.'''
        ...
    
    @classmethod
    @property
    def EX(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is relative to the height of the lowercase letter x of the parent element's font.'''
        ...
    
    @classmethod
    @property
    def CH(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is relative to width of the "0" (zero).'''
        ...
    
    @classmethod
    @property
    def REM(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is relative to font-size of the root element.'''
        ...
    
    @classmethod
    @property
    def VW(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is relative to 1% of the width of the viewport*'''
        ...
    
    @classmethod
    @property
    def VH(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is relative to 1% of the height of the viewport* Try it'''
        ...
    
    @classmethod
    @property
    def VMIN(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is relative to 1% of viewport's* smaller dimension Try it'''
        ...
    
    @classmethod
    @property
    def VMAX(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is relative to 1% of viewport's* larger dimension Try it'''
        ...
    
    @classmethod
    @property
    def CM(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in centimeters'''
        ...
    
    @classmethod
    @property
    def MM(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in millimeters'''
        ...
    
    @classmethod
    @property
    def Q(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in quarter-millimeters'''
        ...
    
    @classmethod
    @property
    def IN(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in inches'''
        ...
    
    @classmethod
    @property
    def PC(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in picas'''
        ...
    
    @classmethod
    @property
    def PT(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in points'''
        ...
    
    @classmethod
    @property
    def PX(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in pixels'''
        ...
    
    @classmethod
    @property
    def DEG(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in degrees.'''
        ...
    
    @classmethod
    @property
    def GRAD(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in gradians.'''
        ...
    
    @classmethod
    @property
    def RAD(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in radians.'''
        ...
    
    @classmethod
    @property
    def TURN(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in turns.'''
        ...
    
    @classmethod
    @property
    def S(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in seconds.'''
        ...
    
    @classmethod
    @property
    def MS(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in milliseconds.'''
        ...
    
    @classmethod
    @property
    def HZ(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in hertz.'''
        ...
    
    @classmethod
    @property
    def K_HZ(cls) -> aspose.html.drawing.UnitType:
        ...
    
    @classmethod
    @property
    def DPI(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in dots per inch.'''
        ...
    
    @classmethod
    @property
    def DPCM(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in dots per centimeters.'''
        ...
    
    @classmethod
    @property
    def DPPX(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in Dots per pixels unit.'''
        ...
    
    @classmethod
    @property
    def AUTO(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is not defined.'''
        ...
    
    @classmethod
    @property
    def PERCENTAGE(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is in percentage.'''
        ...
    
    @classmethod
    @property
    def INTEGER(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is an integer number.'''
        ...
    
    @classmethod
    @property
    def REAL(cls) -> aspose.html.drawing.UnitType:
        '''Measurement is a real number.'''
        ...
    
    ...

class BrushType:
    '''Specifies the type of brush.'''
    
    @classmethod
    @property
    def SOLID(cls) -> BrushType:
        '''Type is ISolidBrush'''
        ...
    
    @classmethod
    @property
    def TEXTURE(cls) -> BrushType:
        '''Type is ITextureBrush'''
        ...
    
    @classmethod
    @property
    def LINEAR_GRADIENT(cls) -> BrushType:
        '''Type is ILinearGradientBrush'''
        ...
    
    ...

class ColorModel:
    '''This enumeration is used to select the color model for working with color components.'''
    
    @classmethod
    @property
    def RGB(cls) -> ColorModel:
        '''Red-Green-Blue color model'''
        ...
    
    @classmethod
    @property
    def HSL(cls) -> ColorModel:
        '''Hue-Saturation-Luminosity color model'''
        ...
    
    @classmethod
    @property
    def HSV(cls) -> ColorModel:
        '''Hue-Saturation-Value color model'''
        ...
    
    @classmethod
    @property
    def HWB(cls) -> ColorModel:
        '''Hue-Whiteness-Blackness color model'''
        ...
    
    @classmethod
    @property
    def CMYK(cls) -> ColorModel:
        '''Cyan-Magenta-Yellow-Key color model'''
        ...
    
    @classmethod
    @property
    def LAB(cls) -> ColorModel:
        '''Lightness-A-B color model'''
        ...
    
    @classmethod
    @property
    def OKLAB(cls) -> ColorModel:
        '''Improved Lightness-A-B model'''
        ...
    
    @classmethod
    @property
    def LCH(cls) -> ColorModel:
        '''Luminance-Chroma-Hue color model'''
        ...
    
    @classmethod
    @property
    def OKLCH(cls) -> ColorModel:
        '''Improved Luminance-Chroma-Hue color model'''
        ...
    
    ...

class SpreadMode:
    '''Specifies how a texture or gradient is tiled when it is smaller than the area being filled.'''
    
    @classmethod
    @property
    def TILE(cls) -> SpreadMode:
        '''The texture or gradient is tiled.'''
        ...
    
    @classmethod
    @property
    def TILE_FLIP_X(cls) -> SpreadMode:
        '''The texture or gradient is tiled and flipped horizontally.'''
        ...
    
    @classmethod
    @property
    def TILE_FLIP_Y(cls) -> SpreadMode:
        '''The texture or gradient is tiled and flipped vertically.'''
        ...
    
    @classmethod
    @property
    def TILE_FLIP_XY(cls) -> SpreadMode:
        '''The texture or gradient is tiled and flipped both horizontally and vertically.'''
        ...
    
    @classmethod
    @property
    def CLAMP(cls) -> SpreadMode:
        '''The texture or gradient is clamped to the edge.'''
        ...
    
    ...

class WebFontStyle:
    '''Specifies the formatting applied to the text.'''
    
    @classmethod
    @property
    def REGULAR(cls) -> WebFontStyle:
        '''Regular text.'''
        ...
    
    @classmethod
    @property
    def BOLD(cls) -> WebFontStyle:
        '''Bold text.'''
        ...
    
    @classmethod
    @property
    def ITALIC(cls) -> WebFontStyle:
        '''Italic text.'''
        ...
    
    ...

class WebImageFormat:
    '''Specifies the supported image formats.'''
    
    @classmethod
    @property
    def BMP(cls) -> WebImageFormat:
        '''The BMP image format.'''
        ...
    
    @classmethod
    @property
    def GIF(cls) -> WebImageFormat:
        '''The GIF image format.'''
        ...
    
    @classmethod
    @property
    def ICO(cls) -> WebImageFormat:
        '''The ICO image format.'''
        ...
    
    @classmethod
    @property
    def JPEG(cls) -> WebImageFormat:
        '''The JPEG image format.'''
        ...
    
    @classmethod
    @property
    def PNG(cls) -> WebImageFormat:
        '''The PNG image format.'''
        ...
    
    @classmethod
    @property
    def WBMP(cls) -> WebImageFormat:
        '''The WBMP image format.'''
        ...
    
    @classmethod
    @property
    def WEBP(cls) -> WebImageFormat:
        '''The WEBP image format.'''
        ...
    
    @classmethod
    @property
    def PKM(cls) -> WebImageFormat:
        '''The PKM image format.'''
        ...
    
    @classmethod
    @property
    def KTX(cls) -> WebImageFormat:
        '''The KTX image format.'''
        ...
    
    @classmethod
    @property
    def ASTC(cls) -> WebImageFormat:
        '''The ASTC image format.'''
        ...
    
    @classmethod
    @property
    def DNG(cls) -> WebImageFormat:
        '''The Adobe DNG image format.'''
        ...
    
    @classmethod
    @property
    def HEIF(cls) -> WebImageFormat:
        '''The HEIF or High Efficiency Image File format.'''
        ...
    
    @classmethod
    @property
    def AVIF(cls) -> WebImageFormat:
        '''Avif image type.'''
        ...
    
    @classmethod
    @property
    def TIFF(cls) -> WebImageFormat:
        '''Tiff image type.'''
        ...
    
    @classmethod
    @property
    def UNKNOWN(cls) -> WebImageFormat:
        '''An unknown image type.'''
        ...
    
    ...

class WebMatrixOrder:
    '''Specifies the order in which matrix transformations are applied.'''
    
    @classmethod
    @property
    def APPEND(cls) -> WebMatrixOrder:
        '''Specifies that the transformation is appended to the existing transformation.'''
        ...
    
    @classmethod
    @property
    def PREPEND(cls) -> WebMatrixOrder:
        '''Specifies that the transformation is prepended to the existing transformation.'''
        ...
    
    ...

