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

class SVGOptimizationOptions:
    '''SVGOptimizationOptions is a class for storing options for optimizing SVG documents.'''
    
    @property
    def collapse_groups(self) -> bool:
        ...
    
    @collapse_groups.setter
    def collapse_groups(self, value : bool):
        ...
    
    @property
    def remove_descriptions(self) -> bool:
        ...
    
    @remove_descriptions.setter
    def remove_descriptions(self, value : bool):
        ...
    
    @property
    def remove_empty_attributes(self) -> bool:
        ...
    
    @remove_empty_attributes.setter
    def remove_empty_attributes(self, value : bool):
        ...
    
    @property
    def remove_empty_containers(self) -> bool:
        ...
    
    @remove_empty_containers.setter
    def remove_empty_containers(self, value : bool):
        ...
    
    @property
    def remove_empty_text(self) -> bool:
        ...
    
    @remove_empty_text.setter
    def remove_empty_text(self, value : bool):
        ...
    
    @property
    def remove_hidden_elements(self) -> bool:
        ...
    
    @remove_hidden_elements.setter
    def remove_hidden_elements(self, value : bool):
        ...
    
    @property
    def remove_metadata(self) -> bool:
        ...
    
    @remove_metadata.setter
    def remove_metadata(self, value : bool):
        ...
    
    @property
    def remove_unused_namespaces(self) -> bool:
        ...
    
    @remove_unused_namespaces.setter
    def remove_unused_namespaces(self, value : bool):
        ...
    
    @property
    def remove_unused_defs(self) -> bool:
        ...
    
    @remove_unused_defs.setter
    def remove_unused_defs(self, value : bool):
        ...
    
    @property
    def remove_useless_stroke_and_fill(self) -> bool:
        ...
    
    @remove_useless_stroke_and_fill.setter
    def remove_useless_stroke_and_fill(self, value : bool):
        ...
    
    @property
    def clean_list_of_values(self) -> bool:
        ...
    
    @clean_list_of_values.setter
    def clean_list_of_values(self, value : bool):
        ...
    
    @property
    def remove_indents_and_line_breaks(self) -> bool:
        ...
    
    @remove_indents_and_line_breaks.setter
    def remove_indents_and_line_breaks(self, value : bool):
        ...
    
    @property
    def path_optimization_options(self) -> aspose.svg.toolkit.optimizers.SVGPathOptimizationOptions:
        ...
    
    @path_optimization_options.setter
    def path_optimization_options(self, value : aspose.svg.toolkit.optimizers.SVGPathOptimizationOptions):
        ...
    
    ...

class SVGOptimizer:
    '''SVGOptimizer is a static class designed to optimize SVG documents.
    By optimization, we mean removing unused or invisible elements and their attributes,
    merging groups, and reducing the size of path segments.'''
    
    @overload
    @staticmethod
    def optimize(document : aspose.svg.SVGDocument):
        '''Optimizes :py:class:`aspose.svg.SVGDocument` by applying a set of default optimization options.
        
        :param document: The instance of SVGDocument.'''
        ...
    
    @overload
    @staticmethod
    def optimize(document : aspose.svg.SVGDocumentoptions : aspose.svg.toolkit.optimizers.SVGOptimizationOptions):
        '''Optimizes :py:class:`aspose.svg.SVGDocument` by applying a set of specified optimization options.
        
        :param document: The instance of SVGDocument.
        :param options: The instance of SVGOptimizationOptions.'''
        ...
    
    ...

class SVGPathOptimizationOptions:
    '''SVGPathOptimizationOptions is a class for storing options for optimizing segments of SVG path elements.'''
    
    @property
    def remove_space_after_flags(self) -> bool:
        ...
    
    @remove_space_after_flags.setter
    def remove_space_after_flags(self, value : bool):
        ...
    
    @property
    def apply_transforms(self) -> bool:
        ...
    
    @apply_transforms.setter
    def apply_transforms(self, value : bool):
        ...
    
    @property
    def float_precision(self) -> int:
        ...
    
    @float_precision.setter
    def float_precision(self, value : int):
        ...
    
    @property
    def arc_building_threshold(self) -> float:
        ...
    
    @arc_building_threshold.setter
    def arc_building_threshold(self, value : float):
        ...
    
    @property
    def arc_building_tolerance(self) -> float:
        ...
    
    @arc_building_tolerance.setter
    def arc_building_tolerance(self, value : float):
        ...
    
    ...

