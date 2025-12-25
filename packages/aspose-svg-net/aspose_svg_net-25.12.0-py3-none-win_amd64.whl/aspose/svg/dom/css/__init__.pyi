from typing import List, Optional, Dict, Iterable
import aspose.pycore
import aspose.pydrawing
import aspose.svg
import aspose.svg.builder
import aspose.svg.collections
import aspose.svg.converters
import aspose.svg.datatypes
import aspose.svg.diagnostics
import aspose.svg.dom
import aspose.svg.dom.attributes
import aspose.svg.dom.css
import aspose.svg.dom.events
import aspose.svg.dom.mutations
import aspose.svg.dom.traversal
import aspose.svg.dom.traversal.filters
import aspose.svg.dom.views
import aspose.svg.dom.xpath
import aspose.svg.drawing
import aspose.svg.events
import aspose.svg.filters
import aspose.svg.imagevectorization
import aspose.svg.io
import aspose.svg.net
import aspose.svg.net.headers
import aspose.svg.net.messagefilters
import aspose.svg.net.messagehandlers
import aspose.svg.paths
import aspose.svg.rendering
import aspose.svg.rendering.fonts
import aspose.svg.rendering.image
import aspose.svg.rendering.pdf
import aspose.svg.rendering.pdf.encryption
import aspose.svg.rendering.skia
import aspose.svg.rendering.xps
import aspose.svg.saving
import aspose.svg.saving.resourcehandlers
import aspose.svg.services
import aspose.svg.toolkit
import aspose.svg.toolkit.optimizers
import aspose.svg.window

class CSSPrimitiveValue(CSSValue):
    '''The CSSPrimitiveValue interface represents a single CSS value. This interface may be used to determine the value of a specific style property currently set in a block or to set a specific style property explicitly within the block. An instance of this interface might be obtained from the getPropertyCSSValue method of the CSSStyleDeclaration interface. A CSSPrimitiveValue object only occurs in a context of a CSS property.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object :py:class:`System.Type`.'''
        ...
    
    def set_float_value(self, unit_type : int, float_value : float):
        '''A method to set the float value with a specified unit. If the property attached with this value can not accept the specified unit or the float value, the value will be unchanged and a DOMException will be raised.
        
        :param unit_type: Type of the unit.
        :param float_value: The float value.'''
        ...
    
    def get_float_value(self, unit_type : int) -> float:
        '''This method is used to get a float value in a specified unit. If this CSS value doesn't contain a float value or can't be converted into the specified unit, a DOMException is raised.
        
        :param unit_type: Type of the unit.
        :returns: Returns value'''
        ...
    
    def set_int_value(self, unit_type : int, int_value : int):
        '''A method to set the int value with a specified unit. If the property attached with this value can not accept the specified unit or the int value, the value will be unchanged and a DOMException will be raised.
        
        :param unit_type: Type of the unit.
        :param int_value: The int value.'''
        ...
    
    def get_int_value(self, unit_type : int) -> int:
        '''This method is used to get an int value in a specified unit. If this CSS value doesn't contain an int value or can't be converted into the specified unit, a DOMException is raised.
        
        :param unit_type: Type of the unit.
        :returns: Returns value'''
        ...
    
    def set_string_value(self, string_type : int, string_value : str):
        '''A method to set the string value with the specified unit. If the property attached to this value can't accept the specified unit or the string value, the value will be unchanged and a DOMException will be raised.
        
        :param string_type: Type of the string.
        :param string_value: The string value.'''
        ...
    
    def get_string_value(self) -> str:
        '''This method is used to get the string value. If the CSS value doesn't contain a string value, a DOMException is raised.
        
        :returns: Returns value'''
        ...
    
    def get_counter_value(self) -> aspose.svg.dom.css.Counter:
        '''This method is used to get the Counter value. If this CSS value doesn't contain a counter value, a DOMException is raised. Modification to the corresponding style property can be achieved using the Counter interface.
        
        :returns: Returns Counter value'''
        ...
    
    def get_rect_value(self) -> aspose.svg.dom.css.Rect:
        '''This method is used to get the Rect value. If this CSS value doesn't contain a rect value, a DOMException is raised. Modification to the corresponding style property can be achieved using the Rect interface.
        
        :returns: Returns Rect value'''
        ...
    
    def get_rgb_color_value(self) -> aspose.svg.dom.css.RGBColor:
        '''This method is used to get the RGB color. If this CSS value doesn't contain a RGB color value, a DOMException is raised. Modification to the corresponding style property can be achieved using the RGBColor interface.
        
        :returns: Returns RGB color value'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def css_value_type(self) -> int:
        ...
    
    @classmethod
    @property
    def CSS_INHERIT(cls) -> int:
        '''The value is inherited and the cssText contains "inherit".'''
        ...
    
    @classmethod
    @property
    def CSS_PRIMITIVE_VALUE(cls) -> int:
        '''The value is a primitive value and an instance of the CSSPrimitiveValue interface can be obtained by using binding-specific casting methods on this instance of the CSSValue interface.'''
        ...
    
    @classmethod
    @property
    def CSS_VALUE_LIST(cls) -> int:
        '''The value is a CSSValue list and an instance of the CSSValueList interface can be obtained by using binding-specific casting methods on this instance of the CSSValue interface.'''
        ...
    
    @classmethod
    @property
    def CSS_CUSTOM(cls) -> int:
        '''The value is a custom value.'''
        ...
    
    @property
    def primitive_type(self) -> int:
        ...
    
    @classmethod
    @property
    def CSS_UNKNOWN(cls) -> int:
        '''The value is not a recognized CSS2 value. The value can only be obtained by using the cssText attribute.'''
        ...
    
    @classmethod
    @property
    def CSS_NUMBER(cls) -> int:
        '''The value is a simple number. The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_PERCENTAGE(cls) -> int:
        '''The value is a percentage. The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_EMS(cls) -> int:
        '''The value is a length (ems). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_EXS(cls) -> int:
        '''The value is a length (exs). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_PX(cls) -> int:
        '''The value is a length (px). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_CM(cls) -> int:
        '''The value is a length (cm). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_MM(cls) -> int:
        '''The value is a length (mm). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_IN(cls) -> int:
        '''The value is a length (in). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_PT(cls) -> int:
        '''The value is a length (pt). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_PC(cls) -> int:
        '''The value is a length (pc). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_DEG(cls) -> int:
        '''The value is an angle (deg). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_RAD(cls) -> int:
        '''The value is an angle (rad). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_GRAD(cls) -> int:
        '''The value is an angle (grad). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_MS(cls) -> int:
        '''The value is a time (ms). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_S(cls) -> int:
        '''The value is a time (s). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_HZ(cls) -> int:
        '''The value is a frequency (Hz). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_KHZ(cls) -> int:
        '''The value is a frequency (kHz). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_DIMENSION(cls) -> int:
        '''The value is a number with an unknown dimension. The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_REM(cls) -> int:
        '''The value is a length (rem). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_CH(cls) -> int:
        '''The value is a length (ch). The value can be obtained by using the getFloatValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_STRING(cls) -> int:
        '''The value is a STRING. The value can be obtained by using the getStringValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_URI(cls) -> int:
        '''The value is a URI. The value can be obtained by using the getStringValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_IDENT(cls) -> int:
        '''The value is an identifier. The value can be obtained by using the getStringValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_ATTR(cls) -> int:
        '''The value is a attribute function. The value can be obtained by using the getStringValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_COUNTER(cls) -> int:
        '''The value is a counter or counters function. The value can be obtained by using the GetCounterValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_RECT(cls) -> int:
        '''The value is a rect function. The value can be obtained by using the GetRectValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_RGBCOLOR(cls) -> int:
        '''The value is a RGB color. The value can be obtained by using the GetRGBColorValue method.'''
        ...
    
    @classmethod
    @property
    def CSS_DPI(cls) -> int:
        '''The value is a dots per inch (dpi).'''
        ...
    
    @classmethod
    @property
    def CSS_DPCM(cls) -> int:
        '''The value is a dots per centimeter (dpcm).'''
        ...
    
    @classmethod
    @property
    def CSS_DPPX(cls) -> int:
        '''The value is a dots per ‘px’ unit (dppx).'''
        ...
    
    @classmethod
    @property
    def CSS_VW(cls) -> int:
        '''The value is a percentage of the full viewport width.'''
        ...
    
    @classmethod
    @property
    def CSS_VH(cls) -> int:
        '''The value is a percentage of the full viewport height.'''
        ...
    
    @classmethod
    @property
    def CSS_VMIN(cls) -> int:
        '''The value is a percentage of the viewport width or height, whichever is smaller.'''
        ...
    
    @classmethod
    @property
    def CSS_VMAX(cls) -> int:
        '''The value is a percentage of the viewport width or height, whichever is larger.'''
        ...
    
    @classmethod
    @property
    def CSS_X(cls) -> int:
        '''The value is a dots per ‘px’ unit (x).'''
        ...
    
    @classmethod
    @property
    def CSS_FR(cls) -> int:
        '''A flexible length or flex is a dimension with the fr unit, which represents a fraction of the leftover space in the grid container'''
        ...
    
    ...

class CSSValue(aspose.svg.dom.DOMObject):
    '''Represents a simple or a complex value. A CSSValue object only occurs in a context of a CSS property.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object :py:class:`System.Type`.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def css_value_type(self) -> int:
        ...
    
    @classmethod
    @property
    def CSS_INHERIT(cls) -> int:
        '''The value is inherited and the cssText contains "inherit".'''
        ...
    
    @classmethod
    @property
    def CSS_PRIMITIVE_VALUE(cls) -> int:
        '''The value is a primitive value and an instance of the CSSPrimitiveValue interface can be obtained by using binding-specific casting methods on this instance of the CSSValue interface.'''
        ...
    
    @classmethod
    @property
    def CSS_VALUE_LIST(cls) -> int:
        '''The value is a CSSValue list and an instance of the CSSValueList interface can be obtained by using binding-specific casting methods on this instance of the CSSValue interface.'''
        ...
    
    @classmethod
    @property
    def CSS_CUSTOM(cls) -> int:
        '''The value is a custom value.'''
        ...
    
    ...

