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

class ArcShape(PieShape):
    '''Represents an arc shape.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.ArcShape` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rectangle : aspose.psd.RectangleF, start_angle : float, sweep_angle : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.ArcShape` class.
        
        :param rectangle: The rectangle.
        :param start_angle: The start angle.
        :param sweep_angle: The sweep angle.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rectangle : aspose.psd.RectangleF, start_angle : float, sweep_angle : float, is_closed : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.ArcShape` class.
        
        :param rectangle: The rectangle.
        :param start_angle: The start angle.
        :param sweep_angle: The sweep angle.
        :param is_closed: If set to ``true`` the arc is closed. The closed arc is actually degenereates to an ellipse.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix, pen : aspose.psd.Pen) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :param pen: The pen to use for object. This can influence the object\'s bounds size.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    def transform(self, transform : aspose.psd.Matrix) -> None:
        '''Applies the specified transformation to the shape.
        
        :param transform: The transformation to apply.'''
        raise NotImplementedError()
    
    def reverse(self) -> None:
        '''Reverses the order of points for this shape.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.'''
        raise NotImplementedError()
    
    @property
    def center(self) -> aspose.psd.PointF:
        '''Gets the shape\'s center.'''
        raise NotImplementedError()
    
    @property
    def segments(self) -> List[aspose.psd.ShapeSegment]:
        '''Gets the shape segments.'''
        raise NotImplementedError()
    
    @property
    def has_segments(self) -> bool:
        '''Gets a value indicating whether shape has segments.'''
        raise NotImplementedError()
    
    @property
    def left_top(self) -> aspose.psd.PointF:
        '''Gets the left top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_top(self) -> aspose.psd.PointF:
        '''Gets the right top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def left_bottom(self) -> aspose.psd.PointF:
        '''Gets the left bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_bottom(self) -> aspose.psd.PointF:
        '''Gets the right bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def rectangle_width(self) -> float:
        '''Gets the rectangle width.'''
        raise NotImplementedError()
    
    @property
    def rectangle_height(self) -> float:
        '''Gets the rectangle height.'''
        raise NotImplementedError()
    
    @property
    def start_angle(self) -> float:
        '''Gets the start angle.'''
        raise NotImplementedError()
    
    @start_angle.setter
    def start_angle(self, value : float) -> None:
        '''Sets the start angle.'''
        raise NotImplementedError()
    
    @property
    def sweep_angle(self) -> float:
        '''Gets the sweep angle.'''
        raise NotImplementedError()
    
    @sweep_angle.setter
    def sweep_angle(self, value : float) -> None:
        '''Sets the sweep angle.'''
        raise NotImplementedError()
    
    @property
    def start_point(self) -> aspose.psd.PointF:
        '''Gets the starting shape point.'''
        raise NotImplementedError()
    
    @property
    def end_point(self) -> aspose.psd.PointF:
        '''Gets the ending shape point.'''
        raise NotImplementedError()
    
    @property
    def is_closed(self) -> bool:
        '''Gets a value indicating whether ordered shape is closed. When processing closed ordered shape the starting and ending points have no meaning.'''
        raise NotImplementedError()
    
    @is_closed.setter
    def is_closed(self, value : bool) -> None:
        '''Sets a value indicating whether ordered shape is closed. When processing closed ordered shape the starting and ending points have no meaning.'''
        raise NotImplementedError()
    

