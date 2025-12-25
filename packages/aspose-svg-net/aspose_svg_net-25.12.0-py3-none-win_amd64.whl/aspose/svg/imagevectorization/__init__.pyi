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

class BezierPathBuilder(IPathBuilder):
    '''The :py:class:`aspose.svg.imagevectorization.BezierPathBuilder` class is responsible for constructing a Bezier path from a given set of points.
    It approximates a trace of points with a Bezier curve, optimizing the number of segments to closely
    match the original trace while minimizing complexity.'''
    
    def build(self, trace : Iterable[aspose.pydrawing.PointF]) -> str:
        ...
    
    @property
    def error_threshold(self) -> float:
        ...
    
    @error_threshold.setter
    def error_threshold(self, value : float):
        ...
    
    @property
    def max_iterations(self) -> int:
        ...
    
    @max_iterations.setter
    def max_iterations(self, value : int):
        ...
    
    @property
    def trace_smoother(self) -> aspose.svg.imagevectorization.IImageTraceSmoother:
        ...
    
    @trace_smoother.setter
    def trace_smoother(self, value : aspose.svg.imagevectorization.IImageTraceSmoother):
        ...
    
    ...

class IImageTraceSimplifier:
    '''The IImageTraceSimplifier interface is responsible for reduction of points in the trace.'''
    
    def simplify(self, trace : Iterable[aspose.pydrawing.PointF]) -> Iterable[aspose.pydrawing.PointF]:
        ...
    
    ...

class IImageTraceSmoother:
    '''The IImageTraceSmoother interface is responsible for smoothing trace.'''
    
    def smooth(self, trace : Iterable[aspose.pydrawing.PointF]) -> Iterable[aspose.pydrawing.PointF]:
        ...
    
    ...

class IPathBuilder:
    '''The IPathBuilder interface is responsible for building path segments :py:class:`aspose.svg.paths.SVGPathSeg` from list of the trace points.'''
    
    def build(self, trace : Iterable[aspose.pydrawing.PointF]) -> str:
        ...
    
    ...

class ImageTraceSimplifier(IImageTraceSimplifier):
    '''The ImageTraceSimplifier class is responsible reducing the number of points in a curve that is approximated by a series of the trace points.'''
    
    def simplify(self, trace : Iterable[aspose.pydrawing.PointF]) -> Iterable[aspose.pydrawing.PointF]:
        ...
    
    @property
    def tolerance(self) -> float:
        '''The value of the tolerance determines the maximum error tolerance allowed for an point to be eliminated from trace.
        It must be in the range from 0 to 4. Any higher or lower values will be aligned with the minimum and maximum values of this range, accordingly.
        The default value is 0.3.'''
        ...
    
    @tolerance.setter
    def tolerance(self, value : float):
        '''The value of the tolerance determines the maximum error tolerance allowed for an point to be eliminated from trace.
        It must be in the range from 0 to 4. Any higher or lower values will be aligned with the minimum and maximum values of this range, accordingly.
        The default value is 0.3.'''
        ...
    
    ...

class ImageTraceSmoother(IImageTraceSmoother):
    '''The ImageTraceSimplifier class is responsible for smoothing the number of points in a curve that is approximated by a series of the trace points.
    This class implement nearest-neighbor approach.'''
    
    def smooth(self, trace : Iterable[aspose.pydrawing.PointF]) -> Iterable[aspose.pydrawing.PointF]:
        ...
    
    @property
    def extent(self) -> int:
        '''Gets of sets extent of the region considered by query point.
        It must be in the range from 1 to 20. Any higher or lower values will be aligned with the minimum and maximum values of this range, accordingly.'''
        ...
    
    @extent.setter
    def extent(self, value : int):
        '''Gets of sets extent of the region considered by query point.
        It must be in the range from 1 to 20. Any higher or lower values will be aligned with the minimum and maximum values of this range, accordingly.'''
        ...
    
    ...

class ImageVectorizer:
    '''This ImageVectorizer class vectorizes raster images like PNG, JPG, GIF, BMP and etc... and returns SVGDocument.
    Under vectorization we mean the process of reducing bitmaps to geometric shapes made up from path elements and stored as SVG.'''
    
    @overload
    def vectorize(self, image_file : str) -> aspose.svg.SVGDocument:
        '''Vectorizes raster image from the specified file.
        
        :param image_file: The path to the image file.
        :returns: The SVG document.'''
        ...
    
    @overload
    def vectorize(self, image_stream : io.RawIOBase) -> aspose.svg.SVGDocument:
        '''Vectorizes raster image from the specified stream.
        
        :param image_stream: The stream with image.
        :returns: The SVG document.'''
        ...
    
    @property
    def configuration(self) -> aspose.svg.imagevectorization.ImageVectorizerConfiguration:
        '''The configuration of image vectorization methods and options'''
        ...
    
    @configuration.setter
    def configuration(self, value : aspose.svg.imagevectorization.ImageVectorizerConfiguration):
        '''The configuration of image vectorization methods and options'''
        ...
    
    ...

