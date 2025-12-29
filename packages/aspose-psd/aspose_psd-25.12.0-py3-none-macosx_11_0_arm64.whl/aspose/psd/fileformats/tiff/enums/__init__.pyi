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

class Group3Options:
    '''Options for CCITT Group 3/4 fax encoding.
    
    Possible values for GROUP3OPTIONS / TiffTag.T4OPTIONS and
    TiffTag.GROUP4OPTIONS / TiffTag.T6OPTIONS tags.'''
    
    ENCODING_1D : Group3Options
    '''1-dimensional coding. (default)'''
    ENCODING_2D : Group3Options
    '''2-dimensional coding.'''
    UNCOMPRESSED : Group3Options
    '''Data not compressed.'''
    FILL_BITS : Group3Options
    '''Fill to byte boundary.'''

class TiffAlphaStorage:
    '''Specifies the alpha storage for tiff documents.'''
    
    UNSPECIFIED : TiffAlphaStorage
    '''The alpha is not specified and stored in the tiff file.'''
    ASSOCIATED : TiffAlphaStorage
    '''The alpha value is stored in premultiplied form. When alpha is restored there may be some rounding effects and restored value may be different from the original.'''
    UNASSOCIATED : TiffAlphaStorage
    '''The alpha value is stored in unassociated form. That means that alpha restored is exactly the same as it was stored to the tiff.'''

class TiffByteOrder:
    '''The byte order for the tiff image'''
    
    BIG_ENDIAN : TiffByteOrder
    '''The big endian byte order (Motorola).'''
    LITTLE_ENDIAN : TiffByteOrder
    '''The little endian byte order (Intel).'''

class TiffCompressions:
    '''Holds compression types'''
    
    NONE : TiffCompressions
    '''Dump mode.'''
    CCITT_RLE : TiffCompressions
    '''CCITT modified Huffman RLE.'''
    CCITT_FAX3 : TiffCompressions
    '''CCITT Group 3 fax encoding.'''
    CCITT_FAX4 : TiffCompressions
    '''CCITT Group 4 fax encoding.'''
    LZW : TiffCompressions
    '''Lempel-Ziv & Welch.'''
    OJPEG : TiffCompressions
    '''Original JPEG / Old-style JPEG (6.0).'''
    JPEG : TiffCompressions
    '''JPEG DCT compression. Introduced post TIFF rev 6.0.'''
    NEXT : TiffCompressions
    '''NeXT 2-bit RLE.'''
    CCITT_RLE_W : TiffCompressions
    '''CCITT RLE.'''
    PACKBITS : TiffCompressions
    '''Macintosh RLE.'''
    THUNDERSCAN : TiffCompressions
    '''ThunderScan RLE.'''
    IT_8_CTPAD : TiffCompressions
    '''IT8 CT w/padding. Reserved for ANSI IT8 TIFF/IT.'''
    IT_8_LW : TiffCompressions
    '''IT8 Linework RLE. Reserved for ANSI IT8 TIFF/IT.'''
    IT_8_MP : TiffCompressions
    '''IT8 Monochrome picture. Reserved for ANSI IT8 TIFF/IT.'''
    IT_8_BL : TiffCompressions
    '''IT8 Binary line art. Reserved for ANSI IT8 TIFF/IT.'''
    PIXAR_FILM : TiffCompressions
    '''Pixar companded 10bit LZW. Reserved for Pixar.'''
    PIXAR_LOG : TiffCompressions
    '''Pixar companded 11bit ZIP. Reserved for Pixar.'''
    DEFLATE : TiffCompressions
    '''Deflate compression.'''
    ADOBE_DEFLATE : TiffCompressions
    '''Deflate compression, as recognized by Adobe.'''
    DCS : TiffCompressions
    '''Kodak DCS encoding.
    Reserved for Oceana Matrix'''
    JBIG : TiffCompressions
    '''ISO Jpeg big.'''
    SGILOG : TiffCompressions
    '''SGI Log Luminance RLE.'''
    SGILOG24 : TiffCompressions
    '''SGI Log 24-bit packed.'''
    JP2000 : TiffCompressions
    '''Leadtools JPEG2000.'''

