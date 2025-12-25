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

class FontMatcher:
    '''This class allows you to control some parts of the font matching algorithm.'''
    
    def match_font_fallback(self, font_matching_properties : aspose.svg.rendering.fonts.FontMatchingProperties, char_code : int) -> bytes:
        '''This method is called if there is no appropriate font found in the fonts lookup folders.
        It should return true type font based on the ``fontMatchingProperties`` which can render ``charCode``, or ``null`` if such font is not available.
        
        :param font_matching_properties: Properties of the matched font.
        :param char_code: Code of the character which will be rendered using the matched font.
        :returns: A byte array containing the fonts data or ``null``.'''
        ...
    
    ...

class FontMatchingProperties:
    '''This class contains properties which describe the font being matched.'''
    
    @property
    def font_families(self) -> Iterable[str]:
        ...
    
    @property
    def font_style(self) -> str:
        ...
    
    @property
    def font_weight(self) -> int:
        ...
    
    @property
    def font_stretch(self) -> float:
        ...
    
    ...