class CSSValueList(CSSValue):
    '''The CSSValueList interface provides the abstraction of an ordered collection of CSS values.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object :py:class:`System.Type`.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def css_value_type(self) -> int:
        ...
    
    @classmethod
    @property
    def CSS_INHERIT(cls) -> int:
        '''The value is inherited and the cssText contains "inherit".'''
        ...
    
    @classmethod
    @property
    def CSS_PRIMITIVE_VALUE(cls) -> int:
        '''The value is a primitive value and an instance of the CSSPrimitiveValue interface can be obtained by using binding-specific casting methods on this instance of the CSSValue interface.'''
        ...
    
    @classmethod
    @property
    def CSS_VALUE_LIST(cls) -> int:
        '''The value is a CSSValue list and an instance of the CSSValueList interface can be obtained by using binding-specific casting methods on this instance of the CSSValue interface.'''
        ...
    
    @classmethod
    @property
    def CSS_CUSTOM(cls) -> int:
        '''The value is a custom value.'''
        ...
    
    @property
    def length(self) -> int:
        '''The length read-only property of the CSSValueList interface represents the number of CSSValues in the list.
        The range of valid values of the indices is 0 to length-1 inclusive.'''
        ...
    
    def __getitem__(self, key : int) -> aspose.svg.dom.css.CSSValue:
        '''Gets the :py:class:`aspose.svg.dom.css.CSSValue` at the specified index.'''
        ...
    
    ...

class Counter(aspose.svg.dom.DOMObject):
    '''The Counter interface is used to represent any counter or counters function value. This interface reflects the values in the underlying style property.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def identifier(self) -> str:
        '''This attribute is used for the identifier of the counter.'''
        ...
    
    @property
    def list_style(self) -> str:
        ...
    
    @property
    def separator(self) -> str:
        '''This attribute is used for the separator of the nested counters.'''
        ...
    
    ...