class TiffDataTypes:
    '''The tiff data type enum.'''
    
    BYTE : TiffDataTypes
    '''8-bit unsigned integer.'''
    ASCII : TiffDataTypes
    '''8-bit bytes with last byte ``null``.'''
    SHORT : TiffDataTypes
    '''16-bit unsigned integer.'''
    LONG : TiffDataTypes
    '''32-bit unsigned integer.'''
    RATIONAL : TiffDataTypes
    '''64-bit unsigned fraction.'''
    SBYTE : TiffDataTypes
    '''8-bit signed integer.'''
    UNDEFINED : TiffDataTypes
    '''8-bit untyped data.'''
    SSHORT : TiffDataTypes
    '''16-bit signed integer.'''
    SLONG : TiffDataTypes
    '''32-bit signed integer.'''
    SRATIONAL : TiffDataTypes
    '''64-bit signed fraction.'''
    FLOAT : TiffDataTypes
    '''32-bit IEEE floating point.'''
    DOUBLE : TiffDataTypes
    '''64-bit IEEE floating point.'''
    IFD : TiffDataTypes
    '''Pointer to Exif image file directory (IFD).'''

class TiffExpectedFormat:
    '''The expected tiff file format.'''
    
    DEFAULT : TiffExpectedFormat
    '''The default tiff format is no compression with B/W 1 bit per pixel only format. You can also use this setting to get an empty options and initialize with your tags or other settings.'''
    TIFF_LZW_BW : TiffExpectedFormat
    '''The tiff having LZW compression and B/W 1 bit per pixel only format.'''
    TIFF_LZW_RGB : TiffExpectedFormat
    '''The tiff having LZW compression and RGB color format.'''
    TIFF_LZW_RGBA : TiffExpectedFormat
    '''The tiff having LZW compression and RGBA with transparency color format.'''
    TIFF_LZW_CMYK : TiffExpectedFormat
    '''The tiff LZW cmyk'''
    TIFF_CCITT_FAX3 : TiffExpectedFormat
    '''The tiff CCITT FAX3 encoding. B/W 1 bit per pixel only supported for that scheme.'''
    TIFF_CCITT_FAX4 : TiffExpectedFormat
    '''The tiff CCITT FAX4 encoding. B/W 1 bit per pixel only supported for that scheme.'''
    TIFF_DEFLATE_BW : TiffExpectedFormat
    '''The tiff having deflate compression and B/W 1 bit per pixel only format.'''
    TIFF_DEFLATE_RGB : TiffExpectedFormat
    '''The tiff having deflate compression and RGB color format.'''
    TIFF_DEFLATE_RGBA : TiffExpectedFormat
    '''The tiff having deflate compression and RGBA color format.'''
    TIFF_CCIT_RLE : TiffExpectedFormat
    '''The tiff CCITT RLE encoding. B/W 1 bit per pixel only supported for that scheme.'''
    TIFF_JPEG_RGB : TiffExpectedFormat
    '''The tiff having Jpeg compression and RGB color format.'''
    TIFF_JPEG_Y_CB_CR : TiffExpectedFormat
    '''The tiff having Jpeg compression and YCBCR color format.'''
    TIFF_NO_COMPRESSION_BW : TiffExpectedFormat
    '''The uncompressed tiff and B/W 1 bit per pixel only format.'''
    TIFF_NO_COMPRESSION_RGB : TiffExpectedFormat
    '''The uncompressed tiff and RGB color format.'''
    TIFF_NO_COMPRESSION_RGBA : TiffExpectedFormat
    '''The uncompressed tiff and RGBA with transparency color format.'''

class TiffFileStandards:
    '''Specifies the TIFF file format standards.'''
    
    BASELINE : TiffFileStandards
    '''The Baseline TIFF 6.0 file standard. This standard is formally known as TIFF 6.0, Part 1: Baseline TIFF.'''
    EXTENDED : TiffFileStandards
    '''The Extended TIFF 6.0 file standard. This standard is formally known as Extended TIFF 6.0, Part 2: TIFF Extensions.'''