class BezierShape(PolygonShape):
    '''Represents a bezier spline.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.BezierShape` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.BezierShape` class.
        
        :param points: The points array.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF], is_closed : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.BezierShape` class.
        
        :param points: The points array.
        :param is_closed: If set to ``true`` the bezier spline is closed.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix, pen : aspose.psd.Pen) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :param pen: The pen to use for object. This can influence the object\'s bounds size.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    def transform(self, transform : aspose.psd.Matrix) -> None:
        '''Applies the specified transformation to the shape.
        
        :param transform: The transformation to apply.'''
        raise NotImplementedError()
    
    def reverse(self) -> None:
        '''Reverses the order of points for this shape.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.'''
        raise NotImplementedError()
    
    @property
    def center(self) -> aspose.psd.PointF:
        '''Gets the shape\'s center.'''
        raise NotImplementedError()
    
    @property
    def segments(self) -> List[aspose.psd.ShapeSegment]:
        '''Gets the shape segments.'''
        raise NotImplementedError()
    
    @property
    def has_segments(self) -> bool:
        '''Gets a value indicating whether shape has segments.'''
        raise NotImplementedError()
    
    @property
    def points(self) -> List[aspose.psd.PointF]:
        '''Gets the curve points.'''
        raise NotImplementedError()
    
    @points.setter
    def points(self, value : List[aspose.psd.PointF]) -> None:
        '''Sets the curve points.'''
        raise NotImplementedError()
    
    @property
    def is_closed(self) -> bool:
        '''Gets a value indicating whether shape is closed.'''
        raise NotImplementedError()
    
    @is_closed.setter
    def is_closed(self, value : bool) -> None:
        '''Sets a value indicating whether shape is closed.'''
        raise NotImplementedError()
    
    @property
    def start_point(self) -> aspose.psd.PointF:
        '''Gets the starting shape point.'''
        raise NotImplementedError()
    
    @property
    def end_point(self) -> aspose.psd.PointF:
        '''Gets the ending shape point.'''
        raise NotImplementedError()
    

class CurveShape(PolygonShape):
    '''Represents a curved spline shape.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.CurveShape` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.CurveShape` class. The default tension of 0.5 is used.
        
        :param points: The points array.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF], is_closed : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.CurveShape` class. The default tension of 0.5 is used.
        
        :param points: The points array.
        :param is_closed: if set to ``true`` the curve is closed.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF], tension : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.CurveShape` class.
        
        :param points: The points array.
        :param tension: The curve tension.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF], tension : float, is_closed : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.CurveShape` class.
        
        :param points: The points array.
        :param tension: The curve tension.
        :param is_closed: if set to ``true`` the curve is closed.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix, pen : aspose.psd.Pen) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :param pen: The pen to use for object. This can influence the object\'s bounds size.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    def transform(self, transform : aspose.psd.Matrix) -> None:
        '''Applies the specified transformation to the shape.
        
        :param transform: The transformation to apply.'''
        raise NotImplementedError()
    
    def reverse(self) -> None:
        '''Reverses the order of points for this shape.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.'''
        raise NotImplementedError()
    
    @property
    def center(self) -> aspose.psd.PointF:
        '''Gets the shape\'s center.'''
        raise NotImplementedError()
    
    @property
    def segments(self) -> List[aspose.psd.ShapeSegment]:
        '''Gets the shape segments.'''
        raise NotImplementedError()
    
    @property
    def has_segments(self) -> bool:
        '''Gets a value indicating whether shape has segments.'''
        raise NotImplementedError()
    
    @property
    def points(self) -> List[aspose.psd.PointF]:
        '''Gets the curve points.'''
        raise NotImplementedError()
    
    @points.setter
    def points(self, value : List[aspose.psd.PointF]) -> None:
        '''Sets the curve points.'''
        raise NotImplementedError()
    
    @property
    def is_closed(self) -> bool:
        '''Gets a value indicating whether shape is closed.'''
        raise NotImplementedError()
    
    @is_closed.setter
    def is_closed(self, value : bool) -> None:
        '''Sets a value indicating whether shape is closed.'''
        raise NotImplementedError()
    
    @property
    def start_point(self) -> aspose.psd.PointF:
        '''Gets the starting shape point.'''
        raise NotImplementedError()
    
    @property
    def end_point(self) -> aspose.psd.PointF:
        '''Gets the ending shape point.'''
        raise NotImplementedError()
    
    @property
    def tension(self) -> float:
        '''Gets the curve tension.'''
        raise NotImplementedError()
    
    @tension.setter
    def tension(self, value : float) -> None:
        '''Sets the curve tension.'''
        raise NotImplementedError()
    