class ICSS2Properties:
    '''Provides interface for CSS2 properties set values manipulation in the context of certain HTML element'''
    
    @property
    def azimuth(self) -> str:
        '''See the azimuth property definition in CSS2.'''
        ...
    
    @azimuth.setter
    def azimuth(self, value : str):
        '''See the azimuth property definition in CSS2.'''
        ...
    
    @property
    def background(self) -> str:
        '''See the background property definition in CSS2.'''
        ...
    
    @background.setter
    def background(self, value : str):
        '''See the background property definition in CSS2.'''
        ...
    
    @property
    def background_attachment(self) -> str:
        ...
    
    @background_attachment.setter
    def background_attachment(self, value : str):
        ...
    
    @property
    def background_color(self) -> str:
        ...
    
    @background_color.setter
    def background_color(self, value : str):
        ...
    
    @property
    def background_image(self) -> str:
        ...
    
    @background_image.setter
    def background_image(self, value : str):
        ...
    
    @property
    def background_position(self) -> str:
        ...
    
    @background_position.setter
    def background_position(self, value : str):
        ...
    
    @property
    def background_repeat(self) -> str:
        ...
    
    @background_repeat.setter
    def background_repeat(self, value : str):
        ...
    
    @property
    def border(self) -> str:
        '''See the border property definition in CSS2.'''
        ...
    
    @border.setter
    def border(self, value : str):
        '''See the border property definition in CSS2.'''
        ...
    
    @property
    def border_collapse(self) -> str:
        ...
    
    @border_collapse.setter
    def border_collapse(self, value : str):
        ...
    
    @property
    def border_color(self) -> str:
        ...
    
    @border_color.setter
    def border_color(self, value : str):
        ...
    
    @property
    def border_spacing(self) -> str:
        ...
    
    @border_spacing.setter
    def border_spacing(self, value : str):
        ...
    
    @property
    def border_style(self) -> str:
        ...
    
    @border_style.setter
    def border_style(self, value : str):
        ...
    
    @property
    def border_top(self) -> str:
        ...
    
    @border_top.setter
    def border_top(self, value : str):
        ...
    
    @property
    def border_right(self) -> str:
        ...
    
    @border_right.setter
    def border_right(self, value : str):
        ...
    
    @property
    def border_bottom(self) -> str:
        ...
    
    @border_bottom.setter
    def border_bottom(self, value : str):
        ...
    
    @property
    def border_left(self) -> str:
        ...
    
    @border_left.setter
    def border_left(self, value : str):
        ...
    
    @property
    def border_top_color(self) -> str:
        ...
    
    @border_top_color.setter
    def border_top_color(self, value : str):
        ...
    
    @property
    def border_right_color(self) -> str:
        ...
    
    @border_right_color.setter
    def border_right_color(self, value : str):
        ...
    
    @property
    def border_bottom_color(self) -> str:
        ...
    
    @border_bottom_color.setter
    def border_bottom_color(self, value : str):
        ...
    
    @property
    def border_left_color(self) -> str:
        ...
    
    @border_left_color.setter
    def border_left_color(self, value : str):
        ...
    
    @property
    def border_top_style(self) -> str:
        ...
    
    @border_top_style.setter
    def border_top_style(self, value : str):
        ...
    
    @property
    def border_right_style(self) -> str:
        ...
    
    @border_right_style.setter
    def border_right_style(self, value : str):
        ...
    
    @property
    def border_bottom_style(self) -> str:
        ...
    
    @border_bottom_style.setter
    def border_bottom_style(self, value : str):
        ...
    
    @property
    def border_left_style(self) -> str:
        ...
    
    @border_left_style.setter
    def border_left_style(self, value : str):
        ...
    
    @property
    def border_top_width(self) -> str:
        ...
    
    @border_top_width.setter
    def border_top_width(self, value : str):
        ...
    
    @property
    def border_right_width(self) -> str:
        ...
    
    @border_right_width.setter
    def border_right_width(self, value : str):
        ...
    
    @property
    def border_bottom_width(self) -> str:
        ...
    
    @border_bottom_width.setter
    def border_bottom_width(self, value : str):
        ...
    
    @property
    def border_left_width(self) -> str:
        ...
    
    @border_left_width.setter
    def border_left_width(self, value : str):
        ...
    
    @property
    def border_width(self) -> str:
        ...
    
    @border_width.setter
    def border_width(self, value : str):
        ...
    
    @property
    def bottom(self) -> str:
        '''See the bottom property definition in CSS2.'''
        ...
    
    @bottom.setter
    def bottom(self, value : str):
        '''See the bottom property definition in CSS2.'''
        ...
    
    @property
    def caption_side(self) -> str:
        ...
    
    @caption_side.setter
    def caption_side(self, value : str):
        ...
    
    @property
    def clear(self) -> str:
        '''See the clear property definition in CSS2.'''
        ...
    
    @clear.setter
    def clear(self, value : str):
        '''See the clear property definition in CSS2.'''
        ...
    
    @property
    def clip(self) -> str:
        '''See the clip property definition in CSS2.'''
        ...
    
    @clip.setter
    def clip(self, value : str):
        '''See the clip property definition in CSS2.'''
        ...
    
    @property
    def color(self) -> str:
        '''See the color property definition in CSS2.'''
        ...
    
    @color.setter
    def color(self, value : str):
        '''See the color property definition in CSS2.'''
        ...
    
    @property
    def content(self) -> str:
        '''See the content property definition in CSS2.'''
        ...
    
    @content.setter
    def content(self, value : str):
        '''See the content property definition in CSS2.'''
        ...
    
    @property
    def counter_increment(self) -> str:
        ...
    
    @counter_increment.setter
    def counter_increment(self, value : str):
        ...
    
    @property
    def counter_reset(self) -> str:
        ...
    
    @counter_reset.setter
    def counter_reset(self, value : str):
        ...
    
    @property
    def cue(self) -> str:
        '''See the cue property definition in CSS2.'''
        ...
    
    @cue.setter
    def cue(self, value : str):
        '''See the cue property definition in CSS2.'''
        ...
    
    @property
    def cue_after(self) -> str:
        ...
    
    @cue_after.setter
    def cue_after(self, value : str):
        ...
    
    @property
    def cue_before(self) -> str:
        ...
    
    @cue_before.setter
    def cue_before(self, value : str):
        ...
    
    @property
    def cursor(self) -> str:
        '''See the cursor property definition in CSS2.'''
        ...
    
    @cursor.setter
    def cursor(self, value : str):
        '''See the cursor property definition in CSS2.'''
        ...
    
    @property
    def direction(self) -> str:
        '''See the direction property definition in CSS2.'''
        ...
    
    @direction.setter
    def direction(self, value : str):
        '''See the direction property definition in CSS2.'''
        ...
    
    @property
    def display(self) -> str:
        '''See the display property definition in CSS2.'''
        ...
    
    @display.setter
    def display(self, value : str):
        '''See the display property definition in CSS2.'''
        ...
    
    @property
    def elevation(self) -> str:
        '''See the elevation property definition in CSS2.'''
        ...
    
    @elevation.setter
    def elevation(self, value : str):
        '''See the elevation property definition in CSS2.'''
        ...
    
    @property
    def empty_cells(self) -> str:
        ...
    
    @empty_cells.setter
    def empty_cells(self, value : str):
        ...
    
    @property
    def float(self) -> str:
        '''See the float property definition in CSS2.'''
        ...
    
    @float.setter
    def float(self, value : str):
        '''See the float property definition in CSS2.'''
        ...
    
    @property
    def font(self) -> str:
        '''See the font property definition in CSS2.'''
        ...
    
    @font.setter
    def font(self, value : str):
        '''See the font property definition in CSS2.'''
        ...
    
    @property
    def font_family(self) -> str:
        ...
    
    @font_family.setter
    def font_family(self, value : str):
        ...
    
    @property
    def font_size(self) -> str:
        ...
    
    @font_size.setter
    def font_size(self, value : str):
        ...
    
    @property
    def font_size_adjust(self) -> str:
        ...
    
    @font_size_adjust.setter
    def font_size_adjust(self, value : str):
        ...
    
    @property
    def font_stretch(self) -> str:
        ...
    
    @font_stretch.setter
    def font_stretch(self, value : str):
        ...
    
    @property
    def font_style(self) -> str:
        ...
    
    @font_style.setter
    def font_style(self, value : str):
        ...
    
    @property
    def font_variant(self) -> str:
        ...
    
    @font_variant.setter
    def font_variant(self, value : str):
        ...
    
    @property
    def font_weight(self) -> str:
        ...
    
    @font_weight.setter
    def font_weight(self, value : str):
        ...
    
    @property
    def grid_template_columns(self) -> str:
        ...
    
    @grid_template_columns.setter
    def grid_template_columns(self, value : str):
        ...
    
    @property
    def grid_template_rows(self) -> str:
        ...
    
    @grid_template_rows.setter
    def grid_template_rows(self, value : str):
        ...
    
    @property
    def grid_template_areas(self) -> str:
        ...
    
    @grid_template_areas.setter
    def grid_template_areas(self, value : str):
        ...
    
    @property
    def height(self) -> str:
        '''See the height property definition in CSS2.'''
        ...
    
    @height.setter
    def height(self, value : str):
        '''See the height property definition in CSS2.'''
        ...
    
    @property
    def left(self) -> str:
        '''See the left property definition in CSS2.'''
        ...
    
    @left.setter
    def left(self, value : str):
        '''See the left property definition in CSS2.'''
        ...
    
    @property
    def letter_spacing(self) -> str:
        ...
    
    @letter_spacing.setter
    def letter_spacing(self, value : str):
        ...
    
    @property
    def line_height(self) -> str:
        ...
    
    @line_height.setter
    def line_height(self, value : str):
        ...
    
    @property
    def list_style(self) -> str:
        ...
    
    @list_style.setter
    def list_style(self, value : str):
        ...
    
    @property
    def list_style_image(self) -> str:
        ...
    
    @list_style_image.setter
    def list_style_image(self, value : str):
        ...
    
    @property
    def list_style_position(self) -> str:
        ...
    
    @list_style_position.setter
    def list_style_position(self, value : str):
        ...
    
    @property
    def list_style_type(self) -> str:
        ...
    
    @list_style_type.setter
    def list_style_type(self, value : str):
        ...
    
    @property
    def margin(self) -> str:
        '''See the margin property definition in CSS2.'''
        ...
    
    @margin.setter
    def margin(self, value : str):
        '''See the margin property definition in CSS2.'''
        ...
    
    @property
    def margin_top(self) -> str:
        ...
    
    @margin_top.setter
    def margin_top(self, value : str):
        ...
    
    @property
    def margin_right(self) -> str:
        ...
    
    @margin_right.setter
    def margin_right(self, value : str):
        ...
    
    @property
    def margin_bottom(self) -> str:
        ...
    
    @margin_bottom.setter
    def margin_bottom(self, value : str):
        ...
    
    @property
    def margin_left(self) -> str:
        ...
    
    @margin_left.setter
    def margin_left(self, value : str):
        ...
    
    @property
    def marker_offset(self) -> str:
        ...
    
    @marker_offset.setter
    def marker_offset(self, value : str):
        ...
    
    @property
    def marks(self) -> str:
        '''See the marks property definition in CSS2.'''
        ...
    
    @marks.setter
    def marks(self, value : str):
        '''See the marks property definition in CSS2.'''
        ...
    
    @property
    def max_height(self) -> str:
        ...
    
    @max_height.setter
    def max_height(self, value : str):
        ...
    
    @property
    def max_width(self) -> str:
        ...
    
    @max_width.setter
    def max_width(self, value : str):
        ...
    
    @property
    def min_height(self) -> str:
        ...
    
    @min_height.setter
    def min_height(self, value : str):
        ...
    
    @property
    def min_width(self) -> str:
        ...
    
    @min_width.setter
    def min_width(self, value : str):
        ...
    
    @property
    def orphans(self) -> str:
        '''See the orphans property definition in CSS2.'''
        ...
    
    @orphans.setter
    def orphans(self, value : str):
        '''See the orphans property definition in CSS2.'''
        ...
    
    @property
    def outline(self) -> str:
        '''See the outline property definition in CSS2.'''
        ...
    
    @outline.setter
    def outline(self, value : str):
        '''See the outline property definition in CSS2.'''
        ...
    
    @property
    def outline_color(self) -> str:
        ...
    
    @outline_color.setter
    def outline_color(self, value : str):
        ...
    
    @property
    def outline_style(self) -> str:
        ...
    
    @outline_style.setter
    def outline_style(self, value : str):
        ...
    
    @property
    def outline_width(self) -> str:
        ...
    
    @outline_width.setter
    def outline_width(self, value : str):
        ...
    
    @property
    def overflow(self) -> str:
        '''See the overflow property definition in CSS2.'''
        ...
    
    @overflow.setter
    def overflow(self, value : str):
        '''See the overflow property definition in CSS2.'''
        ...
    
    @property
    def padding(self) -> str:
        '''See the padding property definition in CSS2.'''
        ...
    
    @padding.setter
    def padding(self, value : str):
        '''See the padding property definition in CSS2.'''
        ...
    
    @property
    def padding_top(self) -> str:
        ...
    
    @padding_top.setter
    def padding_top(self, value : str):
        ...
    
    @property
    def padding_right(self) -> str:
        ...
    
    @padding_right.setter
    def padding_right(self, value : str):
        ...
    
    @property
    def padding_bottom(self) -> str:
        ...
    
    @padding_bottom.setter
    def padding_bottom(self, value : str):
        ...
    
    @property
    def padding_left(self) -> str:
        ...
    
    @padding_left.setter
    def padding_left(self, value : str):
        ...
    
    @property
    def page(self) -> str:
        '''See the page property definition in CSS2.'''
        ...
    
    @page.setter
    def page(self, value : str):
        '''See the page property definition in CSS2.'''
        ...
    
    @property
    def page_break_after(self) -> str:
        ...
    
    @page_break_after.setter
    def page_break_after(self, value : str):
        ...
    
    @property
    def page_break_before(self) -> str:
        ...
    
    @page_break_before.setter
    def page_break_before(self, value : str):
        ...
    
    @property
    def page_break_inside(self) -> str:
        ...
    
    @page_break_inside.setter
    def page_break_inside(self, value : str):
        ...
    
    @property
    def pause(self) -> str:
        '''See the pause property definition in CSS2.'''
        ...
    
    @pause.setter
    def pause(self, value : str):
        '''See the pause property definition in CSS2.'''
        ...
    
    @property
    def pause_after(self) -> str:
        ...
    
    @pause_after.setter
    def pause_after(self, value : str):
        ...
    
    @property
    def pause_before(self) -> str:
        ...
    
    @pause_before.setter
    def pause_before(self, value : str):
        ...
    
    @property
    def pitch(self) -> str:
        '''See the pitch property definition in CSS2.'''
        ...
    
    @pitch.setter
    def pitch(self, value : str):
        '''See the pitch property definition in CSS2.'''
        ...
    
    @property
    def pitch_range(self) -> str:
        ...
    
    @pitch_range.setter
    def pitch_range(self, value : str):
        ...
    
    @property
    def play_during(self) -> str:
        ...
    
    @play_during.setter
    def play_during(self, value : str):
        ...
    
    @property
    def position(self) -> str:
        '''See the position property definition in CSS2.'''
        ...
    
    @position.setter
    def position(self, value : str):
        '''See the position property definition in CSS2.'''
        ...
    
    @property
    def quotes(self) -> str:
        '''See the quotes property definition in CSS2.'''
        ...
    
    @quotes.setter
    def quotes(self, value : str):
        '''See the quotes property definition in CSS2.'''
        ...
    
    @property
    def richness(self) -> str:
        '''See the richness property definition in CSS2.'''
        ...
    
    @richness.setter
    def richness(self, value : str):
        '''See the richness property definition in CSS2.'''
        ...
    
    @property
    def right(self) -> str:
        '''See the right property definition in CSS2.'''
        ...
    
    @right.setter
    def right(self, value : str):
        '''See the right property definition in CSS2.'''
        ...
    
    @property
    def size(self) -> str:
        '''See the size property definition in CSS2.'''
        ...
    
    @size.setter
    def size(self, value : str):
        '''See the size property definition in CSS2.'''
        ...
    
    @property
    def speak(self) -> str:
        '''See the speak property definition in CSS2.'''
        ...
    
    @speak.setter
    def speak(self, value : str):
        '''See the speak property definition in CSS2.'''
        ...
    
    @property
    def speak_header(self) -> str:
        ...
    
    @speak_header.setter
    def speak_header(self, value : str):
        ...
    
    @property
    def speak_numeral(self) -> str:
        ...
    
    @speak_numeral.setter
    def speak_numeral(self, value : str):
        ...
    
    @property
    def speak_punctuation(self) -> str:
        ...
    
    @speak_punctuation.setter
    def speak_punctuation(self, value : str):
        ...
    
    @property
    def speech_rate(self) -> str:
        ...
    
    @speech_rate.setter
    def speech_rate(self, value : str):
        ...
    
    @property
    def stress(self) -> str:
        '''See the stress property definition in CSS2.'''
        ...
    
    @stress.setter
    def stress(self, value : str):
        '''See the stress property definition in CSS2.'''
        ...
    
    @property
    def table_layout(self) -> str:
        ...
    
    @table_layout.setter
    def table_layout(self, value : str):
        ...
    
    @property
    def text_align(self) -> str:
        ...
    
    @text_align.setter
    def text_align(self, value : str):
        ...
    
    @property
    def text_decoration(self) -> str:
        ...
    
    @text_decoration.setter
    def text_decoration(self, value : str):
        ...
    
    @property
    def text_indent(self) -> str:
        ...
    
    @text_indent.setter
    def text_indent(self, value : str):
        ...
    
    @property
    def text_shadow(self) -> str:
        ...
    
    @text_shadow.setter
    def text_shadow(self, value : str):
        ...
    
    @property
    def text_transform(self) -> str:
        ...
    
    @text_transform.setter
    def text_transform(self, value : str):
        ...
    
    @property
    def top(self) -> str:
        '''See the top property definition in CSS2.'''
        ...
    
    @top.setter
    def top(self, value : str):
        '''See the top property definition in CSS2.'''
        ...
    
    @property
    def unicode_bidi(self) -> str:
        ...
    
    @unicode_bidi.setter
    def unicode_bidi(self, value : str):
        ...
    
    @property
    def vertical_align(self) -> str:
        ...
    
    @vertical_align.setter
    def vertical_align(self, value : str):
        ...
    
    @property
    def visibility(self) -> str:
        '''See the visibility property definition in CSS2.'''
        ...
    
    @visibility.setter
    def visibility(self, value : str):
        '''See the visibility property definition in CSS2.'''
        ...
    
    @property
    def voice_family(self) -> str:
        ...
    
    @voice_family.setter
    def voice_family(self, value : str):
        ...
    
    @property
    def volume(self) -> str:
        '''See the volume property definition in CSS2.'''
        ...
    
    @volume.setter
    def volume(self, value : str):
        '''See the volume property definition in CSS2.'''
        ...
    
    @property
    def white_space(self) -> str:
        ...
    
    @white_space.setter
    def white_space(self, value : str):
        ...
    
    @property
    def widows(self) -> str:
        '''See the widows property definition in CSS2.'''
        ...
    
    @widows.setter
    def widows(self, value : str):
        '''See the widows property definition in CSS2.'''
        ...
    
    @property
    def width(self) -> str:
        '''See the width property definition in CSS2.'''
        ...
    
    @width.setter
    def width(self, value : str):
        '''See the width property definition in CSS2.'''
        ...
    
    @property
    def word_spacing(self) -> str:
        ...
    
    @word_spacing.setter
    def word_spacing(self, value : str):
        ...
    
    @property
    def z_index(self) -> str:
        ...
    
    @z_index.setter
    def z_index(self, value : str):
        ...
    
    ...

