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

class BmpOptions(aspose.psd.ImageOptionsBase):
    '''The bmp file format creation options.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.BmpOptions` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, bmp_options : aspose.psd.imageoptions.BmpOptions) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.BmpOptions` class.
        
        :param bmp_options: The BMP options.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.ImageOptionsBase:
        '''Clones this instance.
        
        :returns: Returns shallow copy of this instance'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def default_replacement_font(self) -> str:
        '''Gets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @default_replacement_font.setter
    def default_replacement_font(self, value : str) -> None:
        '''Sets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Gets the XMP metadata container.'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Sets the XMP metadata container.'''
        raise NotImplementedError()
    
    @property
    def source(self) -> aspose.psd.Source:
        '''Gets the source to create image in.'''
        raise NotImplementedError()
    
    @source.setter
    def source(self, value : aspose.psd.Source) -> None:
        '''Sets the source to create image in.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette.'''
        raise NotImplementedError()
    
    @property
    def resolution_settings(self) -> aspose.psd.ResolutionSetting:
        '''Gets the resolution settings.'''
        raise NotImplementedError()
    
    @resolution_settings.setter
    def resolution_settings(self, value : aspose.psd.ResolutionSetting) -> None:
        '''Sets the resolution settings.'''
        raise NotImplementedError()
    
    @property
    def vector_rasterization_options(self) -> aspose.psd.imageoptions.VectorRasterizationOptions:
        '''Gets the vector rasterization options.'''
        raise NotImplementedError()
    
    @vector_rasterization_options.setter
    def vector_rasterization_options(self, value : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Sets the vector rasterization options.'''
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
    def multi_page_options(self) -> aspose.psd.imageoptions.MultiPageOptions:
        '''The multipage options'''
        raise NotImplementedError()
    
    @multi_page_options.setter
    def multi_page_options(self, value : aspose.psd.imageoptions.MultiPageOptions) -> None:
        '''The multipage options'''
        raise NotImplementedError()
    
    @property
    def full_frame(self) -> bool:
        '''Gets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @full_frame.setter
    def full_frame(self, value : bool) -> None:
        '''Sets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @property
    def bits_per_pixel(self) -> int:
        '''Gets the image bits per pixel count.'''
        raise NotImplementedError()
    
    @bits_per_pixel.setter
    def bits_per_pixel(self, value : int) -> None:
        '''Sets the image bits per pixel count.'''
        raise NotImplementedError()
    
    @property
    def compression(self) -> aspose.psd.fileformats.bmp.BitmapCompression:
        '''Gets the compression.'''
        raise NotImplementedError()
    
    @compression.setter
    def compression(self, value : aspose.psd.fileformats.bmp.BitmapCompression) -> None:
        '''Sets the compression.'''
        raise NotImplementedError()
    

class CmxRasterizationOptions(VectorRasterizationOptions):
    '''the CMX exporter options.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.ImageOptionsBase` class.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.ImageOptionsBase:
        '''Clones this instance.
        
        :returns: Returns shallow copy of this instance'''
        raise NotImplementedError()
    
    def copy_to(self, vector_rasterization_options : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Copies to.
        
        :param vector_rasterization_options: The vector rasterization options.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def default_replacement_font(self) -> str:
        '''Gets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @default_replacement_font.setter
    def default_replacement_font(self, value : str) -> None:
        '''Sets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Gets the XMP metadata container.'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Sets the XMP metadata container.'''
        raise NotImplementedError()
    
    @property
    def source(self) -> aspose.psd.Source:
        '''Gets the source to create image in.'''
        raise NotImplementedError()
    
    @source.setter
    def source(self, value : aspose.psd.Source) -> None:
        '''Sets the source to create image in.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette.'''
        raise NotImplementedError()
    
    @property
    def resolution_settings(self) -> aspose.psd.ResolutionSetting:
        '''Gets the resolution settings.'''
        raise NotImplementedError()
    
    @resolution_settings.setter
    def resolution_settings(self, value : aspose.psd.ResolutionSetting) -> None:
        '''Sets the resolution settings.'''
        raise NotImplementedError()
    
    @property
    def vector_rasterization_options(self) -> aspose.psd.imageoptions.VectorRasterizationOptions:
        '''Gets the vector rasterization options.'''
        raise NotImplementedError()
    
    @vector_rasterization_options.setter
    def vector_rasterization_options(self, value : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Sets the vector rasterization options.'''
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
    def multi_page_options(self) -> aspose.psd.imageoptions.MultiPageOptions:
        '''The multipage options'''
        raise NotImplementedError()
    
    @multi_page_options.setter
    def multi_page_options(self, value : aspose.psd.imageoptions.MultiPageOptions) -> None:
        '''The multipage options'''
        raise NotImplementedError()
    
    @property
    def full_frame(self) -> bool:
        '''Gets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @full_frame.setter
    def full_frame(self, value : bool) -> None:
        '''Sets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @property
    def border_x(self) -> float:
        '''Gets the border X.'''
        raise NotImplementedError()
    
    @border_x.setter
    def border_x(self, value : float) -> None:
        '''Sets the border X.'''
        raise NotImplementedError()
    
    @property
    def border_y(self) -> float:
        '''Gets the border Y.'''
        raise NotImplementedError()
    
    @border_y.setter
    def border_y(self, value : float) -> None:
        '''Sets the border Y.'''
        raise NotImplementedError()
    
    @property
    def center_drawing(self) -> bool:
        '''Gets a value indicating whether center drawing.'''
        raise NotImplementedError()
    
    @center_drawing.setter
    def center_drawing(self, value : bool) -> None:
        '''Sets a value indicating whether center drawing.'''
        raise NotImplementedError()
    
    @property
    def page_height(self) -> float:
        '''Gets the page height.'''
        raise NotImplementedError()
    
    @page_height.setter
    def page_height(self, value : float) -> None:
        '''Sets the page height.'''
        raise NotImplementedError()
    
    @property
    def page_size(self) -> aspose.psd.SizeF:
        '''Gets the page size.'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : aspose.psd.SizeF) -> None:
        '''Sets the page size.'''
        raise NotImplementedError()
    
    @property
    def page_width(self) -> float:
        '''Gets the page width.'''
        raise NotImplementedError()
    
    @page_width.setter
    def page_width(self, value : float) -> None:
        '''Sets the page width.'''
        raise NotImplementedError()
    
    @property
    def background_color(self) -> aspose.psd.Color:
        '''Gets a background color.'''
        raise NotImplementedError()
    
    @background_color.setter
    def background_color(self, value : aspose.psd.Color) -> None:
        '''Sets a background color.'''
        raise NotImplementedError()
    
    @property
    def draw_color(self) -> aspose.psd.Color:
        '''Gets a foreground color.'''
        raise NotImplementedError()
    
    @draw_color.setter
    def draw_color(self, value : aspose.psd.Color) -> None:
        '''Sets a foreground color.'''
        raise NotImplementedError()
    
    @property
    def smoothing_mode(self) -> aspose.psd.SmoothingMode:
        '''Gets the smoothing mode.'''
        raise NotImplementedError()
    
    @smoothing_mode.setter
    def smoothing_mode(self, value : aspose.psd.SmoothingMode) -> None:
        '''Sets the smoothing mode.'''
        raise NotImplementedError()
    
    @property
    def text_rendering_hint(self) -> aspose.psd.TextRenderingHint:
        '''Gets the text rendering hint.'''
        raise NotImplementedError()
    
    @text_rendering_hint.setter
    def text_rendering_hint(self, value : aspose.psd.TextRenderingHint) -> None:
        '''Sets the text rendering hint.'''
        raise NotImplementedError()
    
    @property
    def positioning(self) -> aspose.psd.imageoptions.PositioningTypes:
        '''Gets the positioning.'''
        raise NotImplementedError()
    
    @positioning.setter
    def positioning(self, value : aspose.psd.imageoptions.PositioningTypes) -> None:
        '''Sets the positioning.'''
        raise NotImplementedError()
    

class GifOptions(aspose.psd.ImageOptionsBase):
    '''The gif file format creation options.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.GifOptions` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, gif_options : aspose.psd.imageoptions.GifOptions) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.GifOptions` class.
        
        :param gif_options: The GIF Options.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.ImageOptionsBase:
        '''Clones this instance.
        
        :returns: Returns shallow copy of this instance'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def default_replacement_font(self) -> str:
        '''Gets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @default_replacement_font.setter
    def default_replacement_font(self, value : str) -> None:
        '''Sets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Gets the XMP metadata container.'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Sets the XMP metadata container.'''
        raise NotImplementedError()
    
    @property
    def source(self) -> aspose.psd.Source:
        '''Gets the source to create image in.'''
        raise NotImplementedError()
    
    @source.setter
    def source(self, value : aspose.psd.Source) -> None:
        '''Sets the source to create image in.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette.'''
        raise NotImplementedError()
    
    @property
    def resolution_settings(self) -> aspose.psd.ResolutionSetting:
        '''Gets the resolution settings.'''
        raise NotImplementedError()
    
    @resolution_settings.setter
    def resolution_settings(self, value : aspose.psd.ResolutionSetting) -> None:
        '''Sets the resolution settings.'''
        raise NotImplementedError()
    
    @property
    def vector_rasterization_options(self) -> aspose.psd.imageoptions.VectorRasterizationOptions:
        '''Gets the vector rasterization options.'''
        raise NotImplementedError()
    
    @vector_rasterization_options.setter
    def vector_rasterization_options(self, value : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Sets the vector rasterization options.'''
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
    def multi_page_options(self) -> aspose.psd.imageoptions.MultiPageOptions:
        '''The multipage options'''
        raise NotImplementedError()
    
    @multi_page_options.setter
    def multi_page_options(self, value : aspose.psd.imageoptions.MultiPageOptions) -> None:
        '''The multipage options'''
        raise NotImplementedError()
    
    @property
    def full_frame(self) -> bool:
        '''Gets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @full_frame.setter
    def full_frame(self, value : bool) -> None:
        '''Sets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @property
    def do_palette_correction(self) -> bool:
        '''Gets a value indicating whether palette correction is applied.'''
        raise NotImplementedError()
    
    @do_palette_correction.setter
    def do_palette_correction(self, value : bool) -> None:
        '''Sets a value indicating whether palette correction is applied.'''
        raise NotImplementedError()
    
    @property
    def color_resolution(self) -> int:
        '''Gets the GIF color resolution.'''
        raise NotImplementedError()
    
    @color_resolution.setter
    def color_resolution(self, value : int) -> None:
        '''Sets the GIF color resolution.'''
        raise NotImplementedError()
    
    @property
    def is_palette_sorted(self) -> bool:
        '''Gets a value indicating whether palette entries are sorted.'''
        raise NotImplementedError()
    
    @is_palette_sorted.setter
    def is_palette_sorted(self, value : bool) -> None:
        '''Sets a value indicating whether palette entries are sorted.'''
        raise NotImplementedError()
    
    @property
    def pixel_aspect_ratio(self) -> int:
        '''Gets the GIF pixel aspect ratio.'''
        raise NotImplementedError()
    
    @pixel_aspect_ratio.setter
    def pixel_aspect_ratio(self, value : int) -> None:
        '''Sets the GIF pixel aspect ratio.'''
        raise NotImplementedError()
    
    @property
    def background_color_index(self) -> int:
        '''Gets the GIF background color index.'''
        raise NotImplementedError()
    
    @background_color_index.setter
    def background_color_index(self, value : int) -> None:
        '''Sets the GIF background color index.'''
        raise NotImplementedError()
    
    @property
    def has_trailer(self) -> bool:
        '''Gets a value indicating whether GIF has trailer.'''
        raise NotImplementedError()
    
    @has_trailer.setter
    def has_trailer(self, value : bool) -> None:
        '''Sets a value indicating whether GIF has trailer.'''
        raise NotImplementedError()
    
    @property
    def interlaced(self) -> bool:
        '''True if image should be interlaced.'''
        raise NotImplementedError()
    
    @interlaced.setter
    def interlaced(self, value : bool) -> None:
        '''True if image should be interlaced.'''
        raise NotImplementedError()
    
    @property
    def max_diff(self) -> int:
        '''Gets the maximum allowed pixel difference. If greater than zero, lossy compression will be used.
        Recommended value for optimal lossy compression is 80. 30 is very light compression, 200 is heavy.
        It works best when only little loss is introduced, and due to limitation of the compression algorithm very high loss levels won\'t give as much gain.
        The range of allowed values is [0, 1000].'''
        raise NotImplementedError()
    
    @max_diff.setter
    def max_diff(self, value : int) -> None:
        '''Sets the maximum allowed pixel difference. If greater than zero, lossy compression will be used.
        Recommended value for optimal lossy compression is 80. 30 is very light compression, 200 is heavy.
        It works best when only little loss is introduced, and due to limitation of the compression algorithm very high loss levels won\'t give as much gain.
        The range of allowed values is [0, 1000].'''
        raise NotImplementedError()
    

class GraphicsOptions:
    '''Represents graphics options for embedded bitmap.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def text_rendering_hint(self) -> aspose.psd.TextRenderingHint:
        '''Gets text rendering hint.'''
        raise NotImplementedError()
    
    @text_rendering_hint.setter
    def text_rendering_hint(self, value : aspose.psd.TextRenderingHint) -> None:
        '''Sets text rendering hint.'''
        raise NotImplementedError()
    
    @property
    def smoothing_mode(self) -> aspose.psd.SmoothingMode:
        '''Gets smoothing mode.'''
        raise NotImplementedError()
    
    @smoothing_mode.setter
    def smoothing_mode(self, value : aspose.psd.SmoothingMode) -> None:
        '''Sets smoothing mode.'''
        raise NotImplementedError()
    
    @property
    def interpolation_mode(self) -> aspose.psd.InterpolationMode:
        '''Gets interpolation mode.'''
        raise NotImplementedError()
    
    @interpolation_mode.setter
    def interpolation_mode(self, value : aspose.psd.InterpolationMode) -> None:
        '''Sets interpolation mode.'''
        raise NotImplementedError()
    

class Jpeg2000Options(aspose.psd.ImageOptionsBase):
    '''The Jpeg2000 file format options.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.Jpeg2000Options` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, jpeg_2000_options : aspose.psd.imageoptions.Jpeg2000Options) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.Jpeg2000Options` class.
        
        :param jpeg_2000_options: The Jpeg2000 file format options to copy settings from.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.ImageOptionsBase:
        '''Clones this instance.
        
        :returns: Returns shallow copy of this instance'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def default_replacement_font(self) -> str:
        '''Gets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @default_replacement_font.setter
    def default_replacement_font(self, value : str) -> None:
        '''Sets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Gets the XMP metadata container.'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Sets the XMP metadata container.'''
        raise NotImplementedError()
    
    @property
    def source(self) -> aspose.psd.Source:
        '''Gets the source to create image in.'''
        raise NotImplementedError()
    
    @source.setter
    def source(self, value : aspose.psd.Source) -> None:
        '''Sets the source to create image in.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette.'''
        raise NotImplementedError()
    
    @property
    def resolution_settings(self) -> aspose.psd.ResolutionSetting:
        '''Gets the resolution settings.'''
        raise NotImplementedError()
    
    @resolution_settings.setter
    def resolution_settings(self, value : aspose.psd.ResolutionSetting) -> None:
        '''Sets the resolution settings.'''
        raise NotImplementedError()
    
    @property
    def vector_rasterization_options(self) -> aspose.psd.imageoptions.VectorRasterizationOptions:
        '''Gets the vector rasterization options.'''
        raise NotImplementedError()
    
    @vector_rasterization_options.setter
    def vector_rasterization_options(self, value : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Sets the vector rasterization options.'''
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
    def multi_page_options(self) -> aspose.psd.imageoptions.MultiPageOptions:
        '''The multipage options'''
        raise NotImplementedError()
    
    @multi_page_options.setter
    def multi_page_options(self, value : aspose.psd.imageoptions.MultiPageOptions) -> None:
        '''The multipage options'''
        raise NotImplementedError()
    
    @property
    def full_frame(self) -> bool:
        '''Gets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @full_frame.setter
    def full_frame(self, value : bool) -> None:
        '''Sets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @property
    def comments(self) -> List[str]:
        '''Gets the Jpeg comment markers.'''
        raise NotImplementedError()
    
    @comments.setter
    def comments(self, value : List[str]) -> None:
        '''Sets the Jpeg comment markers.'''
        raise NotImplementedError()
    
    @property
    def codec(self) -> aspose.psd.fileformats.jpeg2000.Jpeg2000Codec:
        '''Gets the JPEG2000 codec'''
        raise NotImplementedError()
    
    @codec.setter
    def codec(self, value : aspose.psd.fileformats.jpeg2000.Jpeg2000Codec) -> None:
        '''Sets the JPEG2000 codec'''
        raise NotImplementedError()
    
    @property
    def compression_ratios(self) -> List[int]:
        '''Gets the Array of compression ratio.
        Different compression ratios for successive layers.
        The rate specified for each quality level is the desired
        compression factor.
        Decreasing ratios required.'''
        raise NotImplementedError()
    
    @compression_ratios.setter
    def compression_ratios(self, value : List[int]) -> None:
        '''Sets the Array of compression ratio.
        Different compression ratios for successive layers.
        The rate specified for each quality level is the desired
        compression factor.
        Decreasing ratios required.'''
        raise NotImplementedError()
    
    @property
    def irreversible(self) -> bool:
        '''Gets a value indicating whether use the irreversible DWT 9-7 (true) or use lossless DWT 5-3 compression (default).'''
        raise NotImplementedError()
    
    @irreversible.setter
    def irreversible(self, value : bool) -> None:
        '''Sets a value indicating whether use the irreversible DWT 9-7 (true) or use lossless DWT 5-3 compression (default).'''
        raise NotImplementedError()
    

class JpegOptions(aspose.psd.ImageOptionsBase):
    '''The jpeg file format create options.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.JpegOptions` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, jpeg_options : aspose.psd.imageoptions.JpegOptions) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.JpegOptions` class.
        
        :param jpeg_options: The JPEG options.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.ImageOptionsBase:
        '''Clones this instance.
        
        :returns: Returns shallow copy of this instance'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def default_replacement_font(self) -> str:
        '''Gets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @default_replacement_font.setter
    def default_replacement_font(self, value : str) -> None:
        '''Sets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Gets the XMP metadata container.'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Sets the XMP metadata container.'''
        raise NotImplementedError()
    
    @property
    def source(self) -> aspose.psd.Source:
        '''Gets the source to create image in.'''
        raise NotImplementedError()
    
    @source.setter
    def source(self, value : aspose.psd.Source) -> None:
        '''Sets the source to create image in.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette.'''
        raise NotImplementedError()
    
    @property
    def resolution_settings(self) -> aspose.psd.ResolutionSetting:
        '''Gets the resolution settings.'''
        raise NotImplementedError()
    
    @resolution_settings.setter
    def resolution_settings(self, value : aspose.psd.ResolutionSetting) -> None:
        '''Sets the resolution settings.'''
        raise NotImplementedError()
    
    @property
    def vector_rasterization_options(self) -> aspose.psd.imageoptions.VectorRasterizationOptions:
        '''Gets the vector rasterization options.'''
        raise NotImplementedError()
    
    @vector_rasterization_options.setter
    def vector_rasterization_options(self, value : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Sets the vector rasterization options.'''
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
    def multi_page_options(self) -> aspose.psd.imageoptions.MultiPageOptions:
        '''The multipage options'''
        raise NotImplementedError()
    
    @multi_page_options.setter
    def multi_page_options(self, value : aspose.psd.imageoptions.MultiPageOptions) -> None:
        '''The multipage options'''
        raise NotImplementedError()
    
    @property
    def full_frame(self) -> bool:
        '''Gets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @full_frame.setter
    def full_frame(self, value : bool) -> None:
        '''Sets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @property
    def default_memory_allocation_limit(self) -> int:
        '''Gets the default memory allocation limit.'''
        raise NotImplementedError()
    
    @default_memory_allocation_limit.setter
    def default_memory_allocation_limit(self, value : int) -> None:
        '''Sets the default memory allocation limit.'''
        raise NotImplementedError()
    
    @property
    def jfif(self) -> aspose.psd.fileformats.jpeg.JFIFData:
        '''Gets the jfif.'''
        raise NotImplementedError()
    
    @jfif.setter
    def jfif(self, value : aspose.psd.fileformats.jpeg.JFIFData) -> None:
        '''Sets the jfif.'''
        raise NotImplementedError()
    
    @property
    def comment(self) -> str:
        '''Gets the jpeg file comment.'''
        raise NotImplementedError()
    
    @comment.setter
    def comment(self, value : str) -> None:
        '''Sets the jpeg file comment.'''
        raise NotImplementedError()
    
    @property
    def exif_data(self) -> aspose.psd.exif.JpegExifData:
        '''Get or set exif data container'''
        raise NotImplementedError()
    
    @exif_data.setter
    def exif_data(self, value : aspose.psd.exif.JpegExifData) -> None:
        '''Get or set exif data container'''
        raise NotImplementedError()
    
    @property
    def compression_type(self) -> aspose.psd.fileformats.jpeg.JpegCompressionMode:
        '''Gets the compression type.'''
        raise NotImplementedError()
    
    @compression_type.setter
    def compression_type(self, value : aspose.psd.fileformats.jpeg.JpegCompressionMode) -> None:
        '''Sets the compression type.'''
        raise NotImplementedError()
    
    @property
    def color_type(self) -> aspose.psd.fileformats.jpeg.JpegCompressionColorMode:
        '''Gets the color type for jpeg image.'''
        raise NotImplementedError()
    
    @color_type.setter
    def color_type(self, value : aspose.psd.fileformats.jpeg.JpegCompressionColorMode) -> None:
        '''Sets the color type for jpeg image.'''
        raise NotImplementedError()
    
    @property
    def bits_per_channel(self) -> int:
        '''Gets bits per channel for lossless jpeg image. Now we support from 2 to 8 bits per channel.'''
        raise NotImplementedError()
    
    @bits_per_channel.setter
    def bits_per_channel(self, value : int) -> None:
        '''Sets bits per channel for lossless jpeg image. Now we support from 2 to 8 bits per channel.'''
        raise NotImplementedError()
    
    @property
    def quality(self) -> int:
        '''Gets image quality.'''
        raise NotImplementedError()
    
    @quality.setter
    def quality(self, value : int) -> None:
        '''Sets image quality.'''
        raise NotImplementedError()
    
    @property
    def scaled_quality(self) -> int:
        '''The scaled quality.'''
        raise NotImplementedError()
    
    @property
    def rd_opt_settings(self) -> aspose.psd.imageoptions.RdOptimizerSettings:
        '''Gets the RD optimizer settings.'''
        raise NotImplementedError()
    
    @rd_opt_settings.setter
    def rd_opt_settings(self, value : aspose.psd.imageoptions.RdOptimizerSettings) -> None:
        '''Sets the RD optimizer settings.'''
        raise NotImplementedError()
    
    @property
    def rgb_color_profile(self) -> aspose.psd.sources.StreamSource:
        '''The destination RGB color profile for CMYK jpeg images. Use for saving images. Must be in pair with CMYKColorProfile for correct color conversion.'''
        raise NotImplementedError()
    
    @rgb_color_profile.setter
    def rgb_color_profile(self, value : aspose.psd.sources.StreamSource) -> None:
        '''The destination RGB color profile for CMYK jpeg images. Use for saving images. Must be in pair with CMYKColorProfile for correct color conversion.'''
        raise NotImplementedError()
    
    @property
    def cmyk_color_profile(self) -> aspose.psd.sources.StreamSource:
        '''The destination CMYK color profile for CMYK jpeg images. Use for saving images. Must be in pair with RGBColorProfile for correct color conversion.'''
        raise NotImplementedError()
    
    @cmyk_color_profile.setter
    def cmyk_color_profile(self, value : aspose.psd.sources.StreamSource) -> None:
        '''The destination CMYK color profile for CMYK jpeg images. Use for saving images. Must be in pair with RGBColorProfile for correct color conversion.'''
        raise NotImplementedError()
    
    @property
    def jpeg_ls_allowed_lossy_error(self) -> int:
        '''Gets the JPEG-LS difference bound for near-lossless coding (NEAR parameter from the JPEG-LS specification).'''
        raise NotImplementedError()
    
    @jpeg_ls_allowed_lossy_error.setter
    def jpeg_ls_allowed_lossy_error(self, value : int) -> None:
        '''Sets the JPEG-LS difference bound for near-lossless coding (NEAR parameter from the JPEG-LS specification).'''
        raise NotImplementedError()
    
    @property
    def jpeg_ls_interleave_mode(self) -> aspose.psd.fileformats.jpeg.JpegLsInterleaveMode:
        '''Gets the JPEG-LS interleave mode.'''
        raise NotImplementedError()
    
    @jpeg_ls_interleave_mode.setter
    def jpeg_ls_interleave_mode(self, value : aspose.psd.fileformats.jpeg.JpegLsInterleaveMode) -> None:
        '''Sets the JPEG-LS interleave mode.'''
        raise NotImplementedError()
    
    @property
    def jpeg_ls_preset(self) -> aspose.psd.fileformats.jpeg.JpegLsPresetCodingParameters:
        '''Gets the JPEG-LS preset parameters.'''
        raise NotImplementedError()
    
    @jpeg_ls_preset.setter
    def jpeg_ls_preset(self, value : aspose.psd.fileformats.jpeg.JpegLsPresetCodingParameters) -> None:
        '''Sets the JPEG-LS preset parameters.'''
        raise NotImplementedError()
    
    @property
    def horizontal_sampling(self) -> List[int]:
        '''Gets the horizontal subsamplings for each component.'''
        raise NotImplementedError()
    
    @horizontal_sampling.setter
    def horizontal_sampling(self, value : List[int]) -> None:
        '''Sets the horizontal subsamplings for each component.'''
        raise NotImplementedError()
    
    @property
    def vertical_sampling(self) -> List[int]:
        '''Gets the vertical subsamplings for each component.'''
        raise NotImplementedError()
    
    @vertical_sampling.setter
    def vertical_sampling(self, value : List[int]) -> None:
        '''Sets the vertical subsamplings for each component.'''
        raise NotImplementedError()
    
    @property
    def sample_rounding_mode(self) -> aspose.psd.fileformats.jpeg.SampleRoundingMode:
        '''Gets the sample rounding mode to fit an 8-bit value to an n-bit value. :py:attr:`aspose.psd.imageoptions.JpegOptions.BitsPerChannel`'''
        raise NotImplementedError()
    
    @sample_rounding_mode.setter
    def sample_rounding_mode(self, value : aspose.psd.fileformats.jpeg.SampleRoundingMode) -> None:
        '''Sets the sample rounding mode to fit an 8-bit value to an n-bit value. :py:attr:`aspose.psd.imageoptions.JpegOptions.BitsPerChannel`'''
        raise NotImplementedError()
    
    @property
    def preblend_alpha_if_present(self) -> bool:
        '''Gets a value indicating whether red, green and blue components should be mixed with a background color, if alpha channel is present.'''
        raise NotImplementedError()
    
    @preblend_alpha_if_present.setter
    def preblend_alpha_if_present(self, value : bool) -> None:
        '''Sets a value indicating whether red, green and blue components should be mixed with a background color, if alpha channel is present.'''
        raise NotImplementedError()
    
    @property
    def resolution_unit(self) -> aspose.psd.ResolutionUnit:
        '''Gets the resolution unit.'''
        raise NotImplementedError()
    
    @resolution_unit.setter
    def resolution_unit(self, value : aspose.psd.ResolutionUnit) -> None:
        '''Sets the resolution unit.'''
        raise NotImplementedError()
    

class MultiPageOptions:
    '''Base class for multiple pages supported formats'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.MultiPageOptions` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, pages : List[int]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.MultiPageOptions` class.
        
        :param pages: The pages.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, pages : List[int], export_area : aspose.psd.Rectangle) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.MultiPageOptions` class.
        
        :param pages: The array of pages.
        :param export_area: The export area.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, page_titles : List[str]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.MultiPageOptions` class.
        
        :param page_titles: The page titles.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, page_titles : List[str], export_area : aspose.psd.Rectangle) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.MultiPageOptions` class.
        
        :param page_titles: The page titles.
        :param export_area: The export area.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, ranges : List[aspose.psd.IntRange]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.MultiPageOptions` class.
        
        :param ranges: The :py:class:`aspose.psd.IntRange`.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, ranges : List[aspose.psd.IntRange], export_area : aspose.psd.Rectangle) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.MultiPageOptions` class.
        
        :param ranges: The :py:class:`aspose.psd.IntRange`.
        :param export_area: The export area.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, range : aspose.psd.IntRange) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.MultiPageOptions` class.
        
        :param range: The :py:class:`aspose.psd.IntRange`.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, range : aspose.psd.IntRange, export_area : aspose.psd.Rectangle) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.MultiPageOptions` class.
        
        :param range: The :py:class:`aspose.psd.IntRange`.
        :param export_area: The export area.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, page : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.MultiPageOptions` class.
        
        :param page: The page index.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, page : int, export_area : aspose.psd.Rectangle) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.MultiPageOptions` class.
        
        :param page: The page index.
        :param export_area: The export area.'''
        raise NotImplementedError()
    
    def init_pages(self, ranges : List[aspose.psd.IntRange]) -> None:
        '''Initializes the pages from ranges array
        
        :param ranges: The ranges.'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> List[int]:
        '''Gets the pages.'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : List[int]) -> None:
        '''Sets the pages.'''
        raise NotImplementedError()
    
    @property
    def page_titles(self) -> List[str]:
        '''Gets the page titles.'''
        raise NotImplementedError()
    
    @page_titles.setter
    def page_titles(self, value : List[str]) -> None:
        '''Sets the page titles.'''
        raise NotImplementedError()
    
    @property
    def page_rasterization_options(self) -> List[aspose.psd.imageoptions.VectorRasterizationOptions]:
        '''Gets the page rasterization options.'''
        raise NotImplementedError()
    
    @page_rasterization_options.setter
    def page_rasterization_options(self, value : List[aspose.psd.imageoptions.VectorRasterizationOptions]) -> None:
        '''Sets the page rasterization options.'''
        raise NotImplementedError()
    
    @property
    def export_area(self) -> aspose.psd.Rectangle:
        '''Gets the export area.'''
        raise NotImplementedError()
    
    @export_area.setter
    def export_area(self, value : aspose.psd.Rectangle) -> None:
        '''Sets the export area.'''
        raise NotImplementedError()
    
    @property
    def mode(self) -> aspose.psd.imageoptions.MultiPageMode:
        '''Gets the mode.'''
        raise NotImplementedError()
    
    @mode.setter
    def mode(self, value : aspose.psd.imageoptions.MultiPageMode) -> None:
        '''Sets the mode.'''
        raise NotImplementedError()
    
    @property
    def output_layers_names(self) -> List[str]:
        '''Gets the output layers names(Works if export format supports layers naming, for example for Psd)'''
        raise NotImplementedError()
    
    @output_layers_names.setter
    def output_layers_names(self, value : List[str]) -> None:
        '''Sets the output layers names(Works if export format supports layers naming, for example for Psd)'''
        raise NotImplementedError()
    
    @property
    def merge_layers(self) -> bool:
        '''Gets a value indicating whether [merege layers].'''
        raise NotImplementedError()
    
    @merge_layers.setter
    def merge_layers(self, value : bool) -> None:
        '''Sets a value indicating whether [merege layers].'''
        raise NotImplementedError()
    

class PdfOptions(aspose.psd.ImageOptionsBase):
    '''The PDF options.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.ImageOptionsBase` class.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.ImageOptionsBase:
        '''Clones this instance.
        
        :returns: Returns shallow copy of this instance'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def default_replacement_font(self) -> str:
        '''Gets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @default_replacement_font.setter
    def default_replacement_font(self, value : str) -> None:
        '''Sets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Gets the XMP metadata container.'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Sets the XMP metadata container.'''
        raise NotImplementedError()
    
    @property
    def source(self) -> aspose.psd.Source:
        '''Gets the source to create image in.'''
        raise NotImplementedError()
    
    @source.setter
    def source(self, value : aspose.psd.Source) -> None:
        '''Sets the source to create image in.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette.'''
        raise NotImplementedError()
    
    @property
    def resolution_settings(self) -> aspose.psd.ResolutionSetting:
        '''Gets the resolution settings.'''
        raise NotImplementedError()
    
    @resolution_settings.setter
    def resolution_settings(self, value : aspose.psd.ResolutionSetting) -> None:
        '''Sets the resolution settings.'''
        raise NotImplementedError()
    
    @property
    def vector_rasterization_options(self) -> aspose.psd.imageoptions.VectorRasterizationOptions:
        '''Gets the vector rasterization options.'''
        raise NotImplementedError()
    
    @vector_rasterization_options.setter
    def vector_rasterization_options(self, value : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Sets the vector rasterization options.'''
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
    def multi_page_options(self) -> aspose.psd.imageoptions.MultiPageOptions:
        '''The multipage options'''
        raise NotImplementedError()
    
    @multi_page_options.setter
    def multi_page_options(self, value : aspose.psd.imageoptions.MultiPageOptions) -> None:
        '''The multipage options'''
        raise NotImplementedError()
    
    @property
    def full_frame(self) -> bool:
        '''Gets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @full_frame.setter
    def full_frame(self, value : bool) -> None:
        '''Sets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @property
    def pdf_document_info(self) -> aspose.psd.fileformats.pdf.PdfDocumentInfo:
        '''Gets metadata for document.'''
        raise NotImplementedError()
    
    @pdf_document_info.setter
    def pdf_document_info(self, value : aspose.psd.fileformats.pdf.PdfDocumentInfo) -> None:
        '''Sets metadata for document.'''
        raise NotImplementedError()
    
    @property
    def pdf_core_options(self) -> aspose.psd.fileformats.pdf.PdfCoreOptions:
        '''The PDF core options'''
        raise NotImplementedError()
    
    @pdf_core_options.setter
    def pdf_core_options(self, value : aspose.psd.fileformats.pdf.PdfCoreOptions) -> None:
        '''The PDF core options'''
        raise NotImplementedError()
    
    @property
    def page_size(self) -> aspose.psd.SizeF:
        '''Gets the size of the page.'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : aspose.psd.SizeF) -> None:
        '''Sets the size of the page.'''
        raise NotImplementedError()
    

class PngOptions(aspose.psd.ImageOptionsBase):
    '''The png file format create options.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.PngOptions` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, png_options : aspose.psd.imageoptions.PngOptions) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.PngOptions` class.
        
        :param png_options: The PNG options.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.ImageOptionsBase:
        '''Clones this instance.
        
        :returns: Returns shallow copy of this instance'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def default_replacement_font(self) -> str:
        '''Gets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @default_replacement_font.setter
    def default_replacement_font(self, value : str) -> None:
        '''Sets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Gets the XMP metadata container.'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Sets the XMP metadata container.'''
        raise NotImplementedError()
    
    @property
    def source(self) -> aspose.psd.Source:
        '''Gets the source to create image in.'''
        raise NotImplementedError()
    
    @source.setter
    def source(self, value : aspose.psd.Source) -> None:
        '''Sets the source to create image in.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette.'''
        raise NotImplementedError()
    
    @property
    def resolution_settings(self) -> aspose.psd.ResolutionSetting:
        '''Gets the resolution settings.'''
        raise NotImplementedError()
    
    @resolution_settings.setter
    def resolution_settings(self, value : aspose.psd.ResolutionSetting) -> None:
        '''Sets the resolution settings.'''
        raise NotImplementedError()
    
    @property
    def vector_rasterization_options(self) -> aspose.psd.imageoptions.VectorRasterizationOptions:
        '''Gets the vector rasterization options.'''
        raise NotImplementedError()
    
    @vector_rasterization_options.setter
    def vector_rasterization_options(self, value : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Sets the vector rasterization options.'''
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
    def multi_page_options(self) -> aspose.psd.imageoptions.MultiPageOptions:
        '''The multipage options'''
        raise NotImplementedError()
    
    @multi_page_options.setter
    def multi_page_options(self, value : aspose.psd.imageoptions.MultiPageOptions) -> None:
        '''The multipage options'''
        raise NotImplementedError()
    
    @property
    def full_frame(self) -> bool:
        '''Gets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @full_frame.setter
    def full_frame(self, value : bool) -> None:
        '''Sets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @property
    def color_type(self) -> aspose.psd.fileformats.png.PngColorType:
        '''Gets the type of the color.'''
        raise NotImplementedError()
    
    @color_type.setter
    def color_type(self, value : aspose.psd.fileformats.png.PngColorType) -> None:
        '''Sets the type of the color.'''
        raise NotImplementedError()
    
    @property
    def progressive(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.imageoptions.PngOptions` is progressive.'''
        raise NotImplementedError()
    
    @progressive.setter
    def progressive(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.imageoptions.PngOptions` is progressive.'''
        raise NotImplementedError()
    
    @property
    def filter_type(self) -> aspose.psd.fileformats.png.PngFilterType:
        '''Gets the filter type used during png file save process.'''
        raise NotImplementedError()
    
    @filter_type.setter
    def filter_type(self, value : aspose.psd.fileformats.png.PngFilterType) -> None:
        '''Sets the filter type used during png file save process.'''
        raise NotImplementedError()
    
    @property
    def compression_level(self) -> int:
        '''The png image compression level in the 0-9 range, where 9 is maximum compression and 0 is store mode.'''
        raise NotImplementedError()
    
    @compression_level.setter
    def compression_level(self, value : int) -> None:
        '''The png image compression level in the 0-9 range, where 9 is maximum compression and 0 is store mode.'''
        raise NotImplementedError()
    
    @property
    def bit_depth(self) -> int:
        '''The bit depth.'''
        raise NotImplementedError()
    
    @bit_depth.setter
    def bit_depth(self, value : int) -> None:
        '''The bit depth.'''
        raise NotImplementedError()
    
    @property
    def DEFAULT_COMPRESSION_LEVEL(self) -> int:
        '''The default compression level.'''
        raise NotImplementedError()


