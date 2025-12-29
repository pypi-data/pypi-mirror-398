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

class PsdColorPalette(aspose.psd.IPsdColorPalette):
    '''The PSD color palette.'''
    
    @overload
    def __init__(self, color_palette : aspose.psd.IColorPalette) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdColorPalette` class.
        
        :param color_palette: The color palette.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, color_palette : aspose.psd.IColorPalette, transparent_index : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdColorPalette` class.
        
        :param color_palette: The color palette.
        :param transparent_index: The transparent color index.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, raw_entries_data : List[int], is_compact_palette : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdColorPalette` class.
        
        :param raw_entries_data: The raw entries data.
        :param is_compact_palette: Indicating whether compact it palette.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, raw_entries_data : List[int]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdColorPalette` class and IsCompactPalette is false.
        
        :param raw_entries_data: The raw entries data.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, raw_entries_data : List[int], transparent_index : int, use_compact_palette : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdColorPalette` class.
        
        :param raw_entries_data: The raw entries data.
        :param transparent_index: The transparent color index. Note the index is not the raw entries index instead it is for the converted color array.
        :param use_compact_palette: Indicating whether compact it palette.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, raw_entries_data : List[int], transparent_index : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdColorPalette` class and IsCompactPalette is false.
        
        :param raw_entries_data: The raw entries data.
        :param transparent_index: The transparent color index. Note the index is not the raw entries index instead it is for the converted color array.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, color_palette_argb_32_entries : List[int], is_compact_palette : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdColorPalette` class.
        
        :param color_palette_argb_32_entries: The color palette 32-bit ARGB entries.
        :param is_compact_palette: Indicating whether compact it palette.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, color_palette_entries : List[aspose.psd.Color], is_compact_palette : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdColorPalette` class.
        
        :param color_palette_entries: The color palette entries.
        :param is_compact_palette: Indicating whether compact it palette.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, color_palette_entries : List[aspose.psd.Color]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdColorPalette` class and IsCompactPalette is false.
        
        :param color_palette_entries: The color palette entries.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, color_palette_entries : List[aspose.psd.Color], transparent_index : int, use_compact_palette : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdColorPalette` class.
        
        :param color_palette_entries: The color palette entries.
        :param transparent_index: The transparent color index.
        :param use_compact_palette: Indicating whether compact it palette.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, color_palette_entries : List[aspose.psd.Color], transparent_index : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdColorPalette` class and IsCompactPalette is false.
        
        :param color_palette_entries: The color palette entries.
        :param transparent_index: The transparent color index.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def copy_palette(color_palette : aspose.psd.IColorPalette, use_compact_palette : bool) -> aspose.psd.fileformats.psd.PsdColorPalette:
        '''Copies the palette.
        
        :param color_palette: The color palette.
        :param use_compact_palette: Indicating whether compact palette.
        :returns: The newly created and copied palette or null if null palette passed.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def copy_palette(color_palette : aspose.psd.IColorPalette) -> aspose.psd.fileformats.psd.PsdColorPalette:
        '''Copies the palette.
        
        :param color_palette: The color palette.
        :returns: The newly created and copied palette or null if null palette passed.'''
        raise NotImplementedError()
    
    @overload
    def get_nearest_color_index(self, argb_32_color : int) -> int:
        '''Gets the index of the nearest color.
        
        :param argb_32_color: The 32-bit ARGB color.
        :returns: The index of the nearest color.'''
        raise NotImplementedError()
    
    @overload
    def get_nearest_color_index(self, color : aspose.psd.Color) -> int:
        '''Gets the index of the nearest color.
        
        :param color: The color.
        :returns: The index of the nearest color.'''
        raise NotImplementedError()
    
    def get_argb_32_color(self, index : int) -> int:
        '''Gets the 32-bit ARGB palette color by index.
        
        :param index: The 32-bit ARGB palette color index.
        :returns: The color palette entry specified by the ``index``.'''
        raise NotImplementedError()
    
    def get_color(self, index : int) -> aspose.psd.Color:
        '''Gets the palette color by index.
        
        :param index: The palette color index.
        :returns: The color palette entry specified by the ``index``.'''
        raise NotImplementedError()
    
    @property
    def raw_entries_count(self) -> int:
        '''Gets the raw color palette entries count.'''
        raise NotImplementedError()
    
    @property
    def entries_count(self) -> int:
        '''Gets the entries count.'''
        raise NotImplementedError()
    
    @property
    def argb_32_entries(self) -> List[int]:
        '''Gets an array of 32-bit ARGB colors.'''
        raise NotImplementedError()
    
    @property
    def entries(self) -> List[aspose.psd.Color]:
        '''Gets an array of :py:class:`aspose.psd.Color` structures.'''
        raise NotImplementedError()
    
    @property
    def transparent_index(self) -> int:
        '''Gets the index of the transparent color.'''
        raise NotImplementedError()
    
    @property
    def has_transparent_color(self) -> bool:
        '''Gets a value indicating whether transparent color exists.'''
        raise NotImplementedError()
    
    @property
    def transparent_color(self) -> aspose.psd.Color:
        '''Gets the transparent color.'''
        raise NotImplementedError()
    
    @property
    def raw_entries(self) -> List[int]:
        '''Gets the raw color palette entries data.'''
        raise NotImplementedError()
    
    @property
    def is_compact_palette(self) -> bool:
        '''Gets a value indicating whether compact it palette.'''
        raise NotImplementedError()
    

class PsdImage(aspose.psd.RasterCachedImage):
    '''Defines the PsdImage class that provides the ability to load, edit, save PSD files as well as
    update properties, add watermarks, perform graphics operations or convert one file format to another.
    Aspose.PSD supports import as a layer and export to the following formats:
    Png, Jpeg, Jpeg2000, Gif, Bmp, Tiff, Psd, Psb along with export to Pdf with selectable text'''
    
    @overload
    def __init__(self, path : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdImage` class from specified path from raster image (not psd image in path). Used to initialize psd image with default parameters - Color mode - rgb, 4 channels, 8 bit per channel, Compression - Raw.
        
        :param path: The path to load pixel and palette data from and initialize with.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, path : str, color_mode : aspose.psd.fileformats.psd.ColorModes, channel_bit_depth : int, channels : int, psd_version : int, compression : aspose.psd.fileformats.psd.CompressionMethod) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdImage` class from specified path from raster image (not psd image in path) with constructor parameters.
        
        :param path: The path to load pixel and palette data from and initialize with.
        :param color_mode: The color mode.
        :param channel_bit_depth: The PSD bit depth per channel.
        :param channels: The PSD channels count.
        :param psd_version: The PSD version.
        :param compression: The compression to use.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdImage` class from specified path from raster image (not psd image in stream). Used to initialize psd image with default parameters - Color mode - rgb, 4 channels, 8 bit per channel, Compression - Raw.
        
        :param stream: The stream to load pixel and palette data from and initialize with.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase, color_mode : aspose.psd.fileformats.psd.ColorModes, channel_bit_depth : int, channels : int, psd_version : int, compression : aspose.psd.fileformats.psd.CompressionMethod) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdImage` class from specified path from raster image (not psd image in stream) with constructor parameters.
        
        :param stream: The stream to load pixel and palette data from and initialize with.
        :param color_mode: The color mode.
        :param channel_bit_depth: The PSD bit depth per channel.
        :param channels: The PSD channels count.
        :param psd_version: The PSD version.
        :param compression: The compression to use.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, raster_image : aspose.psd.RasterImage) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdImage` class from existing raster image (not psd image) with RGB color mode with 4 channels 8 bit/channel and no compression.
        
        :param raster_image: The image to load pixel and palette data from and initialize with.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, raster_image : aspose.psd.RasterImage, color_mode : aspose.psd.fileformats.psd.ColorModes, channel_bit_depth : int, channels : int, psd_version : int, compression : aspose.psd.fileformats.psd.CompressionMethod) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdImage` class from existing raster image (not psd image) with constructor parameters.
        
        :param raster_image: The image to load pixel and palette data from and initialize with.
        :param color_mode: The color mode.
        :param channel_bit_depth: The PSD bit depth per channel.
        :param channels: The PSD channels count.
        :param psd_version: The PSD version.
        :param compression: The compression to use.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, width : int, height : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdImage` class with specified width and height. Used to initialize empty psd image.
        
        :param width: The image width.
        :param height: The image height.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, width : int, height : int, color_palette : aspose.psd.IColorPalette, color_mode : aspose.psd.fileformats.psd.ColorModes, channel_bit_depth : int, channels : int, psd_version : int, compression : aspose.psd.fileformats.psd.CompressionMethod) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.PsdImage` class with specified width,height, paletter, color mode, channels count and channels bit-length and specified compression mode parameters. Used to initialize empty psd image.
        
        :param width: The image width.
        :param height: The image height.
        :param color_palette: The color palette.
        :param color_mode: The color mode.
        :param channel_bit_depth: The PSD bit depth per channel.
        :param channels: The PSD channels count.
        :param psd_version: The PSD version.
        :param compression: The compression to use.'''
        raise NotImplementedError()
    
    @overload
    def save(self, stream : io._IOBase, options_base : aspose.psd.ImageOptionsBase, bounds_rectangle : aspose.psd.Rectangle) -> None:
        '''Saves the image\'s data to the specified stream in the specified file format according to save options.
        
        :param stream: The stream to save the image\'s data to.
        :param options_base: The save options.
        :param bounds_rectangle: The destination image bounds rectangle. Set the empty rectangle for use source bounds.'''
        raise NotImplementedError()
    
    @overload
    def save(self) -> None:
        '''Saves the image data to the underlying stream.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str, options : aspose.psd.ImageOptionsBase) -> None:
        '''Saves the object\'s data to the specified file location in the specified file format according to save options.
        
        :param file_path: The file path.
        :param options: The options.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str, options : aspose.psd.ImageOptionsBase, bounds_rectangle : aspose.psd.Rectangle) -> None:
        '''Saves the object\'s data to the specified file location in the specified file format according to save options.
        
        :param file_path: The file path.
        :param options: The options.
        :param bounds_rectangle: The destination image bounds rectangle. Set the empty rectangle for use sourse bounds.'''
        raise NotImplementedError()
    
    @overload
    def save(self, stream : io._IOBase, options_base : aspose.psd.ImageOptionsBase) -> None:
        '''Saves the image\'s data to the specified stream in the specified file format according to save options.
        
        :param stream: The stream to save the image\'s data to.
        :param options_base: The save options.'''
        raise NotImplementedError()
    
    @overload
    def save(self, stream : io._IOBase) -> None:
        '''Saves the object\'s data to the specified stream.
        
        :param stream: The stream to save the object\'s data to.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str) -> None:
        '''Saves the object\'s data to the specified file location.
        
        :param file_path: The file path to save the object\'s data to.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str, over_write : bool) -> None:
        '''Saves the object\'s data to the specified file location.
        
        :param file_path: The file path to save the object\'s data to.
        :param over_write: if set to ``true`` over write the file contents, otherwise append will occur.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def can_load(file_path : str) -> bool:
        '''Determines whether image can be loaded from the specified file path.
        
        :param file_path: The file path.
        :returns: ``true`` if image can be loaded from the specified file; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def can_load(file_path : str, load_options : aspose.psd.LoadOptions) -> bool:
        '''Determines whether image can be loaded from the specified file path and optionally using the specified open options.
        
        :param file_path: The file path.
        :param load_options: The load options.
        :returns: ``true`` if image can be loaded from the specified file; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def can_load(stream : io._IOBase) -> bool:
        '''Determines whether image can be loaded from the specified stream.
        
        :param stream: The stream to load from.
        :returns: ``true`` if image can be loaded from the specified stream; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def can_load(stream : io._IOBase, load_options : aspose.psd.LoadOptions) -> bool:
        '''Determines whether image can be loaded from the specified stream and optionally using the specified ``loadOptions``.
        
        :param stream: The stream to load from.
        :param load_options: The load options.
        :returns: ``true`` if image can be loaded from the specified stream; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def get_file_format(file_path : str) -> aspose.psd.FileFormat:
        '''Gets the file format.
        
        :param file_path: The file path.
        :returns: The determined file format.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def get_file_format(stream : io._IOBase) -> aspose.psd.FileFormat:
        '''Gets the file format.
        
        :param stream: The stream.
        :returns: The determined file format.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def get_fitting_rectangle(rectangle : aspose.psd.Rectangle, width : int, height : int) -> aspose.psd.Rectangle:
        '''Gets rectangle which fits the current image.
        
        :param rectangle: The rectangle to get fitting rectangle for.
        :param width: The object width.
        :param height: The object height.
        :returns: The fitting rectangle or exception if no fitting rectangle can be found.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def get_fitting_rectangle(rectangle : aspose.psd.Rectangle, pixels : List[int], width : int, height : int) -> aspose.psd.Rectangle:
        '''Gets rectangle which fits the current image.
        
        :param rectangle: The rectangle to get fitting rectangle for.
        :param pixels: The 32-bit ARGB pixels.
        :param width: The object width.
        :param height: The object height.
        :returns: The fitting rectangle or exception if no fitting rectangle can be found.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def load(file_path : str, load_options : aspose.psd.LoadOptions) -> aspose.psd.Image:
        '''Loads a new image from the specified file.
        
        :param file_path: The file path to load image from.
        :param load_options: The load options.
        :returns: The loaded image.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def load(file_path : str) -> aspose.psd.Image:
        '''Loads a new image from the specified file.
        
        :param file_path: The file path to load image from.
        :returns: The loaded image.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def load(stream : io._IOBase, load_options : aspose.psd.LoadOptions) -> aspose.psd.Image:
        '''Loads a new image from the specified stream.
        
        :param stream: The stream to load image from.
        :param load_options: The load options.
        :returns: The loaded image.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def load(stream : io._IOBase) -> aspose.psd.Image:
        '''Loads a new image from the specified stream.
        
        :param stream: The stream to load image from.
        :returns: The loaded image.'''
        raise NotImplementedError()
    
    @overload
    def resize(self, new_width : int, new_height : int, resize_type : aspose.psd.ResizeType) -> None:
        '''Resizes the image.
        
        :param new_width: The new width.
        :param new_height: The new height.
        :param resize_type: The resize type.'''
        raise NotImplementedError()
    
    @overload
    def resize(self, new_width : int, new_height : int, settings : aspose.psd.ImageResizeSettings) -> None:
        '''Resizes the image.
        
        :param new_width: The new width.
        :param new_height: The new height.
        :param settings: The resize settings.'''
        raise NotImplementedError()
    
    @overload
    def resize(self, new_width : int, new_height : int) -> None:
        '''Resizes the image. The default :py:attr:`aspose.psd.ResizeType.NEAREST_NEIGHBOUR_RESAMPLE` is used.
        
        :param new_width: The new width.
        :param new_height: The new height.'''
        raise NotImplementedError()
    
    @overload
    def resize_width_proportionally(self, new_width : int, settings : aspose.psd.ImageResizeSettings) -> None:
        '''Resizes the width proportionally.
        
        :param new_width: The new width.
        :param settings: The image resize settings.'''
        raise NotImplementedError()
    
    @overload
    def resize_width_proportionally(self, new_width : int, resize_type : aspose.psd.ResizeType) -> None:
        '''Resizes the width proportionally.
        
        :param new_width: The new width.
        :param resize_type: Type of the resize.'''
        raise NotImplementedError()
    
    @overload
    def resize_width_proportionally(self, new_width : int) -> None:
        '''Resizes the width proportionally. The default :py:attr:`aspose.psd.ResizeType.NEAREST_NEIGHBOUR_RESAMPLE` is used.
        
        :param new_width: The new width.'''
        raise NotImplementedError()
    
    @overload
    def resize_height_proportionally(self, new_height : int, settings : aspose.psd.ImageResizeSettings) -> None:
        '''Resizes the height proportionally.
        
        :param new_height: The new height.
        :param settings: The image resize settings.'''
        raise NotImplementedError()
    
    @overload
    def resize_height_proportionally(self, new_height : int, resize_type : aspose.psd.ResizeType) -> None:
        '''Resizes the height proportionally.
        
        :param new_height: The new height.
        :param resize_type: Type of the resize.'''
        raise NotImplementedError()
    
    @overload
    def resize_height_proportionally(self, new_height : int) -> None:
        '''Resizes the height proportionally.
        
        :param new_height: The new height.'''
        raise NotImplementedError()
    
    @overload
    def dither(self, dithering_method : aspose.psd.DitheringMethod, bits_count : int, custom_palette : aspose.psd.IColorPalette) -> None:
        '''Performs dithering on the current image.
        
        :param dithering_method: The dithering method.
        :param bits_count: The final bits count for dithering.
        :param custom_palette: The custom palette for dithering.'''
        raise NotImplementedError()
    
    @overload
    def dither(self, dithering_method : aspose.psd.DitheringMethod, bits_count : int) -> None:
        '''Performs dithering on the current image.
        
        :param dithering_method: The dithering method.
        :param bits_count: The final bits count for dithering.'''
        raise NotImplementedError()
    
    @overload
    def get_default_raw_data(self, rectangle : aspose.psd.Rectangle, partial_raw_data_loader : aspose.psd.IPartialRawDataLoader, raw_data_settings : aspose.psd.RawDataSettings) -> None:
        '''Gets the default raw data array using partial pixel loader.
        
        :param rectangle: The rectangle to get pixels for.
        :param partial_raw_data_loader: The partial raw data loader.
        :param raw_data_settings: The raw data settings.'''
        raise NotImplementedError()
    
    @overload
    def get_default_raw_data(self, rectangle : aspose.psd.Rectangle, raw_data_settings : aspose.psd.RawDataSettings) -> List[int]:
        '''Gets the default raw data array.
        
        :param rectangle: The rectangle to get raw data for.
        :param raw_data_settings: The raw data settings.
        :returns: The default raw data array.'''
        raise NotImplementedError()
    
    @overload
    def load_raw_data(self, rectangle : aspose.psd.Rectangle, raw_data_settings : aspose.psd.RawDataSettings, raw_data_loader : aspose.psd.IPartialRawDataLoader) -> None:
        '''Loads raw data.
        
        :param rectangle: The rectangle to load raw data from.
        :param raw_data_settings: The raw data settings to use for loaded data. Note if data is not in the format specified then data conversion will be performed.
        :param raw_data_loader: The raw data loader.'''
        raise NotImplementedError()
    
    @overload
    def load_raw_data(self, rectangle : aspose.psd.Rectangle, dest_image_bounds : aspose.psd.Rectangle, raw_data_settings : aspose.psd.RawDataSettings, raw_data_loader : aspose.psd.IPartialRawDataLoader) -> None:
        '''Loads raw data.
        
        :param rectangle: The rectangle to load raw data from.
        :param dest_image_bounds: The dest image bounds.
        :param raw_data_settings: The raw data settings to use for loaded data. Note if data is not in the format specified then data conversion will be performed.
        :param raw_data_loader: The raw data loader.'''
        raise NotImplementedError()
    
    @overload
    def crop(self, rectangle : aspose.psd.Rectangle) -> None:
        '''Cropping the image.
        
        :param rectangle: The rectangle.'''
        raise NotImplementedError()
    
    @overload
    def crop(self, left_shift : int, right_shift : int, top_shift : int, bottom_shift : int) -> None:
        raise NotImplementedError()
    
    @overload
    def binarize_bradley(self, brightness_difference : float, window_size : int) -> None:
        '''Binarization of an image using Bradley\'s adaptive thresholding algorithm using the integral image thresholding
        
        :param brightness_difference: The brightness difference between pixel and the average of an s x s window of pixels centered around this pixel.
        :param window_size: The size of s x s window of pixels centered around this pixel'''
        raise NotImplementedError()
    
    @overload
    def binarize_bradley(self, brightness_difference : float) -> None:
        '''Binarization of an image using Bradley\'s adaptive thresholding algorithm using the integral image thresholding
        
        :param brightness_difference: The brightness difference between pixel and the average of an s x s window of pixels centered around this pixel.'''
        raise NotImplementedError()
    
    @overload
    def adjust_gamma(self, gamma : float) -> None:
        '''Gamma-correction of an image.
        
        :param gamma: Gamma for red, green and blue channels coefficient'''
        raise NotImplementedError()
    
    @overload
    def adjust_gamma(self, gamma_red : float, gamma_green : float, gamma_blue : float) -> None:
        '''Gamma-correction of an image.
        
        :param gamma_red: Gamma for red channel coefficient
        :param gamma_green: Gamma for green channel coefficient
        :param gamma_blue: Gamma for blue channel coefficient'''
        raise NotImplementedError()
    
    @overload
    def rotate(self, angle : float) -> None:
        '''Rotate image around the center.
        
        :param angle: The rotate angle in degrees. Positive values will rotate clockwise.'''
        raise NotImplementedError()
    
    @overload
    def rotate(self, angle : float, resize_proportionally : bool, background_color : aspose.psd.Color) -> None:
        '''Rotate image around the center.
        
        :param angle: The rotate angle in degrees. Positive values will rotate clockwise.
        :param resize_proportionally: if set to ``true`` you will have your image size changed according to rotated rectangle (corner points) projections in other case that leaves dimensions untouched and only internal image contents are rotated.
        :param background_color: Color of the background.'''
        raise NotImplementedError()
    
    @overload
    def normalize_angle(self) -> None:
        raise NotImplementedError()
    
    @overload
    def normalize_angle(self, resize_proportionally : bool, background_color : aspose.psd.Color) -> None:
        raise NotImplementedError()
    
    @overload
    def replace_color(self, old_color_argb : int, old_color_diff : int, new_color_argb : int) -> None:
        '''Replaces one color to another with allowed difference and preserves original alpha value to save smooth edges.
        
        :param old_color_argb: Old color ARGB value to be replaced.
        :param old_color_diff: Allowed difference in old color to be able to widen replaced color tone.
        :param new_color_argb: New color ARGB value to replace old color with.'''
        raise NotImplementedError()
    
    @overload
    def replace_color(self, old_color : aspose.psd.Color, old_color_diff : int, new_color : aspose.psd.Color) -> None:
        raise NotImplementedError()
    
    @overload
    def replace_non_transparent_colors(self, new_color_argb : int) -> None:
        '''Replaces all non-transparent colors with new color and preserves original alpha value to save smooth edges.
        Note: if you use it on images without transparency, all colors will be replaced with a single one.
        
        :param new_color_argb: New color ARGB value to replace non transparent colors with.'''
        raise NotImplementedError()
    
    @overload
    def replace_non_transparent_colors(self, new_color : aspose.psd.Color) -> None:
        raise NotImplementedError()
    
    def cache_data(self) -> None:
        '''Caches the data and ensures no additional data loading will be performed from the underlying :py:attr:`aspose.psd.DataStreamSupporter.data_stream_container`.'''
        raise NotImplementedError()
    
    @staticmethod
    def create(image_options : aspose.psd.ImageOptionsBase, width : int, height : int) -> aspose.psd.Image:
        '''Creates a new image using the specified create options.
        
        :param image_options: The image options.
        :param width: The width.
        :param height: The height.
        :returns: The newly created image.'''
        raise NotImplementedError()
    
    def can_save(self, options : aspose.psd.ImageOptionsBase) -> bool:
        '''Determines whether image can be saved to the specified file format represented by the passed save options.
        
        :param options: The save options to use.
        :returns: ``true`` if image can be saved to the specified file format represented by the passed save options; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def get_default_options(self, args : List[Any]) -> aspose.psd.ImageOptionsBase:
        '''Gets the default options.
        
        :param args: The arguments.
        :returns: Default options'''
        raise NotImplementedError()
    
    def get_original_options(self) -> aspose.psd.ImageOptionsBase:
        '''Gets the options based on the original file settings.
        This can be helpful to keep bit-depth and other parameters of the original image unchanged.
        For example, if we load a black-white PNG image with 1 bit per pixel and then save it using the
        :py:func:`aspose.psd.DataStreamSupporter.save` method, the output PNG image with 8-bit per pixel will be produced.
        To avoid it and save PNG image with 1-bit per pixel, use this method to get corresponding saving options and pass them
        to the :py:func:`aspose.psd.Image.save` method as the second parameter.
        
        :returns: The options based on the original file settings.'''
        raise NotImplementedError()
    
    def rotate_flip(self, rotate_flip_type : aspose.psd.RotateFlipType) -> None:
        '''Rotates, flips, or rotates and flips the image.
        
        :param rotate_flip_type: The rotate flip type.'''
        raise NotImplementedError()
    
    def set_palette(self, palette : aspose.psd.IColorPalette, update_colors : bool) -> None:
        '''Sets the image palette.
        
        :param palette: The palette to set.
        :param update_colors: if set to ``true`` colors will be updated according to the new palette; otherwise color indexes remain unchanged. Note that unchanged indexes may crash the image on loading if some indexes have no corresponding palette entries.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_proportional_width(width : int, height : int, new_height : int) -> int:
        '''Gets a proportional width.
        
        :param width: The width.
        :param height: The height.
        :param new_height: The new height.
        :returns: The proportional width.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_proportional_height(width : int, height : int, new_width : int) -> int:
        '''Gets a proportional height.
        
        :param width: The width.
        :param height: The height.
        :param new_width: The new width.
        :returns: The proportional height.'''
        raise NotImplementedError()
    
    def get_modify_date(self, use_default : bool) -> datetime:
        '''Gets the date and time the resource image was last modified.
        
        :param use_default: if set to ``true`` uses the information from FileInfo as default value.
        :returns: The date and time the resource image was last modified.'''
        raise NotImplementedError()
    
    def get_default_pixels(self, rectangle : aspose.psd.Rectangle, partial_pixel_loader : aspose.psd.IPartialArgb32PixelLoader) -> None:
        '''Gets the default pixels array using partial pixel loader.
        
        :param rectangle: The rectangle to get pixels for.
        :param partial_pixel_loader: The partial pixel loader.'''
        raise NotImplementedError()
    
    def get_default_argb_32_pixels(self, rectangle : aspose.psd.Rectangle) -> List[int]:
        '''Gets the default 32-bit ARGB pixels array.
        
        :param rectangle: The rectangle to get pixels for.
        :returns: The default pixels array.'''
        raise NotImplementedError()
    
    def get_argb_32_pixel(self, x : int, y : int) -> int:
        '''Gets an image 32-bit ARGB pixel.
        
        :param x: The pixel x location.
        :param y: The pixel y location.
        :returns: The 32-bit ARGB pixel for the specified location.'''
        raise NotImplementedError()
    
    def get_pixel(self, x : int, y : int) -> aspose.psd.Color:
        '''Gets an image pixel.
        Performance Warning: Avoid using this method to iterate over all image pixels as it can lead to significant performance issues.
        For more efficient pixel manipulation, use the `LoadArgb32Pixels` method to retrieve the entire pixel array simultaneously.
        
        :param x: The pixel x location.
        :param y: The pixel y location.
        :returns: The pixel color for the specified location.'''
        raise NotImplementedError()
    
    def set_argb_32_pixel(self, x : int, y : int, argb_32_color : int) -> None:
        '''Sets an image 32-bit ARGB pixel for the specified position.
        
        :param x: The pixel x location.
        :param y: The pixel y location.
        :param argb_32_color: The 32-bit ARGB pixel for the specified position.'''
        raise NotImplementedError()
    
    def set_pixel(self, x : int, y : int, color : aspose.psd.Color) -> None:
        '''Sets an image pixel for the specified position.
        
        :param x: The pixel x location.
        :param y: The pixel y location.
        :param color: The pixel color for the specified position.'''
        raise NotImplementedError()
    
    def read_scan_line(self, scan_line_index : int) -> List[aspose.psd.Color]:
        '''Reads the whole scan line by the specified scan line index.
        
        :param scan_line_index: Zero based index of the scan line.
        :returns: The scan line pixel color values array.'''
        raise NotImplementedError()
    
    def read_argb_32_scan_line(self, scan_line_index : int) -> List[int]:
        '''Reads the whole scan line by the specified scan line index.
        
        :param scan_line_index: Zero based index of the scan line.
        :returns: The scan line 32-bit ARGB color values array.'''
        raise NotImplementedError()
    
    def write_scan_line(self, scan_line_index : int, pixels : List[aspose.psd.Color]) -> None:
        '''Writes the whole scan line to the specified scan line index.
        
        :param scan_line_index: Zero based index of the scan line.
        :param pixels: The pixel colors array to write.'''
        raise NotImplementedError()
    
    def write_argb_32_scan_line(self, scan_line_index : int, argb_32_pixels : List[int]) -> None:
        '''Writes the whole scan line to the specified scan line index.
        
        :param scan_line_index: Zero based index of the scan line.
        :param argb_32_pixels: The 32-bit ARGB colors array to write.'''
        raise NotImplementedError()
    
    def load_partial_argb_32_pixels(self, rectangle : aspose.psd.Rectangle, partial_pixel_loader : aspose.psd.IPartialArgb32PixelLoader) -> None:
        '''Loads 32-bit ARGB pixels partially by packs.
        
        :param rectangle: The desired rectangle.
        :param partial_pixel_loader: The 32-bit ARGB pixel loader.'''
        raise NotImplementedError()
    
    def load_partial_pixels(self, desired_rectangle : aspose.psd.Rectangle, pixel_loader : aspose.psd.IPartialPixelLoader) -> None:
        '''Loads pixels partially by packs.
        
        :param desired_rectangle: The desired rectangle.
        :param pixel_loader: The pixel loader.'''
        raise NotImplementedError()
    
    def load_argb_32_pixels(self, rectangle : aspose.psd.Rectangle) -> List[int]:
        '''Loads 32-bit ARGB pixels.
        
        :param rectangle: The rectangle to load pixels from.
        :returns: The loaded 32-bit ARGB pixels array.'''
        raise NotImplementedError()
    
    def load_argb_64_pixels(self, rectangle : aspose.psd.Rectangle) -> List[int]:
        '''Loads 64-bit ARGB pixels.
        
        :param rectangle: The rectangle to load pixels from.
        :returns: The loaded 64-bit ARGB pixels array.'''
        raise NotImplementedError()
    
    def load_pixels(self, rectangle : aspose.psd.Rectangle) -> List[aspose.psd.Color]:
        '''Loads pixels.
        
        :param rectangle: The rectangle to load pixels from.
        :returns: The loaded pixels array.'''
        raise NotImplementedError()
    
    def load_cmyk_pixels(self, rectangle : aspose.psd.Rectangle) -> List[aspose.psd.CmykColor]:
        '''Loads pixels in CMYK format.
        This method is deprecated. Please use more effective the :py:func:`aspose.psd.RasterImage.load_cmyk_32_pixels` method.
        
        :param rectangle: The rectangle to load pixels from.
        :returns: The loaded CMYK pixels array.'''
        raise NotImplementedError()
    
    def load_cmyk_32_pixels(self, rectangle : aspose.psd.Rectangle) -> List[int]:
        '''Loads pixels in CMYK format.
        
        :param rectangle: The rectangle to load pixels from.
        :returns: The loaded CMYK pixels presentes as 32-bit inateger values.'''
        raise NotImplementedError()
    
    def save_raw_data(self, data : List[int], data_offset : int, rectangle : aspose.psd.Rectangle, raw_data_settings : aspose.psd.RawDataSettings) -> None:
        '''Saves the raw data.
        
        :param data: The raw data.
        :param data_offset: The starting raw data offset.
        :param rectangle: The raw data rectangle.
        :param raw_data_settings: The raw data settings the data is in.'''
        raise NotImplementedError()
    
    def save_argb_32_pixels(self, rectangle : aspose.psd.Rectangle, pixels : List[int]) -> None:
        '''Saves the 32-bit ARGB pixels.
        
        :param rectangle: The rectangle to save pixels to.
        :param pixels: The 32-bit ARGB pixels array.'''
        raise NotImplementedError()
    
    def save_pixels(self, rectangle : aspose.psd.Rectangle, pixels : List[aspose.psd.Color]) -> None:
        '''Saves the pixels.
        
        :param rectangle: The rectangle to save pixels to.
        :param pixels: The pixels array.'''
        raise NotImplementedError()
    
    def to_bitmap(self) -> Any:
        raise NotImplementedError()
    
    def save_cmyk_pixels(self, rectangle : aspose.psd.Rectangle, pixels : List[aspose.psd.CmykColor]) -> None:
        raise NotImplementedError()
    
    def save_cmyk_32_pixels(self, rectangle : aspose.psd.Rectangle, pixels : List[int]) -> None:
        raise NotImplementedError()
    
    def set_resolution(self, dpi_x : float, dpi_y : float) -> None:
        '''Sets the resolution for this :py:class:`aspose.psd.fileformats.psd.PsdImage`.
        
        :param dpi_x: The horizontal resolution, in dots per inch, of the :py:class:`aspose.psd.RasterImage`.
        :param dpi_y: The vertical resolution, in dots per inch, of the :py:class:`aspose.psd.RasterImage`.'''
        raise NotImplementedError()
    
    def binarize_fixed(self, threshold : int) -> None:
        '''Binarization of an image with predefined threshold
        
        :param threshold: Threshold value. If corresponding gray value of a pixel is greater than threshold, a value of 255 will be assigned to it, 0 otherwise.'''
        raise NotImplementedError()
    
    def binarize_otsu(self) -> None:
        '''Binarization of an image with Otsu thresholding'''
        raise NotImplementedError()
    
    def grayscale(self) -> None:
        '''Transformation of an image to its grayscale representation'''
        raise NotImplementedError()
    
    def adjust_brightness(self, brightness : int) -> None:
        '''Adjust of a brightness for image.
        
        :param brightness: Brightness value.'''
        raise NotImplementedError()
    
    def adjust_contrast(self, contrast : float) -> None:
        '''Image contrasting
        
        :param contrast: Contrast value (in range [-100; 100])'''
        raise NotImplementedError()
    
    def get_skew_angle(self) -> float:
        raise NotImplementedError()
    
    def filter(self, rectangle : aspose.psd.Rectangle, options : aspose.psd.imagefilters.filteroptions.FilterOptionsBase) -> None:
        '''Filters the specified rectangle.
        
        :param rectangle: The rectangle.
        :param options: The options.'''
        raise NotImplementedError()
    
    def add_layer(self, layer : aspose.psd.fileformats.psd.layers.Layer) -> None:
        '''Adds the layer.
        
        :param layer: The layer.'''
        raise NotImplementedError()
    
    def merge_layers(self, bottom_layer : aspose.psd.fileformats.psd.layers.Layer, top_layer : aspose.psd.fileformats.psd.layers.Layer) -> aspose.psd.fileformats.psd.layers.Layer:
        '''Merges the layers.
        
        :param bottom_layer: The bottom layer.
        :param top_layer: The top layer.
        :returns: Bottom layer after the merge'''
        raise NotImplementedError()
    
    def flatten_image(self) -> None:
        '''Flattens all layers.'''
        raise NotImplementedError()
    
    def add_regular_layer(self) -> aspose.psd.fileformats.psd.layers.Layer:
        '''Adds a new regular layer.
        
        :returns: Created regular layer.'''
        raise NotImplementedError()
    
    def add_text_layer(self, text : str, rect : aspose.psd.Rectangle) -> aspose.psd.fileformats.psd.layers.TextLayer:
        '''Adds a new Text layer.
        
        :param text: The layer\'s text.
        :param rect: The layer\'s rectangle.
        :returns: Created text layer.'''
        raise NotImplementedError()
    
    def add_shape_layer(self) -> aspose.psd.fileformats.psd.layers.ShapeLayer:
        '''Add empty Shape layer.
        Without paths. They should be added to shape layer before save.
        
        :returns: ShapeLayer instance.'''
        raise NotImplementedError()
    
    def add_curves_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.CurvesLayer:
        '''Adds the Curves Adjustment layer.
        
        :returns: Created :py:class:`aspose.psd.fileformats.psd.layers.adjustmentlayers.CurvesLayer` Layer'''
        raise NotImplementedError()
    
    def add_exposure_adjustment_layer(self, exposure : float, offset : float, gamma_correction : float) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.ExposureLayer:
        '''Adds the exposure adjustment layer.
        
        :param exposure: The exposure.
        :param offset: The offset.
        :param gamma_correction: The gamma correction.
        :returns: Created Exposure Adjustment Layer'''
        raise NotImplementedError()
    
    def add_hue_saturation_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.HueSaturationLayer:
        '''Adds the hue/saturation adjustment layer.
        
        :returns: A newly created hue/saturation layer.'''
        raise NotImplementedError()
    
    def add_vibrance_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.VibranceLayer:
        '''Adds the Vibrance adjustment layer.
        
        :returns: A newly created Vibrance layer.'''
        raise NotImplementedError()
    
    def add_color_balance_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.ColorBalanceAdjustmentLayer:
        '''Adds the color balance adjustment layer.
        
        :returns: A newly created color balance layer.'''
        raise NotImplementedError()
    
    def add_levels_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.LevelsLayer:
        '''Adds the Levels adjustment layer.
        
        :returns: A newly created Levels layer'''
        raise NotImplementedError()
    
    def add_photo_filter_layer(self, color : aspose.psd.Color) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.PhotoFilterLayer:
        '''Adds the PhotoFilter layer.
        
        :param color: The color.
        :returns: Created PhotoFilter Layer'''
        raise NotImplementedError()
    
    def add_channel_mixer_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.ChannelMixerLayer:
        '''Adds the channel mixer adjustment layer with default parameters
        
        :returns: Added Channel Mixer Layer'''
        raise NotImplementedError()
    
    def add_brightness_contrast_adjustment_layer(self, brightness : int, contrast : int) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.BrightnessContrastLayer:
        '''Adds the brightness/contrast adjustment layer.
        
        :param brightness: The brightness.
        :param contrast: The contrast.
        :returns: Created brightness/contrast layer'''
        raise NotImplementedError()
    
    def add_invert_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.InvertAdjustmentLayer:
        '''Adds an invert adjustment layer.
        
        :returns: The created invert layer'''
        raise NotImplementedError()
    
    def add_black_white_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.BlackWhiteAdjustmentLayer:
        '''Adds the black white adjustment layer.
        
        :returns: The created black white adjustment layer.'''
        raise NotImplementedError()
    
    def add_selective_color_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.SelectiveColorLayer:
        '''Adds the selective color adjustment layer.
        
        :returns: The created selective color adjustment layer.'''
        raise NotImplementedError()
    
    def add_threshold_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.ThresholdLayer:
        '''Adds the Threshold adjustment layer.
        
        :returns: The created Threshold adjustment layer.'''
        raise NotImplementedError()
    
    def add_posterize_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.PosterizeLayer:
        '''Adds Posterize Adjustment layer.
        
        :returns: PosterizeLayer instance.'''
        raise NotImplementedError()
    
    def add_gradient_map_adjustment_layer(self) -> aspose.psd.fileformats.psd.layers.adjustmentlayers.GradientMapLayer:
        '''Adds GradientMap Adjustment layer.
        
        :returns: GradientMap instance.'''
        raise NotImplementedError()
    
    def add_layer_group(self, group_name : str, index : int, start_behaviour : bool) -> aspose.psd.fileformats.psd.layers.LayerGroup:
        '''Adds the layer group.
        
        :param group_name: Name of the group.
        :param index: The index of the layer to insert after.
        :param start_behaviour: if set to ``true`` [start behaviour] than group will be in open state on start up, otherwise in minimized state.
        :returns: Opening group layer'''
        raise NotImplementedError()
    
    def convert(self, new_options : aspose.psd.imageoptions.PsdOptions) -> None:
        '''Converts this image format to the one specified in options.
        
        :param new_options: The new options.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def data_stream_container(self) -> aspose.psd.StreamContainer:
        '''Gets the object\'s data stream.'''
        raise NotImplementedError()
    
    @property
    def is_cached(self) -> bool:
        '''Gets a value indicating whether image data is cached currently.'''
        raise NotImplementedError()
    
    @property
    def bits_per_pixel(self) -> int:
        '''Gets the image bits per pixel count.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.Rectangle:
        '''Gets the image bounds.'''
        raise NotImplementedError()
    
    @property
    def container(self) -> aspose.psd.Image:
        '''Gets the :py:class:`aspose.psd.Image` container.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Gets the image height.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette. The color palette is not used when pixels are represented directly.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette. The color palette is not used when pixels are represented directly.'''
        raise NotImplementedError()
    
    @property
    def use_palette(self) -> bool:
        '''Gets a value indicating whether the image palette is used.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> aspose.psd.Size:
        '''Gets the image size.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Gets the image width.'''
        raise NotImplementedError()
    
    @property
    def interrupt_monitor(self) -> aspose.psd.multithreading.InterruptMonitor:
        '''Gets the interrupt monitor.'''
        raise NotImplementedError()
    
    @interrupt_monitor.setter
    def interrupt_monitor(self, value : aspose.psd.multithreading.InterruptMonitor) -> None:
        '''Sets the interrupt monitor.'''
        raise NotImplementedError()
    
    @property
    def buffer_size_hint(self) -> int:
        '''Gets the buffer size hint which is defined max allowed size for all internal buffers.'''
        raise NotImplementedError()
    
    @buffer_size_hint.setter
    def buffer_size_hint(self, value : int) -> None:
        '''Sets the buffer size hint which is defined max allowed size for all internal buffers.'''
        raise NotImplementedError()
    
    @property
    def auto_adjust_palette(self) -> bool:
        '''Gets a value indicating whether automatic adjust palette.'''
        raise NotImplementedError()
    
    @auto_adjust_palette.setter
    def auto_adjust_palette(self, value : bool) -> None:
        '''Sets a value indicating whether automatic adjust palette.'''
        raise NotImplementedError()
    
    @property
    def has_background_color(self) -> bool:
        '''Gets a value indicating whether image has background color.'''
        raise NotImplementedError()
    
    @has_background_color.setter
    def has_background_color(self, value : bool) -> None:
        '''Sets a value indicating whether image has background color.'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> aspose.psd.FileFormat:
        '''Gets a value of file format'''
        raise NotImplementedError()
    
    @property
    def background_color(self) -> aspose.psd.Color:
        '''Gets a value for the background color.'''
        raise NotImplementedError()
    
    @background_color.setter
    def background_color(self, value : aspose.psd.Color) -> None:
        '''Sets a value for the background color.'''
        raise NotImplementedError()
    
    @property
    def premultiply_components(self) -> bool:
        '''Gets a value indicating whether the image components must be premultiplied.'''
        raise NotImplementedError()
    
    @premultiply_components.setter
    def premultiply_components(self, value : bool) -> None:
        '''Sets a value indicating whether the image components must be premultiplied.'''
        raise NotImplementedError()
    
    @property
    def use_raw_data(self) -> bool:
        '''Gets a value indicating whether to use raw data loading when the raw data loading is available.'''
        raise NotImplementedError()
    
    @use_raw_data.setter
    def use_raw_data(self, value : bool) -> None:
        '''Sets a value indicating whether to use raw data loading when the raw data loading is available.'''
        raise NotImplementedError()
    
    @property
    def update_xmp_data(self) -> bool:
        '''Gets a value indicating whether to update the XMP metadata.'''
        raise NotImplementedError()
    
    @update_xmp_data.setter
    def update_xmp_data(self, value : bool) -> None:
        '''Sets a value indicating whether to update the XMP metadata.'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Gets the XMP metadata.'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Sets the XMP metadata.'''
        raise NotImplementedError()
    
    @property
    def raw_indexed_color_converter(self) -> aspose.psd.IIndexedColorConverter:
        '''Gets the indexed color converter'''
        raise NotImplementedError()
    
    @raw_indexed_color_converter.setter
    def raw_indexed_color_converter(self, value : aspose.psd.IIndexedColorConverter) -> None:
        '''Sets the indexed color converter'''
        raise NotImplementedError()
    
    @property
    def raw_custom_color_converter(self) -> aspose.psd.IColorConverter:
        '''Gets the custom color converter'''
        raise NotImplementedError()
    
    @raw_custom_color_converter.setter
    def raw_custom_color_converter(self, value : aspose.psd.IColorConverter) -> None:
        '''Sets the custom color converter'''
        raise NotImplementedError()
    
    @property
    def raw_fallback_index(self) -> int:
        '''Gets the fallback index to use when palette index is out of bounds'''
        raise NotImplementedError()
    
    @raw_fallback_index.setter
    def raw_fallback_index(self, value : int) -> None:
        '''Sets the fallback index to use when palette index is out of bounds'''
        raise NotImplementedError()
    
    @property
    def raw_data_settings(self) -> aspose.psd.RawDataSettings:
        '''Gets the current raw data settings. Note when using these settings the data loads without conversion.'''
        raise NotImplementedError()
    
    @property
    def raw_data_format(self) -> aspose.psd.PixelDataFormat:
        '''Gets the raw data format.'''
        raise NotImplementedError()
    
    @property
    def raw_line_size(self) -> int:
        '''Gets the raw line size in bytes.'''
        raise NotImplementedError()
    
    @property
    def is_raw_data_available(self) -> bool:
        '''Gets a value indicating whether raw data loading is available.'''
        raise NotImplementedError()
    
    @property
    def horizontal_resolution(self) -> float:
        '''Gets the horizontal resolution, in pixels per inch, of this :py:class:`aspose.psd.fileformats.psd.PsdImage`.'''
        raise NotImplementedError()
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : float) -> None:
        '''Sets the horizontal resolution, in pixels per inch, of this :py:class:`aspose.psd.fileformats.psd.PsdImage`.'''
        raise NotImplementedError()
    
    @property
    def vertical_resolution(self) -> float:
        '''Gets the vertical resolution, in pixels per inch, of this :py:class:`aspose.psd.fileformats.psd.PsdImage`.'''
        raise NotImplementedError()
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : float) -> None:
        '''Sets the vertical resolution, in pixels per inch, of this :py:class:`aspose.psd.fileformats.psd.PsdImage`.'''
        raise NotImplementedError()
    
    @property
    def has_transparent_color(self) -> bool:
        '''Gets a value indicating whether image has transparent color.'''
        raise NotImplementedError()
    
    @has_transparent_color.setter
    def has_transparent_color(self, value : bool) -> None:
        '''Gets a value indicating whether image has transparent color.'''
        raise NotImplementedError()
    
    @property
    def has_alpha(self) -> bool:
        '''Gets the vertical resolution, in pixels per inch, of this :py:class:`aspose.psd.RasterImage`.'''
        raise NotImplementedError()
    
    @property
    def transparent_color(self) -> aspose.psd.Color:
        '''Gets the image transparent color.'''
        raise NotImplementedError()
    
    @transparent_color.setter
    def transparent_color(self, value : aspose.psd.Color) -> None:
        '''Gets the image transparent color.'''
        raise NotImplementedError()
    
    @property
    def image_opacity(self) -> float:
        '''Gets opacity of this image.'''
        raise NotImplementedError()
    
    @property
    def rgb_color_profile(self) -> aspose.psd.sources.StreamSource:
        '''Gets the RGB color profile for CMYK PSD images. Must be in pair with CmykColorProfile for correct color conversion.'''
        raise NotImplementedError()
    
    @rgb_color_profile.setter
    def rgb_color_profile(self, value : aspose.psd.sources.StreamSource) -> None:
        '''Sets the RGB color profile for CMYK PSD images. Must be in pair with CmykColorProfile for correct color conversion.'''
        raise NotImplementedError()
    
    @property
    def cmyk_color_profile(self) -> aspose.psd.sources.StreamSource:
        '''Gets the CMYK color profile for CMYK PSD images. Must be in pair with RgbColorProfile for correct color conversion.'''
        raise NotImplementedError()
    
    @cmyk_color_profile.setter
    def cmyk_color_profile(self, value : aspose.psd.sources.StreamSource) -> None:
        '''Sets the CMYK color profile for CMYK PSD images. Must be in pair with RgbColorProfile for correct color conversion.'''
        raise NotImplementedError()
    
    @property
    def gray_color_profile(self) -> aspose.psd.sources.StreamSource:
        '''Gets the GRAY (monochrome) color profile for Grayscale PSD images.'''
        raise NotImplementedError()
    
    @gray_color_profile.setter
    def gray_color_profile(self, value : aspose.psd.sources.StreamSource) -> None:
        '''Sets the GRAY (monochrome) color profile for Grayscale PSD images.'''
        raise NotImplementedError()
    
    @property
    def color_mode(self) -> aspose.psd.fileformats.psd.ColorModes:
        '''Gets the color mode.'''
        raise NotImplementedError()
    
    @color_mode.setter
    def color_mode(self, value : aspose.psd.fileformats.psd.ColorModes) -> None:
        '''Sets the color mode.'''
        raise NotImplementedError()
    
    @property
    def compression(self) -> aspose.psd.fileformats.psd.CompressionMethod:
        '''Gets the compression method.'''
        raise NotImplementedError()
    
    @property
    def channels_count(self) -> int:
        '''Gets the PSD channels count.'''
        raise NotImplementedError()
    
    @property
    def bits_per_channel(self) -> int:
        '''Gets the bits per channel.'''
        raise NotImplementedError()
    
    @property
    def image_resources(self) -> List[aspose.psd.fileformats.psd.ResourceBlock]:
        '''Gets the PSD image resources.'''
        raise NotImplementedError()
    
    @image_resources.setter
    def image_resources(self, value : List[aspose.psd.fileformats.psd.ResourceBlock]) -> None:
        '''Sets the PSD image resources.'''
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
    def layers(self) -> List[aspose.psd.fileformats.psd.layers.Layer]:
        '''Gets the PSD layers.'''
        raise NotImplementedError()
    
    @layers.setter
    def layers(self, value : List[aspose.psd.fileformats.psd.layers.Layer]) -> None:
        '''Sets the PSD layers.'''
        raise NotImplementedError()
    
    @property
    def global_layer_resources(self) -> List[aspose.psd.fileformats.psd.layers.LayerResource]:
        '''Gets the global layer resources.'''
        raise NotImplementedError()
    
    @global_layer_resources.setter
    def global_layer_resources(self, value : List[aspose.psd.fileformats.psd.layers.LayerResource]) -> None:
        '''Sets the global layer resources.'''
        raise NotImplementedError()
    
    @property
    def global_layer_mask_info(self) -> aspose.psd.fileformats.psd.layers.GlobalLayerMaskInfo:
        '''Gets the global layer mask info.'''
        raise NotImplementedError()
    
    @property
    def has_transparency_data(self) -> bool:
        '''Gets a value indicating whether first alpha channel contains the transparency data for the merged result when specifying layers data.'''
        raise NotImplementedError()
    
    @has_transparency_data.setter
    def has_transparency_data(self, value : bool) -> None:
        '''Sets a value indicating whether first alpha channel contains the transparency data for the merged result when specifying layers data.'''
        raise NotImplementedError()
    
    @property
    def active_layer(self) -> aspose.psd.fileformats.psd.layers.Layer:
        '''Gets the active layer.'''
        raise NotImplementedError()
    
    @active_layer.setter
    def active_layer(self, value : aspose.psd.fileformats.psd.layers.Layer) -> None:
        '''Sets the active layer.'''
        raise NotImplementedError()
    
    @property
    def is_flatten(self) -> bool:
        '''Gets a value indicating whether psd image is flattened.'''
        raise NotImplementedError()
    
    @property
    def global_angle(self) -> int:
        '''Gets the global angle.'''
        raise NotImplementedError()
    
    @global_angle.setter
    def global_angle(self, value : int) -> None:
        '''Sets the global angle.'''
        raise NotImplementedError()
    
    @property
    def linked_layers_manager(self) -> aspose.psd.fileformats.psd.layers.LinkedLayersManager:
        '''Gets the linked layers manager.'''
        raise NotImplementedError()
    
    @property
    def smart_object_provider(self) -> aspose.psd.fileformats.psd.SmartObjectProvider:
        '''Gets the smart object provider.'''
        raise NotImplementedError()
    
    @property
    def timeline(self) -> aspose.psd.fileformats.psd.layers.animation.Timeline:
        '''Gets the :py:attr:`aspose.psd.fileformats.psd.PsdImage.timeline` of this :py:class:`aspose.psd.fileformats.psd.PsdImage`.'''
        raise NotImplementedError()
    
    @property
    def DEFAULT_VERSION(self) -> int:
        '''The default PSD version.'''
        raise NotImplementedError()


class ResourceBlock:
    '''The resource block.'''
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()


class SmartObjectProvider:
    '''Defines the smart object provider that provides getting / setting data sources from global link resources of the PSD file and their contents.'''
    
    @overload
    def convert_to_smart_object(self, layer_numbers : List[int]) -> aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer:
        '''Converts layers to an embedded smart object.
        
        :param layer_numbers: The layer numbers.
        :returns: The created :py:class:`aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer` instance.'''
        raise NotImplementedError()
    
    @overload
    def convert_to_smart_object(self, layers : List[aspose.psd.fileformats.psd.layers.Layer]) -> aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer:
        '''Converts layers to an embedded smart object.
        
        :param layers: The layers.
        :returns: The created :py:class:`aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer` instance.'''
        raise NotImplementedError()
    
    def embed_all_linked(self) -> None:
        '''Embeds all linked smart objects in the image.'''
        raise NotImplementedError()
    
    def update_all_modified_content(self) -> None:
        '''Updates the content of all modified smart objects in the image.'''
        raise NotImplementedError()
    
    def new_smart_object_via_copy(self, source_layer : aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer) -> aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer:
        '''Creates a new smart object layer by coping the source one.
        
        :param source_layer: The source layer.
        :returns: The cloned :py:class:`aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer` instance.'''
        raise NotImplementedError()
    

class AutoKerning:
    '''The Photoshop auto kerning mode (distance between symbols).'''
    
    MANUAL : AutoKerning
    '''Manual kerning value.'''
    METRIC : AutoKerning
    '''Metrics kerning uses kern pairs, which are included with most fonts (from their designers).'''
    OPTICAL : AutoKerning
    '''Optical kerning adjusts the spacing between adjacent characters based on their shapes.'''

class ColorModes:
    '''Represents the psd file format color modes.'''
    
    BITMAP : ColorModes
    '''The bitmap color mode.'''
    GRAYSCALE : ColorModes
    '''The grayscale mode.'''
    INDEXED : ColorModes
    '''Indexed color mode.'''
    RGB : ColorModes
    '''RGB color mode.'''
    CMYK : ColorModes
    '''CMYK color mode.'''
    MULTICHANNEL : ColorModes
    '''Multichannel color mode.'''
    DUOTONE : ColorModes
    '''Duotone color mode.'''
    LAB : ColorModes
    '''Lab color mode.'''

class CompressionMethod:
    '''Defines the compression method used for image data.'''
    
    RAW : CompressionMethod
    '''No compression. The image data stored as raw bytes in RGBA planar order.
    That means that first all R data is written, then all G is written, then all B and finally all A data is written.'''
    RLE : CompressionMethod
    '''RLE compressed the image data starts with the byte counts for all the scan lines (rows * channels), with each
    count stored as a two-byte value. The RLE compressed data follows, with each scan line compressed separately.
    The RLE compression is the same compression algorithm used by the Macintosh ROM routine PackBits and the TIFF standard.'''
    ZIP_WITHOUT_PREDICTION : CompressionMethod
    '''ZIP without prediction.'''
    ZIP_WITH_PREDICTION : CompressionMethod
    '''ZIP with prediction.'''

class FontBaseline:
    '''This is the font baseline.'''
    
    NONE : FontBaseline
    '''No baseline value'''
    SUPERSCRIPT : FontBaseline
    '''Superscript baseline.'''
    SUBSCRIPT : FontBaseline
    '''Subscript baseline.'''

class FontCaps:
    '''This is the font baseline.'''
    
    NONE : FontCaps
    '''No font caps value.'''
    SMALL_CAPS : FontCaps
    '''The small caps.'''
    ALL_CAPS : FontCaps
    '''The all caps.'''

class JustificationMode:
    '''The text alignment mode.'''
    
    LEFT : JustificationMode
    '''The left align text.
    In a left-to-right mode, the Left position is Left.
    In a right-to-left mode, the Left position is Right.'''
    RIGHT : JustificationMode
    '''The right align text.
    In a left-to-right mode, the Right position is Right.
    In a right-to-left mode, the Right position is Left.'''
    CENTER : JustificationMode
    '''The center text.'''

class LeadingType:
    '''Photoshop leading type (type of distance between lines).'''
    
    BOTTOM_TO_BOTTOM : LeadingType
    '''The bottom-to-bottom leading.'''
    TOP_TO_TOP : LeadingType
    '''The top-to-top leading.'''

class PsdVersion:
    '''File format version'''
    
    PSD : PsdVersion
    '''The default PSD version.'''
    PSB : PsdVersion
    '''The PSB version.'''

class TextOrientation:
    '''Enumeration for text orientation mode.'''
    
    HORIZONTAL : TextOrientation
    '''The horizontal text orientation.'''
    VERTICAL : TextOrientation
    '''The vertical text orientation.'''