class ICSSCharsetRule(ICSSRule):
    '''The CSSCharsetRule interface represents a @charset rule in a CSS style sheet.
    The value of the encoding attribute does not affect the encoding of text data in the DOM objects; this encoding is always UTF-16. After a stylesheet is loaded, the value of the encoding attribute is the value found in the @charset rule. If there was no @charset in the original document, then no CSSCharsetRule is created.
    The value of the encoding attribute may also be used as a hint for the encoding used on serialization of the style sheet.'''
    
    @property
    def encoding(self) -> str:
        '''The encoding information used in this @charset rule.'''
        ...
    
    @encoding.setter
    def encoding(self, value : str):
        '''The encoding information used in this @charset rule.'''
        ...
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSCounterStyleRule(ICSSRule):
    '''The @counter-style rule allows authors to define a custom counter style.'''
    
    @property
    def name(self) -> str:
        '''Gets the name.'''
        ...
    
    @property
    def counter_type(self) -> str:
        ...
    
    @property
    def glyphs(self) -> str:
        '''Gets the glyphs.'''
        ...
    
    @property
    def prefix(self) -> str:
        '''Gets the prefix.'''
        ...
    
    @property
    def suffix(self) -> str:
        '''Gets the suffix.'''
        ...
    
    @property
    def fallback(self) -> str:
        '''Gets the fallback.'''
        ...
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSFontFaceRule(ICSSRule):
    '''The CSSFontFaceRule interface represents a @font-face rule in a CSS style sheet. The @font-face rule is used to hold a set of font descriptions.'''
    
    @property
    def style(self) -> aspose.svg.dom.css.ICSSStyleDeclaration:
        '''The declaration-block of this rule.'''
        ...
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSImportRule(ICSSRule):
    '''The CSSImportRule interface represents a @import rule within a CSS style sheet. The @import rule is used to import style rules from other style sheets.'''
    
    @property
    def href(self) -> str:
        '''The location of the style sheet to be imported. The attribute will not contain the "url(...)" specifier around the URI.'''
        ...
    
    @property
    def media(self) -> aspose.svg.dom.css.IMediaList:
        '''A list of media types for which this style sheet may be used.'''
        ...
    
    @property
    def style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSKeyframeRule(ICSSRule):
    '''The CSSKeyframeRule interface represents the style rule for a single key.'''
    
    @property
    def key_text(self) -> str:
        ...
    
    @property
    def style(self) -> aspose.svg.dom.css.ICSSStyleDeclaration:
        '''This attribute represents the style associated with this keyframe.'''
        ...
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSKeyframesRule(ICSSRule):
    '''The CSSKeyframesRule interface represents a complete set of keyframes for a single animation'''
    
    def append_rule(self, rule : str):
        '''The appendRule method appends the passed CSSKeyframeRule into the list at the passed key
        
        :param rule: The rule to be appended, expressed in the same syntax as one entry in the ‘@keyframes’ rule'''
        ...
    
    def delete_rule(self, key : str):
        '''The deleteRule method deletes the CSSKeyframeRule with the passed key. If a rule with this key does not exist, the method does nothing
        
        :param key: The key which describes the rule to be deleted. The key must resolve to a number between 0 and 1, or the rule is ignored'''
        ...
    
    def find_rule(self, key : str) -> aspose.svg.dom.css.ICSSKeyframeRule:
        '''The findRule method returns the rule with a key matching the passed key. If no such rule exists, a null value is returned
        
        :param key: The key which described the rule to find. The key must resolve to a number between 0 and 1, or the rule is ignored.
        :returns: The found rule'''
        ...
    
    @property
    def name(self) -> str:
        '''This attribute is the name of the keyframes, used by the ‘animation-name’ property.'''
        ...
    
    @property
    def css_rules(self) -> aspose.svg.dom.css.ICSSRuleList:
        ...
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSMarginRule(ICSSRule):
    '''The CSSMarginRule interface represents a margin at-rule.'''
    
    @property
    def name(self) -> str:
        '''The name attribute must return the name of the margin at-rule. The @ character is not included in the name.'''
        ...
    
    @property
    def style(self) -> aspose.svg.dom.css.ICSSStyleDeclaration:
        '''The declaration-block of this rule.'''
        ...
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSMediaRule(ICSSRule):
    '''The CSSMediaRule interface represents a @media rule in a CSS style sheet. A @media rule can be used to delimit style rules for specific media types.'''
    
    def insert_rule(self, rule : str, index : int) -> int:
        '''Used to insert a new rule into the media block.
        
        :param rule: The media rule.
        :param index: The index.
        :returns: The inserted index.'''
        ...
    
    def delete_rule(self, index : int):
        '''Used to delete a rule from the media block.
        
        :param index: The index.'''
        ...
    
    @property
    def media(self) -> aspose.svg.dom.css.IMediaList:
        '''A list of media types for this rule.'''
        ...
    
    @property
    def css_rules(self) -> aspose.svg.dom.css.ICSSRuleList:
        ...
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSPageRule(ICSSRule):
    '''The CSSPageRule interface represents a @page rule within a CSS style sheet. The @page rule is used to specify the dimensions, orientation, margins, etc. of a page box for paged media.'''
    
    @property
    def selector_text(self) -> str:
        ...
    
    @selector_text.setter
    def selector_text(self, value : str):
        ...
    
    @property
    def style(self) -> aspose.svg.dom.css.ICSSStyleDeclaration:
        '''The declaration-block of this rule.'''
        ...
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSRule:
    '''The CSSRule interface is the abstract base interface for any type of CSS statement. This includes both rule sets and at-rules. An implementation is expected to preserve all rules specified in a CSS style sheet, even if the rule is not recognized by the parser. Unrecognized rules are represented using the :py:class:`aspose.svg.dom.css.ICSSUnknownRule` interface.'''
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSRuleList:
    '''The CSSRuleList interface provides the abstraction of an ordered collection of CSS rules.'''
    
    @property
    def length(self) -> int:
        '''The number of CSSRules in the list. The range of valid child rule indices is 0 to length-1 inclusive.'''
        ...
    
    def __getitem__(self, key : int) -> aspose.svg.dom.css.ICSSRule:
        '''Used to retrieve a CSS rule by method item() (http://www.w3.org/TR/DOM-Level-2-Style/css.html#CSS-CSSRuleList). The order in this collection represents the order of the rules in the CSS style sheet. If index is greater than or equal to the number of rules in the list, this returns null.'''
        ...
    
    ...