class TiffFillOrders:
    '''Data order within a byte.
    
    Possible values for FILLORDER tag.'''
    
    MSB_2_LSB : TiffFillOrders
    '''Most significant -> least.'''
    LSB_2_MSB : TiffFillOrders
    '''Least significant -> most.'''

class TiffNewSubFileTypes:
    '''The tiff new sub file type enum.'''
    
    FILE_TYPE_DEFAULT : TiffNewSubFileTypes
    '''The default filetype.'''
    FILE_TYPE_REDUCED_IMAGE : TiffNewSubFileTypes
    '''The reduced image filetype.'''
    FILE_TYPE_PAGE : TiffNewSubFileTypes
    '''The page filetype.'''
    FILE_TYPE_MASK : TiffNewSubFileTypes
    '''The mask filetype.'''
    FILE_TYPE_LAST : TiffNewSubFileTypes
    '''The last filetype.'''

class TiffOrientations:
    '''Image orientation.
    
    Possible values for ORIENTATION tag.'''
    
    TOP_LEFT : TiffOrientations
    '''Row 0 top, Column 0 lhs.'''
    TOP_RIGHT : TiffOrientations
    '''Row 0 top, Column 0 rhs.'''
    BOTTOM_RIGHT : TiffOrientations
    '''Row 0 bottom, Column 0 rhs.'''
    BOTTOM_LEFT : TiffOrientations
    '''Row 0 bottom, Column 0 lhs.'''
    LEFT_TOP : TiffOrientations
    '''Row 0 lhs, Column 0 top.'''
    RIGHT_TOP : TiffOrientations
    '''Row 0 rhs, Column 0 top.'''
    RIGHT_BOTTOM : TiffOrientations
    '''Row 0 rhs, Column 0 bottom.'''
    LEFT_BOTTOM : TiffOrientations
    '''Row 0 lhs, Column 0 bottom.'''

class TiffPhotometrics:
    '''Photometric interpolation enum'''
    
    MIN_IS_WHITE : TiffPhotometrics
    '''Min value is white.'''
    MIN_IS_BLACK : TiffPhotometrics
    '''Min value is black.'''
    RGB : TiffPhotometrics
    '''RGB color model.'''
    PALETTE : TiffPhotometrics
    '''Color map indexed.'''
    MASK : TiffPhotometrics
    '''[obsoleted by TIFF rev. 6.0] Holdout mask.'''
    SEPARATED : TiffPhotometrics
    '''Color separations.'''
    YCBCR : TiffPhotometrics
    '''The CCIR 601.'''
    CIELAB : TiffPhotometrics
    '''1976 CIE L*a*b*.'''
    ICCLAB : TiffPhotometrics
    '''ICC L*a*b*. Introduced post TIFF rev 6.0 by Adobe TIFF Technote 4.'''
    ITULAB : TiffPhotometrics
    '''ITU L*a*b*.'''
    LOGL : TiffPhotometrics
    '''CIE Log2(L).'''
    LOGLUV : TiffPhotometrics
    '''CIE Log2(L) (u\',v\').'''

class TiffPlanarConfigs:
    '''Storage organization.
    
    Possible values for PLANARCONFIG tag.'''
    
    CONTIGUOUS : TiffPlanarConfigs
    '''Single image plane.'''
    SEPARATE : TiffPlanarConfigs
    '''Separate planes of data.'''

class TiffPredictor:
    '''Prediction scheme for LZW'''
    
    NONE : TiffPredictor
    '''No prediction scheme used.'''
    HORIZONTAL : TiffPredictor
    '''Horizontal differencing.'''

class TiffResolutionUnits:
    '''Tiff Resolution Unit Enum'''
    
    NONE : TiffResolutionUnits
    '''No meaningful units.'''
    INCH : TiffResolutionUnits
    '''English system.'''
    CENTIMETER : TiffResolutionUnits
    '''Metric system.'''

