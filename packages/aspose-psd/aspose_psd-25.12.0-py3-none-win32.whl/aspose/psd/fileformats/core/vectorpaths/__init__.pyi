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

class BezierKnotRecord(VectorPathRecord):
    '''Bezier Knot Record Class, used to read/write Bezier knots data from resource.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.BezierKnotRecord` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, data : List[int]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.BezierKnotRecord` class.
        
        :param data: The record data.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.psd.fileformats.core.vectorpaths.VectorPathType:
        '''Gets the type.'''
        raise NotImplementedError()
    
    @property
    def path_points(self) -> List[aspose.psd.PointF]:
        '''Gets the path points.'''
        raise NotImplementedError()
    
    @path_points.setter
    def path_points(self, value : List[aspose.psd.PointF]) -> None:
        '''Sets the path points.'''
        raise NotImplementedError()
    
    @property
    def points(self) -> List[aspose.psd.Point]:
        '''Gets the points.'''
        raise NotImplementedError()
    
    @points.setter
    def points(self, value : List[aspose.psd.Point]) -> None:
        '''Sets the points.'''
        raise NotImplementedError()
    
    @property
    def is_closed(self) -> bool:
        '''Gets a value indicating whether this instance is closed.'''
        raise NotImplementedError()
    
    @is_closed.setter
    def is_closed(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is closed.'''
        raise NotImplementedError()
    
    @property
    def is_linked(self) -> bool:
        '''Gets a value indicating whether this instance is linked.'''
        raise NotImplementedError()
    
    @is_linked.setter
    def is_linked(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is linked.'''
        raise NotImplementedError()
    
    @property
    def is_open(self) -> bool:
        '''Gets a value indicating whether this instance is open.'''
        raise NotImplementedError()
    
    @is_open.setter
    def is_open(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is open.'''
        raise NotImplementedError()
    

class ClipboardRecord(VectorPathRecord):
    '''Clipboard Record Class'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.ClipboardRecord` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, data : List[int]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.ClipboardRecord` class.
        
        :param data: The record data.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.psd.fileformats.core.vectorpaths.VectorPathType:
        '''Gets the type.'''
        raise NotImplementedError()
    
    @property
    def bounding_rect(self) -> aspose.psd.RectangleF:
        '''Gets the bounding rect.'''
        raise NotImplementedError()
    
    @bounding_rect.setter
    def bounding_rect(self, value : aspose.psd.RectangleF) -> None:
        '''Sets the bounding rect.'''
        raise NotImplementedError()
    
    @property
    def resolution(self) -> float:
        '''Gets the resolution.'''
        raise NotImplementedError()
    
    @resolution.setter
    def resolution(self, value : float) -> None:
        '''Sets the resolution.'''
        raise NotImplementedError()
    

class IVectorPathData:
    '''The interface for access to the vector path data.'''
    
    @property
    def paths(self) -> List[aspose.psd.fileformats.core.vectorpaths.VectorPathRecord]:
        '''Gets the path records.'''
        raise NotImplementedError()
    
    @paths.setter
    def paths(self, value : List[aspose.psd.fileformats.core.vectorpaths.VectorPathRecord]) -> None:
        '''Sets the path records.'''
        raise NotImplementedError()
    
    @property
    def version(self) -> int:
        '''Gets the version.'''
        raise NotImplementedError()
    
    @version.setter
    def version(self, value : int) -> None:
        '''Sets the version.'''
        raise NotImplementedError()
    
    @property
    def is_disabled(self) -> bool:
        '''Gets a value indicating whether this instance is disabled.'''
        raise NotImplementedError()
    
    @is_disabled.setter
    def is_disabled(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is disabled.'''
        raise NotImplementedError()
    
    @property
    def is_not_linked(self) -> bool:
        '''Gets a value indicating whether this instance is not linked.'''
        raise NotImplementedError()
    
    @is_not_linked.setter
    def is_not_linked(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is not linked.'''
        raise NotImplementedError()
    
    @property
    def is_inverted(self) -> bool:
        '''Gets a value indicating whether this instance is inverted.'''
        raise NotImplementedError()
    
    @is_inverted.setter
    def is_inverted(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is inverted.'''
        raise NotImplementedError()
    

class InitialFillRuleRecord(VectorPathRecord):
    '''Initial Fill Rule Record Class'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.InitialFillRuleRecord` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, is_fill_starts_with_all_pixels : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.InitialFillRuleRecord` class.
        
        :param is_fill_starts_with_all_pixels: The is fill starts with all pixels.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, data : List[int]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.InitialFillRuleRecord` class.
        
        :param data: The record data.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.psd.fileformats.core.vectorpaths.VectorPathType:
        '''Gets the type.'''
        raise NotImplementedError()
    
    @property
    def is_fill_starts_with_all_pixels(self) -> bool:
        '''Gets a value indicating whether is fill starts with all pixels.'''
        raise NotImplementedError()
    
    @is_fill_starts_with_all_pixels.setter
    def is_fill_starts_with_all_pixels(self, value : bool) -> None:
        '''Sets a value indicating whether is fill starts with all pixels.'''
        raise NotImplementedError()
    

class LengthRecord(VectorPathRecord):
    '''Subpath Length Record Class.'''
    
    @overload
    def __init__(self, data : List[int]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.LengthRecord` class.
        
        :param data: The record data.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.LengthRecord` class.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.psd.fileformats.core.vectorpaths.VectorPathType:
        '''Gets the type.'''
        raise NotImplementedError()
    
    @property
    def is_closed(self) -> bool:
        '''Gets a value indicating whether this instance is closed.'''
        raise NotImplementedError()
    
    @is_closed.setter
    def is_closed(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is closed.'''
        raise NotImplementedError()
    
    @property
    def is_open(self) -> bool:
        '''Gets a value indicating whether this instance is open.'''
        raise NotImplementedError()
    
    @is_open.setter
    def is_open(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is open.'''
        raise NotImplementedError()
    
    @property
    def record_count(self) -> int:
        '''Gets the record count.'''
        raise NotImplementedError()
    
    @record_count.setter
    def record_count(self, value : int) -> None:
        '''Sets the record count.'''
        raise NotImplementedError()
    
    @property
    def bezier_knot_records_count(self) -> int:
        '''Gets the bezier knot records count.'''
        raise NotImplementedError()
    
    @bezier_knot_records_count.setter
    def bezier_knot_records_count(self, value : int) -> None:
        '''Sets the bezier knot records count.'''
        raise NotImplementedError()
    
    @property
    def path_operations(self) -> aspose.psd.fileformats.core.vectorpaths.PathOperations:
        '''Gets the path operations.'''
        raise NotImplementedError()
    
    @path_operations.setter
    def path_operations(self, value : aspose.psd.fileformats.core.vectorpaths.PathOperations) -> None:
        '''Sets the path operations.'''
        raise NotImplementedError()
    
    @property
    def shape_index(self) -> int:
        '''Gets the index of current path shape in layer.'''
        raise NotImplementedError()
    
    @shape_index.setter
    def shape_index(self, value : int) -> None:
        '''Sets the index of current path shape in layer.'''
        raise NotImplementedError()
    

class PathFillRuleRecord(VectorPathRecord):
    '''Path Fill Rule Record Class'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.PathFillRuleRecord` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, data : List[int]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.PathFillRuleRecord` class.
        
        :param data: The record data.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.psd.fileformats.core.vectorpaths.VectorPathType:
        '''Gets the type.'''
        raise NotImplementedError()
    

class VectorPathRecord:
    '''Vector Path Record Class'''
    
    @property
    def type(self) -> aspose.psd.fileformats.core.vectorpaths.VectorPathType:
        '''Gets the type.'''
        raise NotImplementedError()
    

class VectorPathRecordFactory:
    '''Vector Path Record Factory Class.'''
    
    @staticmethod
    def produce_path_record(data : List[int]) -> aspose.psd.fileformats.core.vectorpaths.VectorPathRecord:
        '''Produces the path record.
        
        :param data: The record data.
        :returns: Created :py:class:`aspose.psd.fileformats.core.vectorpaths.VectorPathRecord`.'''
        raise NotImplementedError()
    

class VectorShapeBoundingBox:
    '''Defines vector shape bounding box class.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def left(self) -> float:
        '''Gets the left.'''
        raise NotImplementedError()
    
    @left.setter
    def left(self, value : float) -> None:
        '''Sets the left.'''
        raise NotImplementedError()
    
    @property
    def top(self) -> float:
        '''Gets the top.'''
        raise NotImplementedError()
    
    @top.setter
    def top(self, value : float) -> None:
        '''Sets the top.'''
        raise NotImplementedError()
    
    @property
    def right(self) -> float:
        '''Gets the right.'''
        raise NotImplementedError()
    
    @right.setter
    def right(self, value : float) -> None:
        '''Sets the right.'''
        raise NotImplementedError()
    
    @property
    def bottom(self) -> float:
        '''Gets the bottom.'''
        raise NotImplementedError()
    
    @bottom.setter
    def bottom(self, value : float) -> None:
        '''Sets the bottom.'''
        raise NotImplementedError()
    
    @property
    def quad_version(self) -> int:
        '''Gets the unit value quad version.'''
        raise NotImplementedError()
    
    @quad_version.setter
    def quad_version(self, value : int) -> None:
        '''Sets the unit value quad version.'''
        raise NotImplementedError()
    
    @property
    def points_unit_type(self) -> aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitTypes:
        '''Gets unit type of the points that determine the corners of the box.'''
        raise NotImplementedError()
    
    @points_unit_type.setter
    def points_unit_type(self, value : aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitTypes) -> None:
        '''Sets unit type of the points that determine the corners of the box.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.Rectangle:
        '''Gets the bounds of the shape bounding box.'''
        raise NotImplementedError()
    
    @bounds.setter
    def bounds(self, value : aspose.psd.Rectangle) -> None:
        '''Sets the bounds of the shape bounding box.'''
        raise NotImplementedError()
    

class VectorShapeOriginSettings:
    '''Vector shape origination settings.'''
    
    @overload
    def __init__(self, is_shape_invalidated : bool, origin_index : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.VectorShapeOriginSettings` class.
        
        :param is_shape_invalidated: The shape is invalidated value.
        :param origin_index: The shape origin index.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.VectorShapeOriginSettings` class.'''
        raise NotImplementedError()
    
    @property
    def is_shape_invalidated(self) -> bool:
        '''Gets a value indicating whether shape is invalidated.'''
        raise NotImplementedError()
    
    @is_shape_invalidated.setter
    def is_shape_invalidated(self, value : bool) -> None:
        '''Sets a value indicating whether shape is invalidated.'''
        raise NotImplementedError()
    
    @property
    def origin_index(self) -> int:
        '''Gets the origin shape index.'''
        raise NotImplementedError()
    
    @origin_index.setter
    def origin_index(self, value : int) -> None:
        '''Sets the origin shape index.'''
        raise NotImplementedError()
    
    @property
    def origin_type(self) -> int:
        '''Gets the type of the origin.'''
        raise NotImplementedError()
    
    @origin_type.setter
    def origin_type(self, value : int) -> None:
        '''Sets the type of the origin.'''
        raise NotImplementedError()
    
    @property
    def origin_resolution(self) -> float:
        '''Gets the origin resolution.'''
        raise NotImplementedError()
    
    @origin_resolution.setter
    def origin_resolution(self, value : float) -> None:
        '''Sets the origin resolution.'''
        raise NotImplementedError()
    
    @property
    def origin_shape_box(self) -> aspose.psd.fileformats.core.vectorpaths.VectorShapeBoundingBox:
        '''Gets the origin shape bounding box.'''
        raise NotImplementedError()
    
    @origin_shape_box.setter
    def origin_shape_box(self, value : aspose.psd.fileformats.core.vectorpaths.VectorShapeBoundingBox) -> None:
        '''Sets the origin shape bounding box.'''
        raise NotImplementedError()
    
    @property
    def origin_radii_rectangle(self) -> aspose.psd.fileformats.core.vectorpaths.VectorShapeRadiiRectangle:
        '''Gets the origin radii rectangle.'''
        raise NotImplementedError()
    
    @origin_radii_rectangle.setter
    def origin_radii_rectangle(self, value : aspose.psd.fileformats.core.vectorpaths.VectorShapeRadiiRectangle) -> None:
        '''Sets the origin radii rectangle.'''
        raise NotImplementedError()
    
    @property
    def transform(self) -> aspose.psd.fileformats.core.vectorpaths.VectorShapeTransform:
        '''Gets the transformation matrix.'''
        raise NotImplementedError()
    
    @transform.setter
    def transform(self, value : aspose.psd.fileformats.core.vectorpaths.VectorShapeTransform) -> None:
        '''Sets the transformation matrix.'''
        raise NotImplementedError()
    
    @property
    def is_shape_invalidated_present(self) -> bool:
        '''Gets a value indicating whether this instance has a shape invalidated property set.'''
        raise NotImplementedError()
    
    @property
    def is_origin_index_present(self) -> bool:
        '''Gets a value indicating whether this instance has origin index property.'''
        raise NotImplementedError()
    
    @property
    def is_origin_type_present(self) -> bool:
        '''Gets a value indicating whether this instance has origin type property.'''
        raise NotImplementedError()
    
    @property
    def is_origin_resolution_present(self) -> bool:
        '''Gets a value indicating whether this instance has origin resolution property.'''
        raise NotImplementedError()
    
    @property
    def is_origin_radii_rectangle_present(self) -> bool:
        '''Gets a value indicating whether this instance has the origin radii rectangle property.'''
        raise NotImplementedError()
    
    @property
    def is_origin_shape_b_box_present(self) -> bool:
        '''Gets a value indicating whether this instance has the rectangle property.'''
        raise NotImplementedError()
    
    @property
    def is_origin_box_corners_present(self) -> bool:
        '''Gets a value indicating whether this instance has the origin box corners property.'''
        raise NotImplementedError()
    
    @property
    def is_transform_present(self) -> bool:
        '''Gets a value indicating whether this instance has the transform property.'''
        raise NotImplementedError()
    
    @property
    def origin_box_corners(self) -> List[float]:
        '''Gets the origin box corners.'''
        raise NotImplementedError()
    
    @origin_box_corners.setter
    def origin_box_corners(self, value : List[float]) -> None:
        '''Sets the origin box corners.'''
        raise NotImplementedError()
    

class VectorShapeRadiiRectangle:
    '''Defines vector shape radii rectangle class'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def top_left(self) -> float:
        '''Gets the top left.'''
        raise NotImplementedError()
    
    @top_left.setter
    def top_left(self, value : float) -> None:
        '''Sets the top left.'''
        raise NotImplementedError()
    
    @property
    def top_right(self) -> float:
        '''Gets the top right.'''
        raise NotImplementedError()
    
    @top_right.setter
    def top_right(self, value : float) -> None:
        '''Sets the top right.'''
        raise NotImplementedError()
    
    @property
    def bottom_right(self) -> float:
        '''Gets the bottom right.'''
        raise NotImplementedError()
    
    @bottom_right.setter
    def bottom_right(self, value : float) -> None:
        '''Sets the bottom right.'''
        raise NotImplementedError()
    
    @property
    def bottom_left(self) -> float:
        '''Gets the bottom.'''
        raise NotImplementedError()
    
    @bottom_left.setter
    def bottom_left(self, value : float) -> None:
        '''Sets the bottom.'''
        raise NotImplementedError()
    
    @property
    def quad_version(self) -> int:
        '''Gets the unit value quad version.'''
        raise NotImplementedError()
    
    @quad_version.setter
    def quad_version(self, value : int) -> None:
        '''Sets the unit value quad version.'''
        raise NotImplementedError()
    

class VectorShapeTransform:
    '''Defines vector shape transformation matrix class'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.core.vectorpaths.VectorShapeTransform` class.'''
        raise NotImplementedError()
    
    @property
    def xx(self) -> float:
        '''Gets the XX value.'''
        raise NotImplementedError()
    
    @xx.setter
    def xx(self, value : float) -> None:
        '''Sets the XX value.'''
        raise NotImplementedError()
    
    @property
    def xy(self) -> float:
        '''Gets the XY value.'''
        raise NotImplementedError()
    
    @xy.setter
    def xy(self, value : float) -> None:
        '''Sets the XY value.'''
        raise NotImplementedError()
    
    @property
    def yx(self) -> float:
        '''Gets the YX value.'''
        raise NotImplementedError()
    
    @yx.setter
    def yx(self, value : float) -> None:
        '''Sets the YX value.'''
        raise NotImplementedError()
    
    @property
    def yy(self) -> float:
        '''Gets the YY value.'''
        raise NotImplementedError()
    
    @yy.setter
    def yy(self, value : float) -> None:
        '''Sets the YY value.'''
        raise NotImplementedError()
    
    @property
    def tx(self) -> float:
        '''Gets the TX value.'''
        raise NotImplementedError()
    
    @tx.setter
    def tx(self, value : float) -> None:
        '''Sets the TX value.'''
        raise NotImplementedError()
    
    @property
    def ty(self) -> float:
        '''Gets the TY value.'''
        raise NotImplementedError()
    
    @ty.setter
    def ty(self, value : float) -> None:
        '''Sets the TY value.'''
        raise NotImplementedError()
    

class PathOperations:
    '''The operations for the path shapes combining (Boolean operations).'''
    
    EXCLUDE_OVERLAPPING_SHAPES : PathOperations
    '''Exclude Overlapping Shapes (XOR operation).'''
    COMBINE_SHAPES : PathOperations
    '''Combine Shapes (OR operation). This is default value in Photoshop.'''
    SUBTRACT_FRONT_SHAPE : PathOperations
    '''Subtract Front Shape (NOT operation).'''
    INTERSECT_SHAPE_AREAS : PathOperations
    '''Intersect Shape Areas (AND operation).'''

class VectorPathType:
    '''Vector Path Type according to PSD Format Specification'''
    
    CLOSED_SUBPATH_LENGTH_RECORD : VectorPathType
    '''The closed subpath length record'''
    CLOSED_SUBPATH_BEZIER_KNOT_LINKED : VectorPathType
    '''The closed subpath bezier knot linked'''
    CLOSED_SUBPATH_BEZIER_KNOT_UNLINKED : VectorPathType
    '''The closed subpath bezier knot unlinked'''
    OPEN_SUBPATH_LENGTH_RECORD : VectorPathType
    '''The open subpath length record'''
    OPEN_SUBPATH_BEZIER_KNOT_LINKED : VectorPathType
    '''The open subpath bezier knot linked'''
    OPEN_SUBPATH_BEZIER_KNOT_UNLINKED : VectorPathType
    '''The open subpath bezier knot unlinked'''
    PATH_FILL_RULE_RECORD : VectorPathType
    '''The path fill rule record'''
    CLIPBOARD_RECORD : VectorPathType
    '''The clipboard record'''
    INITIAL_FILL_RULE_RECORD : VectorPathType
    '''The initial fill rule record'''