class ICSSStyleDeclaration(ICSS2Properties):
    '''The CSSStyleDeclaration interface represents a single CSS declaration block. This interface may be used to determine the style properties currently set in a block or to set style properties explicitly within the block.'''
    
    @overload
    def set_property(self, property_name : str, value : str):
        '''Used to set a property value with default priority within this declaration block.
        Default priority is not "important" i.e. String.Empty
        
        :param property_name: Name of the property.
        :param value: The value.'''
        ...
    
    @overload
    def set_property(self, property_name : str, value : str, priority : str):
        '''Used to set a property value and priority within this declaration block.
        
        :param property_name: Name of the property.
        :param value: The value.
        :param priority: The priority.'''
        ...
    
    def get_property_value(self, property_name : str) -> str:
        '''Used to retrieve the value of a CSS property if it has been explicitly set within this declaration block.
        
        :param property_name: Name of the property.
        :returns: Returns property value'''
        ...
    
    def get_property_css_value(self, property_name : str) -> aspose.svg.dom.css.CSSValue:
        '''Used to retrieve the object representation of the value of a CSS property if it has been explicitly set within this declaration block. This method returns null if the property is a shorthand property. Shorthand property values can only be accessed and modified as strings, using the getPropertyValue and setProperty methods.
        
        :param property_name: Name of the property.
        :returns: Returns property value'''
        ...
    
    def remove_property(self, property_name : str) -> str:
        '''Used to remove a CSS property if it has been explicitly set within this declaration block.
        
        :param property_name: Name of the property.
        :returns: Returns property value'''
        ...
    
    def get_property_priority(self, property_name : str) -> str:
        '''Used to retrieve the priority of a CSS property (e.g. the "important" qualifier) if the property has been explicitly set in this declaration block.
        
        :param property_name: Name of the property.
        :returns: Returns property priority'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def length(self) -> int:
        '''The number of properties that have been explicitly set in this declaration block. The range of valid indices is 0 to length-1 inclusive.'''
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    @property
    def azimuth(self) -> str:
        '''See the azimuth property definition in CSS2.'''
        ...
    
    @azimuth.setter
    def azimuth(self, value : str):
        '''See the azimuth property definition in CSS2.'''
        ...
    
    @property
    def background(self) -> str:
        '''See the background property definition in CSS2.'''
        ...
    
    @background.setter
    def background(self, value : str):
        '''See the background property definition in CSS2.'''
        ...
    
    @property
    def background_attachment(self) -> str:
        ...
    
    @background_attachment.setter
    def background_attachment(self, value : str):
        ...
    
    @property
    def background_color(self) -> str:
        ...
    
    @background_color.setter
    def background_color(self, value : str):
        ...
    
    @property
    def background_image(self) -> str:
        ...
    
    @background_image.setter
    def background_image(self, value : str):
        ...
    
    @property
    def background_position(self) -> str:
        ...
    
    @background_position.setter
    def background_position(self, value : str):
        ...
    
    @property
    def background_repeat(self) -> str:
        ...
    
    @background_repeat.setter
    def background_repeat(self, value : str):
        ...
    
    @property
    def border(self) -> str:
        '''See the border property definition in CSS2.'''
        ...
    
    @border.setter
    def border(self, value : str):
        '''See the border property definition in CSS2.'''
        ...
    
    @property
    def border_collapse(self) -> str:
        ...
    
    @border_collapse.setter
    def border_collapse(self, value : str):
        ...
    
    @property
    def border_color(self) -> str:
        ...
    
    @border_color.setter
    def border_color(self, value : str):
        ...
    
    @property
    def border_spacing(self) -> str:
        ...
    
    @border_spacing.setter
    def border_spacing(self, value : str):
        ...
    
    @property
    def border_style(self) -> str:
        ...
    
    @border_style.setter
    def border_style(self, value : str):
        ...
    
    @property
    def border_top(self) -> str:
        ...
    
    @border_top.setter
    def border_top(self, value : str):
        ...
    
    @property
    def border_right(self) -> str:
        ...
    
    @border_right.setter
    def border_right(self, value : str):
        ...
    
    @property
    def border_bottom(self) -> str:
        ...
    
    @border_bottom.setter
    def border_bottom(self, value : str):
        ...
    
    @property
    def border_left(self) -> str:
        ...
    
    @border_left.setter
    def border_left(self, value : str):
        ...
    
    @property
    def border_top_color(self) -> str:
        ...
    
    @border_top_color.setter
    def border_top_color(self, value : str):
        ...
    
    @property
    def border_right_color(self) -> str:
        ...
    
    @border_right_color.setter
    def border_right_color(self, value : str):
        ...
    
    @property
    def border_bottom_color(self) -> str:
        ...
    
    @border_bottom_color.setter
    def border_bottom_color(self, value : str):
        ...
    
    @property
    def border_left_color(self) -> str:
        ...
    
    @border_left_color.setter
    def border_left_color(self, value : str):
        ...
    
    @property
    def border_top_style(self) -> str:
        ...
    
    @border_top_style.setter
    def border_top_style(self, value : str):
        ...
    
    @property
    def border_right_style(self) -> str:
        ...
    
    @border_right_style.setter
    def border_right_style(self, value : str):
        ...
    
    @property
    def border_bottom_style(self) -> str:
        ...
    
    @border_bottom_style.setter
    def border_bottom_style(self, value : str):
        ...
    
    @property
    def border_left_style(self) -> str:
        ...
    
    @border_left_style.setter
    def border_left_style(self, value : str):
        ...
    
    @property
    def border_top_width(self) -> str:
        ...
    
    @border_top_width.setter
    def border_top_width(self, value : str):
        ...
    
    @property
    def border_right_width(self) -> str:
        ...
    
    @border_right_width.setter
    def border_right_width(self, value : str):
        ...
    
    @property
    def border_bottom_width(self) -> str:
        ...
    
    @border_bottom_width.setter
    def border_bottom_width(self, value : str):
        ...
    
    @property
    def border_left_width(self) -> str:
        ...
    
    @border_left_width.setter
    def border_left_width(self, value : str):
        ...
    
    @property
    def border_width(self) -> str:
        ...
    
    @border_width.setter
    def border_width(self, value : str):
        ...
    
    @property
    def bottom(self) -> str:
        '''See the bottom property definition in CSS2.'''
        ...
    
    @bottom.setter
    def bottom(self, value : str):
        '''See the bottom property definition in CSS2.'''
        ...
    
    @property
    def caption_side(self) -> str:
        ...
    
    @caption_side.setter
    def caption_side(self, value : str):
        ...
    
    @property
    def clear(self) -> str:
        '''See the clear property definition in CSS2.'''
        ...
    
    @clear.setter
    def clear(self, value : str):
        '''See the clear property definition in CSS2.'''
        ...
    
    @property
    def clip(self) -> str:
        '''See the clip property definition in CSS2.'''
        ...
    
    @clip.setter
    def clip(self, value : str):
        '''See the clip property definition in CSS2.'''
        ...
    
    @property
    def color(self) -> str:
        '''See the color property definition in CSS2.'''
        ...
    
    @color.setter
    def color(self, value : str):
        '''See the color property definition in CSS2.'''
        ...
    
    @property
    def content(self) -> str:
        '''See the content property definition in CSS2.'''
        ...
    
    @content.setter
    def content(self, value : str):
        '''See the content property definition in CSS2.'''
        ...
    
    @property
    def counter_increment(self) -> str:
        ...
    
    @counter_increment.setter
    def counter_increment(self, value : str):
        ...
    
    @property
    def counter_reset(self) -> str:
        ...
    
    @counter_reset.setter
    def counter_reset(self, value : str):
        ...
    
    @property
    def cue(self) -> str:
        '''See the cue property definition in CSS2.'''
        ...
    
    @cue.setter
    def cue(self, value : str):
        '''See the cue property definition in CSS2.'''
        ...
    
    @property
    def cue_after(self) -> str:
        ...
    
    @cue_after.setter
    def cue_after(self, value : str):
        ...
    
    @property
    def cue_before(self) -> str:
        ...
    
    @cue_before.setter
    def cue_before(self, value : str):
        ...
    
    @property
    def cursor(self) -> str:
        '''See the cursor property definition in CSS2.'''
        ...
    
    @cursor.setter
    def cursor(self, value : str):
        '''See the cursor property definition in CSS2.'''
        ...
    
    @property
    def direction(self) -> str:
        '''See the direction property definition in CSS2.'''
        ...
    
    @direction.setter
    def direction(self, value : str):
        '''See the direction property definition in CSS2.'''
        ...
    
    @property
    def display(self) -> str:
        '''See the display property definition in CSS2.'''
        ...
    
    @display.setter
    def display(self, value : str):
        '''See the display property definition in CSS2.'''
        ...
    
    @property
    def elevation(self) -> str:
        '''See the elevation property definition in CSS2.'''
        ...
    
    @elevation.setter
    def elevation(self, value : str):
        '''See the elevation property definition in CSS2.'''
        ...
    
    @property
    def empty_cells(self) -> str:
        ...
    
    @empty_cells.setter
    def empty_cells(self, value : str):
        ...
    
    @property
    def float(self) -> str:
        '''See the float property definition in CSS2.'''
        ...
    
    @float.setter
    def float(self, value : str):
        '''See the float property definition in CSS2.'''
        ...
    
    @property
    def font(self) -> str:
        '''See the font property definition in CSS2.'''
        ...
    
    @font.setter
    def font(self, value : str):
        '''See the font property definition in CSS2.'''
        ...
    
    @property
    def font_family(self) -> str:
        ...
    
    @font_family.setter
    def font_family(self, value : str):
        ...
    
    @property
    def font_size(self) -> str:
        ...
    
    @font_size.setter
    def font_size(self, value : str):
        ...
    
    @property
    def font_size_adjust(self) -> str:
        ...
    
    @font_size_adjust.setter
    def font_size_adjust(self, value : str):
        ...
    
    @property
    def font_stretch(self) -> str:
        ...
    
    @font_stretch.setter
    def font_stretch(self, value : str):
        ...
    
    @property
    def font_style(self) -> str:
        ...
    
    @font_style.setter
    def font_style(self, value : str):
        ...
    
    @property
    def font_variant(self) -> str:
        ...
    
    @font_variant.setter
    def font_variant(self, value : str):
        ...
    
    @property
    def font_weight(self) -> str:
        ...
    
    @font_weight.setter
    def font_weight(self, value : str):
        ...
    
    @property
    def grid_template_columns(self) -> str:
        ...
    
    @grid_template_columns.setter
    def grid_template_columns(self, value : str):
        ...
    
    @property
    def grid_template_rows(self) -> str:
        ...
    
    @grid_template_rows.setter
    def grid_template_rows(self, value : str):
        ...
    
    @property
    def grid_template_areas(self) -> str:
        ...
    
    @grid_template_areas.setter
    def grid_template_areas(self, value : str):
        ...
    
    @property
    def height(self) -> str:
        '''See the height property definition in CSS2.'''
        ...
    
    @height.setter
    def height(self, value : str):
        '''See the height property definition in CSS2.'''
        ...
    
    @property
    def left(self) -> str:
        '''See the left property definition in CSS2.'''
        ...
    
    @left.setter
    def left(self, value : str):
        '''See the left property definition in CSS2.'''
        ...
    
    @property
    def letter_spacing(self) -> str:
        ...
    
    @letter_spacing.setter
    def letter_spacing(self, value : str):
        ...
    
    @property
    def line_height(self) -> str:
        ...
    
    @line_height.setter
    def line_height(self, value : str):
        ...
    
    @property
    def list_style(self) -> str:
        ...
    
    @list_style.setter
    def list_style(self, value : str):
        ...
    
    @property
    def list_style_image(self) -> str:
        ...
    
    @list_style_image.setter
    def list_style_image(self, value : str):
        ...
    
    @property
    def list_style_position(self) -> str:
        ...
    
    @list_style_position.setter
    def list_style_position(self, value : str):
        ...
    
    @property
    def list_style_type(self) -> str:
        ...
    
    @list_style_type.setter
    def list_style_type(self, value : str):
        ...
    
    @property
    def margin(self) -> str:
        '''See the margin property definition in CSS2.'''
        ...
    
    @margin.setter
    def margin(self, value : str):
        '''See the margin property definition in CSS2.'''
        ...
    
    @property
    def margin_top(self) -> str:
        ...
    
    @margin_top.setter
    def margin_top(self, value : str):
        ...
    
    @property
    def margin_right(self) -> str:
        ...
    
    @margin_right.setter
    def margin_right(self, value : str):
        ...
    
    @property
    def margin_bottom(self) -> str:
        ...
    
    @margin_bottom.setter
    def margin_bottom(self, value : str):
        ...
    
    @property
    def margin_left(self) -> str:
        ...
    
    @margin_left.setter
    def margin_left(self, value : str):
        ...
    
    @property
    def marker_offset(self) -> str:
        ...
    
    @marker_offset.setter
    def marker_offset(self, value : str):
        ...
    
    @property
    def marks(self) -> str:
        '''See the marks property definition in CSS2.'''
        ...
    
    @marks.setter
    def marks(self, value : str):
        '''See the marks property definition in CSS2.'''
        ...
    
    @property
    def max_height(self) -> str:
        ...
    
    @max_height.setter
    def max_height(self, value : str):
        ...
    
    @property
    def max_width(self) -> str:
        ...
    
    @max_width.setter
    def max_width(self, value : str):
        ...
    
    @property
    def min_height(self) -> str:
        ...
    
    @min_height.setter
    def min_height(self, value : str):
        ...
    
    @property
    def min_width(self) -> str:
        ...
    
    @min_width.setter
    def min_width(self, value : str):
        ...
    
    @property
    def orphans(self) -> str:
        '''See the orphans property definition in CSS2.'''
        ...
    
    @orphans.setter
    def orphans(self, value : str):
        '''See the orphans property definition in CSS2.'''
        ...
    
    @property
    def outline(self) -> str:
        '''See the outline property definition in CSS2.'''
        ...
    
    @outline.setter
    def outline(self, value : str):
        '''See the outline property definition in CSS2.'''
        ...
    
    @property
    def outline_color(self) -> str:
        ...
    
    @outline_color.setter
    def outline_color(self, value : str):
        ...
    
    @property
    def outline_style(self) -> str:
        ...
    
    @outline_style.setter
    def outline_style(self, value : str):
        ...
    
    @property
    def outline_width(self) -> str:
        ...
    
    @outline_width.setter
    def outline_width(self, value : str):
        ...
    
    @property
    def overflow(self) -> str:
        '''See the overflow property definition in CSS2.'''
        ...
    
    @overflow.setter
    def overflow(self, value : str):
        '''See the overflow property definition in CSS2.'''
        ...
    
    @property
    def padding(self) -> str:
        '''See the padding property definition in CSS2.'''
        ...
    
    @padding.setter
    def padding(self, value : str):
        '''See the padding property definition in CSS2.'''
        ...
    
    @property
    def padding_top(self) -> str:
        ...
    
    @padding_top.setter
    def padding_top(self, value : str):
        ...
    
    @property
    def padding_right(self) -> str:
        ...
    
    @padding_right.setter
    def padding_right(self, value : str):
        ...
    
    @property
    def padding_bottom(self) -> str:
        ...
    
    @padding_bottom.setter
    def padding_bottom(self, value : str):
        ...
    
    @property
    def padding_left(self) -> str:
        ...
    
    @padding_left.setter
    def padding_left(self, value : str):
        ...
    
    @property
    def page(self) -> str:
        '''See the page property definition in CSS2.'''
        ...
    
    @page.setter
    def page(self, value : str):
        '''See the page property definition in CSS2.'''
        ...
    
    @property
    def page_break_after(self) -> str:
        ...
    
    @page_break_after.setter
    def page_break_after(self, value : str):
        ...
    
    @property
    def page_break_before(self) -> str:
        ...
    
    @page_break_before.setter
    def page_break_before(self, value : str):
        ...
    
    @property
    def page_break_inside(self) -> str:
        ...
    
    @page_break_inside.setter
    def page_break_inside(self, value : str):
        ...
    
    @property
    def pause(self) -> str:
        '''See the pause property definition in CSS2.'''
        ...
    
    @pause.setter
    def pause(self, value : str):
        '''See the pause property definition in CSS2.'''
        ...
    
    @property
    def pause_after(self) -> str:
        ...
    
    @pause_after.setter
    def pause_after(self, value : str):
        ...
    
    @property
    def pause_before(self) -> str:
        ...
    
    @pause_before.setter
    def pause_before(self, value : str):
        ...
    
    @property
    def pitch(self) -> str:
        '''See the pitch property definition in CSS2.'''
        ...
    
    @pitch.setter
    def pitch(self, value : str):
        '''See the pitch property definition in CSS2.'''
        ...
    
    @property
    def pitch_range(self) -> str:
        ...
    
    @pitch_range.setter
    def pitch_range(self, value : str):
        ...
    
    @property
    def play_during(self) -> str:
        ...
    
    @play_during.setter
    def play_during(self, value : str):
        ...
    
    @property
    def position(self) -> str:
        '''See the position property definition in CSS2.'''
        ...
    
    @position.setter
    def position(self, value : str):
        '''See the position property definition in CSS2.'''
        ...
    
    @property
    def quotes(self) -> str:
        '''See the quotes property definition in CSS2.'''
        ...
    
    @quotes.setter
    def quotes(self, value : str):
        '''See the quotes property definition in CSS2.'''
        ...
    
    @property
    def richness(self) -> str:
        '''See the richness property definition in CSS2.'''
        ...
    
    @richness.setter
    def richness(self, value : str):
        '''See the richness property definition in CSS2.'''
        ...
    
    @property
    def right(self) -> str:
        '''See the right property definition in CSS2.'''
        ...
    
    @right.setter
    def right(self, value : str):
        '''See the right property definition in CSS2.'''
        ...
    
    @property
    def size(self) -> str:
        '''See the size property definition in CSS2.'''
        ...
    
    @size.setter
    def size(self, value : str):
        '''See the size property definition in CSS2.'''
        ...
    
    @property
    def speak(self) -> str:
        '''See the speak property definition in CSS2.'''
        ...
    
    @speak.setter
    def speak(self, value : str):
        '''See the speak property definition in CSS2.'''
        ...
    
    @property
    def speak_header(self) -> str:
        ...
    
    @speak_header.setter
    def speak_header(self, value : str):
        ...
    
    @property
    def speak_numeral(self) -> str:
        ...
    
    @speak_numeral.setter
    def speak_numeral(self, value : str):
        ...
    
    @property
    def speak_punctuation(self) -> str:
        ...
    
    @speak_punctuation.setter
    def speak_punctuation(self, value : str):
        ...
    
    @property
    def speech_rate(self) -> str:
        ...
    
    @speech_rate.setter
    def speech_rate(self, value : str):
        ...
    
    @property
    def stress(self) -> str:
        '''See the stress property definition in CSS2.'''
        ...
    
    @stress.setter
    def stress(self, value : str):
        '''See the stress property definition in CSS2.'''
        ...
    
    @property
    def table_layout(self) -> str:
        ...
    
    @table_layout.setter
    def table_layout(self, value : str):
        ...
    
    @property
    def text_align(self) -> str:
        ...
    
    @text_align.setter
    def text_align(self, value : str):
        ...
    
    @property
    def text_decoration(self) -> str:
        ...
    
    @text_decoration.setter
    def text_decoration(self, value : str):
        ...
    
    @property
    def text_indent(self) -> str:
        ...
    
    @text_indent.setter
    def text_indent(self, value : str):
        ...
    
    @property
    def text_shadow(self) -> str:
        ...
    
    @text_shadow.setter
    def text_shadow(self, value : str):
        ...
    
    @property
    def text_transform(self) -> str:
        ...
    
    @text_transform.setter
    def text_transform(self, value : str):
        ...
    
    @property
    def top(self) -> str:
        '''See the top property definition in CSS2.'''
        ...
    
    @top.setter
    def top(self, value : str):
        '''See the top property definition in CSS2.'''
        ...
    
    @property
    def unicode_bidi(self) -> str:
        ...
    
    @unicode_bidi.setter
    def unicode_bidi(self, value : str):
        ...
    
    @property
    def vertical_align(self) -> str:
        ...
    
    @vertical_align.setter
    def vertical_align(self, value : str):
        ...
    
    @property
    def visibility(self) -> str:
        '''See the visibility property definition in CSS2.'''
        ...
    
    @visibility.setter
    def visibility(self, value : str):
        '''See the visibility property definition in CSS2.'''
        ...
    
    @property
    def voice_family(self) -> str:
        ...
    
    @voice_family.setter
    def voice_family(self, value : str):
        ...
    
    @property
    def volume(self) -> str:
        '''See the volume property definition in CSS2.'''
        ...
    
    @volume.setter
    def volume(self, value : str):
        '''See the volume property definition in CSS2.'''
        ...
    
    @property
    def white_space(self) -> str:
        ...
    
    @white_space.setter
    def white_space(self, value : str):
        ...
    
    @property
    def widows(self) -> str:
        '''See the widows property definition in CSS2.'''
        ...
    
    @widows.setter
    def widows(self, value : str):
        '''See the widows property definition in CSS2.'''
        ...
    
    @property
    def width(self) -> str:
        '''See the width property definition in CSS2.'''
        ...
    
    @width.setter
    def width(self, value : str):
        '''See the width property definition in CSS2.'''
        ...
    
    @property
    def word_spacing(self) -> str:
        ...
    
    @word_spacing.setter
    def word_spacing(self, value : str):
        ...
    
    @property
    def z_index(self) -> str:
        ...
    
    @z_index.setter
    def z_index(self, value : str):
        ...
    
    def __getitem__(self, key : int) -> str:
        '''Used to retrieve the properties that have been explicitly set in this declaration block. The order of the properties retrieved using this method does not have to be the order in which they were set. This method can be used to iterate over all properties in this declaration block.'''
        ...
    
    ...

class ICSSStyleRule(ICSSRule):
    '''The CSSStyleRule interface represents a single rule set in a CSS style sheet.'''
    
    @property
    def selector_text(self) -> str:
        ...
    
    @property
    def style(self) -> aspose.svg.dom.css.ICSSStyleDeclaration:
        '''The declaration-block of this rule set.'''
        ...
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSStyleSheet(IStyleSheet):
    '''The CSSStyleSheet interface is a concrete interface used to represent a CSS style sheet i.e., a style sheet whose content type is "text/css".'''
    
    def insert_rule(self, rule : str, index : int) -> int:
        '''Used to insert a new rule into the style sheet. The new rule now becomes part of the cascade.
        
        :param rule: The style rule.
        :param index: The rule index.
        :returns: The inserted index'''
        ...
    
    def delete_rule(self, index : int):
        '''Used to delete a rule from the style sheet.
        
        :param index: The index.'''
        ...
    
    @property
    def owner_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    @property
    def css_rules(self) -> aspose.svg.dom.css.ICSSRuleList:
        ...
    
    @property
    def type(self) -> str:
        '''This specifies the style sheet language for this style sheet. The style sheet language is specified as a content type (e.g. "text/css").'''
        ...
    
    @property
    def disabled(self) -> bool:
        '''false if the style sheet is applied to the document. true if it is not. Modifying this attribute may cause a new resolution of style for the document. A stylesheet only applies if both an appropriate medium definition is present and the disabled attribute is false. So, if the media doesn't apply to the current user agent, the disabled attribute is ignored.'''
        ...
    
    @disabled.setter
    def disabled(self, value : bool):
        '''false if the style sheet is applied to the document. true if it is not. Modifying this attribute may cause a new resolution of style for the document. A stylesheet only applies if both an appropriate medium definition is present and the disabled attribute is false. So, if the media doesn't apply to the current user agent, the disabled attribute is ignored.'''
        ...
    
    @property
    def owner_node(self) -> aspose.svg.dom.Node:
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.IStyleSheet:
        ...
    
    @property
    def href(self) -> str:
        '''If the style sheet is a linked style sheet, the value of its attribute is its location. For inline style sheets, the value of this attribute is null.'''
        ...
    
    @property
    def title(self) -> str:
        '''The advisory title.'''
        ...
    
    @property
    def media(self) -> aspose.svg.dom.css.IMediaList:
        '''The intended destination media for style information.'''
        ...
    
    ...

