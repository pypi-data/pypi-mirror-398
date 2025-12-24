from typing import List, Optional, Dict, Iterable, Any, overload
import io
import collections.abc
from collections.abc import Sequence
from datetime import datetime
from aspose.pyreflection import Type
import aspose.pycore
import aspose.pydrawing
from uuid import UUID
import groupdocs.viewer
import groupdocs.viewer.caching
import groupdocs.viewer.drawing
import groupdocs.viewer.exceptions
import groupdocs.viewer.fonts
import groupdocs.viewer.interfaces
import groupdocs.viewer.logging
import groupdocs.viewer.options
import groupdocs.viewer.results

class Argb32Color:
    '''Represents 32-bit color in ARGB format, with 8 bits per every channel (Alpha, Red, Green, Blue). Supports transparency.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def from_other_with_alpha(other : groupdocs.viewer.drawing.Argb32Color, new_alpha : int) -> groupdocs.viewer.drawing.Argb32Color:
        '''Creates a new :py:class:`groupdocs.viewer.drawing.Argb32Color` instance from specified, but with re-defined alpha (opacity) value
        
        :param other: Other :py:class:`groupdocs.viewer.drawing.Argb32Color` instance, from which the new one will be created
        :param new_alpha: Re-defined alpha channel value (255 - fully opaque, 0 - fully transparent)
        :returns: New :py:class:`groupdocs.viewer.drawing.Argb32Color` instance'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def from_other_with_alpha(other : groupdocs.viewer.drawing.Rgb24Color, new_alpha : int) -> groupdocs.viewer.drawing.Argb32Color:
        '''Creates a new :py:class:`groupdocs.viewer.drawing.Argb32Color` instance from specified :py:class:`groupdocs.viewer.drawing.Rgb24Color`, but with specified alpha (opacity) value
        
        :param other: Other :py:class:`groupdocs.viewer.drawing.Rgb24Color` instance, from which the new one will be created
        :param new_alpha: Alpha channel value (255 - fully opaque, 0 - fully transparent)
        :returns: New :py:class:`groupdocs.viewer.drawing.Argb32Color` instance'''
        raise NotImplementedError()
    
    @overload
    def equals(self, other : groupdocs.viewer.drawing.Argb32Color) -> bool:
        '''Checks this color with specified :py:class:`groupdocs.viewer.drawing.Argb32Color` color for equality
        
        :param other: The other :py:class:`groupdocs.viewer.drawing.Argb32Color` color
        :returns: True if both colors or equal, otherwise false.'''
        raise NotImplementedError()
    
    @overload
    def equals(self, other : groupdocs.viewer.drawing.Rgb24Color) -> bool:
        '''Checks this color with specified :py:class:`groupdocs.viewer.drawing.Rgb24Color` color for equality
        
        :param other: The other :py:class:`groupdocs.viewer.drawing.Rgb24Color` color
        :returns: True if both colors or equal, otherwise false.'''
        raise NotImplementedError()
    
    @staticmethod
    def from_rgba(red : int, green : int, blue : int, alpha : int) -> groupdocs.viewer.drawing.Argb32Color:
        '''Creates one :py:class:`groupdocs.viewer.drawing.Argb32Color` value from specified Red, Green, Blue, and Alpha channels
        
        :param red: Red channel value
        :param green: Green channel value
        :param blue: Blue channel value
        :param alpha: Alpha channel value
        :returns: New :py:class:`groupdocs.viewer.drawing.Argb32Color` value'''
        raise NotImplementedError()
    
    @staticmethod
    def from_argb(argb : int) -> groupdocs.viewer.drawing.Argb32Color:
        '''Creates a :py:class:`groupdocs.viewer.drawing.Argb32Color` instance from its 32-bit component (alpha, red, green, and blue) values, compatible with value, produced by the ``System.Drawing.Color.ToArgb()`` method
        
        :param argb: A value specifying the 32-bit ARGB value
        :returns: New :py:class:`groupdocs.viewer.drawing.Argb32Color` value'''
        raise NotImplementedError()
    
    @staticmethod
    def from_rgb(red : int, green : int, blue : int) -> groupdocs.viewer.drawing.Argb32Color:
        '''Creates one :py:class:`groupdocs.viewer.drawing.Argb32Color` value from specified Red, Green, Blue channels, while Alpha channel is fully opaque
        
        :param red: Red channel value
        :param green: Green channel value
        :param blue: Blue channel value
        :returns: New :py:class:`groupdocs.viewer.drawing.Argb32Color` value'''
        raise NotImplementedError()
    
    @staticmethod
    def from_single_value_rgb(value : int) -> groupdocs.viewer.drawing.Argb32Color:
        '''Creates a fully opaque (A=255) color from single value, which will be applied to all channels
        
        :param value: A byte value, same for Red, Green, and Blue channels
        :returns: New :py:class:`groupdocs.viewer.drawing.Argb32Color` instance'''
        raise NotImplementedError()
    
    def get_brightness(self) -> float:
        '''Returns the Hue-Saturation-Lightness (HSL) lightness/brightness for this :py:class:`groupdocs.viewer.drawing.Argb32Color` instance.'''
        raise NotImplementedError()
    
    def get_hue(self) -> float:
        '''Returns the Hue-Saturation-Lightness (HSL) hue value, in degrees, for this :py:class:`groupdocs.viewer.drawing.Argb32Color` instance. If R == G == B, the hue is meaningless, and the return value is 0.'''
        raise NotImplementedError()
    
    def get_saturation(self) -> float:
        '''The Hue-Saturation-Lightness (HSL) saturation for this :py:class:`groupdocs.viewer.drawing.Argb32Color` instance'''
        raise NotImplementedError()
    
    def to_argb(self) -> int:
        '''Returns the ARGB value of this :py:class:`groupdocs.viewer.drawing.Argb32Color` instance, compatible with ``System.Drawing.Color.ToArgb()`` method
        
        :returns: 32-bit ARGB value of this instance as :py:class:`int`, identical to ``System.Drawing.Color.ToArgb()`` call for the same color. Never throws an exception.'''
        raise NotImplementedError()
    
    def to_rgba(self) -> str:
        '''Serializes this :py:class:`groupdocs.viewer.drawing.Argb32Color` instance to the \'rgba\' CSS function notation
        
        :returns: A string with \'rgba(r, g, b, a)\' format'''
        raise NotImplementedError()
    
    def to_rgb(self) -> str:
        '''Serializes this :py:class:`groupdocs.viewer.drawing.Argb32Color` instance to the \'rgb\' CSS function notation. Alpha channel of this color will be omitted during serialization.
        
        :returns: A string in \'rgb(r, g, b)\' format'''
        raise NotImplementedError()
    
    @property
    def value(self) -> int:
        '''Gets the Int32 value of the color as 32-bit signed integer'''
        raise NotImplementedError()
    
    @property
    def a(self) -> int:
        '''Gets the alpha part of the color as 8-bit unsigned integer [0..255]'''
        raise NotImplementedError()
    
    @property
    def alpha(self) -> float:
        '''Gets the alpha part of the color in percent in (0..1) range.'''
        raise NotImplementedError()
    
    @property
    def r(self) -> int:
        '''Gets the red part of the color as 8-bit unsigned integer [0..255]'''
        raise NotImplementedError()
    
    @property
    def g(self) -> int:
        '''Gets the green part of the color as 8-bit unsigned integer [0..255]'''
        raise NotImplementedError()
    
    @property
    def b(self) -> int:
        '''Gets the blue part of the color as 8-bit unsigned integer [0..255]'''
        raise NotImplementedError()
    
    @property
    def is_empty(self) -> bool:
        '''Indicates whether this :py:class:`groupdocs.viewer.drawing.Argb32Color` color instance is uninitialized - all 4 channels are set to 0. Same as Default and Transparent. Same as :py:attr:`groupdocs.viewer.drawing.Argb32Color.IsDefault`'''
        raise NotImplementedError()
    
    @property
    def is_fully_transparent(self) -> bool:
        '''Indicates whether this :py:class:`groupdocs.viewer.drawing.Argb32Color` instance is fully transparent - its Alpha channel has the min (0) value, so other R, G, and B channels has no visible effect.'''
        raise NotImplementedError()
    
    @property
    def is_translucent(self) -> bool:
        '''Indicates whether this :py:class:`groupdocs.viewer.drawing.Argb32Color` instance is translucent (not fully transparent, but also not fully opaque)'''
        raise NotImplementedError()
    
    @property
    def is_fully_opaque(self) -> bool:
        '''Indicates whether this :py:class:`groupdocs.viewer.drawing.Argb32Color` instance is fully opaque, without transparency (its Alpha channel has max value)'''
        raise NotImplementedError()
    
    @property
    def EMPTY(self) -> groupdocs.viewer.drawing.Argb32Color:
        '''Returns an empty color, which has no channels info and is fully transparent. Same as \':py:attr:`groupdocs.viewer.drawing.Argb32Color.TRANSPARENT`\'. Default value.'''
        raise NotImplementedError()

    @property
    def TRANSPARENT(self) -> groupdocs.viewer.drawing.Argb32Color:
        '''Fully transparent empty color. The same as default \':py:attr:`groupdocs.viewer.drawing.Argb32Color.EMPTY`\' color value.'''
        raise NotImplementedError()


