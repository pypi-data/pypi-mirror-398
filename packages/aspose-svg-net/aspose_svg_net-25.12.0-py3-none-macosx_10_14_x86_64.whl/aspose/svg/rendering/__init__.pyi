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

class CssOptions:
    '''Represents css rendering options.'''
    
    @property
    def media_type(self) -> aspose.svg.rendering.MediaType:
        ...
    
    @media_type.setter
    def media_type(self, value : aspose.svg.rendering.MediaType):
        ...
    
    ...

class Device:
    '''Represents a base class for implementing rendering devices that are used to draw graphics in various formats and environments.'''
    
    ...

class GlyphInfo:
    '''Contains glyph related information.'''
    
    @property
    def width(self) -> float:
        '''Gets the width of the glyph, in points.'''
        ...
    
    @property
    def offset(self) -> float:
        '''Gets the offset to the next glyph in points.'''
        ...
    
    @property
    def index(self) -> int:
        '''Gets the index of this glyph in the font.'''
        ...
    
    @property
    def string_representation(self) -> str:
        ...
    
    ...

class GraphicContext:
    '''Holds current graphics control parameters.
    These parameters define the global framework within which the graphics operators execute.'''
    
    def transform(self, matrix : aspose.svg.drawing.IMatrix):
        '''Modify the current transformation matrix by multiplying the specified matrix.
        
        :param matrix: Transformation matrix.'''
        ...
    
    def clone(self) -> aspose.svg.rendering.GraphicContext:
        '''Creates a new instance of a GraphicContext class with the same property values as an existing instance.
        
        :returns: Instance of a GraphicContext'''
        ...
    
    @property
    def current_element(self) -> aspose.svg.dom.Element:
        ...
    
    @property
    def line_cap(self) -> aspose.svg.drawing.StrokeLineCap:
        ...
    
    @line_cap.setter
    def line_cap(self, value : aspose.svg.drawing.StrokeLineCap):
        ...
    
    @property
    def line_dash_offset(self) -> float:
        ...
    
    @line_dash_offset.setter
    def line_dash_offset(self, value : float):
        ...
    
    @property
    def line_dash_pattern(self) -> List[float]:
        ...
    
    @line_dash_pattern.setter
    def line_dash_pattern(self, value : List[float]):
        ...
    
    @property
    def line_join(self) -> aspose.svg.drawing.StrokeLineJoin:
        ...
    
    @line_join.setter
    def line_join(self, value : aspose.svg.drawing.StrokeLineJoin):
        ...
    
    @property
    def line_width(self) -> float:
        ...
    
    @line_width.setter
    def line_width(self, value : float):
        ...
    
    @property
    def miter_limit(self) -> float:
        ...
    
    @miter_limit.setter
    def miter_limit(self, value : float):
        ...
    
    @property
    def fill_brush(self) -> aspose.svg.drawing.IBrush:
        ...
    
    @fill_brush.setter
    def fill_brush(self, value : aspose.svg.drawing.IBrush):
        ...
    
    @property
    def stroke_brush(self) -> aspose.svg.drawing.IBrush:
        ...
    
    @stroke_brush.setter
    def stroke_brush(self, value : aspose.svg.drawing.IBrush):
        ...
    
    @property
    def font(self) -> aspose.svg.drawing.ITrueTypeFont:
        '''Sets or gets the true type font object that is used for rendering text.'''
        ...
    
    @font.setter
    def font(self, value : aspose.svg.drawing.ITrueTypeFont):
        '''Sets or gets the true type font object that is used for rendering text.'''
        ...
    
    @property
    def font_size(self) -> float:
        ...
    
    @font_size.setter
    def font_size(self, value : float):
        ...
    
    @property
    def font_style(self) -> aspose.svg.drawing.WebFontStyle:
        ...
    
    @font_style.setter
    def font_style(self, value : aspose.svg.drawing.WebFontStyle):
        ...
    
    @property
    def character_spacing(self) -> float:
        ...
    
    @character_spacing.setter
    def character_spacing(self, value : float):
        ...
    
    @property
    def transformation_matrix(self) -> aspose.svg.drawing.IMatrix:
        ...
    
    @transformation_matrix.setter
    def transformation_matrix(self, value : aspose.svg.drawing.IMatrix):
        ...
    
    @property
    def text_info(self) -> aspose.svg.rendering.TextInfo:
        ...
    
    ...