class PsdOptions(aspose.psd.ImageOptionsBase):
    '''The psd file format create options.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.PsdOptions` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, options : aspose.psd.imageoptions.PsdOptions) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.PsdOptions` class.
        
        :param options: The options.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, image : aspose.psd.fileformats.psd.PsdImage) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.PsdOptions` class.
        
        :param image: The image.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.ImageOptionsBase:
        '''Clones this instance.
        
        :returns: Returns shallow copy of this instance'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def default_replacement_font(self) -> str:
        '''Gets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @default_replacement_font.setter
    def default_replacement_font(self, value : str) -> None:
        '''Sets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Get or set XMP data container'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Get or set XMP data container'''
        raise NotImplementedError()
    
    @property
    def source(self) -> aspose.psd.Source:
        '''Gets the source to create image in.'''
        raise NotImplementedError()
    
    @source.setter
    def source(self, value : aspose.psd.Source) -> None:
        '''Sets the source to create image in.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette.'''
        raise NotImplementedError()
    
    @property
    def resolution_settings(self) -> aspose.psd.ResolutionSetting:
        '''Gets the resolution settings.'''
        raise NotImplementedError()
    
    @resolution_settings.setter
    def resolution_settings(self, value : aspose.psd.ResolutionSetting) -> None:
        '''Sets the resolution settings.'''
        raise NotImplementedError()
    
    @property
    def vector_rasterization_options(self) -> aspose.psd.imageoptions.VectorRasterizationOptions:
        '''Gets the vector rasterization options.'''
        raise NotImplementedError()
    
    @vector_rasterization_options.setter
    def vector_rasterization_options(self, value : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Sets the vector rasterization options.'''
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
    def multi_page_options(self) -> aspose.psd.imageoptions.MultiPageOptions:
        '''The multipage options'''
        raise NotImplementedError()
    
    @multi_page_options.setter
    def multi_page_options(self, value : aspose.psd.imageoptions.MultiPageOptions) -> None:
        '''The multipage options'''
        raise NotImplementedError()
    
    @property
    def full_frame(self) -> bool:
        '''Gets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @full_frame.setter
    def full_frame(self, value : bool) -> None:
        '''Sets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @property
    def resources(self) -> List[aspose.psd.fileformats.psd.ResourceBlock]:
        '''Gets the psd resources.'''
        raise NotImplementedError()
    
    @resources.setter
    def resources(self, value : List[aspose.psd.fileformats.psd.ResourceBlock]) -> None:
        '''Sets the psd resources.'''
        raise NotImplementedError()
    
    @property
    def version(self) -> int:
        '''Gets the psd file version.'''
        raise NotImplementedError()
    
    @version.setter
    def version(self, value : int) -> None:
        '''Sets the psd file version.'''
        raise NotImplementedError()
    
    @property
    def compression_method(self) -> aspose.psd.fileformats.psd.CompressionMethod:
        '''Gets the psd compression method.'''
        raise NotImplementedError()
    
    @compression_method.setter
    def compression_method(self, value : aspose.psd.fileformats.psd.CompressionMethod) -> None:
        '''Sets the psd compression method.'''
        raise NotImplementedError()
    
    @property
    def psd_version(self) -> aspose.psd.fileformats.psd.PsdVersion:
        '''Gets the file format version. It can be PSD or PSB.'''
        raise NotImplementedError()
    
    @psd_version.setter
    def psd_version(self, value : aspose.psd.fileformats.psd.PsdVersion) -> None:
        '''Sets the file format version. It can be PSD or PSB.'''
        raise NotImplementedError()
    
    @property
    def color_mode(self) -> aspose.psd.fileformats.psd.ColorModes:
        '''Gets the psd color mode.'''
        raise NotImplementedError()
    
    @color_mode.setter
    def color_mode(self, value : aspose.psd.fileformats.psd.ColorModes) -> None:
        '''Sets the psd color mode.'''
        raise NotImplementedError()
    
    @property
    def channel_bits_count(self) -> int:
        '''Gets the bits count per color channel.'''
        raise NotImplementedError()
    
    @channel_bits_count.setter
    def channel_bits_count(self, value : int) -> None:
        '''Sets the bits count per color channel.'''
        raise NotImplementedError()
    
    @property
    def channels_count(self) -> int:
        '''Gets the color channels count.'''
        raise NotImplementedError()
    
    @channels_count.setter
    def channels_count(self, value : int) -> None:
        '''Sets the color channels count.'''
        raise NotImplementedError()
    
    @property
    def remove_global_text_engine_resource(self) -> bool:
        '''Gets a value indicating whether - Remove the global text engine resource - Used for some text-layered psd files, in only case, when they can not be opened in Adobe Photoshop after processing (mostly for absent fonts text layers related).
        After using this option, user need to Make next in opened in Photoshop file: Menu "Text" -> "Process absent fonts". After that operation all text will appear again.
        Please note, that this operation may cause some final layout changes.'''
        raise NotImplementedError()
    
    @remove_global_text_engine_resource.setter
    def remove_global_text_engine_resource(self, value : bool) -> None:
        '''Sets a value indicating whether - Remove the global text engine resource - Used for some text-layered psd files, in only case, when they can not be opened in Adobe Photoshop after processing (mostly for absent fonts text layers related).
        After using this option, user need to Make next in opened in Photoshop file: Menu "Text" -> "Process absent fonts". After that operation all text will appear again.
        Please note, that this operation may cause some final layout changes.'''
        raise NotImplementedError()
    
    @property
    def refresh_image_preview_data(self) -> bool:
        '''Gets a value indicating whether [refresh image preview data] - option used to maximize compatibility with another PSD image viewers.
        Please note, text layers drawing to final layout is not supported for Compact Framework platform'''
        raise NotImplementedError()
    
    @refresh_image_preview_data.setter
    def refresh_image_preview_data(self, value : bool) -> None:
        '''Sets a value indicating whether [refresh image preview data] - option used to maximize compatibility with another PSD image viewers.
        Please note, text layers drawing to final layout is not supported for Compact Framework platform'''
        raise NotImplementedError()
    
    @property
    def update_metadata(self) -> bool:
        '''Gets a value indicating whether [update metadata].
        If the value is true, the metadata will be updated while saving an image.'''
        raise NotImplementedError()
    
    @update_metadata.setter
    def update_metadata(self, value : bool) -> None:
        '''Sets a value indicating whether [update metadata].
        If the value is true, the metadata will be updated while saving an image.'''
        raise NotImplementedError()
    
    @property
    def background_contents(self) -> aspose.psd.fileformats.psd.core.rawcolor.RawColor:
        '''Gets the color of background.
        It can be seen under transparent objects.'''
        raise NotImplementedError()
    
    @background_contents.setter
    def background_contents(self, value : aspose.psd.fileformats.psd.core.rawcolor.RawColor) -> None:
        '''Sets the color of background.
        It can be seen under transparent objects.'''
        raise NotImplementedError()
    

class RdOptimizerSettings:
    '''RD optimizer settings class'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def create() -> aspose.psd.imageoptions.RdOptimizerSettings:
        '''Creates this instance.
        
        :returns: returns RDOptimizerSettings class instance'''
        raise NotImplementedError()
    
    @property
    def bpp_scale(self) -> int:
        '''Gets the BPP (bits per pixel) scale factor.'''
        raise NotImplementedError()
    
    @bpp_scale.setter
    def bpp_scale(self, value : int) -> None:
        '''Sets the BPP (bits per pixel) scale factor.'''
        raise NotImplementedError()
    
    @property
    def bpp_max(self) -> float:
        '''Gets the maximum R value for consideration in  in bits per pixel'''
        raise NotImplementedError()
    
    @bpp_max.setter
    def bpp_max(self, value : float) -> None:
        '''Sets the maximum R value for consideration in  in bits per pixel'''
        raise NotImplementedError()
    
    @property
    def max_q(self) -> int:
        '''Gets the maximum quantization value.'''
        raise NotImplementedError()
    
    @max_q.setter
    def max_q(self, value : int) -> None:
        '''Sets the maximum quantization value.'''
        raise NotImplementedError()
    
    @property
    def min_q(self) -> int:
        '''Gets the minimum allowed quantization value.'''
        raise NotImplementedError()
    
    @property
    def max_pixel_value(self) -> int:
        '''Gets the maximum pixel value.'''
        raise NotImplementedError()
    
    @property
    def psnr_max(self) -> int:
        '''Gets the PSNR maximum expected value.'''
        raise NotImplementedError()
    
    @property
    def discretized_bpp_max(self) -> int:
        '''Gets the maximum R value for consideration.'''
        raise NotImplementedError()
    

class RenderResult:
    '''Represents information with results of rendering'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def message(self) -> str:
        '''Gets string message'''
        raise NotImplementedError()
    
    @message.setter
    def message(self, value : str) -> None:
        '''Sets string message'''
        raise NotImplementedError()
    
    @property
    def render_code(self) -> aspose.psd.imageoptions.RenderErrorCode:
        '''Gets code of error'''
        raise NotImplementedError()
    
    @render_code.setter
    def render_code(self, value : aspose.psd.imageoptions.RenderErrorCode) -> None:
        '''Sets code of error'''
        raise NotImplementedError()
    

class TiffOptions(aspose.psd.ImageOptionsBase):
    '''The tiff file format options.
    Note that width and height tags will get overwritten on image creation by width and height parameters so there is no need to specify them directly.
    Note that many options return a default value but that does not mean that this option is set explicitly as a tag value. To verify the tag is present use Tags property or the corresponding IsTagPresent method.'''
    
    @overload
    def __init__(self, expected_format : aspose.psd.fileformats.tiff.enums.TiffExpectedFormat, byte_order : aspose.psd.fileformats.tiff.enums.TiffByteOrder) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.TiffOptions` class.
        
        :param expected_format: The expected tiff file format.
        :param byte_order: The tiff file format byte order to use.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, expected_format : aspose.psd.fileformats.tiff.enums.TiffExpectedFormat) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.TiffOptions` class. By default little endian convention is used.
        
        :param expected_format: The expected tiff file format.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, options : aspose.psd.imageoptions.TiffOptions) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.TiffOptions` class.
        
        :param options: The options to copy from.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, tags : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageoptions.TiffOptions` class.
        
        :param tags: The tags to initialize options with.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.ImageOptionsBase:
        '''Clones this instance.
        
        :returns: Returns shallow copy of this instance'''
        raise NotImplementedError()
    
    def is_tag_present(self, tag : aspose.psd.fileformats.tiff.enums.TiffTags) -> bool:
        '''Determines whether tag is present in the options or not.
        
        :param tag: The tag id to check.
        :returns: ``true`` if tag is present; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_valid_tags_count(tags : List[aspose.psd.fileformats.tiff.TiffDataType]) -> int:
        '''Gets the valid tags count.
        
        :param tags: The tags to validate.
        :returns: The valid tags count.'''
        raise NotImplementedError()
    
    def remove_tag(self, tag : aspose.psd.fileformats.tiff.enums.TiffTags) -> bool:
        '''Removes the tag.
        
        :param tag: The tag to remove.
        :returns: true if successfully removed'''
        raise NotImplementedError()
    
    def validate(self) -> None:
        '''Validates if options have valid combination of tags'''
        raise NotImplementedError()
    
    def add_tags(self, tags_to_add : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Adds the tags.
        
        :param tags_to_add: The tags to add.'''
        raise NotImplementedError()
    
    def add_tag(self, tag_to_add : aspose.psd.fileformats.tiff.TiffDataType) -> None:
        '''Adds a new tag.
        
        :param tag_to_add: The tag to add.'''
        raise NotImplementedError()
    
    def get_tag_by_type(self, tag_key : aspose.psd.fileformats.tiff.enums.TiffTags) -> aspose.psd.fileformats.tiff.TiffDataType:
        '''Gets the instance of the tag by type.
        
        :param tag_key: The tag key.
        :returns: Instance of the tag if exists or null otherwise.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def default_replacement_font(self) -> str:
        '''Gets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @default_replacement_font.setter
    def default_replacement_font(self, value : str) -> None:
        '''Sets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Gets the XMP metadata container.'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Sets the XMP metadata container.'''
        raise NotImplementedError()
    
    @property
    def source(self) -> aspose.psd.Source:
        '''Gets the source to create image in.'''
        raise NotImplementedError()
    
    @source.setter
    def source(self, value : aspose.psd.Source) -> None:
        '''Sets the source to create image in.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette.'''
        raise NotImplementedError()
    
    @property
    def resolution_settings(self) -> aspose.psd.ResolutionSetting:
        '''Gets the resolution settings.'''
        raise NotImplementedError()
    
    @resolution_settings.setter
    def resolution_settings(self, value : aspose.psd.ResolutionSetting) -> None:
        '''Sets the resolution settings.'''
        raise NotImplementedError()
    
    @property
    def vector_rasterization_options(self) -> aspose.psd.imageoptions.VectorRasterizationOptions:
        '''Gets the vector rasterization options.'''
        raise NotImplementedError()
    
    @vector_rasterization_options.setter
    def vector_rasterization_options(self, value : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Sets the vector rasterization options.'''
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
    def multi_page_options(self) -> aspose.psd.imageoptions.MultiPageOptions:
        '''The multipage options'''
        raise NotImplementedError()
    
    @multi_page_options.setter
    def multi_page_options(self, value : aspose.psd.imageoptions.MultiPageOptions) -> None:
        '''The multipage options'''
        raise NotImplementedError()
    
    @property
    def full_frame(self) -> bool:
        '''Gets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @full_frame.setter
    def full_frame(self, value : bool) -> None:
        '''Sets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @property
    def file_standard(self) -> aspose.psd.fileformats.tiff.enums.TiffFileStandards:
        '''Gets the TIFF file standard.'''
        raise NotImplementedError()
    
    @file_standard.setter
    def file_standard(self, value : aspose.psd.fileformats.tiff.enums.TiffFileStandards) -> None:
        '''Sets the TIFF file standard.'''
        raise NotImplementedError()
    
    @property
    def default_memory_allocation_limit(self) -> int:
        '''Gets the default memory allocation limit.'''
        raise NotImplementedError()
    
    @default_memory_allocation_limit.setter
    def default_memory_allocation_limit(self, value : int) -> None:
        '''Sets the default memory allocation limit.'''
        raise NotImplementedError()
    
    @property
    def premultiply_components(self) -> bool:
        '''Gets a value indicating whether components must be premultiplied.'''
        raise NotImplementedError()
    
    @premultiply_components.setter
    def premultiply_components(self, value : bool) -> None:
        '''Sets a value indicating whether components must be premultiplied.'''
        raise NotImplementedError()
    
    @property
    def is_valid(self) -> bool:
        '''Gets a value indicating whether the :py:class:`aspose.psd.imageoptions.TiffOptions` have been properly configured. Use Validate method as to find the failure reason.'''
        raise NotImplementedError()
    
    @property
    def y_cb_cr_subsampling(self) -> List[int]:
        '''Gets the subsampling factors for YCbCr photometric.'''
        raise NotImplementedError()
    
    @y_cb_cr_subsampling.setter
    def y_cb_cr_subsampling(self, value : List[int]) -> None:
        '''Sets the subsampling factors for YCbCr photometric.'''
        raise NotImplementedError()
    
    @property
    def y_cb_cr_coefficients(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the YCbCrCoefficients.'''
        raise NotImplementedError()
    
    @y_cb_cr_coefficients.setter
    def y_cb_cr_coefficients(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the YCbCrCoefficients.'''
        raise NotImplementedError()
    
    @property
    def is_tiled(self) -> bool:
        '''Gets a value indicating whether image is tiled.'''
        raise NotImplementedError()
    
    @property
    def artist(self) -> str:
        '''Gets the artist.'''
        raise NotImplementedError()
    
    @artist.setter
    def artist(self, value : str) -> None:
        '''Sets the artist.'''
        raise NotImplementedError()
    
    @property
    def byte_order(self) -> aspose.psd.fileformats.tiff.enums.TiffByteOrder:
        '''Gets a value indicating the tiff byte order.'''
        raise NotImplementedError()
    
    @byte_order.setter
    def byte_order(self, value : aspose.psd.fileformats.tiff.enums.TiffByteOrder) -> None:
        '''Sets a value indicating the tiff byte order.'''
        raise NotImplementedError()
    
    @property
    def bits_per_sample(self) -> List[int]:
        '''Gets the bits per sample.'''
        raise NotImplementedError()
    
    @bits_per_sample.setter
    def bits_per_sample(self, value : List[int]) -> None:
        '''Sets the bits per sample.'''
        raise NotImplementedError()
    
    @property
    def compression(self) -> aspose.psd.fileformats.tiff.enums.TiffCompressions:
        '''Gets the compression.'''
        raise NotImplementedError()
    
    @compression.setter
    def compression(self, value : aspose.psd.fileformats.tiff.enums.TiffCompressions) -> None:
        '''Sets the compression.'''
        raise NotImplementedError()
    
    @property
    def compressed_quality(self) -> int:
        '''Gets compressed image quality.
        Used with the Jpeg compression.'''
        raise NotImplementedError()
    
    @compressed_quality.setter
    def compressed_quality(self, value : int) -> None:
        '''Sets compressed image quality.
        Used with the Jpeg compression.'''
        raise NotImplementedError()
    
    @property
    def copyright(self) -> str:
        '''Gets the copyright.'''
        raise NotImplementedError()
    
    @copyright.setter
    def copyright(self, value : str) -> None:
        '''Sets the copyright.'''
        raise NotImplementedError()
    
    @property
    def color_map(self) -> List[int]:
        '''Gets the color map.'''
        raise NotImplementedError()
    
    @color_map.setter
    def color_map(self, value : List[int]) -> None:
        '''Sets the color map.'''
        raise NotImplementedError()
    
    @property
    def date_time(self) -> str:
        '''Gets the date and time.'''
        raise NotImplementedError()
    
    @date_time.setter
    def date_time(self, value : str) -> None:
        '''Sets the date and time.'''
        raise NotImplementedError()
    
    @property
    def document_name(self) -> str:
        '''Gets the name of the document.'''
        raise NotImplementedError()
    
    @document_name.setter
    def document_name(self, value : str) -> None:
        '''Sets the name of the document.'''
        raise NotImplementedError()
    
    @property
    def alpha_storage(self) -> aspose.psd.fileformats.tiff.enums.TiffAlphaStorage:
        '''Gets the alpha storage option. Options other than :py:attr:`aspose.psd.fileformats.tiff.enums.TiffAlphaStorage.UNSPECIFIED`
        are used when there are more than 3 :py:attr:`aspose.psd.imageoptions.TiffOptions.samples_per_pixel` defined.'''
        raise NotImplementedError()
    
    @alpha_storage.setter
    def alpha_storage(self, value : aspose.psd.fileformats.tiff.enums.TiffAlphaStorage) -> None:
        '''Sets the alpha storage option. Options other than :py:attr:`aspose.psd.fileformats.tiff.enums.TiffAlphaStorage.UNSPECIFIED`
        are used when there are more than 3 :py:attr:`aspose.psd.imageoptions.TiffOptions.samples_per_pixel` defined.'''
        raise NotImplementedError()
    
    @property
    def is_extra_samples_present(self) -> bool:
        '''Gets a value indicating whether the extra samples is present.'''
        raise NotImplementedError()
    
    @property
    def fill_order(self) -> aspose.psd.fileformats.tiff.enums.TiffFillOrders:
        '''Gets the byte bits fill order.'''
        raise NotImplementedError()
    
    @fill_order.setter
    def fill_order(self, value : aspose.psd.fileformats.tiff.enums.TiffFillOrders) -> None:
        '''Sets the byte bits fill order.'''
        raise NotImplementedError()
    
    @property
    def half_tone_hints(self) -> List[int]:
        '''Gets the halftone hints.'''
        raise NotImplementedError()
    
    @half_tone_hints.setter
    def half_tone_hints(self, value : List[int]) -> None:
        '''Sets the halftone hints.'''
        raise NotImplementedError()
    
    @property
    def image_description(self) -> str:
        '''Gets the image description.'''
        raise NotImplementedError()
    
    @image_description.setter
    def image_description(self, value : str) -> None:
        '''Sets the image description.'''
        raise NotImplementedError()
    
    @property
    def ink_names(self) -> str:
        '''Gets the ink names.'''
        raise NotImplementedError()
    
    @ink_names.setter
    def ink_names(self, value : str) -> None:
        '''Sets the ink names.'''
        raise NotImplementedError()
    
    @property
    def scanner_manufacturer(self) -> str:
        '''Gets the scanner manufacturer.'''
        raise NotImplementedError()
    
    @scanner_manufacturer.setter
    def scanner_manufacturer(self, value : str) -> None:
        '''Sets the scanner manufacturer.'''
        raise NotImplementedError()
    
    @property
    def max_sample_value(self) -> List[int]:
        '''Gets the max sample value.'''
        raise NotImplementedError()
    
    @max_sample_value.setter
    def max_sample_value(self, value : List[int]) -> None:
        '''Sets the max sample value.'''
        raise NotImplementedError()
    
    @property
    def min_sample_value(self) -> List[int]:
        '''Gets the min sample value.'''
        raise NotImplementedError()
    
    @min_sample_value.setter
    def min_sample_value(self, value : List[int]) -> None:
        '''Sets the min sample value.'''
        raise NotImplementedError()
    
    @property
    def scanner_model(self) -> str:
        '''Gets the scanner model.'''
        raise NotImplementedError()
    
    @scanner_model.setter
    def scanner_model(self, value : str) -> None:
        '''Sets the scanner model.'''
        raise NotImplementedError()
    
    @property
    def orientation(self) -> aspose.psd.fileformats.tiff.enums.TiffOrientations:
        '''Gets the orientation.'''
        raise NotImplementedError()
    
    @orientation.setter
    def orientation(self, value : aspose.psd.fileformats.tiff.enums.TiffOrientations) -> None:
        '''Sets the orientation.'''
        raise NotImplementedError()
    
    @property
    def page_name(self) -> str:
        '''Gets the page name.'''
        raise NotImplementedError()
    
    @page_name.setter
    def page_name(self, value : str) -> None:
        '''Sets the page name.'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> List[int]:
        '''Gets the page number tag.'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : List[int]) -> None:
        '''Sets the page number tag.'''
        raise NotImplementedError()
    
    @property
    def photometric(self) -> aspose.psd.fileformats.tiff.enums.TiffPhotometrics:
        '''Gets the photometric.'''
        raise NotImplementedError()
    
    @photometric.setter
    def photometric(self, value : aspose.psd.fileformats.tiff.enums.TiffPhotometrics) -> None:
        '''Sets the photometric.'''
        raise NotImplementedError()
    
    @property
    def planar_configuration(self) -> aspose.psd.fileformats.tiff.enums.TiffPlanarConfigs:
        '''Gets the planar configuration.'''
        raise NotImplementedError()
    
    @planar_configuration.setter
    def planar_configuration(self, value : aspose.psd.fileformats.tiff.enums.TiffPlanarConfigs) -> None:
        '''Sets the planar configuration.'''
        raise NotImplementedError()
    
    @property
    def resolution_unit(self) -> aspose.psd.fileformats.tiff.enums.TiffResolutionUnits:
        '''Gets the resolution unit.'''
        raise NotImplementedError()
    
    @resolution_unit.setter
    def resolution_unit(self, value : aspose.psd.fileformats.tiff.enums.TiffResolutionUnits) -> None:
        '''Sets the resolution unit.'''
        raise NotImplementedError()
    
    @property
    def rows_per_strip(self) -> int:
        '''Gets the rows per strip.'''
        raise NotImplementedError()
    
    @rows_per_strip.setter
    def rows_per_strip(self, value : int) -> None:
        '''Sets the rows per strip.'''
        raise NotImplementedError()
    
    @property
    def tile_width(self) -> int:
        '''Gets ot sets tile width.'''
        raise NotImplementedError()
    
    @tile_width.setter
    def tile_width(self, value : int) -> None:
        '''Gets ot sets tile width.'''
        raise NotImplementedError()
    
    @property
    def tile_length(self) -> int:
        '''Gets ot sets tile length.'''
        raise NotImplementedError()
    
    @tile_length.setter
    def tile_length(self, value : int) -> None:
        '''Gets ot sets tile length.'''
        raise NotImplementedError()
    
    @property
    def sample_format(self) -> List[aspose.psd.fileformats.tiff.enums.TiffSampleFormats]:
        '''Gets the sample format.'''
        raise NotImplementedError()
    
    @sample_format.setter
    def sample_format(self, value : List[aspose.psd.fileformats.tiff.enums.TiffSampleFormats]) -> None:
        '''Sets the sample format.'''
        raise NotImplementedError()
    
    @property
    def samples_per_pixel(self) -> int:
        '''Gets the samples per pixel. To change this property value use the :py:attr:`aspose.psd.imageoptions.TiffOptions.bits_per_sample` property setter.'''
        raise NotImplementedError()
    
    @property
    def smax_sample_value(self) -> List[int]:
        '''Gets the max sample value. The value has a field type which best matches the sample data (Byte, Short or Long type).'''
        raise NotImplementedError()
    
    @smax_sample_value.setter
    def smax_sample_value(self, value : List[int]) -> None:
        '''Sets the max sample value. The value has a field type which best matches the sample data (Byte, Short or Long type).'''
        raise NotImplementedError()
    
    @property
    def smin_sample_value(self) -> List[int]:
        '''Gets the min sample value. The value has a field type which best matches the sample data (Byte, Short or Long type).'''
        raise NotImplementedError()
    
    @smin_sample_value.setter
    def smin_sample_value(self, value : List[int]) -> None:
        '''Sets the min sample value. The value has a field type which best matches the sample data (Byte, Short or Long type).'''
        raise NotImplementedError()
    
    @property
    def software_type(self) -> str:
        '''Gets the software type.'''
        raise NotImplementedError()
    
    @software_type.setter
    def software_type(self, value : str) -> None:
        '''Sets the software type.'''
        raise NotImplementedError()
    
    @property
    def strip_byte_counts(self) -> List[int]:
        '''Gets the strip byte counts.'''
        raise NotImplementedError()
    
    @strip_byte_counts.setter
    def strip_byte_counts(self, value : List[int]) -> None:
        '''Sets the strip byte counts.'''
        raise NotImplementedError()
    
    @property
    def strip_offsets(self) -> List[int]:
        '''Gets the strip offsets.'''
        raise NotImplementedError()
    
    @strip_offsets.setter
    def strip_offsets(self, value : List[int]) -> None:
        '''Sets the strip offsets.'''
        raise NotImplementedError()
    
    @property
    def tile_byte_counts(self) -> List[int]:
        '''Gets the tile byte counts.'''
        raise NotImplementedError()
    
    @tile_byte_counts.setter
    def tile_byte_counts(self, value : List[int]) -> None:
        '''Sets the tile byte counts.'''
        raise NotImplementedError()
    
    @property
    def tile_offsets(self) -> List[int]:
        '''Gets the tile offsets.'''
        raise NotImplementedError()
    
    @tile_offsets.setter
    def tile_offsets(self, value : List[int]) -> None:
        '''Sets the tile offsets.'''
        raise NotImplementedError()
    
    @property
    def sub_file_type(self) -> aspose.psd.fileformats.tiff.enums.TiffNewSubFileTypes:
        '''Gets a general indication of the kind of data contained in this subfile.'''
        raise NotImplementedError()
    
    @sub_file_type.setter
    def sub_file_type(self, value : aspose.psd.fileformats.tiff.enums.TiffNewSubFileTypes) -> None:
        '''Sets a general indication of the kind of data contained in this subfile.'''
        raise NotImplementedError()
    
    @property
    def target_printer(self) -> str:
        '''Gets the target printer.'''
        raise NotImplementedError()
    
    @target_printer.setter
    def target_printer(self, value : str) -> None:
        '''Sets the target printer.'''
        raise NotImplementedError()
    
    @property
    def threshholding(self) -> aspose.psd.fileformats.tiff.enums.TiffThresholds:
        '''Gets the threshholding.'''
        raise NotImplementedError()
    
    @threshholding.setter
    def threshholding(self, value : aspose.psd.fileformats.tiff.enums.TiffThresholds) -> None:
        '''Sets the threshholding.'''
        raise NotImplementedError()
    
    @property
    def total_pages(self) -> int:
        '''Gets the total pages.'''
        raise NotImplementedError()
    
    @property
    def xposition(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the x position.'''
        raise NotImplementedError()
    
    @xposition.setter
    def xposition(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the x position.'''
        raise NotImplementedError()
    
    @property
    def xresolution(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the x resolution.'''
        raise NotImplementedError()
    
    @xresolution.setter
    def xresolution(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the x resolution.'''
        raise NotImplementedError()
    
    @property
    def yposition(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the y position.'''
        raise NotImplementedError()
    
    @yposition.setter
    def yposition(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the y position.'''
        raise NotImplementedError()
    
    @property
    def yresolution(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the y resolution.'''
        raise NotImplementedError()
    
    @yresolution.setter
    def yresolution(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the y resolution.'''
        raise NotImplementedError()
    
    @property
    def fax_t4_options(self) -> aspose.psd.fileformats.tiff.enums.Group3Options:
        '''Gets the fax t4 options.'''
        raise NotImplementedError()
    
    @fax_t4_options.setter
    def fax_t4_options(self, value : aspose.psd.fileformats.tiff.enums.Group3Options) -> None:
        '''Sets the fax t4 options.'''
        raise NotImplementedError()
    
    @property
    def predictor(self) -> aspose.psd.fileformats.tiff.enums.TiffPredictor:
        '''Gets the predictor for LZW compression.'''
        raise NotImplementedError()
    
    @predictor.setter
    def predictor(self, value : aspose.psd.fileformats.tiff.enums.TiffPredictor) -> None:
        '''Sets the predictor for LZW compression.'''
        raise NotImplementedError()
    
    @property
    def image_length(self) -> int:
        '''Gets the image length.'''
        raise NotImplementedError()
    
    @image_length.setter
    def image_length(self, value : int) -> None:
        '''Sets the image length.'''
        raise NotImplementedError()
    
    @property
    def image_width(self) -> int:
        '''Gets the image width.'''
        raise NotImplementedError()
    
    @image_width.setter
    def image_width(self, value : int) -> None:
        '''Sets the image width.'''
        raise NotImplementedError()
    
    @property
    def exif_ifd(self) -> aspose.psd.fileformats.tiff.TiffExifIfd:
        '''Gets the pointer to EXIF IFD.'''
        raise NotImplementedError()
    
    @property
    def tags(self) -> List[aspose.psd.fileformats.tiff.TiffDataType]:
        '''Gets the tags.'''
        raise NotImplementedError()
    
    @tags.setter
    def tags(self, value : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Sets the tags.'''
        raise NotImplementedError()
    
    @property
    def valid_tag_count(self) -> int:
        '''Gets the valid tag count. This is not the total tags count but the number of tags which may be preserved.'''
        raise NotImplementedError()
    
    @property
    def bits_per_pixel(self) -> int:
        '''Gets the bits per pixel.'''
        raise NotImplementedError()
    
    @property
    def xp_title(self) -> str:
        '''Gets information about image, which used by Windows Explorer.'''
        raise NotImplementedError()
    
    @xp_title.setter
    def xp_title(self, value : str) -> None:
        '''Sets information about image, which used by Windows Explorer.'''
        raise NotImplementedError()
    
    @property
    def xp_comment(self) -> str:
        '''Gets comment on image, which used by Windows Explorer.'''
        raise NotImplementedError()
    
    @xp_comment.setter
    def xp_comment(self, value : str) -> None:
        '''Sets comment on image, which used by Windows Explorer.'''
        raise NotImplementedError()
    
    @property
    def xp_author(self) -> str:
        '''Gets image author, which used by Windows Explorer.'''
        raise NotImplementedError()
    
    @xp_author.setter
    def xp_author(self, value : str) -> None:
        '''Sets image author, which used by Windows Explorer.'''
        raise NotImplementedError()
    
    @property
    def xp_keywords(self) -> str:
        '''Gets subject image, which used by Windows Explorer.'''
        raise NotImplementedError()
    
    @xp_keywords.setter
    def xp_keywords(self, value : str) -> None:
        '''Sets subject image, which used by Windows Explorer.'''
        raise NotImplementedError()
    
    @property
    def xp_subject(self) -> str:
        '''Gets information about image, which used by Windows Explorer.'''
        raise NotImplementedError()
    
    @xp_subject.setter
    def xp_subject(self, value : str) -> None:
        '''Sets information about image, which used by Windows Explorer.'''
        raise NotImplementedError()
    

class TiffOptionsUtils:
    '''The tiff file format options utility class.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def get_valid_tags_count(tags : List[aspose.psd.fileformats.tiff.TiffDataType]) -> int:
        '''Gets the valid tags count.
        
        :param tags: The tags to validate.
        :returns: The valid tags count.'''
        raise NotImplementedError()
    

class VectorRasterizationOptions(aspose.psd.ImageOptionsBase):
    '''The vector rasterization options.'''
    
    def clone(self) -> aspose.psd.ImageOptionsBase:
        '''Clones this instance.
        
        :returns: Returns shallow copy of this instance'''
        raise NotImplementedError()
    
    def copy_to(self, vector_rasterization_options : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Copies to.
        
        :param vector_rasterization_options: The vector rasterization options.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def default_replacement_font(self) -> str:
        '''Gets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @default_replacement_font.setter
    def default_replacement_font(self, value : str) -> None:
        '''Sets the default replacement font (font that will be used to draw text when exporting to raster, if existing layer font in PSD file is not presented in system).
        To take proper name of default font can be used next code snippet:
        System.Drawing.Text.InstalledFontCollection col = new System.Drawing.Text.InstalledFontCollection();
        System.Drawing.FontFamily[] families = col.Families;
        string defaultFontName = families[0].Name;
        PsdLoadOptions psdLoadOptions = new PsdLoadOptions() { DefaultReplacementFont = defaultFontName });'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Gets the XMP metadata container.'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Sets the XMP metadata container.'''
        raise NotImplementedError()
    
    @property
    def source(self) -> aspose.psd.Source:
        '''Gets the source to create image in.'''
        raise NotImplementedError()
    
    @source.setter
    def source(self, value : aspose.psd.Source) -> None:
        '''Sets the source to create image in.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette.'''
        raise NotImplementedError()
    
    @property
    def resolution_settings(self) -> aspose.psd.ResolutionSetting:
        '''Gets the resolution settings.'''
        raise NotImplementedError()
    
    @resolution_settings.setter
    def resolution_settings(self, value : aspose.psd.ResolutionSetting) -> None:
        '''Sets the resolution settings.'''
        raise NotImplementedError()
    
    @property
    def vector_rasterization_options(self) -> aspose.psd.imageoptions.VectorRasterizationOptions:
        '''Gets the vector rasterization options.'''
        raise NotImplementedError()
    
    @vector_rasterization_options.setter
    def vector_rasterization_options(self, value : aspose.psd.imageoptions.VectorRasterizationOptions) -> None:
        '''Sets the vector rasterization options.'''
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
    def multi_page_options(self) -> aspose.psd.imageoptions.MultiPageOptions:
        '''The multipage options'''
        raise NotImplementedError()
    
    @multi_page_options.setter
    def multi_page_options(self, value : aspose.psd.imageoptions.MultiPageOptions) -> None:
        '''The multipage options'''
        raise NotImplementedError()
    
    @property
    def full_frame(self) -> bool:
        '''Gets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @full_frame.setter
    def full_frame(self, value : bool) -> None:
        '''Sets a value indicating whether [full frame].'''
        raise NotImplementedError()
    
    @property
    def border_x(self) -> float:
        '''Gets the border X.'''
        raise NotImplementedError()
    
    @border_x.setter
    def border_x(self, value : float) -> None:
        '''Sets the border X.'''
        raise NotImplementedError()
    
    @property
    def border_y(self) -> float:
        '''Gets the border Y.'''
        raise NotImplementedError()
    
    @border_y.setter
    def border_y(self, value : float) -> None:
        '''Sets the border Y.'''
        raise NotImplementedError()
    
    @property
    def center_drawing(self) -> bool:
        '''Gets a value indicating whether center drawing.'''
        raise NotImplementedError()
    
    @center_drawing.setter
    def center_drawing(self, value : bool) -> None:
        '''Sets a value indicating whether center drawing.'''
        raise NotImplementedError()
    
    @property
    def page_height(self) -> float:
        '''Gets the page height.'''
        raise NotImplementedError()
    
    @page_height.setter
    def page_height(self, value : float) -> None:
        '''Sets the page height.'''
        raise NotImplementedError()
    
    @property
    def page_size(self) -> aspose.psd.SizeF:
        '''Gets the page size.'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : aspose.psd.SizeF) -> None:
        '''Sets the page size.'''
        raise NotImplementedError()
    
    @property
    def page_width(self) -> float:
        '''Gets the page width.'''
        raise NotImplementedError()
    
    @page_width.setter
    def page_width(self, value : float) -> None:
        '''Sets the page width.'''
        raise NotImplementedError()
    
    @property
    def background_color(self) -> aspose.psd.Color:
        '''Gets a background color.'''
        raise NotImplementedError()
    
    @background_color.setter
    def background_color(self, value : aspose.psd.Color) -> None:
        '''Sets a background color.'''
        raise NotImplementedError()
    
    @property
    def draw_color(self) -> aspose.psd.Color:
        '''Gets a foreground color.'''
        raise NotImplementedError()
    
    @draw_color.setter
    def draw_color(self, value : aspose.psd.Color) -> None:
        '''Sets a foreground color.'''
        raise NotImplementedError()
    
    @property
    def smoothing_mode(self) -> aspose.psd.SmoothingMode:
        '''Gets the smoothing mode.'''
        raise NotImplementedError()
    
    @smoothing_mode.setter
    def smoothing_mode(self, value : aspose.psd.SmoothingMode) -> None:
        '''Sets the smoothing mode.'''
        raise NotImplementedError()
    
    @property
    def text_rendering_hint(self) -> aspose.psd.TextRenderingHint:
        '''Gets the text rendering hint.'''
        raise NotImplementedError()
    
    @text_rendering_hint.setter
    def text_rendering_hint(self, value : aspose.psd.TextRenderingHint) -> None:
        '''Sets the text rendering hint.'''
        raise NotImplementedError()
    

class MultiPageMode:
    '''Represents multipage mode'''
    
    PAGES : MultiPageMode
    '''Used page indicies'''
    TITLES : MultiPageMode
    '''Used page titles'''
    RANGE : MultiPageMode
    '''Used range of pages'''
    ALL_PAGES : MultiPageMode
    '''Used all pages'''

class PositioningTypes:
    '''Positioning and size types for graphics scene.'''
    
    DEFINED_BY_DOCUMENT : PositioningTypes
    '''The absolute positioning on the page that is defined by document page settings.'''
    DEFINED_BY_OPTIONS : PositioningTypes
    '''The absolute positioning on the page that is defined by options page settings.'''
    RELATIVE : PositioningTypes
    '''The relative positioning and size. Determined by the boundary of all graphics objects.'''

class RenderErrorCode:
    '''Represents possible missing sections in CAD file'''
    
    MISSING_HEADER : RenderErrorCode
    '''Header is missing'''
    MISSING_LAYOUTS : RenderErrorCode
    '''Layouts information is missing'''
    MISSING_BLOCKS : RenderErrorCode
    '''Block information is missing'''
    MISSING_DIMENSION_STYLES : RenderErrorCode
    '''Dimension styles information is missing'''
    MISSING_STYLES : RenderErrorCode
    '''Styles information is missing'''

class TiffOptionsError:
    '''The tiff options error codes.'''
    
    NO_ERROR : TiffOptionsError
    '''No error code.'''
    NO_COLOR_MAP : TiffOptionsError
    '''The color map is not defined.'''
    COLOR_MAP_LENGTH_INVALID : TiffOptionsError
    '''The color map length is invalid.'''
    COMPRESSION_SPP_MISMATCH : TiffOptionsError
    '''The compression does not match the samples per pixel count.'''
    PHOTOMETRIC_COMPRESSION_MISMATCH : TiffOptionsError
    '''The compression does not match the photometric settings.'''
    PHOTOMETRIC_SPP_MISMATCH : TiffOptionsError
    '''The photometric does not match the samples per pixel count.'''
    NOT_SUPPORTED_ALPHA_STORAGE : TiffOptionsError
    '''The alpha storage is not supported.'''
    PHOTOMETRIC_BITS_PER_SAMPLE_MISMATCH : TiffOptionsError
    '''The photometric bits per sample is invalid'''
    BASELINE_6_OPTIONS_MISMATCH : TiffOptionsError
    '''The specified TIFF options parameters don\'t conform to TIFF Baseline 6.0 standard'''

class TypeOfEntities:
    '''Represents types of entities to render'''
    
    ENTITIES_2D : TypeOfEntities
    '''Render 2D entities'''
    ENTITIES_3D : TypeOfEntities
    '''Render 3D entities'''

