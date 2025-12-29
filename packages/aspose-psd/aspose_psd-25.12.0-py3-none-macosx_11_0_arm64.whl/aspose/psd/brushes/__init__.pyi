from typing import List, Optional, Dict, Iterable, Any, overload
import io
import collections.abc
from collections.abc import Sequence
from datetime import datetime
from aspose.pyreflection import Type
import aspose.pycore
import aspose.pydrawing
from uuid import UUID
import aspose.psd
import aspose.psd.asynctask
import aspose.psd.brushes
import aspose.psd.coreexceptions
import aspose.psd.coreexceptions.compressors
import aspose.psd.coreexceptions.imageformats
import aspose.psd.customfonthandler
import aspose.psd.dithering
import aspose.psd.evalute
import aspose.psd.exif
import aspose.psd.exif.enums
import aspose.psd.extensions
import aspose.psd.fileformats
import aspose.psd.fileformats.ai
import aspose.psd.fileformats.bmp
import aspose.psd.fileformats.core
import aspose.psd.fileformats.core.blending
import aspose.psd.fileformats.core.vectorpaths
import aspose.psd.fileformats.jpeg
import aspose.psd.fileformats.jpeg2000
import aspose.psd.fileformats.pdf
import aspose.psd.fileformats.png
import aspose.psd.fileformats.psd
import aspose.psd.fileformats.psd.core
import aspose.psd.fileformats.psd.core.rawcolor
import aspose.psd.fileformats.psd.layers
import aspose.psd.fileformats.psd.layers.adjustmentlayers
import aspose.psd.fileformats.psd.layers.animation
import aspose.psd.fileformats.psd.layers.filllayers
import aspose.psd.fileformats.psd.layers.fillsettings
import aspose.psd.fileformats.psd.layers.gradient
import aspose.psd.fileformats.psd.layers.layereffects
import aspose.psd.fileformats.psd.layers.layerresources
import aspose.psd.fileformats.psd.layers.layerresources.strokeresources
import aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures
import aspose.psd.fileformats.psd.layers.smartfilters
import aspose.psd.fileformats.psd.layers.smartfilters.rendering
import aspose.psd.fileformats.psd.layers.smartobjects
import aspose.psd.fileformats.psd.layers.text
import aspose.psd.fileformats.psd.layers.warp
import aspose.psd.fileformats.psd.resources
import aspose.psd.fileformats.psd.resources.enums
import aspose.psd.fileformats.psd.resources.resolutionenums
import aspose.psd.fileformats.tiff
import aspose.psd.fileformats.tiff.enums
import aspose.psd.fileformats.tiff.filemanagement
import aspose.psd.flatarray
import aspose.psd.flatarray.exceptions
import aspose.psd.imagefilters
import aspose.psd.imagefilters.filteroptions
import aspose.psd.imageloadoptions
import aspose.psd.imageoptions
import aspose.psd.interfaces
import aspose.psd.memorymanagement
import aspose.psd.multithreading
import aspose.psd.palettehelper
import aspose.psd.progressmanagement
import aspose.psd.shapes
import aspose.psd.shapesegments
import aspose.psd.sources
import aspose.psd.xmp
import aspose.psd.xmp.schemas
import aspose.psd.xmp.schemas.dublincore
import aspose.psd.xmp.schemas.pdf
import aspose.psd.xmp.schemas.photoshop
import aspose.psd.xmp.schemas.xmpbaseschema
import aspose.psd.xmp.schemas.xmpdm
import aspose.psd.xmp.schemas.xmpmm
import aspose.psd.xmp.schemas.xmprm
import aspose.psd.xmp.types
import aspose.psd.xmp.types.basic
import aspose.psd.xmp.types.complex
import aspose.psd.xmp.types.complex.colorant
import aspose.psd.xmp.types.complex.dimensions
import aspose.psd.xmp.types.complex.font
import aspose.psd.xmp.types.complex.resourceevent
import aspose.psd.xmp.types.complex.resourceref
import aspose.psd.xmp.types.complex.thumbnail
import aspose.psd.xmp.types.complex.version
import aspose.psd.xmp.types.derived

class HatchBrush(aspose.psd.Brush):
    '''Defines a rectangular brush with a hatch style, a foreground color, and a background color. This class cannot be inherited.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def deep_clone(self) -> aspose.psd.Brush:
        '''Creates a new deep clone of the current :py:class:`aspose.psd.Brush`.
        
        :returns: A new :py:class:`aspose.psd.Brush` which is the deep clone of this :py:class:`aspose.psd.Brush` instance.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @property
    def foreground_color(self) -> aspose.psd.Color:
        '''Gets the color of hatch lines.'''
        raise NotImplementedError()
    
    @foreground_color.setter
    def foreground_color(self, value : aspose.psd.Color) -> None:
        '''Sets the color of hatch lines.'''
        raise NotImplementedError()
    
    @property
    def background_color(self) -> aspose.psd.Color:
        '''Gets the color of spaces between the hatch lines.'''
        raise NotImplementedError()
    
    @background_color.setter
    def background_color(self, value : aspose.psd.Color) -> None:
        '''Sets the color of spaces between the hatch lines.'''
        raise NotImplementedError()
    
    @property
    def hatch_style(self) -> aspose.psd.HatchStyle:
        '''Gets the hatch style of this brush.'''
        raise NotImplementedError()
    
    @hatch_style.setter
    def hatch_style(self, value : aspose.psd.HatchStyle) -> None:
        '''Sets the hatch style of this brush.'''
        raise NotImplementedError()
    