class IDevice:
    '''Defines methods and properties that support custom rendering of the graphic elements like paths, text and images.'''
    
    def save_graphic_context(self):
        '''Pushes a copy of the entire graphics context onto the stack.'''
        ...
    
    def restore_graphic_context(self):
        '''Restores the entire graphics context to its former value by popping it from the stack.'''
        ...
    
    def begin_document(self, document : aspose.svg.dom.Document):
        '''Begins rendering of the document.
        
        :param document: The document.'''
        ...
    
    def end_document(self):
        '''Ends rendering of the document.'''
        ...
    
    def begin_page(self, size : aspose.pydrawing.SizeF):
        '''Begins rendering of the new page.
        
        :param size: Size of the page.'''
        ...
    
    def end_page(self):
        '''Ends rendering of the current page.'''
        ...
    
    def begin_element(self, element : aspose.svg.dom.Element, rect : aspose.pydrawing.RectangleF) -> bool:
        '''Begins rendering of the element.
        
        :param element: The :py:class:`aspose.svg.dom.Element`.
        :param rect: Bounding box of the node.
        :returns: Returns [true] if element should be processed.'''
        ...
    
    def end_element(self, element : aspose.svg.dom.Element):
        '''Ends rendering of the element.
        
        :param element: The :py:class:`aspose.svg.dom.Element`.'''
        ...
    
    def close_path(self):
        '''Closes the current subpath by appending a straight line segment from the current point to the starting point of the subpath.
        If the current subpath is already closed, "ClosePath" does nothing.
        This operator terminates the current subpath. Appending another segment to the current path begins a new subpath,
        even if the new segment begins at the endpoint reached by the "ClosePath" method.'''
        ...
    
    def move_to(self, pt : aspose.pydrawing.PointF):
        '''Begins a new subpath by moving the current point to coordinates of the parameter pt, omitting any connecting line segment.
        If the previous path construction method in the current path was also "MoveTo", the new "MoveTo" overrides it;
        no vestige of the previous "MoveTo" operation remains in the path.
        
        :param pt: Point of where to move the path to.'''
        ...
    
    def line_to(self, pt : aspose.pydrawing.PointF):
        '''Appends a straight line segment from the current point to the point (pt). The new current point is pt.
        
        :param pt: Point of where to create the line to.'''
        ...
    
    def add_rect(self, rect : aspose.pydrawing.RectangleF):
        '''Appends a rectangle to the current path as a complete subpath.
        
        :param rect: A rectangle to draw.'''
        ...
    
    def cubic_bezier_to(self, pt1 : aspose.pydrawing.PointF, pt2 : aspose.pydrawing.PointF, pt3 : aspose.pydrawing.PointF):
        '''Appends a cubic Bézier curve to the current path. The curve extends from the current point to the point pt3,
        using pt1 and pt2 as the Bézier control points. The new current point is pt3.
        
        :param pt1: Coordinates of first point
        :param pt2: Coordinates of second point
        :param pt3: Coordinates of third point'''
        ...
    
    def stroke(self):
        '''Strokes a line along the current path. The stroked line follows each straight or curved segment in the path,
        centered on the segment with sides parallel to it. Each of the path’s subpaths is treated separately.
        This method terminates current path.'''
        ...
    
    def fill(self, rule : aspose.svg.drawing.FillRule):
        '''Fills the entire region enclosed by the current path.
        If the path consists of several disconnected subpaths, it fills the insides of all subpaths,
        considered together.
        This method terminates current path.
        
        :param rule: Filling rule specifies how the interior of a closed path is filled'''
        ...
    
    def clip(self, rule : aspose.svg.drawing.FillRule):
        '''Modifies the current clipping path by intersecting it with the current path, using the FillRule to determine the region to fill.
        This method terminates current path.
        
        :param rule: Filling rule specifies how the interior of a closed path is clipped'''
        ...
    
    def stroke_and_fill(self, rule : aspose.svg.drawing.FillRule):
        '''Strokes and fill current path.
        This method terminates current path.
        
        :param rule: Filling rule specifies how the interior of a closed path is filled.'''
        ...
    
    def fill_text(self, text : str, pt : aspose.pydrawing.PointF):
        '''Fills the specified text string at the specified location.
        
        :param text: String to fill.
        :param pt: Point that specifies the coordinates of the text.'''
        ...
    
    def stroke_text(self, text : str, pt : aspose.pydrawing.PointF):
        '''Strokes the specified text string at the specified location.
        
        :param text: String to stroke.
        :param pt: Point that specifies the coordinates where to start the text.'''
        ...
    
    def draw_image(self, data : bytes, image_format : aspose.svg.drawing.WebImageFormat, rect : aspose.pydrawing.RectangleF):
        '''Draws the specified image.
        
        :param data: An array of bytes representing the image.
        :param image_format: Image format.
        :param rect: A rectangle which determines position and size to draw.'''
        ...
    
    def flush(self):
        '''Flushes all data to output stream.'''
        ...
    
    @property
    def options(self) -> aspose.svg.rendering.RenderingOptions:
        '''Gets rendering options.'''
        ...
    
    @property
    def graphic_context(self) -> aspose.svg.rendering.GraphicContext:
        ...
    
    ...