class ICSSUnknownRule(ICSSRule):
    '''The CSSUnknownRule interface represents an at-rule not supported by this user agent.'''
    
    @property
    def type(self) -> int:
        '''The type of the rule, as defined above. The expectation is that binding-specific casting methods can be used to cast down from an instance of the CSSRule interface to the specific derived interface implied by the type.'''
        ...
    
    @property
    def css_text(self) -> str:
        ...
    
    @css_text.setter
    def css_text(self, value : str):
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.ICSSStyleSheet:
        ...
    
    @property
    def parent_rule(self) -> aspose.svg.dom.css.ICSSRule:
        ...
    
    ...

class ICSSValueList:
    '''The interface provides the abstraction of an ordered collection of CSS values.'''
    
    @property
    def length(self) -> int:
        '''The number of CSSValues in the list.'''
        ...
    
    def __getitem__(self, key : int) -> aspose.svg.dom.css.CSSValue:
        '''Method returns the :py:class:`aspose.svg.dom.css.CSSValue` at the specified index.
        http://www.w3.org/TR/2000/REC-DOM-Level-2-Style-20001113/css.html#CSS-CSSValueList'''
        ...
    
    ...

class IDocumentCSS(IDocumentStyle):
    '''This interface represents a document with a CSS view.'''
    
    def get_override_style(self, elt : aspose.svg.dom.Element, pseudo_elt : str) -> aspose.svg.dom.css.ICSSStyleDeclaration:
        '''This method is used to retrieve the override style declaration for a specified element and a specified pseudo-element.
        
        :param elt: The element whose style is to be modified. This parameter cannot be null.
        :param pseudo_elt: The pseudo-element or null if none.
        :returns: The override style declaration'''
        ...
    
    @property
    def style_sheets(self) -> aspose.svg.dom.css.IStyleSheetList:
        ...
    
    ...