class EllipseShape(RectangleShape):
    '''Represents an ellipse shape.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.EllipseShape` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rectangle : aspose.psd.RectangleF) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.EllipseShape` class.
        
        :param rectangle: The rectangle.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix, pen : aspose.psd.Pen) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :param pen: The pen to use for object. This can influence the object\'s bounds size.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    def transform(self, transform : aspose.psd.Matrix) -> None:
        '''Applies the specified transformation to the shape.
        
        :param transform: The transformation to apply.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.'''
        raise NotImplementedError()
    
    @property
    def center(self) -> aspose.psd.PointF:
        '''Gets the shape\'s center.'''
        raise NotImplementedError()
    
    @property
    def segments(self) -> List[aspose.psd.ShapeSegment]:
        '''Gets the shape segments.'''
        raise NotImplementedError()
    
    @property
    def has_segments(self) -> bool:
        '''Gets a value indicating whether shape has segments.'''
        raise NotImplementedError()
    
    @property
    def left_top(self) -> aspose.psd.PointF:
        '''Gets the left top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_top(self) -> aspose.psd.PointF:
        '''Gets the right top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def left_bottom(self) -> aspose.psd.PointF:
        '''Gets the left bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_bottom(self) -> aspose.psd.PointF:
        '''Gets the right bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def rectangle_width(self) -> float:
        '''Gets the rectangle width.'''
        raise NotImplementedError()
    
    @property
    def rectangle_height(self) -> float:
        '''Gets the rectangle height.'''
        raise NotImplementedError()
    

class PieShape(EllipseShape):
    '''Represents a pie shape.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.PieShape` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rectangle : aspose.psd.RectangleF, start_angle : float, sweep_angle : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.PieShape` class.
        
        :param rectangle: The rectangle.
        :param start_angle: The start angle.
        :param sweep_angle: The sweep angle.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix, pen : aspose.psd.Pen) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :param pen: The pen to use for object. This can influence the object\'s bounds size.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    def transform(self, transform : aspose.psd.Matrix) -> None:
        '''Applies the specified transformation to the shape.
        
        :param transform: The transformation to apply.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.'''
        raise NotImplementedError()
    
    @property
    def center(self) -> aspose.psd.PointF:
        '''Gets the shape\'s center.'''
        raise NotImplementedError()
    
    @property
    def segments(self) -> List[aspose.psd.ShapeSegment]:
        '''Gets the shape segments.'''
        raise NotImplementedError()
    
    @property
    def has_segments(self) -> bool:
        '''Gets a value indicating whether shape has segments.'''
        raise NotImplementedError()
    
    @property
    def left_top(self) -> aspose.psd.PointF:
        '''Gets the left top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_top(self) -> aspose.psd.PointF:
        '''Gets the right top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def left_bottom(self) -> aspose.psd.PointF:
        '''Gets the left bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_bottom(self) -> aspose.psd.PointF:
        '''Gets the right bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def rectangle_width(self) -> float:
        '''Gets the rectangle width.'''
        raise NotImplementedError()
    
    @property
    def rectangle_height(self) -> float:
        '''Gets the rectangle height.'''
        raise NotImplementedError()
    
    @property
    def start_angle(self) -> float:
        '''Gets the start angle.'''
        raise NotImplementedError()
    
    @start_angle.setter
    def start_angle(self, value : float) -> None:
        '''Sets the start angle.'''
        raise NotImplementedError()
    
    @property
    def sweep_angle(self) -> float:
        '''Gets the sweep angle.'''
        raise NotImplementedError()
    
    @sweep_angle.setter
    def sweep_angle(self, value : float) -> None:
        '''Sets the sweep angle.'''
        raise NotImplementedError()
    