class PageSetup:
    '''Represents a page setup object is used for configuration output page-set.'''
    
    def set_left_right_page(self, left_page : aspose.svg.drawing.Page, right_page : aspose.svg.drawing.Page):
        '''Sets the Left/Right page configuration.
        
        :param left_page: The left page.
        :param right_page: The right page.'''
        ...
    
    @property
    def at_page_priority(self) -> aspose.svg.rendering.AtPagePriority:
        ...
    
    @at_page_priority.setter
    def at_page_priority(self, value : aspose.svg.rendering.AtPagePriority):
        ...
    
    @property
    def left_page(self) -> aspose.svg.drawing.Page:
        ...
    
    @property
    def right_page(self) -> aspose.svg.drawing.Page:
        ...
    
    @property
    def any_page(self) -> aspose.svg.drawing.Page:
        ...
    
    @any_page.setter
    def any_page(self, value : aspose.svg.drawing.Page):
        ...
    
    @property
    def first_page(self) -> aspose.svg.drawing.Page:
        ...
    
    @first_page.setter
    def first_page(self, value : aspose.svg.drawing.Page):
        ...
    
    @property
    def sizing(self) -> aspose.svg.rendering.SizingType:
        '''Gets the sizing type.'''
        ...
    
    @sizing.setter
    def sizing(self, value : aspose.svg.rendering.SizingType):
        '''Sets the sizing type.'''
        ...
    
    ...

class Renderer:
    '''Represents a base class for all renderers and implemnts IDisposable interface.'''
    
    ...

class RenderingOptions:
    '''Represents rendering options.'''
    
    @property
    def css(self) -> aspose.svg.rendering.CssOptions:
        '''Gets a :py:class:`aspose.svg.rendering.CssOptions` object which is used for configuration of css properties processing.'''
        ...
    
    @property
    def page_setup(self) -> aspose.svg.rendering.PageSetup:
        ...
    
    @property
    def horizontal_resolution(self) -> aspose.svg.drawing.Resolution:
        ...
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : aspose.svg.drawing.Resolution):
        ...
    
    @property
    def background_color(self) -> aspose.pydrawing.Color:
        ...
    
    @background_color.setter
    def background_color(self, value : aspose.pydrawing.Color):
        ...
    
    @property
    def vertical_resolution(self) -> aspose.svg.drawing.Resolution:
        ...
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : aspose.svg.drawing.Resolution):
        ...
    
    ...