class ImageVectorizerConfiguration:
    '''The :py:class:`aspose.svg.imagevectorization.ImageVectorizerConfiguration` class defines a configuration of image vectorization methods and options.
    The configuration is used to initialize an ImageVectorizer and provides the configuration options for
    vectorizing images.'''
    
    @property
    def path_builder(self) -> aspose.svg.imagevectorization.IPathBuilder:
        ...
    
    @path_builder.setter
    def path_builder(self, value : aspose.svg.imagevectorization.IPathBuilder):
        ...
    
    @property
    def colors_limit(self) -> int:
        ...
    
    @colors_limit.setter
    def colors_limit(self, value : int):
        ...
    
    @property
    def image_size_limit(self) -> int:
        ...
    
    @image_size_limit.setter
    def image_size_limit(self, value : int):
        ...
    
    @property
    def line_width(self) -> float:
        ...
    
    @line_width.setter
    def line_width(self, value : float):
        ...
    
    @property
    def background_color(self) -> aspose.svg.drawing.Color:
        ...
    
    @background_color.setter
    def background_color(self, value : aspose.svg.drawing.Color):
        ...
    
    @property
    def stencil(self) -> aspose.svg.imagevectorization.StencilConfiguration:
        '''Gets stencil effect configuration.
        By default, no stencil effect is applied.'''
        ...
    
    @stencil.setter
    def stencil(self, value : aspose.svg.imagevectorization.StencilConfiguration):
        '''Sets stencil effect configuration.
        By default, no stencil effect is applied.'''
        ...
    
    ...

class SplinePathBuilder(IPathBuilder):
    '''The :py:class:`aspose.svg.imagevectorization.SplinePathBuilder` class is designed to construct a smooth path by transforming Centripetal Catmull–Rom splines into Bezier curves.
    It offers a method to generate a path that smoothly interpolates through a set of points, providing a balance between fidelity to the points and smoothness of the curve.'''
    
    def build(self, trace : Iterable[aspose.pydrawing.PointF]) -> str:
        ...
    
    @property
    def trace_smoother(self) -> aspose.svg.imagevectorization.IImageTraceSmoother:
        ...
    
    @trace_smoother.setter
    def trace_smoother(self, value : aspose.svg.imagevectorization.IImageTraceSmoother):
        ...
    
    @property
    def trace_simplifier(self) -> aspose.svg.imagevectorization.IImageTraceSimplifier:
        ...
    
    @trace_simplifier.setter
    def trace_simplifier(self, value : aspose.svg.imagevectorization.IImageTraceSimplifier):
        ...
    
    @property
    def tension(self) -> float:
        '''The value of the tensions affects how sharply the curve bends at the (interpolated) control points.
        It must be in the range from 0 to 1. Any higher or lower values will be aligned with the minimum and maximum values of this range, accordingly.'''
        ...
    
    @tension.setter
    def tension(self, value : float):
        '''The value of the tensions affects how sharply the curve bends at the (interpolated) control points.
        It must be in the range from 0 to 1. Any higher or lower values will be aligned with the minimum and maximum values of this range, accordingly.'''
        ...
    
    ...

class StencilConfiguration:
    '''The :py:class:`aspose.svg.imagevectorization.StencilConfiguration` class defines a configuration of stencil effect options.'''
    
    @property
    def type(self) -> aspose.svg.imagevectorization.StencilType:
        '''Gets the :py:class:`aspose.svg.imagevectorization.StencilType`.'''
        ...
    
    @type.setter
    def type(self, value : aspose.svg.imagevectorization.StencilType):
        '''Sets the :py:class:`aspose.svg.imagevectorization.StencilType`.'''
        ...
    
    @property
    def color(self) -> aspose.svg.drawing.Color:
        '''Gets the color for rendering stencil lines for the MonoColor type.'''
        ...
    
    @color.setter
    def color(self, value : aspose.svg.drawing.Color):
        '''Sets the color for rendering stencil lines for the MonoColor type.'''
        ...
    
    ...

class StencilType:
    '''The :py:class:`aspose.svg.imagevectorization.StencilType` enum defines stencil types.'''
    
    @classmethod
    @property
    def NONE(cls) -> StencilType:
        '''The stencil effect will not be applied.'''
        ...
    
    @classmethod
    @property
    def MONO_COLOR(cls) -> StencilType:
        '''Only one color is used for rendering stencil lines.'''
        ...
    
    @classmethod
    @property
    def AUTO(cls) -> StencilType:
        '''The colors for rendering stencil lines detects automatically.'''
        ...
    
    ...