class IDocumentStyle:
    '''The DocumentStyle interface provides a mechanism by which the style sheets embedded in a document can be retrieved. The expectation is that an instance of the DocumentStyle interface can be obtained by using binding-specific casting methods on an instance of the Document interface.'''
    
    @property
    def style_sheets(self) -> aspose.svg.dom.css.IStyleSheetList:
        ...
    
    ...

class IElementCSSInlineStyle:
    '''Inline style information attached to elements is exposed through the style attribute. This represents the contents of the STYLE attribute for HTML elements (or elements in other schemas or DTDs which use the STYLE attribute in the same way).'''
    
    @property
    def style(self) -> aspose.svg.dom.css.ICSSStyleDeclaration:
        '''Represents Represents a style attribute that allows author to directly apply style information to specific element.'''
        ...
    
    ...

class ILinkStyle:
    '''The LinkStyle interface provides a mechanism by which a style sheet can be retrieved from the node responsible for linking it into a document. An instance of the LinkStyle interface can be obtained using binding-specific casting methods on an instance of a linking node (HTMLLinkElement, HTMLStyleElement or ProcessingInstruction in DOM Level 2).'''
    
    @property
    def sheet(self) -> aspose.svg.dom.css.IStyleSheet:
        '''Gets the associated style sheet.'''
        ...
    
    ...