class SvgRenderer(Renderer):
    '''Represents SVG document renderer.'''
    
    @overload
    def render(self, device : aspose.svg.rendering.IDevice, timeout : TimeSpan, sources : List[aspose.svg.SVGDocument]):
        ...
    
    @overload
    def render(self, device : aspose.svg.rendering.IDevice, source : aspose.svg.SVGDocument):
        ...
    
    @overload
    def render(self, device : aspose.svg.rendering.IDevice, source : aspose.svg.SVGDocument, timeout : TimeSpan):
        ...
    
    @overload
    def render(self, device : aspose.svg.rendering.IDevice, source : aspose.svg.SVGDocument, timeout : int):
        ...
    
    @overload
    def render(self, device : aspose.svg.rendering.IDevice, sources : List[aspose.svg.SVGDocument]):
        ...
    
    @overload
    def render(self, device : aspose.svg.rendering.IDevice, timeout : int, sources : List[aspose.svg.SVGDocument]):
        ...
    
    ...

class TextInfo:
    '''Contains information about rendered text.'''
    
    @property
    def glyph_infos(self) -> List[aspose.svg.rendering.GlyphInfo]:
        ...
    
    ...

class AtPagePriority:
    '''Specifies possible orders of applying page size declarations.'''
    
    @classmethod
    @property
    def OPTIONS_PRIORITY(cls) -> AtPagePriority:
        '''Specifies that :py:class:`aspose.svg.rendering.PageSetup` values declared in :py:class:`aspose.svg.rendering.RenderingOptions` will override values defined in css by ``@page`` rules :link:`https://www.w3.org/TR/CSS2/page.html#page-selectors`.'''
        ...
    
    @classmethod
    @property
    def CSS_PRIORITY(cls) -> AtPagePriority:
        '''Specifies that ``@page`` rules :link:`https://www.w3.org/TR/CSS2/page.html#page-selectors` defined in css will override values defined in :py:class:`aspose.svg.rendering.PageSetup`.'''
        ...
    
    ...

class BooleanPathOp:
    '''Specifies the boolean operation used when combining two paths.'''
    
    @classmethod
    @property
    def UNION(cls) -> BooleanPathOp:
        '''Union: the combined area of both paths.'''
        ...
    
    @classmethod
    @property
    def DIFFERENCE(cls) -> BooleanPathOp:
        '''Difference: the area of the first path minus the second path (A - B).'''
        ...
    
    @classmethod
    @property
    def INTERSECTION(cls) -> BooleanPathOp:
        '''Intersection: the area common to both paths.'''
        ...
    
    @classmethod
    @property
    def EXCLUSION(cls) -> BooleanPathOp:
        '''Exclusion: the symmetric difference of the two paths (XOR).'''
        ...
    
    ...

class MediaType:
    '''Specifies possible media types used during rendering.'''
    
    @classmethod
    @property
    def PRINT(cls) -> MediaType:
        '''The ``Print`` media is used during rendering.'''
        ...
    
    @classmethod
    @property
    def SCREEN(cls) -> MediaType:
        '''The ``Screen`` media is used during rendering.'''
        ...
    
    ...

class SizingType:
    '''Represents the enumeration of page sizing types.'''
    
    @classmethod
    @property
    def FIT_CONTENT(cls) -> SizingType:
        '''Changing given sizes of the page to fit the size of the content it contains.'''
        ...
    
    @classmethod
    @property
    def SCALE_CONTENT(cls) -> SizingType:
        '''Scaling a content size in accordance to the given size of the page.'''
        ...
    
    @classmethod
    @property
    def CONTAIN(cls) -> SizingType:
        '''Fitting the content size to the page size while maintaining the preferred aspect ratio insofar as possible.'''
        ...
    
    @classmethod
    @property
    def CROP(cls) -> SizingType:
        '''Placing the content on page and crop everything that out of given page size.'''
        ...
    
    ...

