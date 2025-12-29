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

class SmartObjectLayer(aspose.psd.fileformats.psd.layers.Layer):
    '''Defines the SmartObjectLayer class that contains embedded in the PSD file or linked smart object in the external file.
    With Smart Objects, you can:
    Perform nondestructive transforms. You can scale, rotate, skew, distort, perspective transform, or warp a layer
    without losing original image data or quality because the transforms don�t affect the original data.
    Work with vector data, such as vector artwork from Illustrator, that otherwise would be rasterized.
    Perform nondestructive filtering. You can edit filters applied to Smart Objects at any time.
    Edit one Smart Object and automatically update all its linked instances.
    Apply a layer mask that�s either linked or unlinked to the Smart Object layer.
    Try various designs with low-resolution placeholder images that you later replace with final versions.
    In Adobe� Photoshop�, you can embed the contents of an image into a PSD document.
    More information is here: :link:`https://helpx.adobe.com/photoshop/using/create-smart-objects.html`
    A layer with an embedded smart object contains placed (PlLd) and SoLd resources with smart object properties.
    The PlLd resource can be alone for PSD versions older then 10.
    These resources contain UniqueId of the LiFdDataSource in the global Lnk2Resource with the embedded filename
    and other parameters, including the embedded file contents in the original format as a byte array.'''
    
    def __init__(self, stream : io._IOBase) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer` class.
        
        :param stream: The stream of items'''
        raise NotImplementedError()
    
    @overload
    def save(self, stream : io._IOBase) -> None:
        '''Saves the object\'s data to the specified stream.
        
        :param stream: The stream to save the object\'s data to.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str, options : aspose.psd.ImageOptionsBase) -> None:
        '''Saves the object\'s data to the specified file location in the specified file format according to save options.
        
        :param file_path: The file path.
        :param options: The options.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str, over_write : bool) -> None:
        '''Saves the object\'s data to the specified file location.
        
        :param file_path: The file path to save the object\'s data to.
        :param over_write: if set to ``true`` over write the file contents, otherwise append will occur.'''
        raise NotImplementedError()
    
    @overload
    def save(self, stream : io._IOBase, options_base : aspose.psd.ImageOptionsBase, bounds_rectangle : aspose.psd.Rectangle) -> None:
        '''Saves the image\'s data to the specified stream in the specified file format according to save options.
        
        :param stream: The stream to save the image\'s data to.
        :param options_base: The save options.
        :param bounds_rectangle: The destination image bounds rectangle. Set the empty rectangle for use source bounds.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str, options : aspose.psd.ImageOptionsBase, bounds_rectangle : aspose.psd.Rectangle) -> None:
        '''Saves the object\'s data to the specified file location in the specified file format according to save options.
        
        :param file_path: The file path.
        :param options: The options.
        :param bounds_rectangle: The destination image bounds rectangle. Set the empty rectangle for use source bounds.'''
        raise NotImplementedError()
    
    @overload
    def save(self) -> None:
        '''Saves the image data to the underlying stream.'''
        raise NotImplementedError()
    
    @overload
    def save(self, stream : io._IOBase, options_base : aspose.psd.ImageOptionsBase) -> None:
        '''Saves the image\'s data to the specified stream in the specified file format according to save options.
        
        :param stream: The stream to save the image\'s data to.
        :param options_base: The save options.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str) -> None:
        '''Saves the object\'s data to the specified file location.
        
        :param file_path: The file path to save the object\'s data to.'''
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
    def resize_width_proportionally(self, new_width : int) -> None:
        '''Resizes the width proportionally. The default :py:attr:`aspose.psd.ResizeType.NEAREST_NEIGHBOUR_RESAMPLE` is used.
        
        :param new_width: The new width.'''
        raise NotImplementedError()
    
    @overload
    def resize_width_proportionally(self, new_width : int, resize_type : aspose.psd.ResizeType) -> None:
        '''Resizes the width proportionally.
        
        :param new_width: The new width.
        :param resize_type: Type of the resize.'''
        raise NotImplementedError()
    
    @overload
    def resize_width_proportionally(self, new_width : int, settings : aspose.psd.ImageResizeSettings) -> None:
        '''Resizes the width proportionally.
        
        :param new_width: The new width.
        :param settings: The image resize settings.'''
        raise NotImplementedError()
    
    @overload
    def resize_height_proportionally(self, new_height : int) -> None:
        '''Resizes the height proportionally.
        
        :param new_height: The new height.'''
        raise NotImplementedError()
    
    @overload
    def resize_height_proportionally(self, new_height : int, resize_type : aspose.psd.ResizeType) -> None:
        '''Resizes the height proportionally.
        
        :param new_height: The new height.
        :param resize_type: Type of the resize.'''
        raise NotImplementedError()
    
    @overload
    def resize_height_proportionally(self, new_height : int, settings : aspose.psd.ImageResizeSettings) -> None:
        '''Resizes the height proportionally.
        
        :param new_height: The new height.
        :param settings: The image resize settings.'''
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
    def adjust_gamma(self, gamma_red : float, gamma_green : float, gamma_blue : float) -> None:
        '''Gamma-correction of an image.
        
        :param gamma_red: Gamma for red channel coefficient
        :param gamma_green: Gamma for green channel coefficient
        :param gamma_blue: Gamma for blue channel coefficient'''
        raise NotImplementedError()
    
    @overload
    def adjust_gamma(self, gamma : float) -> None:
        '''Gamma-correction of an image.
        
        :param gamma: Gamma for red, green and blue channels coefficient'''
        raise NotImplementedError()
    
    @overload
    def rotate(self, angle : float, resize_proportionally : bool, background_color : aspose.psd.Color) -> None:
        '''Rotate image around the center.
        
        :param angle: The rotate angle in degrees. Positive values will rotate clockwise.
        :param resize_proportionally: if set to ``true`` you will have your image size changed according to rotated rectangle (corner points) projections in other case that leaves dimensions untouched and only internal image contents are rotated.
        :param background_color: Color of the background.'''
        raise NotImplementedError()
    
    @overload
    def rotate(self, angle : float) -> None:
        raise NotImplementedError()
    
    @overload
    def normalize_angle(self) -> None:
        raise NotImplementedError()
    
    @overload
    def normalize_angle(self, resize_proportionally : bool, background_color : aspose.psd.Color) -> None:
        raise NotImplementedError()
    
    @overload
    def replace_color(self, old_color : aspose.psd.Color, old_color_diff : int, new_color : aspose.psd.Color) -> None:
        raise NotImplementedError()
    
    @overload
    def replace_color(self, old_color_argb : int, old_color_diff : int, new_color_argb : int) -> None:
        raise NotImplementedError()
    
    @overload
    def replace_non_transparent_colors(self, new_color : aspose.psd.Color) -> None:
        raise NotImplementedError()
    
    @overload
    def replace_non_transparent_colors(self, new_color_argb : int) -> None:
        raise NotImplementedError()
    
    @overload
    def replace_contents(self, image : aspose.psd.Image) -> None:
        '''Replaces the smart object contents embedded in the smart object layer.
        
        :param image: The image.'''
        raise NotImplementedError()
    
    @overload
    def replace_contents(self, image : aspose.psd.Image, resolution : aspose.psd.ResolutionSetting) -> None:
        '''Replaces the smart object contents embedded in the smart object layer.
        
        :param image: The image.
        :param resolution: The resolution settings. If null the image resolution will be used.'''
        raise NotImplementedError()
    
    @overload
    def replace_contents(self, linked_path : str, resolution : aspose.psd.ResolutionSetting) -> None:
        '''Replaces the contents with a file.
        There is no need to call UpdateModifiedContent method afterwards.
        
        :param linked_path: The linked path.
        :param resolution: The resolution settings. If null the image resolution will be used.'''
        raise NotImplementedError()
    
    @overload
    def replace_contents(self, linked_path : str, resolution : aspose.psd.ResolutionSetting, is_replace_only_this : bool) -> None:
        '''Replaces the contents with a file.
        There is no need to call UpdateModifiedContent method afterwards.
        
        :param linked_path: The linked path.
        :param resolution: The resolution settings. If null the image resolution will be used.
        :param is_replace_only_this: The flag shows replace content from this Smart Layer or to all Smart Layers with this content'''
        raise NotImplementedError()
    
    @overload
    def replace_contents(self, linked_path : str) -> None:
        '''Replaces the contents with a file.
        There is no need to call UpdateModifiedContent method afterwards.
        
        :param linked_path: The linked path.'''
        raise NotImplementedError()
    
    @overload
    def replace_contents(self, linked_path : str, is_replace_only_this : bool) -> None:
        '''Replaces the contents with a file.
        There is no need to call UpdateModifiedContent method afterwards.
        
        :param linked_path: The linked path.
        :param is_replace_only_this: The flag shows replace content from this Smart Layer or to all Smart Layers with this content'''
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
        raise NotImplementedError()
    
    def shallow_copy(self) -> aspose.psd.fileformats.psd.layers.Layer:
        '''Creates a shallow copy of the current Layer.
        Please :link:`https://msdn.microsoft.com/ru-ru/library/system.object.memberwiseclone(v=vs.110).aspx` for explanation.
        
        :returns: A shallow copy of the current Layer.'''
        raise NotImplementedError()
    
    def add_layer_mask(self, layer_mask : aspose.psd.fileformats.psd.layers.LayerMaskData) -> None:
        '''Adds the mask to current layer.
        
        :param layer_mask: The layer mask.'''
        raise NotImplementedError()
    
    def apply_layer_mask(self) -> None:
        '''Applies the layer mask to layer, then deletes the mask.'''
        raise NotImplementedError()
    
    def merge_layer_to(self, layer_to_merge_into : aspose.psd.fileformats.psd.layers.Layer) -> None:
        '''Merges the layer to specified layer
        
        :param layer_to_merge_into: The layer to merge into.'''
        raise NotImplementedError()
    
    def draw_image(self, location : aspose.psd.Point, image : aspose.psd.RasterImage) -> None:
        '''Draws the image on layer.
        
        :param location: The location.
        :param image: The image.'''
        raise NotImplementedError()
    
    def export_contents(self, file_path : str) -> None:
        '''Exports the embedded or linked contents to a file.
        
        :param file_path: The export file path.'''
        raise NotImplementedError()
    
    def load_contents(self, options : aspose.psd.LoadOptions) -> aspose.psd.Image:
        '''Gets the embedded or linked image contents of the smart object layer.
        
        :param options: The options.
        :returns: The loaded :py:class:`aspose.psd.Image` smart object instance.'''
        raise NotImplementedError()
    
    def embed_linked(self) -> None:
        '''Embeds the linked smart object in this layer.'''
        raise NotImplementedError()
    
    def convert_to_linked(self, linked_path : str) -> None:
        '''Converts this embedded smart object to a linked smart object.
        
        :param linked_path: The linked path.'''
        raise NotImplementedError()
    
    def relink_to_file(self, linked_path : str) -> None:
        '''Re-links the linked smart object to a new file.
        There is no need to call UpdateModifiedContent method afterwards.
        
        :param linked_path: The linked path.'''
        raise NotImplementedError()
    
    def update_modified_content(self) -> None:
        '''Updates the smart object layer image cache with the modified content.'''
        raise NotImplementedError()
    
    def new_smart_object_via_copy(self) -> aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer:
        '''Creates a new smart object layer by coping this one.
        Reproduces `Layer -> Smart Objects -> New Smart Object via Copy` functionality of Adobe� Photoshop�.
        Notice that it is enabled only for embedded smart objects because the embedded image is also copied.
        If you want to share the embedded image use :py:func:`aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer.duplicate_layer` method.
        
        :returns: The cloned :py:class:`aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer` instance.'''
        raise NotImplementedError()
    
    def duplicate_layer(self) -> aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer:
        '''Creates a new smart object layer by coping this one.
        Notice that for embedded smart objects the embedded image is shared.
        If you want to copy the embedded image use :py:func:`aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer.new_smart_object_via_copy` method.
        
        :returns: The cloned :py:class:`aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer` instance.'''
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
        '''Gets the horizontal resolution, in pixels per inch, of this :py:class:`aspose.psd.RasterImage`.'''
        raise NotImplementedError()
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : float) -> None:
        '''Sets the horizontal resolution, in pixels per inch, of this :py:class:`aspose.psd.RasterImage`.'''
        raise NotImplementedError()
    
    @property
    def vertical_resolution(self) -> float:
        '''Gets the vertical resolution, in pixels per inch, of this :py:class:`aspose.psd.RasterImage`.'''
        raise NotImplementedError()
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : float) -> None:
        '''Sets the vertical resolution, in pixels per inch, of this :py:class:`aspose.psd.RasterImage`.'''
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
        '''Gets a value indicating whether this instance has alpha.'''
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
    def resources(self) -> List[aspose.psd.fileformats.psd.layers.LayerResource]:
        '''Gets the layer resources.'''
        raise NotImplementedError()
    
    @resources.setter
    def resources(self, value : List[aspose.psd.fileformats.psd.layers.LayerResource]) -> None:
        '''Sets the layer resources.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the layer name.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the layer name.'''
        raise NotImplementedError()
    
    @property
    def blending_options(self) -> aspose.psd.fileformats.psd.layers.layereffects.BlendingOptions:
        '''Gets the blending options.'''
        raise NotImplementedError()
    
    @property
    def display_name(self) -> str:
        '''Gets the display name of the layer.'''
        raise NotImplementedError()
    
    @display_name.setter
    def display_name(self, value : str) -> None:
        '''Sets the display name of the layer.'''
        raise NotImplementedError()
    
    @property
    def fill_opacity(self) -> int:
        '''Gets the fill opacity.'''
        raise NotImplementedError()
    
    @fill_opacity.setter
    def fill_opacity(self, value : int) -> None:
        '''Sets the fill opacity.'''
        raise NotImplementedError()
    
    @property
    def layer_creation_date_time(self) -> datetime:
        '''Gets the layer creation date time.'''
        raise NotImplementedError()
    
    @layer_creation_date_time.setter
    def layer_creation_date_time(self, value : datetime) -> None:
        '''Sets the layer creation date time.'''
        raise NotImplementedError()
    
    @property
    def sheet_color_highlight(self) -> aspose.psd.fileformats.psd.layers.layerresources.SheetColorHighlightEnum:
        '''Gets the decorative sheet color highlight in layers\' list'''
        raise NotImplementedError()
    
    @sheet_color_highlight.setter
    def sheet_color_highlight(self, value : aspose.psd.fileformats.psd.layers.layerresources.SheetColorHighlightEnum) -> None:
        '''Sets the decorative sheet color highlight in layers\' list'''
        raise NotImplementedError()
    
    @property
    def top(self) -> int:
        '''Gets the top layer position.'''
        raise NotImplementedError()
    
    @top.setter
    def top(self, value : int) -> None:
        '''Sets the top layer position.'''
        raise NotImplementedError()
    
    @property
    def left(self) -> int:
        '''Gets the left layer position.'''
        raise NotImplementedError()
    
    @left.setter
    def left(self, value : int) -> None:
        '''Sets the left layer position.'''
        raise NotImplementedError()
    
    @property
    def bottom(self) -> int:
        '''Gets the bottom layer position.'''
        raise NotImplementedError()
    
    @bottom.setter
    def bottom(self, value : int) -> None:
        '''Sets the bottom layer position.'''
        raise NotImplementedError()
    
    @property
    def right(self) -> int:
        '''Gets the right layer position.'''
        raise NotImplementedError()
    
    @right.setter
    def right(self, value : int) -> None:
        '''Sets the right layer position.'''
        raise NotImplementedError()
    
    @property
    def channels_count(self) -> int:
        '''Gets the layer\'s channels count.'''
        raise NotImplementedError()
    
    @property
    def channel_information(self) -> List[aspose.psd.fileformats.psd.layers.ChannelInformation]:
        '''Gets the channel information.'''
        raise NotImplementedError()
    
    @channel_information.setter
    def channel_information(self, value : List[aspose.psd.fileformats.psd.layers.ChannelInformation]) -> None:
        '''Sets the channel information.'''
        raise NotImplementedError()
    
    @property
    def blend_mode_signature(self) -> int:
        '''Gets the blend mode signature.'''
        raise NotImplementedError()
    
    @property
    def blend_mode_key(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blend mode key.'''
        raise NotImplementedError()
    
    @blend_mode_key.setter
    def blend_mode_key(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blend mode key.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> int:
        '''Gets the layer opacity. 0 = transparent, 255 = opaque.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : int) -> None:
        '''Sets the layer opacity. 0 = transparent, 255 = opaque.'''
        raise NotImplementedError()
    
    @property
    def clipping(self) -> int:
        '''Gets the layer clipping. 0 = base, 1 = non-base.'''
        raise NotImplementedError()
    
    @clipping.setter
    def clipping(self, value : int) -> None:
        '''Sets the layer clipping. 0 = base, 1 = non-base.'''
        raise NotImplementedError()
    
    @property
    def flags(self) -> aspose.psd.fileformats.psd.layers.LayerFlags:
        '''Gets the layer flags.
        bit 0 = transparency protected;
        bit 1 = visible;
        bit 2 = obsolete;
        bit 3 = 1 for Photoshop 5.0 and later, tells if bit 4 has useful information;
        bit 4 = pixel data irrelevant to appearance of document.'''
        raise NotImplementedError()
    
    @flags.setter
    def flags(self, value : aspose.psd.fileformats.psd.layers.LayerFlags) -> None:
        '''Sets the layer flags.
        bit 0 = transparency protected;
        bit 1 = visible;
        bit 2 = obsolete;
        bit 3 = 1 for Photoshop 5.0 and later, tells if bit 4 has useful information;
        bit 4 = pixel data irrelevant to appearance of document.'''
        raise NotImplementedError()
    
    @property
    def filler(self) -> int:
        '''Gets the layer filler.'''
        raise NotImplementedError()
    
    @filler.setter
    def filler(self, value : int) -> None:
        '''Sets the layer filler.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the overall layer length in bytes.'''
        raise NotImplementedError()
    
    @property
    def extra_length(self) -> int:
        '''Gets the layer extra information length in bytes.'''
        raise NotImplementedError()
    
    @property
    def layer_mask_data(self) -> aspose.psd.fileformats.psd.layers.LayerMaskData:
        '''Gets the layer mask data.'''
        raise NotImplementedError()
    
    @layer_mask_data.setter
    def layer_mask_data(self, value : aspose.psd.fileformats.psd.layers.LayerMaskData) -> None:
        '''Sets the layer mask data.'''
        raise NotImplementedError()
    
    @property
    def layer_blending_ranges_data(self) -> aspose.psd.fileformats.psd.layers.LayerBlendingRangesData:
        '''Gets the layer blending ranges data.'''
        raise NotImplementedError()
    
    @layer_blending_ranges_data.setter
    def layer_blending_ranges_data(self, value : aspose.psd.fileformats.psd.layers.LayerBlendingRangesData) -> None:
        '''Sets the layer blending ranges data.'''
        raise NotImplementedError()
    
    @property
    def layer_options(self) -> aspose.psd.imageoptions.PsdOptions:
        '''Gets the layer options.'''
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        '''Gets a value indicating whether the layer is visible'''
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        '''Sets a value indicating whether the layer is visible'''
        raise NotImplementedError()
    
    @property
    def is_visible_in_group(self) -> bool:
        '''Gets a value indicating whether this instance is visible in group(If layer is not in group it means root group).'''
        raise NotImplementedError()
    
    @property
    def layer_lock(self) -> aspose.psd.fileformats.psd.layers.layerresources.LayerLockType:
        '''Gets the layer lock.
        Note that if flag LayerFlags.TransparencyProtected is set it will be overwritten by layer lock flag.
        To return LayerFlags.TransparencyProtected flag need to apply for layer option layer.Flags |= LayerFlags.TransparencyProtected'''
        raise NotImplementedError()
    
    @layer_lock.setter
    def layer_lock(self, value : aspose.psd.fileformats.psd.layers.layerresources.LayerLockType) -> None:
        '''Sets the layer lock.
        Note that if flag LayerFlags.TransparencyProtected is set it will be overwritten by layer lock flag.
        To return LayerFlags.TransparencyProtected flag need to apply for layer option layer.Flags |= LayerFlags.TransparencyProtected'''
        raise NotImplementedError()
    
    @property
    def blend_clipped_elements(self) -> bool:
        '''Gets the blending of clipped element.'''
        raise NotImplementedError()
    
    @blend_clipped_elements.setter
    def blend_clipped_elements(self, value : bool) -> None:
        '''Sets the blending of clipped element.'''
        raise NotImplementedError()
    
    @property
    def LAYER_HEADER_SIZE(self) -> int:
        '''The layer header size.'''
        raise NotImplementedError()

    @property
    def BLEND_SIGNATURE(self) -> int:
        '''Represents blend mode signature.'''
        raise NotImplementedError()

    @property
    def smart_filters(self) -> aspose.psd.fileformats.psd.layers.smartfilters.SmartFilters:
        '''Gets the smart filters.'''
        raise NotImplementedError()
    
    @property
    def warp_settings(self) -> aspose.psd.fileformats.psd.layers.warp.WarpSettings:
        '''It gets Warp parameters that was set or get from resource (default)'''
        raise NotImplementedError()
    
    @warp_settings.setter
    def warp_settings(self, value : aspose.psd.fileformats.psd.layers.warp.WarpSettings) -> None:
        '''It gets or sets Warp parameters that was set or get from resource (default)'''
        raise NotImplementedError()
    
    @property
    def contents_bounds(self) -> aspose.psd.Rectangle:
        '''Gets the smart object content\'s bounds.'''
        raise NotImplementedError()
    
    @contents_bounds.setter
    def contents_bounds(self, value : aspose.psd.Rectangle) -> None:
        '''Sets the smart object content\'s bounds.'''
        raise NotImplementedError()
    
    @property
    def contents_source(self) -> aspose.psd.fileformats.psd.layers.layerresources.LinkDataSource:
        '''Gets the smart object content\'s source.'''
        raise NotImplementedError()
    
    @contents_source.setter
    def contents_source(self, value : aspose.psd.fileformats.psd.layers.layerresources.LinkDataSource) -> None:
        '''Sets the smart object content\'s source.'''
        raise NotImplementedError()
    
    @property
    def content_type(self) -> aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectType:
        '''Gets the type of the smart object layer content.
        The embedded smart object contents is the embedded raw image file: :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LiFdDataSource.data`.
        The linked smart object contents is the raw contents of the linked image file if it is available: :py:class:`aspose.psd.fileformats.psd.layers.layerresources.LiFeDataSource`.
        We do not support loading from the Adobe� Photoshop� �� Graphics Library when :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LinkDataSource.is_library_link` is true.
        For regular link files, at first, we use :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LiFeDataSource.relative_path` to look for the file relatively
        to the source image path :py:attr:`aspose.psd.DataStreamSupporter.SourceImagePath`,
        if it is not available we look at :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LiFeDataSource.full_path`,
        if not then we look for the link file in the same directory where our image is: :py:attr:`aspose.psd.DataStreamSupporter.SourceImagePath`.'''
        raise NotImplementedError()
    
    @property
    def contents(self) -> List[int]:
        '''Gets the smart object layer contents.
        The embedded smart object contents is the embedded raw image file: :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LiFdDataSource.data` and its properties.
        The linked smart object contents is the raw content of the linked image file if it is available and its properties: :py:class:`aspose.psd.fileformats.psd.layers.layerresources.LiFeDataSource`.
        We do not support loading from the Adobe� Photoshop� �� Graphics Library when :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LinkDataSource.is_library_link` is true.
        For regular link files, at first, we use :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LiFeDataSource.relative_path` to look for the file relatively
        to the source image path :py:attr:`aspose.psd.DataStreamSupporter.SourceImagePath`,
        if it is not available we look at :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LiFeDataSource.full_path`,
        if not then we look for the link file in the same directory where our image is: :py:attr:`aspose.psd.DataStreamSupporter.SourceImagePath`.'''
        raise NotImplementedError()
    
    @contents.setter
    def contents(self, value : List[int]) -> None:
        '''Sets the smart object layer contents.
        The embedded smart object contents is the embedded raw image file: :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LiFdDataSource.data` and its properties.
        The linked smart object contents is the raw content of the linked image file if it is available and its properties: :py:class:`aspose.psd.fileformats.psd.layers.layerresources.LiFeDataSource`.
        We do not support loading from the Adobe� Photoshop� �� Graphics Library when :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LinkDataSource.is_library_link` is true.
        For regular link files, at first, we use :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LiFeDataSource.relative_path` to look for the file relatively
        to the source image path :py:attr:`aspose.psd.DataStreamSupporter.SourceImagePath`,
        if it is not available we look at :py:attr:`aspose.psd.fileformats.psd.layers.layerresources.LiFeDataSource.full_path`,
        if not then we look for the link file in the same directory where our image is: :py:attr:`aspose.psd.DataStreamSupporter.SourceImagePath`.'''
        raise NotImplementedError()
    
    @property
    def smart_object_provider(self) -> aspose.psd.fileformats.psd.SmartObjectProvider:
        '''Gets the smart object provider.'''
        raise NotImplementedError()
    

class SmartObjectType:
    '''Defines the SmartObjectType enumeration for smart object content type'''
    
    EMBEDDED : SmartObjectType
    '''The embedded content'''
    AVAILABLE_LINKED : SmartObjectType
    '''The linked file that is available'''
    UNAVAILABLE_LINKED : SmartObjectType
    '''The linked file that is unavailable'''
    LIBRARY_LINK : SmartObjectType
    '''The Adobe® Photoshop® ÑÑ library link'''