class IMediaList:
    '''The MediaList interface provides the abstraction of an ordered collection of media, without defining or constraining how this collection is implemented. An empty list is the same as a list that contains the medium "all".'''
    
    def delete_medium(self, old_medium : str):
        '''Deletes the medium indicated by oldMedium from the list.
        
        :param old_medium: The old medium.'''
        ...
    
    def append_medium(self, new_medium : str):
        '''Adds the medium newMedium to the end of the list. If the newMedium is already used, it is first removed.
        
        :param new_medium: The new medium.'''
        ...
    
    @property
    def media_text(self) -> str:
        ...
    
    @property
    def length(self) -> int:
        '''The number of media in the list. The range of valid media is 0 to length-1 inclusive.'''
        ...
    
    def __getitem__(self, key : int) -> str:
        '''Returns the indexth in the list. If index is greater than or equal to the number of media in the list, this returns null.'''
        ...
    
    ...

class IStyleSheet:
    '''The StyleSheet interface is the abstract base interface for any type of style sheet. It represents a single style sheet associated with a structured document.'''
    
    @property
    def type(self) -> str:
        '''This specifies the style sheet language for this style sheet. The style sheet language is specified as a content type (e.g. "text/css").'''
        ...
    
    @property
    def disabled(self) -> bool:
        '''false if the style sheet is applied to the document. true if it is not. Modifying this attribute may cause a new resolution of style for the document. A stylesheet only applies if both an appropriate medium definition is present and the disabled attribute is false. So, if the media doesn't apply to the current user agent, the disabled attribute is ignored.'''
        ...
    
    @disabled.setter
    def disabled(self, value : bool):
        '''false if the style sheet is applied to the document. true if it is not. Modifying this attribute may cause a new resolution of style for the document. A stylesheet only applies if both an appropriate medium definition is present and the disabled attribute is false. So, if the media doesn't apply to the current user agent, the disabled attribute is ignored.'''
        ...
    
    @property
    def owner_node(self) -> aspose.svg.dom.Node:
        ...
    
    @property
    def parent_style_sheet(self) -> aspose.svg.dom.css.IStyleSheet:
        ...
    
    @property
    def href(self) -> str:
        '''If the style sheet is a linked style sheet, the value of its attribute is its location. For inline style sheets, the value of this attribute is null.'''
        ...
    
    @property
    def title(self) -> str:
        '''The advisory title.'''
        ...
    
    @property
    def media(self) -> aspose.svg.dom.css.IMediaList:
        '''The intended destination media for style information.'''
        ...
    
    ...

class IStyleSheetList:
    '''The StyleSheetList interface provides the abstraction of an ordered collection of style sheets.'''
    
    @property
    def length(self) -> int:
        '''The number of StyleSheets in the list. The range of valid child stylesheet indices is 0 to length-1 inclusive.'''
        ...
    
    def __getitem__(self, key : int) -> aspose.svg.dom.css.ICSSStyleSheet:
        '''Used to retrieve a style sheet by method item(int index) accordind to http://www.w3.org/TR/2000/REC-DOM-Level-2-Style-20001113/stylesheets.html.'''
        ...
    
    ...

class IViewCSS(aspose.svg.dom.views.IAbstractView):
    '''This interface represents a CSS view.'''
    
    @overload
    def get_computed_style(self, element : aspose.svg.dom.Element) -> aspose.svg.dom.css.ICSSStyleDeclaration:
        '''This method is used to get the computed style as it is defined in CSS2.
        
        :param element: The element whose style is to be computed. This parameter cannot be null.
        :returns: The computed style'''
        ...
    
    @overload
    def get_computed_style(self, element : aspose.svg.dom.Element, pseudo_element : str) -> aspose.svg.dom.css.ICSSStyleDeclaration:
        '''This method is used to get the computed style as it is defined in CSS2.
        
        :param element: The element whose style is to be computed. This parameter cannot be null.
        :param pseudo_element: The pseudo element.
        :returns: The computed style'''
        ...
    
    @property
    def document(self) -> aspose.svg.dom.views.IDocumentView:
        '''The source DocumentView of which this is an AbstractView.'''
        ...
    
    ...

class RGBColor(aspose.svg.dom.DOMObject):
    '''The RGBColor interface is used to represent any RGB color value. This interface reflects the values in the underlying style property. Hence, modifications made to the CSSPrimitiveValue objects modify the style property.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def to_native(self) -> aspose.pydrawing.Color:
        '''Converts to the native color object.
        
        :returns: The :py:class:`aspose.pydrawing.Color` object.'''
        ...
    
    @property
    def red(self) -> aspose.svg.dom.css.CSSPrimitiveValue:
        '''Gets the red component value of this Color class.'''
        ...
    
    @property
    def green(self) -> aspose.svg.dom.css.CSSPrimitiveValue:
        '''Gets the green component value of this Color class.'''
        ...
    
    @property
    def blue(self) -> aspose.svg.dom.css.CSSPrimitiveValue:
        '''Gets the blue component value of this Color class.'''
        ...
    
    @property
    def alpha(self) -> aspose.svg.dom.css.CSSPrimitiveValue:
        '''Gets the alpha component value of this Color class.'''
        ...
    
    ...

class Rect(aspose.svg.dom.DOMObject):
    '''The Rect interface is used to represent any rect value. This interface reflects the values in the underlying style property. Hence, modifications made to the CSSPrimitiveValue objects modify the style property.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def top(self) -> aspose.svg.dom.css.CSSPrimitiveValue:
        '''This attribute is used for the top of the rect.'''
        ...
    
    @property
    def right(self) -> aspose.svg.dom.css.CSSPrimitiveValue:
        '''This attribute is used for the right of the rect.'''
        ...
    
    @property
    def bottom(self) -> aspose.svg.dom.css.CSSPrimitiveValue:
        '''This attribute is used for the bottom of the rect.'''
        ...
    
    @property
    def left(self) -> aspose.svg.dom.css.CSSPrimitiveValue:
        '''This attribute is used for the left of the rect.'''
        ...
    
    ...

class CSSEngineMode:
    '''Specifies CSSEngine mode'''
    
    @classmethod
    @property
    def DEFAULT(cls) -> CSSEngineMode:
        '''CSS engine will work like usual.'''
        ...
    
    @classmethod
    @property
    def NOT_STRICT(cls) -> CSSEngineMode:
        '''CSS parser will work in not strict mode. All not documented properties will be parsed and could be accessed through :py:class:`aspose.svg.dom.css.ICSSStyleDeclaration`.'''
        ...
    
    ...