class TiffSampleFormats:
    '''Sample format enum'''
    
    UINT : TiffSampleFormats
    '''Unsigned integer data'''
    INT : TiffSampleFormats
    '''Signed integer data'''
    IEEE_FP : TiffSampleFormats
    '''IEEE floating point data'''
    VOID : TiffSampleFormats
    '''Untyped data'''
    COMPLEX_INT : TiffSampleFormats
    '''Complex signed int'''
    COMPLEX_IEEE_FP : TiffSampleFormats
    '''Complex ieee floating'''

class TiffTags:
    '''The tiff tag enum.'''
    
    SUB_FILE_TYPE : TiffTags
    '''Subfile data descriptor.'''
    OSUBFILE_TYPE : TiffTags
    '''[obsoleted by TIFF rev. 5.0]
    
    Kind of data in subfile.'''
    IMAGE_WIDTH : TiffTags
    '''Image width in pixels.'''
    IMAGE_LENGTH : TiffTags
    '''Image height in pixels.'''
    BITS_PER_SAMPLE : TiffTags
    '''Bits per channel (sample).'''
    COMPRESSION : TiffTags
    '''Data compression technique.'''
    PHOTOMETRIC : TiffTags
    '''Photometric interpretation.'''
    THRESHOLDING : TiffTags
    '''[obsoleted by TIFF rev. 5.0]
    
    Thresholding used on data.'''
    CELL_WIDTH : TiffTags
    '''[obsoleted by TIFF rev. 5.0]
    
    Dithering matrix width.'''
    CELL_LENGTH : TiffTags
    '''[obsoleted by TIFF rev. 5.0]
    
    Dithering matrix height.'''
    FILL_ORDER : TiffTags
    '''Data order within a byte.'''
    DOCUMENT_NAME : TiffTags
    '''Name of document which holds for image.'''
    IMAGE_DESCRIPTION : TiffTags
    '''Information about image.'''
    MAKE : TiffTags
    '''Scanner manufacturer name.'''
    MODEL : TiffTags
    '''Scanner model name/number.'''
    STRIP_OFFSETS : TiffTags
    '''Offsets to data strips.'''
    ORIENTATION : TiffTags
    '''[obsoleted by TIFF rev. 5.0]
    
    Image orientation.'''
    SAMPLES_PER_PIXEL : TiffTags
    '''Samples per pixel.'''
    ROWS_PER_STRIP : TiffTags
    '''Rows per strip of data.'''
    STRIP_BYTE_COUNTS : TiffTags
    '''Bytes counts for strips.'''
    MIN_SAMPLE_VALUE : TiffTags
    '''[obsoleted by TIFF rev. 5.0]
    
    Minimum sample value.'''
    MAX_SAMPLE_VALUE : TiffTags
    '''[obsoleted by TIFF rev. 5.0]
    
    Maximum sample value.'''
    XRESOLUTION : TiffTags
    '''Pixels/resolution in x.'''
    YRESOLUTION : TiffTags
    '''Pixels/resolution in y.'''
    PLANAR_CONFIG : TiffTags
    '''Storage organization.'''
    PAGE_NAME : TiffTags
    '''Page name image is from.'''
    XPOSITION : TiffTags
    '''X page offset of image lhs.'''
    YPOSITION : TiffTags
    '''Y page offset of image lhs.'''
    FREE_OFFSETS : TiffTags
    '''[obsoleted by TIFF rev. 5.0]
    
    Byte offset to free block.'''
    FREE_BYTE_COUNTS : TiffTags
    '''[obsoleted by TIFF rev. 5.0]
    
    Sizes of free blocks.'''
    GRAY_RESPONSE_UNIT : TiffTags
    '''[obsoleted by TIFF rev. 6.0]
    
    Gray scale curve accuracy.'''
    GRAY_RESPONSE_CURVE : TiffTags
    '''[obsoleted by TIFF rev. 6.0]
    
    Gray scale response curve.'''
    T4_OPTIONS : TiffTags
    '''TIFF 6.0 proper name alias for GROUP3OPTIONS.
    Options for CCITT Group 3 fax encoding. 32 flag bits.'''
    T6_OPTIONS : TiffTags
    '''Options for CCITT Group 4 fax encoding. 32 flag bits.
    TIFF 6.0 proper name alias for GROUP4OPTIONS.'''
    RESOLUTION_UNIT : TiffTags
    '''Units of resolutions.'''
    PAGE_NUMBER : TiffTags
    '''Page numbers of multi-page.'''
    COLOR_RESPONSE_UNIT : TiffTags
    '''[obsoleted by TIFF rev. 6.0]
    
    Color curve accuracy.'''
    TRANSFER_FUNCTION : TiffTags
    '''Colorimetry info.'''
    SOFTWARE : TiffTags
    '''Name & release.'''
    DATE_TIME : TiffTags
    '''Creation date and time.'''
    ARTIST : TiffTags
    '''Creator of image.'''
    HOST_COMPUTER : TiffTags
    '''Machine where created.'''
    PREDICTOR : TiffTags
    '''Prediction scheme w/ LZW.'''
    WHITE_POINT : TiffTags
    '''Image white point.'''
    PRIMARY_CHROMATICITIES : TiffTags
    '''Primary chromaticities.'''
    COLOR_MAP : TiffTags
    '''RGB map for pallette image.'''
    HALFTONE_HINTS : TiffTags
    '''Highlight + shadow info.'''
    TILE_WIDTH : TiffTags
    '''Tile width in pixels.'''
    TILE_LENGTH : TiffTags
    '''Tile height in pixels.'''
    TILE_OFFSETS : TiffTags
    '''Offsets to data tiles.'''
    TILE_BYTE_COUNTS : TiffTags
    '''Byte counts for tiles.'''
    BAD_FAX_LINES : TiffTags
    '''Lines with wrong pixel count.'''
    CLEAN_FAX_DATA : TiffTags
    '''Regenerated line info.'''
    CONSECUTIVE_BAD_FAX_LINES : TiffTags
    '''Max consecutive bad lines.'''
    SUB_IFD : TiffTags
    '''Subimage descriptors.'''
    INK_SET : TiffTags
    '''Inks in separated image.'''
    INK_NAMES : TiffTags
    '''ASCII names of inks.'''
    NUMBER_OF_INKS : TiffTags
    '''Number of inks.'''
    DOT_RANGE : TiffTags
    '''0% and 100% dot codes.'''
    TARGET_PRINTER : TiffTags
    '''Separation target.'''
    EXTRA_SAMPLES : TiffTags
    '''Information about extra samples.'''
    SAMPLE_FORMAT : TiffTags
    '''Data sample format.'''
    SMIN_SAMPLE_VALUE : TiffTags
    '''Variable MinSampleValue.'''
    SMAX_SAMPLE_VALUE : TiffTags
    '''Variable MaxSampleValue.'''
    TRANSFER_RANGE : TiffTags
    '''Variable TransferRange'''
    CLIP_PATH : TiffTags
    '''ClipPath. Introduced post TIFF rev 6.0 by Adobe TIFF technote 2.'''
    XCLIPPATHUNITS : TiffTags
    '''XClipPathUnits. Introduced post TIFF rev 6.0 by Adobe TIFF technote 2.'''
    YCLIPPATHUNITS : TiffTags
    '''YClipPathUnits. Introduced post TIFF rev 6.0 by Adobe TIFF technote 2.'''
    INDEXED : TiffTags
    '''Indexed. Introduced post TIFF rev 6.0 by Adobe TIFF Technote 3.'''
    JPEG_TABLES : TiffTags
    '''JPEG table stream. Introduced post TIFF rev 6.0.'''
    OPI_PROXY : TiffTags
    '''OPI Proxy. Introduced post TIFF rev 6.0 by Adobe TIFF technote.'''
    JPEG_PROC : TiffTags
    '''[obsoleted by Technical Note #2 which specifies a revised JPEG-in-TIFF scheme]
    
    JPEG processing algorithm.'''
    JPEG_INERCHANGE_FORMAT : TiffTags
    '''[obsoleted by Technical Note #2 which specifies a revised JPEG-in-TIFF scheme]
    
    Pointer to SOI marker.'''
    JPEG_INTERCHANGE_FORMAT_LENGTH : TiffTags
    '''[obsoleted by Technical Note #2 which specifies a revised JPEG-in-TIFF scheme]
    
    JFIF stream length'''
    JPEG_RESTART_INTERVAL : TiffTags
    '''[obsoleted by Technical Note #2 which specifies a revised JPEG-in-TIFF scheme]
    
    Restart interval length.'''
    JPEG_LOSSLESS_PREDICTORS : TiffTags
    '''[obsoleted by Technical Note #2 which specifies a revised JPEG-in-TIFF scheme]
    
    Lossless proc predictor.'''
    JPEG_POINT_TRANSFORM : TiffTags
    '''[obsoleted by Technical Note #2 which specifies a revised JPEG-in-TIFF scheme]
    
    Lossless point transform.'''
    JPEG_Q_TABLES : TiffTags
    '''[obsoleted by Technical Note #2 which specifies a revised JPEG-in-TIFF scheme]
    
    Q matrice offsets.'''
    JPEG_D_CTABLES : TiffTags
    '''[obsoleted by Technical Note #2 which specifies a revised JPEG-in-TIFF scheme]
    
    DCT table offsets.'''
    JPEG_A_CTABLES : TiffTags
    '''[obsoleted by Technical Note #2 which specifies a revised JPEG-in-TIFF scheme]
    
    AC coefficient offsets.'''
    YCBCR_COEFFICIENTS : TiffTags
    '''RGB -> YCbCr transform.'''
    YCBCR_SUB_SAMPLING : TiffTags
    '''YCbCr subsampling factors.'''
    YCBCR_POSITIONING : TiffTags
    '''Subsample positioning.'''
    REFERENCE_BLACK_WHITE : TiffTags
    '''Colorimetry info.'''
    XML_PACKET : TiffTags
    '''XML packet. Introduced post TIFF rev 6.0 by Adobe XMP Specification, January 2004.'''
    OPI_IMAGEID : TiffTags
    '''OPI ImageID. Introduced post TIFF rev 6.0 by Adobe TIFF technote.'''
    REFPTS : TiffTags
    '''Image reference points. Private tag registered to Island Graphics.'''
    COPYRIGHT : TiffTags
    '''Copyright string. This tag is listed in the TIFF rev. 6.0 w/ unknown ownership.'''
    PHOTOSHOP_RESOURCES : TiffTags
    '''Photoshop image resources.'''
    ICC_PROFILE : TiffTags
    '''The embedded ICC device profile'''
    EXIF_IFD_POINTER : TiffTags
    '''A pointer to the Exif IFD.'''
    XP_TITLE : TiffTags
    '''Information about image, used by Windows Explorer.
    The :py:attr:`aspose.psd.fileformats.tiff.enums.TiffTags.XP_TITLE` is ignored by Windows Explorer if the :py:attr:`aspose.psd.fileformats.tiff.enums.TiffTags.IMAGE_DESCRIPTION` tag exists.'''
    XP_COMMENT : TiffTags
    '''Comment on image, used by Windows Explorer.'''
    XP_AUTHOR : TiffTags
    '''Image Author, used by Windows Explorer.
    The :py:attr:`aspose.psd.fileformats.tiff.enums.TiffTags.XP_AUTHOR` is ignored by Windows Explorer if the :py:attr:`aspose.psd.fileformats.tiff.enums.TiffTags.ARTIST` tag exists.'''
    XP_KEYWORDS : TiffTags
    '''Image Keywords, used by Windows Explorer.'''
    XP_SUBJECT : TiffTags
    '''Subject image, used by Windows Explorer.'''

class TiffThresholds:
    '''Thresholding used on data.'''
    
    NO_DITHERING : TiffThresholds
    '''No dithering is performed.'''
    HALF_TONE : TiffThresholds
    '''Dithered scan.'''
    ERROR_DIFFUSE : TiffThresholds
    '''Usually Floyd-Steinberg.'''