class Image2DFormat:
    '''Represents most common 2D image formats, supports both raster and vector formats'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.viewer.drawing.Image2DFormat) -> bool:
        '''Determines whether this instance is equal with specified ":py:class:`groupdocs.viewer.drawing.Image2DFormat`" instance
        
        :param other: Other :py:class:`groupdocs.viewer.drawing.Image2DFormat` instance to check on equality with this
        :returns: True if are equal, false if are unequal'''
        raise NotImplementedError()
    
    @staticmethod
    def parse_from_filename_with_extension(filename : str) -> groupdocs.viewer.drawing.Image2DFormat:
        '''Returns ImageFormat value, which is equivalent of filename extension, which is extracted from specified filename
        
        :param filename: Arbitrary filename, can be a relative or full path
        :returns: ImageFormat value. Returns :py:attr:`groupdocs.viewer.drawing.Image2DFormat.undefined`, if extension cannot be recognized.'''
        raise NotImplementedError()
    
    @staticmethod
    def parse_from_mime(mime_code : str) -> groupdocs.viewer.drawing.Image2DFormat:
        '''Returns :py:class:`groupdocs.viewer.drawing.Image2DFormat` value, which is equivalent of specified MIME code
        
        :param mime_code: Arbitrary MIME-code
        :returns: :py:class:`groupdocs.viewer.drawing.Image2DFormat` value. Returns :py:attr:`groupdocs.viewer.drawing.Image2DFormat.undefined`, if extension cannot be recognized.'''
        raise NotImplementedError()
    
    @property
    def undefined(self) -> groupdocs.viewer.drawing.Image2DFormat:
        '''Undefined image type - special value, which should not normally occur'''
        raise NotImplementedError()

    @property
    def jpeg(self) -> groupdocs.viewer.drawing.Image2DFormat:
        '''JPEG image type'''
        raise NotImplementedError()

    @property
    def png(self) -> groupdocs.viewer.drawing.Image2DFormat:
        '''PNG image type'''
        raise NotImplementedError()

    @property
    def bmp(self) -> groupdocs.viewer.drawing.Image2DFormat:
        '''BMP image type'''
        raise NotImplementedError()

    @property
    def gif(self) -> groupdocs.viewer.drawing.Image2DFormat:
        '''GIF image type'''
        raise NotImplementedError()

    @property
    def icon(self) -> groupdocs.viewer.drawing.Image2DFormat:
        '''ICON image type'''
        raise NotImplementedError()

    @property
    def svg(self) -> groupdocs.viewer.drawing.Image2DFormat:
        '''SVG vector image type'''
        raise NotImplementedError()

    @property
    def wmf(self) -> groupdocs.viewer.drawing.Image2DFormat:
        '''WMF (Windows MetaFile) vector image type'''
        raise NotImplementedError()

    @property
    def emf(self) -> groupdocs.viewer.drawing.Image2DFormat:
        '''EMF (Enhanced MetaFile) vector image type'''
        raise NotImplementedError()

    @property
    def tiff(self) -> groupdocs.viewer.drawing.Image2DFormat:
        '''TIFF (Tagged Image File Format) raster image type'''
        raise NotImplementedError()

    @property
    def name(self) -> str:
        '''Returns a formal name of this image format. Never reurns NULL. If instance is not corrupted, never throws an exception.'''
        raise NotImplementedError()
    
    @property
    def is_vector(self) -> bool:
        '''Indicates whether this particular format is vector (``true``) or raster (``false``)'''
        raise NotImplementedError()
    
    @property
    def file_extension(self) -> str:
        '''File extension (without leading dot character) of a particular image type in lower case. For the :py:attr:`groupdocs.viewer.drawing.Image2DFormat.undefined` value returns a string \'undefined\'.'''
        raise NotImplementedError()
    
    @property
    def mime_code(self) -> str:
        '''MIME code of a particular image type as a string. For the Undefined type returns a string \'unsefined\'.'''
        raise NotImplementedError()
    