class LinearGradientBrush(LinearGradientBrushBase):
    '''Encapsulates a :py:class:`aspose.psd.Brush` with a linear gradient. This class cannot be inherited.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearGradientBrush` class with default parameters.
        The starting color is black, the ending color is white, the angle is 45 degrees and the rectangle is located in (0,0) with size (1,1).'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, point1 : aspose.psd.Point, point2 : aspose.psd.Point, color1 : aspose.psd.Color, color2 : aspose.psd.Color) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearGradientBrush` class with the specified points and colors.
        
        :param point1: A :py:class:`aspose.psd.Point` structure that represents the starting point of the linear gradient.
        :param point2: A :py:class:`aspose.psd.Point` structure that represents the endpoint of the linear gradient.
        :param color1: A :py:class:`aspose.psd.Color` structure that represents the starting color of the linear gradient.
        :param color2: A :py:class:`aspose.psd.Color` structure that represents the ending color of the linear gradient.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, point1 : aspose.psd.PointF, point2 : aspose.psd.PointF, color1 : aspose.psd.Color, color2 : aspose.psd.Color) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearGradientBrush` class with the specified points and colors.
        
        :param point1: A :py:class:`aspose.psd.PointF` structure that represents the starting point of the linear gradient.
        :param point2: A :py:class:`aspose.psd.PointF` structure that represents the endpoint of the linear gradient.
        :param color1: A :py:class:`aspose.psd.Color` structure that represents the starting color of the linear gradient.
        :param color2: A :py:class:`aspose.psd.Color` structure that represents the ending color of the linear gradient.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rect : aspose.psd.Rectangle, color1 : aspose.psd.Color, color2 : aspose.psd.Color, angle : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearGradientBrush` class based on a rectangle, starting and ending colors, and an orientation angle.
        
        :param rect: A :py:class:`aspose.psd.RectangleF` structure that specifies the bounds of the linear gradient.
        :param color1: A :py:class:`aspose.psd.Color` structure that represents the starting color for the gradient.
        :param color2: A :py:class:`aspose.psd.Color` structure that represents the ending color for the gradient.
        :param angle: The angle, measured in degrees clockwise from the x-axis, of the gradient\'s orientation line.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rect : aspose.psd.RectangleF, color1 : aspose.psd.Color, color2 : aspose.psd.Color, angle : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearGradientBrush` class based on a rectangle, starting and ending colors, and an orientation angle.
        
        :param rect: A :py:class:`aspose.psd.RectangleF` structure that specifies the bounds of the linear gradient.
        :param color1: A :py:class:`aspose.psd.Color` structure that represents the starting color for the gradient.
        :param color2: A :py:class:`aspose.psd.Color` structure that represents the ending color for the gradient.
        :param angle: The angle, measured in degrees clockwise from the x-axis, of the gradient\'s orientation line.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rect : aspose.psd.Rectangle, color1 : aspose.psd.Color, color2 : aspose.psd.Color, angle : float, is_angle_scalable : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearGradientBrush` class based on a rectangle, starting and ending colors, and an orientation angle.
        
        :param rect: A :py:class:`aspose.psd.RectangleF` structure that specifies the bounds of the linear gradient.
        :param color1: A :py:class:`aspose.psd.Color` structure that represents the starting color for the gradient.
        :param color2: A :py:class:`aspose.psd.Color` structure that represents the ending color for the gradient.
        :param angle: The angle, measured in degrees clockwise from the x-axis, of the gradient\'s orientation line.
        :param is_angle_scalable: if set to ``true`` the angle is changed during transformations with this :py:class:`aspose.psd.brushes.LinearGradientBrush`.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rect : aspose.psd.RectangleF, color1 : aspose.psd.Color, color2 : aspose.psd.Color, angle : float, is_angle_scalable : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearGradientBrush` class based on a rectangle, starting and ending colors, and an orientation angle.
        
        :param rect: A :py:class:`aspose.psd.RectangleF` structure that specifies the bounds of the linear gradient.
        :param color1: A :py:class:`aspose.psd.Color` structure that represents the starting color for the gradient.
        :param color2: A :py:class:`aspose.psd.Color` structure that represents the ending color for the gradient.
        :param angle: The angle, measured in degrees clockwise from the x-axis, of the gradient\'s orientation line.
        :param is_angle_scalable: if set to ``true`` the angle is changed during transformations with this :py:class:`aspose.psd.brushes.LinearGradientBrush`.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` by prepending the specified :py:class:`aspose.psd.Matrix`.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix, order : aspose.psd.MatrixOrder) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` in the specified order.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies in which order to multiply the two matrices.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float) -> None:
        '''Translates the local geometric transform by the specified dimensions. This method prepends the translation to the transform.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Translates the local geometric transform by the specified dimensions in the specified order.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.
        :param order: The order (prepend or append) in which to apply the translation.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float) -> None:
        '''Scales the local geometric transform by the specified amounts. This method prepends the scaling matrix to the transform.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Scales the local geometric transform by the specified amounts in the specified order.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the scaling matrix.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float) -> None:
        '''Rotates the local geometric transform by the specified amount. This method prepends the rotation to the transform.
        
        :param angle: The angle of rotation.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float, order : aspose.psd.MatrixOrder) -> None:
        '''Rotates the local geometric transform by the specified amount in the specified order.
        
        :param angle: The angle of rotation.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the rotation matrix.'''
        raise NotImplementedError()
    
    @overload
    def set_sigma_bell_shape(self, focus : float) -> None:
        '''Creates a gradient falloff based on a bell-shaped curve.
        
        :param focus: A value from 0 through 1 that specifies the center of the gradient (the point where the starting color and ending color are blended equally).'''
        raise NotImplementedError()
    
    @overload
    def set_sigma_bell_shape(self, focus : float, scale : float) -> None:
        '''Creates a gradient falloff based on a bell-shaped curve.
        
        :param focus: A value from 0 through 1 that specifies the center of the gradient (the point where the gradient is composed of only the ending color).
        :param scale: A value from 0 through 1 that specifies how fast the colors falloff from the ``focus``.'''
        raise NotImplementedError()
    
    @overload
    def set_blend_triangular_shape(self, focus : float) -> None:
        '''Creates a linear gradient with a center color and a linear falloff to a single color on both ends.
        
        :param focus: A value from 0 through 1 that specifies the center of the gradient (the point where the gradient is composed of only the ending color).'''
        raise NotImplementedError()
    
    @overload
    def set_blend_triangular_shape(self, focus : float, scale : float) -> None:
        '''Creates a linear gradient with a center color and a linear falloff to a single color on both ends.
        
        :param focus: A value from 0 through 1 that specifies the center of the gradient (the point where the gradient is composed of only the ending color).
        :param scale: A value from 0 through1 that specifies how fast the colors falloff from the starting color to ``focus`` (ending color)'''
        raise NotImplementedError()
    
    def deep_clone(self) -> aspose.psd.Brush:
        '''Creates a new deep clone of the current :py:class:`aspose.psd.Brush`.
        
        :returns: A new :py:class:`aspose.psd.Brush` which is the deep clone of this :py:class:`aspose.psd.Brush` instance.'''
        raise NotImplementedError()
    
    def reset_transform(self) -> None:
        '''Resets the :py:attr:`aspose.psd.brushes.TransformBrush.transform` property to identity.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @property
    def wrap_mode(self) -> aspose.psd.WrapMode:
        '''Gets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @wrap_mode.setter
    def wrap_mode(self, value : aspose.psd.WrapMode) -> None:
        '''Sets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def transform(self) -> aspose.psd.Matrix:
        '''Gets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @transform.setter
    def transform(self, value : aspose.psd.Matrix) -> None:
        '''Sets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def is_transform_changed(self) -> bool:
        '''Gets a value indicating whether transformations were changed in some way. For example setting the transformation matrix or
        calling any of the methods altering the transformation matrix. The property is introduced for backward compatibility with GDI+.'''
        raise NotImplementedError()
    
    @property
    def rectangle(self) -> aspose.psd.RectangleF:
        '''Gets a rectangular region that defines the starting and ending points of the gradient.'''
        raise NotImplementedError()
    
    @rectangle.setter
    def rectangle(self, value : aspose.psd.RectangleF) -> None:
        '''Sets a rectangular region that defines the starting and ending points of the gradient.'''
        raise NotImplementedError()
    
    @property
    def angle(self) -> float:
        '''Gets the gradient angle.'''
        raise NotImplementedError()
    
    @angle.setter
    def angle(self, value : float) -> None:
        '''Sets the gradient angle.'''
        raise NotImplementedError()
    
    @property
    def is_angle_scalable(self) -> bool:
        '''Gets a value indicating whether :py:attr:`aspose.psd.brushes.LinearGradientBrushBase.angle` is changed during trasnformations with this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    
    @is_angle_scalable.setter
    def is_angle_scalable(self, value : bool) -> None:
        '''Sets a value indicating whether :py:attr:`aspose.psd.brushes.LinearGradientBrushBase.angle` is changed during trasnformations with this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    
    @property
    def gamma_correction(self) -> bool:
        '''Gets a value indicating whether gamma correction is enabled for this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    
    @gamma_correction.setter
    def gamma_correction(self, value : bool) -> None:
        '''Sets a value indicating whether gamma correction is enabled for this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    
    @property
    def interpolation_colors(self) -> aspose.psd.ColorBlend:
        '''Gets a :py:class:`aspose.psd.ColorBlend` that defines a multicolor linear gradient.'''
        raise NotImplementedError()
    
    @interpolation_colors.setter
    def interpolation_colors(self, value : aspose.psd.ColorBlend) -> None:
        '''Sets a :py:class:`aspose.psd.ColorBlend` that defines a multicolor linear gradient.'''
        raise NotImplementedError()
    
    @property
    def linear_colors(self) -> List[aspose.psd.Color]:
        '''Gets the starting and ending colors of the gradient.'''
        raise NotImplementedError()
    
    @linear_colors.setter
    def linear_colors(self, value : List[aspose.psd.Color]) -> None:
        '''Sets the starting and ending colors of the gradient.'''
        raise NotImplementedError()
    
    @property
    def start_color(self) -> aspose.psd.Color:
        '''Gets the starting gradient color.'''
        raise NotImplementedError()
    
    @start_color.setter
    def start_color(self, value : aspose.psd.Color) -> None:
        '''Sets the starting gradient color.'''
        raise NotImplementedError()
    
    @property
    def end_color(self) -> aspose.psd.Color:
        '''Gets the ending gradient color.'''
        raise NotImplementedError()
    
    @end_color.setter
    def end_color(self, value : aspose.psd.Color) -> None:
        '''Sets the ending gradient color.'''
        raise NotImplementedError()
    
    @property
    def blend(self) -> aspose.psd.Blend:
        '''Gets a :py:class:`aspose.psd.Blend` that specifies positions and factors that define a custom falloff for the gradient.'''
        raise NotImplementedError()
    
    @blend.setter
    def blend(self, value : aspose.psd.Blend) -> None:
        '''Sets a :py:class:`aspose.psd.Blend` that specifies positions and factors that define a custom falloff for the gradient.'''
        raise NotImplementedError()
    

class LinearGradientBrushBase(TransformBrush):
    '''Represents a :py:class:`aspose.psd.Brush` with gradient capabilities and appropriate properties.'''
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` by prepending the specified :py:class:`aspose.psd.Matrix`.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix, order : aspose.psd.MatrixOrder) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` in the specified order.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies in which order to multiply the two matrices.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float) -> None:
        '''Translates the local geometric transform by the specified dimensions. This method prepends the translation to the transform.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Translates the local geometric transform by the specified dimensions in the specified order.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.
        :param order: The order (prepend or append) in which to apply the translation.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float) -> None:
        '''Scales the local geometric transform by the specified amounts. This method prepends the scaling matrix to the transform.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Scales the local geometric transform by the specified amounts in the specified order.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the scaling matrix.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float) -> None:
        '''Rotates the local geometric transform by the specified amount. This method prepends the rotation to the transform.
        
        :param angle: The angle of rotation.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float, order : aspose.psd.MatrixOrder) -> None:
        '''Rotates the local geometric transform by the specified amount in the specified order.
        
        :param angle: The angle of rotation.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the rotation matrix.'''
        raise NotImplementedError()
    
    def deep_clone(self) -> aspose.psd.Brush:
        '''Creates a new deep clone of the current :py:class:`aspose.psd.Brush`.
        
        :returns: A new :py:class:`aspose.psd.Brush` which is the deep clone of this :py:class:`aspose.psd.Brush` instance.'''
        raise NotImplementedError()
    
    def reset_transform(self) -> None:
        '''Resets the :py:attr:`aspose.psd.brushes.TransformBrush.transform` property to identity.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @property
    def wrap_mode(self) -> aspose.psd.WrapMode:
        '''Gets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @wrap_mode.setter
    def wrap_mode(self, value : aspose.psd.WrapMode) -> None:
        '''Sets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def transform(self) -> aspose.psd.Matrix:
        '''Gets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @transform.setter
    def transform(self, value : aspose.psd.Matrix) -> None:
        '''Sets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def is_transform_changed(self) -> bool:
        '''Gets a value indicating whether transformations were changed in some way. For example setting the transformation matrix or
        calling any of the methods altering the transformation matrix. The property is introduced for backward compatibility with GDI+.'''
        raise NotImplementedError()
    
    @property
    def rectangle(self) -> aspose.psd.RectangleF:
        '''Gets a rectangular region that defines the starting and ending points of the gradient.'''
        raise NotImplementedError()
    
    @rectangle.setter
    def rectangle(self, value : aspose.psd.RectangleF) -> None:
        '''Sets a rectangular region that defines the starting and ending points of the gradient.'''
        raise NotImplementedError()
    
    @property
    def angle(self) -> float:
        '''Gets the gradient angle.'''
        raise NotImplementedError()
    
    @angle.setter
    def angle(self, value : float) -> None:
        '''Sets the gradient angle.'''
        raise NotImplementedError()
    
    @property
    def is_angle_scalable(self) -> bool:
        '''Gets a value indicating whether :py:attr:`aspose.psd.brushes.LinearGradientBrushBase.angle` is changed during trasnformations with this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    
    @is_angle_scalable.setter
    def is_angle_scalable(self, value : bool) -> None:
        '''Sets a value indicating whether :py:attr:`aspose.psd.brushes.LinearGradientBrushBase.angle` is changed during trasnformations with this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    
    @property
    def gamma_correction(self) -> bool:
        '''Gets a value indicating whether gamma correction is enabled for this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    
    @gamma_correction.setter
    def gamma_correction(self, value : bool) -> None:
        '''Sets a value indicating whether gamma correction is enabled for this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    

class LinearMulticolorGradientBrush(LinearGradientBrushBase):
    '''Represents a :py:class:`aspose.psd.Brush` with linear gradient defined by multiple colors and appropriate positions. This class cannot be inherited.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearMulticolorGradientBrush` class with default parameters.
        The starting color is black, the ending color is white, the angle is 45 degrees and the rectangle is located in (0,0) with size (1,1).'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, point1 : aspose.psd.Point, point2 : aspose.psd.Point) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearMulticolorGradientBrush` class with the specified points.
        
        :param point1: A :py:class:`aspose.psd.Point` structure that represents the starting point of the linear gradient.
        :param point2: A :py:class:`aspose.psd.Point` structure that represents the endpoint of the linear gradient.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, point1 : aspose.psd.PointF, point2 : aspose.psd.PointF) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearMulticolorGradientBrush` class with the specified points.
        
        :param point1: A :py:class:`aspose.psd.PointF` structure that represents the starting point of the linear gradient.
        :param point2: A :py:class:`aspose.psd.PointF` structure that represents the endpoint of the linear gradient.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rect : aspose.psd.Rectangle, angle : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearMulticolorGradientBrush` class based on a rectangle and an orientation angle.
        
        :param rect: A :py:class:`aspose.psd.RectangleF` structure that specifies the bounds of the linear gradient.
        :param angle: The angle, measured in degrees clockwise from the x-axis, of the gradient\'s orientation line.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rect : aspose.psd.RectangleF, angle : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearMulticolorGradientBrush` class based on a rectangle and an orientation angle.
        
        :param rect: A :py:class:`aspose.psd.RectangleF` structure that specifies the bounds of the linear gradient.
        :param angle: The angle, measured in degrees clockwise from the x-axis, of the gradient\'s orientation line.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rect : aspose.psd.Rectangle, angle : float, is_angle_scalable : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearMulticolorGradientBrush` class based on a rectangle and an orientation angle.
        
        :param rect: A :py:class:`aspose.psd.RectangleF` structure that specifies the bounds of the linear gradient.
        :param angle: The angle, measured in degrees clockwise from the x-axis, of the gradient\'s orientation line.
        :param is_angle_scalable: if set to ``true`` the angle is changed during transformations with this :py:class:`aspose.psd.brushes.LinearMulticolorGradientBrush`.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rect : aspose.psd.RectangleF, angle : float, is_angle_scalable : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.LinearMulticolorGradientBrush` class based on a rectangle and an orientation angle.
        
        :param rect: A :py:class:`aspose.psd.RectangleF` structure that specifies the bounds of the linear gradient.
        :param angle: The angle, measured in degrees clockwise from the x-axis, of the gradient\'s orientation line.
        :param is_angle_scalable: if set to ``true`` the angle is changed during transformations with this :py:class:`aspose.psd.brushes.LinearMulticolorGradientBrush`.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` by prepending the specified :py:class:`aspose.psd.Matrix`.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix, order : aspose.psd.MatrixOrder) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` in the specified order.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies in which order to multiply the two matrices.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float) -> None:
        '''Translates the local geometric transform by the specified dimensions. This method prepends the translation to the transform.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Translates the local geometric transform by the specified dimensions in the specified order.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.
        :param order: The order (prepend or append) in which to apply the translation.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float) -> None:
        '''Scales the local geometric transform by the specified amounts. This method prepends the scaling matrix to the transform.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Scales the local geometric transform by the specified amounts in the specified order.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the scaling matrix.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float) -> None:
        '''Rotates the local geometric transform by the specified amount. This method prepends the rotation to the transform.
        
        :param angle: The angle of rotation.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float, order : aspose.psd.MatrixOrder) -> None:
        '''Rotates the local geometric transform by the specified amount in the specified order.
        
        :param angle: The angle of rotation.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the rotation matrix.'''
        raise NotImplementedError()
    
    def deep_clone(self) -> aspose.psd.Brush:
        '''Creates a new deep clone of the current :py:class:`aspose.psd.Brush`.
        
        :returns: A new :py:class:`aspose.psd.Brush` which is the deep clone of this :py:class:`aspose.psd.Brush` instance.'''
        raise NotImplementedError()
    
    def reset_transform(self) -> None:
        '''Resets the :py:attr:`aspose.psd.brushes.TransformBrush.transform` property to identity.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @property
    def wrap_mode(self) -> aspose.psd.WrapMode:
        '''Gets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @wrap_mode.setter
    def wrap_mode(self, value : aspose.psd.WrapMode) -> None:
        '''Sets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def transform(self) -> aspose.psd.Matrix:
        '''Gets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @transform.setter
    def transform(self, value : aspose.psd.Matrix) -> None:
        '''Sets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def is_transform_changed(self) -> bool:
        '''Gets a value indicating whether transformations were changed in some way. For example setting the transformation matrix or
        calling any of the methods altering the transformation matrix. The property is introduced for backward compatibility with GDI+.'''
        raise NotImplementedError()
    
    @property
    def rectangle(self) -> aspose.psd.RectangleF:
        '''Gets a rectangular region that defines the starting and ending points of the gradient.'''
        raise NotImplementedError()
    
    @rectangle.setter
    def rectangle(self, value : aspose.psd.RectangleF) -> None:
        '''Sets a rectangular region that defines the starting and ending points of the gradient.'''
        raise NotImplementedError()
    
    @property
    def angle(self) -> float:
        '''Gets the gradient angle.'''
        raise NotImplementedError()
    
    @angle.setter
    def angle(self, value : float) -> None:
        '''Sets the gradient angle.'''
        raise NotImplementedError()
    
    @property
    def is_angle_scalable(self) -> bool:
        '''Gets a value indicating whether :py:attr:`aspose.psd.brushes.LinearGradientBrushBase.angle` is changed during trasnformations with this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    
    @is_angle_scalable.setter
    def is_angle_scalable(self, value : bool) -> None:
        '''Sets a value indicating whether :py:attr:`aspose.psd.brushes.LinearGradientBrushBase.angle` is changed during trasnformations with this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    
    @property
    def gamma_correction(self) -> bool:
        '''Gets a value indicating whether gamma correction is enabled for this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    
    @gamma_correction.setter
    def gamma_correction(self, value : bool) -> None:
        '''Sets a value indicating whether gamma correction is enabled for this :py:class:`aspose.psd.brushes.LinearGradientBrushBase`.'''
        raise NotImplementedError()
    
    @property
    def interpolation_colors(self) -> aspose.psd.ColorBlend:
        '''Gets a :py:class:`aspose.psd.ColorBlend` that defines a multicolor linear gradient.'''
        raise NotImplementedError()
    
    @interpolation_colors.setter
    def interpolation_colors(self, value : aspose.psd.ColorBlend) -> None:
        '''Sets a :py:class:`aspose.psd.ColorBlend` that defines a multicolor linear gradient.'''
        raise NotImplementedError()
    

class PathGradientBrush(PathGradientBrushBase):
    '''Encapsulates a :py:class:`aspose.psd.Brush` object with a gradient. This class cannot be inherited.'''
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.PathGradientBrush` class with the specified points.
        
        :param points: An array of :py:class:`aspose.psd.PointF` structures that represents the points that make up the vertices of the path.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF], wrap_mode : aspose.psd.WrapMode) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.PathGradientBrush` class with the specified points and wrap mode.
        
        :param points: An array of :py:class:`aspose.psd.PointF` structures that represents the points that make up the vertices of the path.
        :param wrap_mode: A :py:class:`aspose.psd.WrapMode` that specifies how fills drawn with this :py:class:`aspose.psd.brushes.PathGradientBrush` are tiled.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.Point]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.PathGradientBrush` class with the specified points.
        
        :param points: An array of :py:class:`aspose.psd.Point` structures that represents the points that make up the vertices of the path.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.Point], wrap_mode : aspose.psd.WrapMode) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.PathGradientBrush` class with the specified points and wrap mode.
        
        :param points: An array of :py:class:`aspose.psd.Point` structures that represents the points that make up the vertices of the path.
        :param wrap_mode: A :py:class:`aspose.psd.WrapMode` that specifies how fills drawn with this :py:class:`aspose.psd.brushes.PathGradientBrush` are tiled.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, path : aspose.psd.GraphicsPath) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.PathGradientBrush` class with the specified path.
        
        :param path: The :py:class:`aspose.psd.GraphicsPath` that defines the area filled by this :py:class:`aspose.psd.brushes.PathGradientBrush`.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` by prepending the specified :py:class:`aspose.psd.Matrix`.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix, order : aspose.psd.MatrixOrder) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` in the specified order.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies in which order to multiply the two matrices.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float) -> None:
        '''Translates the local geometric transform by the specified dimensions. This method prepends the translation to the transform.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Translates the local geometric transform by the specified dimensions in the specified order.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.
        :param order: The order (prepend or append) in which to apply the translation.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float) -> None:
        '''Scales the local geometric transform by the specified amounts. This method prepends the scaling matrix to the transform.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Scales the local geometric transform by the specified amounts in the specified order.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the scaling matrix.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float) -> None:
        '''Rotates the local geometric transform by the specified amount. This method prepends the rotation to the transform.
        
        :param angle: The angle of rotation.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float, order : aspose.psd.MatrixOrder) -> None:
        '''Rotates the local geometric transform by the specified amount in the specified order.
        
        :param angle: The angle of rotation.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the rotation matrix.'''
        raise NotImplementedError()
    
    @overload
    def set_sigma_bell_shape(self, focus : float) -> None:
        '''Creates a gradient brush that changes color starting from the center of the path outward to the path\'s boundary. The transition from one color to another is based on a bell-shaped curve.
        
        :param focus: A value from 0 through 1 that specifies where, along any radial from the center of the path to the path\'s boundary, the center color will be at its highest intensity. A value of 1 (the default) places the highest intensity at the center of the path.'''
        raise NotImplementedError()
    
    @overload
    def set_sigma_bell_shape(self, focus : float, scale : float) -> None:
        '''Creates a gradient brush that changes color starting from the center of the path outward to the path\'s boundary. The transition from one color to another is based on a bell-shaped curve.
        
        :param focus: A value from 0 through 1 that specifies where, along any radial from the center of the path to the path\'s boundary, the center color will be at its highest intensity. A value of 1 (the default) places the highest intensity at the center of the path.
        :param scale: A value from 0 through 1 that specifies the maximum intensity of the center color that gets blended with the boundary color. A value of 1 causes the highest possible intensity of the center color, and it is the default value.'''
        raise NotImplementedError()
    
    @overload
    def set_blend_triangular_shape(self, focus : float) -> None:
        '''Creates a gradient with a center color and a linear falloff to one surrounding color.
        
        :param focus: A value from 0 through 1 that specifies where, along any radial from the center of the path to the path\'s boundary, the center color will be at its highest intensity. A value of 1 (the default) places the highest intensity at the center of the path.'''
        raise NotImplementedError()
    
    @overload
    def set_blend_triangular_shape(self, focus : float, scale : float) -> None:
        '''Creates a gradient with a center color and a linear falloff to each surrounding color.
        
        :param focus: A value from 0 through 1 that specifies where, along any radial from the center of the path to the path\'s boundary, the center color will be at its highest intensity. A value of 1 (the default) places the highest intensity at the center of the path.
        :param scale: A value from 0 through 1 that specifies the maximum intensity of the center color that gets blended with the boundary color. A value of 1 causes the highest possible intensity of the center color, and it is the default value.'''
        raise NotImplementedError()
    
    def deep_clone(self) -> aspose.psd.Brush:
        '''Creates a new deep clone of the current :py:class:`aspose.psd.Brush`.
        
        :returns: A new :py:class:`aspose.psd.Brush` which is the deep clone of this :py:class:`aspose.psd.Brush` instance.'''
        raise NotImplementedError()
    
    def reset_transform(self) -> None:
        '''Resets the :py:attr:`aspose.psd.brushes.TransformBrush.transform` property to identity.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @property
    def wrap_mode(self) -> aspose.psd.WrapMode:
        '''Gets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @wrap_mode.setter
    def wrap_mode(self, value : aspose.psd.WrapMode) -> None:
        '''Sets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def transform(self) -> aspose.psd.Matrix:
        '''Gets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @transform.setter
    def transform(self, value : aspose.psd.Matrix) -> None:
        '''Sets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def is_transform_changed(self) -> bool:
        '''Gets a value indicating whether transformations were changed in some way. For example setting the transformation matrix or
        calling any of the methods altering the transformation matrix. The property is introduced for backward compatibility with GDI+.'''
        raise NotImplementedError()
    
    @property
    def path_points(self) -> List[aspose.psd.PointF]:
        '''Gets the path points this brush was build upon.'''
        raise NotImplementedError()
    
    @property
    def graphics_path(self) -> aspose.psd.GraphicsPath:
        '''Gets the graphics path this brush was build upon.'''
        raise NotImplementedError()
    
    @property
    def center_point(self) -> aspose.psd.PointF:
        '''Gets the center point of the path gradient.'''
        raise NotImplementedError()
    
    @center_point.setter
    def center_point(self, value : aspose.psd.PointF) -> None:
        '''Sets the center point of the path gradient.'''
        raise NotImplementedError()
    
    @property
    def focus_scales(self) -> aspose.psd.PointF:
        '''Gets the focus point for the gradient falloff.'''
        raise NotImplementedError()
    
    @focus_scales.setter
    def focus_scales(self, value : aspose.psd.PointF) -> None:
        '''Sets the focus point for the gradient falloff.'''
        raise NotImplementedError()
    
    @property
    def interpolation_colors(self) -> aspose.psd.ColorBlend:
        '''Gets a :py:class:`aspose.psd.ColorBlend` that defines a multicolor linear gradient.'''
        raise NotImplementedError()
    
    @interpolation_colors.setter
    def interpolation_colors(self, value : aspose.psd.ColorBlend) -> None:
        '''Sets a :py:class:`aspose.psd.ColorBlend` that defines a multicolor linear gradient.'''
        raise NotImplementedError()
    
    @property
    def center_color(self) -> aspose.psd.Color:
        '''Gets the color at the center of the path gradient.'''
        raise NotImplementedError()
    
    @center_color.setter
    def center_color(self, value : aspose.psd.Color) -> None:
        '''Sets the color at the center of the path gradient.'''
        raise NotImplementedError()
    
    @property
    def surround_colors(self) -> List[aspose.psd.Color]:
        '''Gets an array of colors that correspond to the points in the path this :py:class:`aspose.psd.brushes.PathGradientBrush` fills.'''
        raise NotImplementedError()
    
    @surround_colors.setter
    def surround_colors(self, value : List[aspose.psd.Color]) -> None:
        '''Sets an array of colors that correspond to the points in the path this :py:class:`aspose.psd.brushes.PathGradientBrush` fills.'''
        raise NotImplementedError()
    
    @property
    def blend(self) -> aspose.psd.Blend:
        '''Gets a :py:class:`aspose.psd.Blend` that specifies positions and factors that define a custom falloff for the gradient.'''
        raise NotImplementedError()
    
    @blend.setter
    def blend(self, value : aspose.psd.Blend) -> None:
        '''Sets a :py:class:`aspose.psd.Blend` that specifies positions and factors that define a custom falloff for the gradient.'''
        raise NotImplementedError()
    

class PathGradientBrushBase(TransformBrush):
    '''Represents a :py:class:`aspose.psd.Brush` with base path gradient functionality.'''
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` by prepending the specified :py:class:`aspose.psd.Matrix`.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix, order : aspose.psd.MatrixOrder) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` in the specified order.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies in which order to multiply the two matrices.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float) -> None:
        '''Translates the local geometric transform by the specified dimensions. This method prepends the translation to the transform.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Translates the local geometric transform by the specified dimensions in the specified order.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.
        :param order: The order (prepend or append) in which to apply the translation.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float) -> None:
        '''Scales the local geometric transform by the specified amounts. This method prepends the scaling matrix to the transform.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Scales the local geometric transform by the specified amounts in the specified order.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the scaling matrix.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float) -> None:
        '''Rotates the local geometric transform by the specified amount. This method prepends the rotation to the transform.
        
        :param angle: The angle of rotation.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float, order : aspose.psd.MatrixOrder) -> None:
        '''Rotates the local geometric transform by the specified amount in the specified order.
        
        :param angle: The angle of rotation.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the rotation matrix.'''
        raise NotImplementedError()
    
    def deep_clone(self) -> aspose.psd.Brush:
        '''Creates a new deep clone of the current :py:class:`aspose.psd.Brush`.
        
        :returns: A new :py:class:`aspose.psd.Brush` which is the deep clone of this :py:class:`aspose.psd.Brush` instance.'''
        raise NotImplementedError()
    
    def reset_transform(self) -> None:
        '''Resets the :py:attr:`aspose.psd.brushes.TransformBrush.transform` property to identity.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @property
    def wrap_mode(self) -> aspose.psd.WrapMode:
        '''Gets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @wrap_mode.setter
    def wrap_mode(self, value : aspose.psd.WrapMode) -> None:
        '''Sets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def transform(self) -> aspose.psd.Matrix:
        '''Gets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @transform.setter
    def transform(self, value : aspose.psd.Matrix) -> None:
        '''Sets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def is_transform_changed(self) -> bool:
        '''Gets a value indicating whether transformations were changed in some way. For example setting the transformation matrix or
        calling any of the methods altering the transformation matrix. The property is introduced for backward compatibility with GDI+.'''
        raise NotImplementedError()
    
    @property
    def path_points(self) -> List[aspose.psd.PointF]:
        '''Gets the path points this brush was build upon.'''
        raise NotImplementedError()
    
    @property
    def graphics_path(self) -> aspose.psd.GraphicsPath:
        '''Gets the graphics path this brush was build upon.'''
        raise NotImplementedError()
    
    @property
    def center_point(self) -> aspose.psd.PointF:
        '''Gets the center point of the path gradient.'''
        raise NotImplementedError()
    
    @center_point.setter
    def center_point(self, value : aspose.psd.PointF) -> None:
        '''Sets the center point of the path gradient.'''
        raise NotImplementedError()
    
    @property
    def focus_scales(self) -> aspose.psd.PointF:
        '''Gets the focus point for the gradient falloff.'''
        raise NotImplementedError()
    
    @focus_scales.setter
    def focus_scales(self, value : aspose.psd.PointF) -> None:
        '''Sets the focus point for the gradient falloff.'''
        raise NotImplementedError()
    

class PathMulticolorGradientBrush(PathGradientBrushBase):
    '''Encapsulates a :py:class:`aspose.psd.Brush` object with a gradient. This class cannot be inherited.'''
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.PathMulticolorGradientBrush` class with the specified points.
        
        :param points: An array of :py:class:`aspose.psd.PointF` structures that represents the points that make up the vertices of the path.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF], wrap_mode : aspose.psd.WrapMode) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.PathMulticolorGradientBrush` class with the specified points and wrap mode.
        
        :param points: An array of :py:class:`aspose.psd.PointF` structures that represents the points that make up the vertices of the path.
        :param wrap_mode: A :py:class:`aspose.psd.WrapMode` that specifies how fills drawn with this :py:class:`aspose.psd.brushes.PathMulticolorGradientBrush` are tiled.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.Point]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.PathMulticolorGradientBrush` class with the specified points.
        
        :param points: An array of :py:class:`aspose.psd.Point` structures that represents the points that make up the vertices of the path.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.Point], wrap_mode : aspose.psd.WrapMode) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.PathMulticolorGradientBrush` class with the specified points and wrap mode.
        
        :param points: An array of :py:class:`aspose.psd.Point` structures that represents the points that make up the vertices of the path.
        :param wrap_mode: A :py:class:`aspose.psd.WrapMode` that specifies how fills drawn with this :py:class:`aspose.psd.brushes.PathMulticolorGradientBrush` are tiled.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, path : aspose.psd.GraphicsPath) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.PathMulticolorGradientBrush` class with the specified path.
        
        :param path: The :py:class:`aspose.psd.GraphicsPath` that defines the area filled by this :py:class:`aspose.psd.brushes.PathMulticolorGradientBrush`.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` by prepending the specified :py:class:`aspose.psd.Matrix`.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix, order : aspose.psd.MatrixOrder) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` in the specified order.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies in which order to multiply the two matrices.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float) -> None:
        '''Translates the local geometric transform by the specified dimensions. This method prepends the translation to the transform.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Translates the local geometric transform by the specified dimensions in the specified order.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.
        :param order: The order (prepend or append) in which to apply the translation.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float) -> None:
        '''Scales the local geometric transform by the specified amounts. This method prepends the scaling matrix to the transform.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Scales the local geometric transform by the specified amounts in the specified order.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the scaling matrix.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float) -> None:
        '''Rotates the local geometric transform by the specified amount. This method prepends the rotation to the transform.
        
        :param angle: The angle of rotation.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float, order : aspose.psd.MatrixOrder) -> None:
        '''Rotates the local geometric transform by the specified amount in the specified order.
        
        :param angle: The angle of rotation.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the rotation matrix.'''
        raise NotImplementedError()
    
    def deep_clone(self) -> aspose.psd.Brush:
        '''Creates a new deep clone of the current :py:class:`aspose.psd.Brush`.
        
        :returns: A new :py:class:`aspose.psd.Brush` which is the deep clone of this :py:class:`aspose.psd.Brush` instance.'''
        raise NotImplementedError()
    
    def reset_transform(self) -> None:
        '''Resets the :py:attr:`aspose.psd.brushes.TransformBrush.transform` property to identity.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @property
    def wrap_mode(self) -> aspose.psd.WrapMode:
        '''Gets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @wrap_mode.setter
    def wrap_mode(self, value : aspose.psd.WrapMode) -> None:
        '''Sets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def transform(self) -> aspose.psd.Matrix:
        '''Gets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @transform.setter
    def transform(self, value : aspose.psd.Matrix) -> None:
        '''Sets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def is_transform_changed(self) -> bool:
        '''Gets a value indicating whether transformations were changed in some way. For example setting the transformation matrix or
        calling any of the methods altering the transformation matrix. The property is introduced for backward compatibility with GDI+.'''
        raise NotImplementedError()
    
    @property
    def path_points(self) -> List[aspose.psd.PointF]:
        '''Gets the path points this brush was build upon.'''
        raise NotImplementedError()
    
    @property
    def graphics_path(self) -> aspose.psd.GraphicsPath:
        '''Gets the graphics path this brush was build upon.'''
        raise NotImplementedError()
    
    @property
    def center_point(self) -> aspose.psd.PointF:
        '''Gets the center point of the path gradient.'''
        raise NotImplementedError()
    
    @center_point.setter
    def center_point(self, value : aspose.psd.PointF) -> None:
        '''Sets the center point of the path gradient.'''
        raise NotImplementedError()
    
    @property
    def focus_scales(self) -> aspose.psd.PointF:
        '''Gets the focus point for the gradient falloff.'''
        raise NotImplementedError()
    
    @focus_scales.setter
    def focus_scales(self, value : aspose.psd.PointF) -> None:
        '''Sets the focus point for the gradient falloff.'''
        raise NotImplementedError()
    
    @property
    def interpolation_colors(self) -> aspose.psd.ColorBlend:
        '''Gets a :py:class:`aspose.psd.ColorBlend` that defines a multicolor linear gradient.'''
        raise NotImplementedError()
    
    @interpolation_colors.setter
    def interpolation_colors(self, value : aspose.psd.ColorBlend) -> None:
        '''Sets a :py:class:`aspose.psd.ColorBlend` that defines a multicolor linear gradient.'''
        raise NotImplementedError()
    

class SolidBrush(aspose.psd.Brush):
    '''Solid brush is intended for drawing continiously with specific color. This class cannot be inherited.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.SolidBrush` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, color : aspose.psd.Color) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.SolidBrush` class.
        
        :param color: The solid brush color.'''
        raise NotImplementedError()
    
    def deep_clone(self) -> aspose.psd.Brush:
        '''Creates a new deep clone of the current :py:class:`aspose.psd.Brush`.
        
        :returns: A new :py:class:`aspose.psd.Brush` which is the deep clone of this :py:class:`aspose.psd.Brush` instance.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @property
    def color(self) -> aspose.psd.Color:
        '''Gets the brush color.'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : aspose.psd.Color) -> None:
        '''Sets the brush color.'''
        raise NotImplementedError()
    

class TextureBrush(TransformBrush):
    '''Each property of the :py:class:`aspose.psd.brushes.TextureBrush` class is a :py:class:`aspose.psd.Brush` object that uses an image to fill the interior of a shape. This class cannot be inherited.'''
    
    @overload
    def __init__(self, image : aspose.psd.Image) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.TextureBrush` class that uses the specified image.
        
        :param image: The :py:class:`aspose.psd.Image` object with which this :py:class:`aspose.psd.brushes.TextureBrush` object fills interiors.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, image : aspose.psd.Image, wrap_mode : aspose.psd.WrapMode) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.TextureBrush` class that uses the specified image and wrap mode.
        
        :param image: The :py:class:`aspose.psd.Image` object with which this :py:class:`aspose.psd.brushes.TextureBrush` object fills interiors.
        :param wrap_mode: A :py:class:`aspose.psd.WrapMode` enumeration that specifies how this :py:class:`aspose.psd.brushes.TextureBrush` object is tiled.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, image : aspose.psd.Image, wrap_mode : aspose.psd.WrapMode, destination_rectangle : aspose.psd.RectangleF) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.TextureBrush` class that uses the specified image, wrap mode, and bounding rectangle.
        
        :param image: The :py:class:`aspose.psd.Image` object with which this :py:class:`aspose.psd.brushes.TextureBrush` object fills interiors.
        :param wrap_mode: A :py:class:`aspose.psd.WrapMode` enumeration that specifies how this :py:class:`aspose.psd.brushes.TextureBrush` object is tiled.
        :param destination_rectangle: A :py:class:`aspose.psd.RectangleF` structure that represents the bounding rectangle for this :py:class:`aspose.psd.brushes.TextureBrush` object.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, image : aspose.psd.Image, wrap_mode : aspose.psd.WrapMode, destination_rectangle : aspose.psd.Rectangle) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.TextureBrush` class that uses the specified image, wrap mode, and bounding rectangle.
        
        :param image: The :py:class:`aspose.psd.Image` object with which this :py:class:`aspose.psd.brushes.TextureBrush` object fills interiors.
        :param wrap_mode: A :py:class:`aspose.psd.WrapMode` enumeration that specifies how this :py:class:`aspose.psd.brushes.TextureBrush` object is tiled.
        :param destination_rectangle: A :py:class:`aspose.psd.Rectangle` structure that represents the bounding rectangle for this :py:class:`aspose.psd.brushes.TextureBrush` object.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, image : aspose.psd.Image, destination_rectangle : aspose.psd.RectangleF) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.TextureBrush` class that uses the specified image and bounding rectangle.
        
        :param image: The :py:class:`aspose.psd.Image` object with which this :py:class:`aspose.psd.brushes.TextureBrush` object fills interiors.
        :param destination_rectangle: A :py:class:`aspose.psd.RectangleF` structure that represents the bounding rectangle for this :py:class:`aspose.psd.brushes.TextureBrush` object.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, image : aspose.psd.Image, destination_rectangle : aspose.psd.RectangleF, image_attributes : aspose.psd.ImageAttributes) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.TextureBrush` class that uses the specified image, bounding rectangle, and image attributes.
        
        :param image: The :py:class:`aspose.psd.Image` object with which this :py:class:`aspose.psd.brushes.TextureBrush` object fills interiors.
        :param destination_rectangle: A :py:class:`aspose.psd.RectangleF` structure that represents the bounding rectangle for this :py:class:`aspose.psd.brushes.TextureBrush` object.
        :param image_attributes: An :py:class:`aspose.psd.ImageAttributes` object that contains additional information about the image used by this :py:class:`aspose.psd.brushes.TextureBrush` object.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, image : aspose.psd.Image, destination_rectangle : aspose.psd.Rectangle) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.TextureBrush` class that uses the specified image and bounding rectangle.
        
        :param image: The :py:class:`aspose.psd.Image` object with which this :py:class:`aspose.psd.brushes.TextureBrush` object fills interiors.
        :param destination_rectangle: A :py:class:`aspose.psd.Rectangle` structure that represents the bounding rectangle for this :py:class:`aspose.psd.brushes.TextureBrush` object.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, image : aspose.psd.Image, destination_rectangle : aspose.psd.Rectangle, image_attributes : aspose.psd.ImageAttributes) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.brushes.TextureBrush` class that uses the specified image, bounding rectangle, and image attributes.
        
        :param image: The :py:class:`aspose.psd.Image` object with which this :py:class:`aspose.psd.brushes.TextureBrush` object fills interiors.
        :param destination_rectangle: A :py:class:`aspose.psd.Rectangle` structure that represents the bounding rectangle for this :py:class:`aspose.psd.brushes.TextureBrush` object.
        :param image_attributes: An :py:class:`aspose.psd.ImageAttributes` object that contains additional information about the image used by this :py:class:`aspose.psd.brushes.TextureBrush` object.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` by prepending the specified :py:class:`aspose.psd.Matrix`.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix, order : aspose.psd.MatrixOrder) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` in the specified order.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies in which order to multiply the two matrices.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float) -> None:
        '''Translates the local geometric transform by the specified dimensions. This method prepends the translation to the transform.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Translates the local geometric transform by the specified dimensions in the specified order.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.
        :param order: The order (prepend or append) in which to apply the translation.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float) -> None:
        '''Scales the local geometric transform by the specified amounts. This method prepends the scaling matrix to the transform.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Scales the local geometric transform by the specified amounts in the specified order.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the scaling matrix.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float) -> None:
        '''Rotates the local geometric transform by the specified amount. This method prepends the rotation to the transform.
        
        :param angle: The angle of rotation.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float, order : aspose.psd.MatrixOrder) -> None:
        '''Rotates the local geometric transform by the specified amount in the specified order.
        
        :param angle: The angle of rotation.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the rotation matrix.'''
        raise NotImplementedError()
    
    def deep_clone(self) -> aspose.psd.Brush:
        '''Creates a new deep clone of the current :py:class:`aspose.psd.Brush`.
        
        :returns: A new :py:class:`aspose.psd.Brush` which is the deep clone of this :py:class:`aspose.psd.Brush` instance.'''
        raise NotImplementedError()
    
    def reset_transform(self) -> None:
        '''Resets the :py:attr:`aspose.psd.brushes.TransformBrush.transform` property to identity.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @property
    def wrap_mode(self) -> aspose.psd.WrapMode:
        '''Gets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @wrap_mode.setter
    def wrap_mode(self, value : aspose.psd.WrapMode) -> None:
        '''Sets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def transform(self) -> aspose.psd.Matrix:
        '''Gets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @transform.setter
    def transform(self, value : aspose.psd.Matrix) -> None:
        '''Sets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def is_transform_changed(self) -> bool:
        '''Gets a value indicating whether transformations were changed in some way. For example setting the transformation matrix or
        calling any of the methods altering the transformation matrix. The property is introduced for backward compatibility with GDI+.'''
        raise NotImplementedError()
    
    @property
    def image(self) -> aspose.psd.Image:
        '''Gets the :py:class:`aspose.psd.Image` object associated with this :py:class:`aspose.psd.brushes.TextureBrush` object.'''
        raise NotImplementedError()
    
    @property
    def image_attributes(self) -> aspose.psd.ImageAttributes:
        '''Gets the :py:attr:`aspose.psd.brushes.TextureBrush.image_attributes` associated with this :py:class:`aspose.psd.brushes.TextureBrush`.'''
        raise NotImplementedError()
    
    @property
    def image_rectangle(self) -> aspose.psd.RectangleF:
        '''Gets the :py:class:`aspose.psd.Rectangle` associated with this :py:class:`aspose.psd.brushes.TextureBrush`.'''
        raise NotImplementedError()
    

class TransformBrush(aspose.psd.Brush):
    '''A :py:class:`aspose.psd.Brush` with transform capabilities.'''
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` by prepending the specified :py:class:`aspose.psd.Matrix`.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.'''
        raise NotImplementedError()
    
    @overload
    def multiply_transform(self, matrix : aspose.psd.Matrix, order : aspose.psd.MatrixOrder) -> None:
        '''Multiplies the :py:class:`aspose.psd.Matrix` that represents the local geometric transform of this :py:class:`aspose.psd.brushes.LinearGradientBrush` by the specified :py:class:`aspose.psd.Matrix` in the specified order.
        
        :param matrix: The :py:class:`aspose.psd.Matrix` by which to multiply the geometric transform.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies in which order to multiply the two matrices.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float) -> None:
        '''Translates the local geometric transform by the specified dimensions. This method prepends the translation to the transform.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.'''
        raise NotImplementedError()
    
    @overload
    def translate_transform(self, dx : float, dy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Translates the local geometric transform by the specified dimensions in the specified order.
        
        :param dx: The value of the translation in x.
        :param dy: The value of the translation in y.
        :param order: The order (prepend or append) in which to apply the translation.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float) -> None:
        '''Scales the local geometric transform by the specified amounts. This method prepends the scaling matrix to the transform.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.'''
        raise NotImplementedError()
    
    @overload
    def scale_transform(self, sx : float, sy : float, order : aspose.psd.MatrixOrder) -> None:
        '''Scales the local geometric transform by the specified amounts in the specified order.
        
        :param sx: The amount by which to scale the transform in the x-axis direction.
        :param sy: The amount by which to scale the transform in the y-axis direction.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the scaling matrix.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float) -> None:
        '''Rotates the local geometric transform by the specified amount. This method prepends the rotation to the transform.
        
        :param angle: The angle of rotation.'''
        raise NotImplementedError()
    
    @overload
    def rotate_transform(self, angle : float, order : aspose.psd.MatrixOrder) -> None:
        '''Rotates the local geometric transform by the specified amount in the specified order.
        
        :param angle: The angle of rotation.
        :param order: A :py:class:`aspose.psd.MatrixOrder` that specifies whether to append or prepend the rotation matrix.'''
        raise NotImplementedError()
    
    def deep_clone(self) -> aspose.psd.Brush:
        '''Creates a new deep clone of the current :py:class:`aspose.psd.Brush`.
        
        :returns: A new :py:class:`aspose.psd.Brush` which is the deep clone of this :py:class:`aspose.psd.Brush` instance.'''
        raise NotImplementedError()
    
    def reset_transform(self) -> None:
        '''Resets the :py:attr:`aspose.psd.brushes.TransformBrush.transform` property to identity.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the brush opacity. The value should be between 0 and 1. Value of 0 means that brush is fully visible, value of 1 means the brush is fully opaque.'''
        raise NotImplementedError()
    
    @property
    def wrap_mode(self) -> aspose.psd.WrapMode:
        '''Gets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @wrap_mode.setter
    def wrap_mode(self, value : aspose.psd.WrapMode) -> None:
        '''Sets a :py:class:`aspose.psd.WrapMode` enumeration that indicates the wrap mode for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def transform(self) -> aspose.psd.Matrix:
        '''Gets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @transform.setter
    def transform(self, value : aspose.psd.Matrix) -> None:
        '''Sets a copy :py:class:`aspose.psd.Matrix` that defines a local geometric transform for this :py:class:`aspose.psd.brushes.TransformBrush`.'''
        raise NotImplementedError()
    
    @property
    def is_transform_changed(self) -> bool:
        '''Gets a value indicating whether transformations were changed in some way. For example setting the transformation matrix or
        calling any of the methods altering the transformation matrix. The property is introduced for backward compatibility with GDI+.'''
        raise NotImplementedError()
    