class PolygonShape(aspose.psd.Shape):
    '''Represents a polygon shape.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.PolygonShape` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.PolygonShape` class.
        
        :param points: The points array.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, points : List[aspose.psd.PointF], is_closed : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.PolygonShape` class.
        
        :param points: The points array.
        :param is_closed: If set to ``true`` the polygon is closed.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix, pen : aspose.psd.Pen) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :param pen: The pen to use for object. This can influence the object\'s bounds size.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    def transform(self, transform : aspose.psd.Matrix) -> None:
        '''Applies the specified transformation to the shape.
        
        :param transform: The transformation to apply.'''
        raise NotImplementedError()
    
    def reverse(self) -> None:
        '''Reverses the order of points for this shape.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.'''
        raise NotImplementedError()
    
    @property
    def center(self) -> aspose.psd.PointF:
        '''Gets the shape\'s center.'''
        raise NotImplementedError()
    
    @property
    def segments(self) -> List[aspose.psd.ShapeSegment]:
        '''Gets the shape segments.'''
        raise NotImplementedError()
    
    @property
    def has_segments(self) -> bool:
        '''Gets a value indicating whether shape has segments.'''
        raise NotImplementedError()
    
    @property
    def points(self) -> List[aspose.psd.PointF]:
        '''Gets the curve points.'''
        raise NotImplementedError()
    
    @points.setter
    def points(self, value : List[aspose.psd.PointF]) -> None:
        '''Sets the curve points.'''
        raise NotImplementedError()
    
    @property
    def is_closed(self) -> bool:
        '''Gets a value indicating whether shape is closed.'''
        raise NotImplementedError()
    
    @is_closed.setter
    def is_closed(self, value : bool) -> None:
        '''Sets a value indicating whether shape is closed.'''
        raise NotImplementedError()
    
    @property
    def start_point(self) -> aspose.psd.PointF:
        '''Gets the starting shape point.'''
        raise NotImplementedError()
    
    @property
    def end_point(self) -> aspose.psd.PointF:
        '''Gets the ending shape point.'''
        raise NotImplementedError()
    

class RectangleProjectedShape(aspose.psd.Shape):
    '''Represents a shape which is projected over rectangle turned to a particular orientation.
    Specified by four points which can be rotated in space maintaining the same edges length and 90 degrees between adjacent edges.'''
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix, pen : aspose.psd.Pen) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :param pen: The pen to use for object. This can influence the object\'s bounds size.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    def transform(self, transform : aspose.psd.Matrix) -> None:
        '''Applies the specified transformation to the shape.
        
        :param transform: The transformation to apply.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.'''
        raise NotImplementedError()
    
    @property
    def center(self) -> aspose.psd.PointF:
        '''Gets the shape\'s center.'''
        raise NotImplementedError()
    
    @property
    def segments(self) -> List[aspose.psd.ShapeSegment]:
        '''Gets the shape segments.'''
        raise NotImplementedError()
    
    @property
    def has_segments(self) -> bool:
        '''Gets a value indicating whether shape has segments.'''
        raise NotImplementedError()
    
    @property
    def left_top(self) -> aspose.psd.PointF:
        '''Gets the left top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_top(self) -> aspose.psd.PointF:
        '''Gets the right top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def left_bottom(self) -> aspose.psd.PointF:
        '''Gets the left bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_bottom(self) -> aspose.psd.PointF:
        '''Gets the right bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def rectangle_width(self) -> float:
        '''Gets the rectangle width.'''
        raise NotImplementedError()
    
    @property
    def rectangle_height(self) -> float:
        '''Gets the rectangle height.'''
        raise NotImplementedError()
    