class Rgb24Color:
    '''Represents 24-bit color in RGB format, with 8 bits per every channel (Red, Green, Blue). Does not support transparency.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def equals(self, other : groupdocs.viewer.drawing.Argb32Color) -> bool:
        '''Checks this color with specified :py:class:`groupdocs.viewer.drawing.Argb32Color` color for equality
        
        :param other: The other :py:class:`groupdocs.viewer.drawing.Argb32Color` color
        :returns: True if both colors or equal, otherwise false.'''
        raise NotImplementedError()
    
    @overload
    def equals(self, other : groupdocs.viewer.drawing.Rgb24Color) -> bool:
        '''Checks this color with specified :py:class:`groupdocs.viewer.drawing.Rgb24Color` color for equality
        
        :param other: The other :py:class:`groupdocs.viewer.drawing.Rgb24Color` color
        :returns: True if both colors or equal, otherwise false.'''
        raise NotImplementedError()
    
    @staticmethod
    def from_rgb(red : int, green : int, blue : int) -> groupdocs.viewer.drawing.Rgb24Color:
        '''Creates one :py:class:`groupdocs.viewer.drawing.Rgb24Color` value from specified Red, Green, Blue channels
        
        :param red: Red channel value
        :param green: Green channel value
        :param blue: Blue channel value
        :returns: New :py:class:`groupdocs.viewer.drawing.Rgb24Color` value'''
        raise NotImplementedError()
    
    def get_brightness(self) -> float:
        '''Returns the Hue-Saturation-Lightness (HSL) lightness/brightness for this :py:class:`groupdocs.viewer.drawing.Rgb24Color` instance.'''
        raise NotImplementedError()
    
    def get_hue(self) -> float:
        '''Returns the Hue-Saturation-Lightness (HSL) hue value, in degrees, for this :py:class:`groupdocs.viewer.drawing.Rgb24Color` instance. If R == G == B, the hue is meaningless, and the return value is 0.'''
        raise NotImplementedError()
    
    def get_saturation(self) -> float:
        '''The Hue-Saturation-Lightness (HSL) saturation for this :py:class:`groupdocs.viewer.drawing.Rgb24Color` instance'''
        raise NotImplementedError()
    
    def to_argb(self) -> int:
        '''Returns the ARGB value of this :py:class:`groupdocs.viewer.drawing.Rgb24Color` instance, compatible with :py:class:`aspose.pydrawing.Color`
        
        :returns: 32-bit ARGB value of this instance as :py:class:`int`, the identical to :py:func:`aspose.pydrawing.Color.ToArgb` call for the same color. Never throws an exception.'''
        raise NotImplementedError()
    
    def to_rgb(self) -> str:
        '''Serializes this :py:class:`groupdocs.viewer.drawing.Rgb24Color` instance to the \'rgb\' CSS function notation.
        
        :returns: A string in \'rgb(r, g, b)\' format'''
        raise NotImplementedError()
    
    def to_hex(self) -> str:
        '''Returns this color in hexadecimal string representation
        
        :returns: Color hex representation string'''
        raise NotImplementedError()
    
    @property
    def r(self) -> int:
        '''Gets the red part of the color as 8-bit unsigned integer [0..255]'''
        raise NotImplementedError()
    
    @property
    def g(self) -> int:
        '''Gets the green part of the color as 8-bit unsigned integer [0..255]'''
        raise NotImplementedError()
    
    @property
    def b(self) -> int:
        '''Gets the blue part of the color as 8-bit unsigned integer [0..255]'''
        raise NotImplementedError()
    
    @property
    def is_default(self) -> bool:
        '''Indicates whether this :py:class:`groupdocs.viewer.drawing.Rgb24Color` instance is default (Black) - all 3 channels are set to 0.'''
        raise NotImplementedError()
    

