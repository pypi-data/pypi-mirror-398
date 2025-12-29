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

class IText:
    '''Interface for Text Editing for Text Layers'''
    
    def produce_portion(self) -> aspose.psd.fileformats.psd.layers.text.ITextPortion:
        '''Produces the new portion with default parameters
        
        :returns: Reference to newly created :py:class:`aspose.psd.fileformats.psd.layers.text.ITextPortion`.'''
        raise NotImplementedError()
    
    def produce_portions(self, portions_of_text : List[str], style_prototype : aspose.psd.fileformats.psd.layers.text.ITextStyle, paragraph_prototype : aspose.psd.fileformats.psd.layers.text.ITextParagraph) -> List[aspose.psd.fileformats.psd.layers.text.ITextPortion]:
        '''Produces the new portions with input or default parameters.
        
        :param portions_of_text: The portions of text to create new :py:class:`aspose.psd.fileformats.psd.layers.text.ITextPortion`.
        :param style_prototype: A style that, if not null, will be applied in the new :py:class:`aspose.psd.fileformats.psd.layers.text.ITextPortion`, otherwise will be default.
        :param paragraph_prototype: A paragraph that, if not null, will be applied in the new :py:class:`aspose.psd.fileformats.psd.layers.text.ITextPortion`, otherwise will be default.
        :returns: Returns the new portions :py:class:`aspose.psd.fileformats.psd.layers.text.ITextPortion` based on input parameters.'''
        raise NotImplementedError()
    
    def add_portion(self, portion : aspose.psd.fileformats.psd.layers.text.ITextPortion) -> None:
        '''Adds the portion of text to the end
        
        :param portion: The portion.'''
        raise NotImplementedError()
    
    def insert_portion(self, portion : aspose.psd.fileformats.psd.layers.text.ITextPortion, index : int) -> None:
        '''Inserts the :py:class:`aspose.psd.fileformats.psd.layers.text.ITextPortion` to specified position
        
        :param portion: The portion.
        :param index: The index.'''
        raise NotImplementedError()
    
    def remove_portion(self, index : int) -> None:
        '''Removes the portion in specified index
        
        :param index: The index.'''
        raise NotImplementedError()
    
    def update_layer_data(self) -> None:
        '''Updates the layer data.'''
        raise NotImplementedError()
    
    @property
    def items(self) -> List[aspose.psd.fileformats.psd.layers.text.ITextPortion]:
        '''Gets the items.'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Gets the text.'''
        raise NotImplementedError()
    
    @property
    def text_orientation(self) -> aspose.psd.fileformats.psd.TextOrientation:
        '''Gets the text orientation.'''
        raise NotImplementedError()
    
    @text_orientation.setter
    def text_orientation(self, value : aspose.psd.fileformats.psd.TextOrientation) -> None:
        '''Sets the text orientation.'''
        raise NotImplementedError()
    