class RectangleShape(RectangleProjectedShape):
    '''Represents a rectangular shape.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.RectangleShape` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, rectangle : aspose.psd.RectangleF) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.RectangleShape` class.
        
        :param rectangle: The rectangle.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix, pen : aspose.psd.Pen) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :param pen: The pen to use for object. This can influence the object\'s bounds size.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    def transform(self, transform : aspose.psd.Matrix) -> None:
        '''Applies the specified transformation to the shape.
        
        :param transform: The transformation to apply.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.'''
        raise NotImplementedError()
    
    @property
    def center(self) -> aspose.psd.PointF:
        '''Gets the shape\'s center.'''
        raise NotImplementedError()
    
    @property
    def segments(self) -> List[aspose.psd.ShapeSegment]:
        '''Gets the shape segments.'''
        raise NotImplementedError()
    
    @property
    def has_segments(self) -> bool:
        '''Gets a value indicating whether shape has segments.'''
        raise NotImplementedError()
    
    @property
    def left_top(self) -> aspose.psd.PointF:
        '''Gets the left top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_top(self) -> aspose.psd.PointF:
        '''Gets the right top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def left_bottom(self) -> aspose.psd.PointF:
        '''Gets the left bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_bottom(self) -> aspose.psd.PointF:
        '''Gets the right bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def rectangle_width(self) -> float:
        '''Gets the rectangle width.'''
        raise NotImplementedError()
    
    @property
    def rectangle_height(self) -> float:
        '''Gets the rectangle height.'''
        raise NotImplementedError()
    

class TextShape(RectangleProjectedShape):
    '''Represents a text shape.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.TextShape` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, text : str, rectangle : aspose.psd.RectangleF, font : aspose.psd.Font, string_format : aspose.psd.StringFormat) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.shapes.TextShape` class.
        
        :param text: The text to draw.
        :param rectangle: The text rectangle.
        :param font: The font to use.
        :param string_format: The string format.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    @overload
    def get_bounds(self, matrix : aspose.psd.Matrix, pen : aspose.psd.Pen) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.
        
        :param matrix: The matrix to apply before bounds will be calculated.
        :param pen: The pen to use for object. This can influence the object\'s bounds size.
        :returns: The estimated object\'s bounds.'''
        raise NotImplementedError()
    
    def transform(self, transform : aspose.psd.Matrix) -> None:
        '''Applies the specified transformation to the shape.
        
        :param transform: The transformation to apply.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.RectangleF:
        '''Gets the object\'s bounds.'''
        raise NotImplementedError()
    
    @property
    def center(self) -> aspose.psd.PointF:
        '''Gets the shape\'s center.'''
        raise NotImplementedError()
    
    @property
    def segments(self) -> List[aspose.psd.ShapeSegment]:
        '''Gets the shape segments.'''
        raise NotImplementedError()
    
    @property
    def has_segments(self) -> bool:
        '''Gets a value indicating whether shape has segments.'''
        raise NotImplementedError()
    
    @property
    def left_top(self) -> aspose.psd.PointF:
        '''Gets the left top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_top(self) -> aspose.psd.PointF:
        '''Gets the right top rectangle point.'''
        raise NotImplementedError()
    
    @property
    def left_bottom(self) -> aspose.psd.PointF:
        '''Gets the left bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def right_bottom(self) -> aspose.psd.PointF:
        '''Gets the right bottom rectangle point.'''
        raise NotImplementedError()
    
    @property
    def rectangle_width(self) -> float:
        '''Gets the rectangle width.'''
        raise NotImplementedError()
    
    @property
    def rectangle_height(self) -> float:
        '''Gets the rectangle height.'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Gets the drawn text.'''
        raise NotImplementedError()
    
    @text.setter
    def text(self, value : str) -> None:
        '''Sets the drawn text.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.psd.Font:
        '''Gets the font used to draw the text.'''
        raise NotImplementedError()
    
    @font.setter
    def font(self, value : aspose.psd.Font) -> None:
        '''Sets the font used to draw the text.'''
        raise NotImplementedError()
    
    @property
    def text_format(self) -> aspose.psd.StringFormat:
        '''Gets the text format.'''
        raise NotImplementedError()
    
    @text_format.setter
    def text_format(self, value : aspose.psd.StringFormat) -> None:
        '''Sets the text format.'''
        raise NotImplementedError()
    