class ITextParagraph:
    '''The interface to work with paragraph'''
    
    def apply(self, paragraph : aspose.psd.fileformats.psd.layers.text.ITextParagraph) -> None:
        '''Applies the specified paragraph.
        
        :param paragraph: The paragraph.'''
        raise NotImplementedError()
    
    def is_equal(self, paragraph : aspose.psd.fileformats.psd.layers.text.ITextParagraph) -> bool:
        '''Determines whether the specified paragraph is equal.
        
        :param paragraph: The paragraph.
        :returns: ``true`` if the specified paragraph is equal; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def justification(self) -> aspose.psd.fileformats.psd.JustificationMode:
        '''Gets the justification.'''
        raise NotImplementedError()
    
    @justification.setter
    def justification(self, value : aspose.psd.fileformats.psd.JustificationMode) -> None:
        '''Sets the justification.'''
        raise NotImplementedError()
    
    @property
    def first_line_indent(self) -> float:
        '''Gets the first line indent.'''
        raise NotImplementedError()
    
    @first_line_indent.setter
    def first_line_indent(self, value : float) -> None:
        '''Sets the first line indent.'''
        raise NotImplementedError()
    
    @property
    def start_indent(self) -> float:
        '''Gets the start indent.'''
        raise NotImplementedError()
    
    @start_indent.setter
    def start_indent(self, value : float) -> None:
        '''Sets the start indent.'''
        raise NotImplementedError()
    
    @property
    def end_indent(self) -> float:
        '''Gets the end indent.'''
        raise NotImplementedError()
    
    @end_indent.setter
    def end_indent(self, value : float) -> None:
        '''Sets the end indent.'''
        raise NotImplementedError()
    
    @property
    def space_before(self) -> float:
        '''Gets the space before.'''
        raise NotImplementedError()
    
    @space_before.setter
    def space_before(self, value : float) -> None:
        '''Sets the space before.'''
        raise NotImplementedError()
    
    @property
    def space_after(self) -> float:
        '''Gets the space after.'''
        raise NotImplementedError()
    
    @space_after.setter
    def space_after(self, value : float) -> None:
        '''Sets the space after.'''
        raise NotImplementedError()
    
    @property
    def auto_hyphenate(self) -> bool:
        '''Gets a value indicating whether [automatic hyphenate].'''
        raise NotImplementedError()
    
    @auto_hyphenate.setter
    def auto_hyphenate(self, value : bool) -> None:
        '''Sets a value indicating whether [automatic hyphenate].'''
        raise NotImplementedError()
    
    @property
    def hyphenated_word_size(self) -> int:
        '''Gets the size of the hyphenated word.'''
        raise NotImplementedError()
    
    @hyphenated_word_size.setter
    def hyphenated_word_size(self, value : int) -> None:
        '''Sets the size of the hyphenated word.'''
        raise NotImplementedError()
    
    @property
    def pre_hyphen(self) -> int:
        '''Gets the pre hyphen.'''
        raise NotImplementedError()
    
    @pre_hyphen.setter
    def pre_hyphen(self, value : int) -> None:
        '''Sets the pre hyphen.'''
        raise NotImplementedError()
    
    @property
    def post_hyphen(self) -> int:
        '''Gets the post hyphen.'''
        raise NotImplementedError()
    
    @post_hyphen.setter
    def post_hyphen(self, value : int) -> None:
        '''Sets the post hyphen.'''
        raise NotImplementedError()
    
    @property
    def consecutive_hyphens(self) -> int:
        '''Gets the consecutive hyphens.'''
        raise NotImplementedError()
    
    @consecutive_hyphens.setter
    def consecutive_hyphens(self, value : int) -> None:
        '''Sets the consecutive hyphens.'''
        raise NotImplementedError()
    
    @property
    def zone(self) -> float:
        '''Gets the zone.'''
        raise NotImplementedError()
    
    @zone.setter
    def zone(self, value : float) -> None:
        '''Sets the zone.'''
        raise NotImplementedError()
    
    @property
    def word_spacing(self) -> List[float]:
        '''Gets the word spacing.'''
        raise NotImplementedError()
    
    @word_spacing.setter
    def word_spacing(self, value : List[float]) -> None:
        '''Sets the word spacing.'''
        raise NotImplementedError()
    
    @property
    def letter_spacing(self) -> List[float]:
        '''Gets the letter spacing.'''
        raise NotImplementedError()
    
    @letter_spacing.setter
    def letter_spacing(self, value : List[float]) -> None:
        '''Sets the letter spacing.'''
        raise NotImplementedError()
    
    @property
    def glyph_spacing(self) -> List[float]:
        '''Gets the glyph spacing.'''
        raise NotImplementedError()
    
    @glyph_spacing.setter
    def glyph_spacing(self, value : List[float]) -> None:
        '''Sets the glyph spacing.'''
        raise NotImplementedError()
    
    @property
    def auto_leading(self) -> float:
        '''Gets the automatic leading.'''
        raise NotImplementedError()
    
    @auto_leading.setter
    def auto_leading(self, value : float) -> None:
        '''Sets the automatic leading.'''
        raise NotImplementedError()
    
    @property
    def leading_type(self) -> aspose.psd.fileformats.psd.LeadingType:
        '''Gets the type of the leading.'''
        raise NotImplementedError()
    
    @leading_type.setter
    def leading_type(self, value : aspose.psd.fileformats.psd.LeadingType) -> None:
        '''Sets the type of the leading.'''
        raise NotImplementedError()
    
    @property
    def hanging(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.text.ITextParagraph` is hanging.'''
        raise NotImplementedError()
    
    @hanging.setter
    def hanging(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.text.ITextParagraph` is hanging.'''
        raise NotImplementedError()
    
    @property
    def burasagari(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.text.ITextParagraph` is burasagiri.'''
        raise NotImplementedError()
    
    @burasagari.setter
    def burasagari(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.text.ITextParagraph` is burasagiri.'''
        raise NotImplementedError()
    
    @property
    def kinsoku_order(self) -> int:
        '''Gets the kinsoku order.'''
        raise NotImplementedError()
    
    @kinsoku_order.setter
    def kinsoku_order(self, value : int) -> None:
        '''Sets the kinsoku order.'''
        raise NotImplementedError()
    
    @property
    def every_line_composer(self) -> bool:
        '''Gets a value indicating whether [every line composer].'''
        raise NotImplementedError()
    
    @every_line_composer.setter
    def every_line_composer(self, value : bool) -> None:
        '''Sets a value indicating whether [every line composer].'''
        raise NotImplementedError()
    

class ITextPortion:
    '''Interface to manipulate text portions'''
    
    @property
    def text(self) -> str:
        '''Gets the text.'''
        raise NotImplementedError()
    
    @text.setter
    def text(self, value : str) -> None:
        '''Sets the text.'''
        raise NotImplementedError()
    
    @property
    def style(self) -> aspose.psd.fileformats.psd.layers.text.ITextStyle:
        '''Gets the style.'''
        raise NotImplementedError()
    
    @property
    def paragraph(self) -> aspose.psd.fileformats.psd.layers.text.ITextParagraph:
        '''Sets the style.'''
        raise NotImplementedError()
    

class ITextStyle:
    '''Interface to work with Text Style'''
    
    def apply(self, style : aspose.psd.fileformats.psd.layers.text.ITextStyle) -> None:
        '''Applies the specified style.
        
        :param style: The style.'''
        raise NotImplementedError()
    
    def is_equal(self, style : aspose.psd.fileformats.psd.layers.text.ITextStyle) -> bool:
        '''Determines whether the specified style is equal.
        
        :param style: The style.
        :returns: ``true`` if the specified style is equal; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def font_size(self) -> float:
        '''Gets the size of the font.'''
        raise NotImplementedError()
    
    @font_size.setter
    def font_size(self, value : float) -> None:
        '''Sets the size of the font.'''
        raise NotImplementedError()
    
    @property
    def font_index(self) -> int:
        '''Gets the font index.'''
        raise NotImplementedError()
    
    @property
    def font_name(self) -> str:
        '''Gets the font name.'''
        raise NotImplementedError()
    
    @font_name.setter
    def font_name(self, value : str) -> None:
        '''Sets the font name.'''
        raise NotImplementedError()
    
    @property
    def auto_leading(self) -> bool:
        '''Gets a value indicating whether [automatic leading].'''
        raise NotImplementedError()
    
    @auto_leading.setter
    def auto_leading(self, value : bool) -> None:
        '''Sets a value indicating whether [automatic leading].'''
        raise NotImplementedError()
    
    @property
    def leading(self) -> float:
        '''Gets the leading.'''
        raise NotImplementedError()
    
    @leading.setter
    def leading(self, value : float) -> None:
        '''Sets the leading.'''
        raise NotImplementedError()
    
    @property
    def tracking(self) -> int:
        '''Gets the tracking.'''
        raise NotImplementedError()
    
    @tracking.setter
    def tracking(self, value : int) -> None:
        '''Sets the tracking.'''
        raise NotImplementedError()
    
    @property
    def kerning(self) -> int:
        '''Gets the kerning.'''
        raise NotImplementedError()
    
    @kerning.setter
    def kerning(self, value : int) -> None:
        '''Sets the kerning.'''
        raise NotImplementedError()
    
    @property
    def auto_kerning(self) -> aspose.psd.fileformats.psd.AutoKerning:
        '''Gets the auto kerning.'''
        raise NotImplementedError()
    
    @auto_kerning.setter
    def auto_kerning(self, value : aspose.psd.fileformats.psd.AutoKerning) -> None:
        '''Sets the auto kerning.'''
        raise NotImplementedError()
    
    @property
    def fill_color(self) -> aspose.psd.Color:
        '''Gets the color of the fill.'''
        raise NotImplementedError()
    
    @fill_color.setter
    def fill_color(self, value : aspose.psd.Color) -> None:
        '''Sets the color of the fill.'''
        raise NotImplementedError()
    
    @property
    def stroke_color(self) -> aspose.psd.Color:
        '''Gets the color of the stroke.'''
        raise NotImplementedError()
    
    @stroke_color.setter
    def stroke_color(self, value : aspose.psd.Color) -> None:
        '''Sets the color of the stroke.'''
        raise NotImplementedError()
    
    @property
    def hindi_numbers(self) -> bool:
        '''Gets a value indicating whether [hindi numbers].'''
        raise NotImplementedError()
    
    @hindi_numbers.setter
    def hindi_numbers(self, value : bool) -> None:
        '''Sets a value indicating whether [hindi numbers].'''
        raise NotImplementedError()
    
    @property
    def faux_bold(self) -> bool:
        '''Gets the faux bold is enabled.'''
        raise NotImplementedError()
    
    @faux_bold.setter
    def faux_bold(self, value : bool) -> None:
        '''Sets the faux bold is enabled.'''
        raise NotImplementedError()
    
    @property
    def faux_italic(self) -> bool:
        '''Gets the faux bold is enabled.'''
        raise NotImplementedError()
    
    @faux_italic.setter
    def faux_italic(self, value : bool) -> None:
        '''Sets the faux bold is enabled.'''
        raise NotImplementedError()
    
    @property
    def underline(self) -> bool:
        '''Gets a value indicating whether [underline].'''
        raise NotImplementedError()
    
    @underline.setter
    def underline(self, value : bool) -> None:
        '''Sets a value indicating whether [underline].'''
        raise NotImplementedError()
    
    @property
    def strikethrough(self) -> bool:
        '''Gets a value indicating whether [strikethrough].'''
        raise NotImplementedError()
    
    @strikethrough.setter
    def strikethrough(self, value : bool) -> None:
        '''Sets a value indicating whether [strikethrough].'''
        raise NotImplementedError()
    
    @property
    def font_baseline(self) -> aspose.psd.fileformats.psd.FontBaseline:
        '''The font baseline.'''
        raise NotImplementedError()
    
    @font_baseline.setter
    def font_baseline(self, value : aspose.psd.fileformats.psd.FontBaseline) -> None:
        '''The font baseline.'''
        raise NotImplementedError()
    
    @property
    def baseline_shift(self) -> float:
        '''The baseline shift.'''
        raise NotImplementedError()
    
    @baseline_shift.setter
    def baseline_shift(self, value : float) -> None:
        '''The baseline shift.'''
        raise NotImplementedError()
    
    @property
    def font_caps(self) -> aspose.psd.fileformats.psd.FontCaps:
        '''The font caps.'''
        raise NotImplementedError()
    
    @font_caps.setter
    def font_caps(self, value : aspose.psd.fileformats.psd.FontCaps) -> None:
        '''The font caps.'''
        raise NotImplementedError()
    
    @property
    def standard_ligatures(self) -> bool:
        '''The standard contextual ligatures used to connect letters together.'''
        raise NotImplementedError()
    
    @standard_ligatures.setter
    def standard_ligatures(self, value : bool) -> None:
        '''The standard contextual ligatures used to connect letters together.'''
        raise NotImplementedError()
    
    @property
    def discretionary_ligatures(self) -> bool:
        '''The discretionary ligatures used to connect letters, especially in script fonts.'''
        raise NotImplementedError()
    
    @discretionary_ligatures.setter
    def discretionary_ligatures(self, value : bool) -> None:
        '''The discretionary ligatures used to connect letters, especially in script fonts.'''
        raise NotImplementedError()
    
    @property
    def contextual_alternates(self) -> bool:
        '''The contextual alternates used to connect letters together.'''
        raise NotImplementedError()
    
    @contextual_alternates.setter
    def contextual_alternates(self, value : bool) -> None:
        '''The contextual alternates used to connect letters together.'''
        raise NotImplementedError()
    
    @property
    def language_index(self) -> int:
        '''Gets the language index.'''
        raise NotImplementedError()
    
    @property
    def vertical_scale(self) -> float:
        '''The vertical scale.'''
        raise NotImplementedError()
    
    @vertical_scale.setter
    def vertical_scale(self, value : float) -> None:
        '''The vertical scale.'''
        raise NotImplementedError()
    
    @property
    def horizontal_scale(self) -> float:
        '''The horizontal scale.'''
        raise NotImplementedError()
    
    @horizontal_scale.setter
    def horizontal_scale(self, value : float) -> None:
        '''The horizontal scale.'''
        raise NotImplementedError()
    
    @property
    def fractions(self) -> bool:
        '''The fractions symbols can be replaced with special glyph.'''
        raise NotImplementedError()
    
    @fractions.setter
    def fractions(self, value : bool) -> None:
        '''The fractions symbols can be replaced with special glyph.'''
        raise NotImplementedError()
    
    @property
    def is_standard_vertical_roman_alignment_enabled(self) -> bool:
        '''Gets the standard vertical Roman alignment.
        This based on BaselineDirection resource value applies only when text orientation is :py:attr:`aspose.psd.fileformats.psd.TextOrientation.VERTICAL`.'''
        raise NotImplementedError()
    
    @is_standard_vertical_roman_alignment_enabled.setter
    def is_standard_vertical_roman_alignment_enabled(self, value : bool) -> None:
        '''Sets the standard vertical Roman alignment.
        This based on BaselineDirection resource value applies only when text orientation is :py:attr:`aspose.psd.fileformats.psd.TextOrientation.VERTICAL`.'''
        raise NotImplementedError()
    
    @property
    def no_break(self) -> bool:
        '''Gets ot sets the no break value.'''
        raise NotImplementedError()
    
    @no_break.setter
    def no_break(self, value : bool) -> None:
        '''Gets ot sets the no break value.'''
        raise NotImplementedError()
    

class TextFontInfo:
    '''Represents the information about font. This class cannot be inherited.'''
    
    @property
    def font_type(self) -> int:
        '''Gets the type of the font.'''
        raise NotImplementedError()
    
    @property
    def script(self) -> int:
        '''Gets the script.'''
        raise NotImplementedError()
    
    @property
    def synthetic(self) -> bool:
        '''Gets a value indicating whether this :py:class:`Aspose.PSD.FileFormats.Psd.Layers.Text.FontInformation` is synthetic.'''
        raise NotImplementedError()
    
    @property
    def post_script_name(self) -> str:
        '''Gets the PostScript name'''
        raise NotImplementedError()
    
    @property
    def family_name(self) -> str:
        '''Gets font family name'''
        raise NotImplementedError()
    
    @property
    def style(self) -> aspose.psd.FontStyle:
        '''Gets font style parsed from subfamily name'''
        raise NotImplementedError()
    

